# Quick Deployment Reference

## Pipeline Triggers

| Workflow | Trigger | Action |
|----------|---------|--------|
| **test.yml** | Push to main/develop, PR | Run tests, lint, build image, security scan |
| **build-and-push.yml** | Push to main, git tags, test completion | Build multi-platform image, push to registry |
| **release.yml** | Changes to pyproject.toml | Create git tag and GitHub release |
| **deploy-staging.yml** | build-and-push completion, manual | Deploy to staging with health checks |
| **deploy-production.yml** | Git tag (v*), manual | Deploy to production with validation |

## Create a Release (for Production Deployment)

```bash
# 1. Update version in pyproject.toml
# version = "0.5.2"

# 2. Commit the change
git add pyproject.toml
git commit -m "Release version 0.5.2"
git push origin main

# Wait for release.yml to create the tag (watch Actions tab)
# This will trigger build-and-push, then deploy-staging, then deploy-production
```

## Manual Deployments

### Deploy Staging (Manual)
```
1. GitHub → Actions → deploy-staging
2. Click "Run workflow"
3. Enter image tag (e.g., "latest", "v0.5.2")
4. Click "Run workflow"
5. Wait for approval (if configured)
```

### Deploy Production (Manual)
```
1. GitHub → Actions → deploy-production
2. Click "Run workflow"
3. Enter image tag (required, e.g., "v0.5.2")
4. Click "Run workflow"
5. Approve in environment protection rules
6. Wait for health checks and smoke tests
```

## Rollback

### Staging Rollback
Automatic on failure. For manual rollback:
```bash
ssh deploy@staging.example.com
cd /app
docker-compose down
git checkout previous-tag  # or revert docker-compose.yml
docker-compose up -d
```

### Production Rollback
Must be manual:
```bash
ssh deploy@api.example.com
cd /app
export IMAGE_TAG=v0.5.1  # Previous version
docker-compose up -d  # Redeploys with old version
```

## Environment Variables

### Staging
Required secrets in GitHub:
- `STAGING_DEPLOY_KEY`: SSH private key (base64)
- `STAGING_DEPLOY_HOST`: e.g., staging.example.com
- `STAGING_DEPLOY_USER`: e.g., deploy

### Production
Required secrets in GitHub:
- `PRODUCTION_DEPLOY_KEY`: SSH private key (base64)
- `PRODUCTION_DEPLOY_HOST`: e.g., api.example.com
- `PRODUCTION_DEPLOY_USER`: e.g., deploy

## Health Checks

Both staging and production run health checks:
```bash
curl -f http://localhost:8000/healthz
```

Timeout: 30 seconds (30 retries × 1 second)

## View Logs

```bash
# Test results
GitHub Actions → test.yml → latest run

# Build logs
GitHub Actions → build-and-push.yml → latest run

# Deployment logs
GitHub Actions → deploy-staging.yml or deploy-production.yml → latest run

# Container logs
ssh deploy@host
docker logs agent-shell-api
docker compose logs -f
```

## Container Registry

Images stored at: `ghcr.io/<username>/<repo-name>`

Pull an image:
```bash
docker login ghcr.io
docker pull ghcr.io/<username>/<repo-name>:v0.5.2
```

List tags:
```bash
docker run --rm alpine/flake8 sh -c 'curl -s https://ghcr.io/v2/<username>/<repo-name>/tags/list | jq .tags'
```

## Supported Image Tags

- `latest` — Latest main branch build
- `main-<commit-sha>` — Specific commit from main
- `v1.2.3` — Release tag (from git tag)
- `develop` — Latest develop branch build

## Example: Full Release Workflow

```bash
# 1. Update version
sed -i 's/version = "0.5.1"/version = "0.5.2"/' pyproject.toml

# 2. Commit and push
git add pyproject.toml
git commit -m "Release version 0.5.2"
git push origin main

# 3. Wait 2-3 minutes for:
#    - test.yml to pass
#    - build-and-push.yml to push image
#    - release.yml to create tag v0.5.2
#    - deploy-staging.yml to deploy automatically

# 4. Verify staging at https://staging-api.example.com/healthz

# 5. Deploy to production (automatic or manual from GitHub)

# 6. Verify production at https://api.example.com/healthz
```

## Troubleshooting Commands

```bash
# Check if image exists
docker pull ghcr.io/<username>/<repo-name>:v0.5.2

# Test health endpoint
curl -v http://localhost:8000/healthz

# View container status
docker ps -a
docker inspect agent-shell-api

# Check container logs
docker logs agent-shell-api
docker logs --tail 100 -f agent-shell-api

# Test network connectivity
docker exec agent-shell-api curl -f http://localhost:8000/healthz

# Check available disk space
docker system df
```

## Resource Limits

Current limits in docker-compose.yml:
```yaml
CPU limit: 2 cores
CPU reserve: 1 core
Memory limit: 2GB
Memory reserve: 1GB
```

To modify:
```bash
# Edit docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
    reservations:
      cpus: '2'
      memory: 2G

# Restart
docker-compose up -d
```

## Pipeline Failure Debugging

### Test fails
```
GitHub Actions → test.yml → latest failed run
→ View job logs
→ Check test output, coverage, linting errors
```

### Build fails
```
Likely: Docker layer caching issue
Fix: Push to main to rebuild with fresh cache
GitHub → Actions → build-and-push.yml → Rerun
```

### Deployment fails
```
1. Check health check endpoint is responding
   ssh deploy@host
   docker logs agent-shell-api

2. Check port is accessible
   docker inspect agent-shell-api | grep PortBindings

3. Check network
   docker network inspect agent-network
```

## Security

- All images scanned with Trivy
- Secrets stored in GitHub Secrets (encrypted)
- SSH keys encrypted in transit
- Container runs as non-root user
- Health checks validate service health before marking as ready
