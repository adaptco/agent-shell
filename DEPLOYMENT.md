# Deployment Pipeline Guide

This document describes the deployment pipeline for the agent-shell-service-runtime application.

## Pipeline Overview

The deployment pipeline consists of five GitHub Actions workflows that work together to test, build, push, and deploy your application.

```
Commit to main/develop
         ↓
    ┌─────────────────────────────────────┐
    │      test.yml                       │
    ├─────────────────────────────────────┤
    │ • Run pytest with coverage          │
    │ • Lint with Ruff                    │
    │ • Build Docker image                │
    │ • Health check container            │
    │ • Security scan (Trivy)             │
    └─────────────────────────────────────┘
         ↓ (on success)
    ┌─────────────────────────────────────┐
    │    build-and-push.yml               │
    ├─────────────────────────────────────┤
    │ • Multi-platform build (AMD64/ARM64)│
    │ • Push to ghcr.io                   │
    │ • Cache with GitHub Actions         │
    └─────────────────────────────────────┘
         ↓
    ┌─────────────────────────────────────┐
    │   deploy-staging.yml                │
    ├─────────────────────────────────────┤
    │ • Deploy latest to staging          │
    │ • Health checks                     │
    │ • Smoke tests                       │
    │ • Auto-rollback on failure          │
    └─────────────────────────────────────┘
              ↓
    Create git tag (vX.Y.Z)
              ↓
    ┌─────────────────────────────────────┐
    │   deploy-production.yml             │
    ├─────────────────────────────────────┤
    │ • Validate image                    │
    │ • Deploy to production              │
    │ • Health checks                     │
    │ • Smoke tests                       │
    │ • Alert on failure                  │
    └─────────────────────────────────────┘
```

## Workflow Details

### 1. test.yml - Testing & Validation

**Triggers:** Push to main/develop, Pull requests

**Jobs:**
- **test**: Runs unit tests with coverage analysis on Python 3.13
- **docker-build**: Builds and tests Docker image with health check
- **security-scan**: Runs Trivy to scan for vulnerabilities

**Key Features:**
- Single-version Python testing (3.13)
- Code coverage tracking with Codecov
- Ruff linting
- Trivy security scanning with SARIF report upload
- Container health check validation

### 2. build-and-push.yml - Docker Build & Registry Push

**Triggers:** Push to main, git tags, workflow completion of test.yml

**Jobs:**
- **build**: Builds multi-platform image and pushes to GitHub Container Registry

**Key Features:**
- Multi-platform builds (linux/amd64, linux/arm64)
- Automatic tag generation:
  - Branch: `main`, `develop`
  - Tags: `v1.2.3`
  - SHAs: `main-abc123def`
  - Latest: `latest` (for main branch)
- GitHub Actions cache for faster builds
- Metadata extraction using docker/metadata-action

**Registry:** ghcr.io/${{ github.repository }}

### 3. release.yml - Version Management

**Triggers:** Changes to pyproject.toml on main branch

**Jobs:**
- **check-version**: Extracts version from pyproject.toml, checks if tag exists
- **create-release**: Creates git tag and GitHub release
- **notify**: Reports status

**Key Features:**
- Automatic version extraction from pyproject.toml
- Prevents duplicate releases
- Creates GitHub Release

### 4. deploy-staging.yml - Staging Deployment

**Triggers:** Workflow completion of build-and-push.yml, manual dispatch

**Jobs:**
- **deploy**: Deploys to staging environment
- **rollback**: Automatic rollback on failure

**Key Features:**
- Health check with retry logic (30 attempts, 5s intervals)
- Smoke tests support
- Automatic rollback on failure
- Creates GitHub issue on failure
- Manual trigger with custom image tag

**Environment Secrets Required:**
- `STAGING_DEPLOY_KEY`: SSH private key
- `STAGING_DEPLOY_HOST`: Deployment host
- `STAGING_DEPLOY_USER`: SSH user

### 5. deploy-production.yml - Production Deployment

**Triggers:** Push of git tags (v*), manual dispatch

**Jobs:**
- **validate**: Ensures image exists in registry
- **deploy**: Deploys to production
- **rollback**: Alerts on failure (requires manual intervention)

**Key Features:**
- Image validation before deployment
- Health checks with longer intervals (10s)
- Smoke tests
- Release notes update
- Oncall alert on failure
- Requires environment approval

**Environment Secrets Required:**
- `PRODUCTION_DEPLOY_KEY`: SSH private key
- `PRODUCTION_DEPLOY_HOST`: Deployment host
- `PRODUCTION_DEPLOY_USER`: SSH user

## Setup Instructions

### 1. GitHub Secrets Configuration

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

**Staging Secrets:**
```
STAGING_DEPLOY_KEY      # SSH private key for staging server
STAGING_DEPLOY_HOST     # e.g., staging.example.com
STAGING_DEPLOY_USER     # e.g., deploy
```

**Production Secrets:**
```
PRODUCTION_DEPLOY_KEY   # SSH private key for production server
PRODUCTION_DEPLOY_HOST  # e.g., api.example.com
PRODUCTION_DEPLOY_USER  # e.g., deploy
```

### 2. GitHub Environment Protection Rules

Create two environments in GitHub (Settings → Environments):

**staging**
- No protection rules required
- Optional: Add approvers for manual deployments

**production**
- Required reviewers (recommended: at least 2)
- Deployment branches: main
- Custom deployment branches disabled

### 3. Deploy Server Setup

On your deploy servers, ensure:

1. Docker and Docker Compose are installed
2. SSH key is added to `~/.ssh/authorized_keys`
3. User can run docker commands (add to docker group)
4. Create deployment directory (e.g., `/app`)

Example setup script:
```bash
#!/bin/bash
mkdir -p /app
cd /app

# Create environment file
cat > .env << EOF
REGISTRY_OWNER=<github-username-or-org>
REGISTRY_REPO=<repo-name>
IMAGE_TAG=latest
API_PORT=8000
LOG_LEVEL=info
EOF

# Create docker-compose.yml (use production version)
# Copy from your repo

# Start service
docker-compose up -d
```

### 4. SSH Key Setup

Generate SSH key pair for deployments:

```bash
ssh-keygen -t rsa -b 4096 -f deployment_key -N ""
```

Add public key to deploy servers:
```bash
cat deployment_key.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Add private key as GitHub secret:
```bash
cat deployment_key | base64 | xclip -selection clipboard
# Paste into STAGING_DEPLOY_KEY or PRODUCTION_DEPLOY_KEY
```

### 5. Docker Compose Configuration

Use the provided `docker-compose.yml` which includes:

- Volume management for persistent data
- Health checks
- Resource limits (CPU/Memory)
- Network isolation
- Production-ready configuration

Deploy with:
```bash
export IMAGE_TAG=v1.2.3
docker-compose up -d
```

## Manual Deployments

### Deploy Staging (Custom Tag)

1. Go to Actions → deploy-staging
2. Click "Run workflow"
3. Enter image tag (default: latest)
4. Confirm

### Deploy Production (Custom Tag)

1. Go to Actions → deploy-production
2. Click "Run workflow"
3. Enter image tag (required, e.g., v1.2.3)
4. Confirm
5. Approve deployment in environment

## Monitoring & Alerts

### Health Checks
- Staging: 30s interval, 3 retries
- Production: 30s interval, 3 retries

### Smoke Tests
Customize in the deploy workflows:
```yaml
- name: Smoke tests
  run: |
    curl -f https://api.example.com/healthz
    curl -f https://api.example.com/api/status
```

### Failure Alerts
- Staging: GitHub Issue created
- Production: GitHub Issue + requires manual intervention

## Troubleshooting

### Build fails with rate limit
- Ensure `cache-from: type=gha` and `cache-to: type=gha,mode=max` are set
- Consider enabling Docker Build Cloud (set `ENABLE_DOCKER_BUILD_CLOUD=true` in repo settings)

### Deployment health check times out
1. Check container logs: `docker logs agent-shell-api`
2. Verify port is accessible: `curl http://localhost:8000/healthz`
3. Check network: `docker network inspect agent-network`

### SSH deployment fails
1. Verify SSH key is in `authorized_keys`: `cat ~/.ssh/authorized_keys`
2. Test SSH manually: `ssh -i key user@host docker ps`
3. Check deploy user has docker permissions: `groups $USER`

### Image not found in registry
1. Check build status in Actions tab
2. Verify image pushed: `docker pull ghcr.io/username/repo:tag`
3. Check registry permissions in GitHub

## Rollback Procedures

### Staging Rollback
Automatic on deployment failure. Manual rollback:
```bash
ssh deploy@staging.example.com
cd /app
docker-compose down
docker-compose up -d  # Or previous version
```

### Production Rollback (Manual)
On production deployment failure, you must manually intervene:

1. SSH to production server
2. Revert docker-compose configuration or image tag
3. Restart service: `docker-compose up -d`
4. Verify health: `curl https://api.example.com/healthz`

## Performance Optimization

### Build Cache
- Uses GitHub Actions Cache
- Optional: Enable Docker Build Cloud for 50% faster builds
- Set `ENABLE_DOCKER_BUILD_CLOUD=true` in repository variables

### Multi-platform Builds
- Builds for AMD64 and ARM64 in parallel
- Requires buildx setup (automated by docker/setup-buildx-action)

### Test Parallelization
- Tests run on Python 3.13 in parallel
- Docker build and security scan run in parallel

## Next Steps

1. Update deployment host URLs and secrets
2. Configure health check endpoints
3. Add smoke tests specific to your API
4. Set up environment approval rules in GitHub
5. Test with manual deployment workflow
6. Monitor first few automatic deployments
