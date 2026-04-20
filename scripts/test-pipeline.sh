#!/bin/bash
# Local deployment pipeline test script
# Tests the deployment pipeline without pushing to remote

set -e

REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")
VERSION=$(grep -oP 'version = "\K[^"]+' pyproject.toml)
IMAGE_TAG="test-${VERSION}-$(date +%s)"
REGISTRY="ghcr.io/$(git config --get remote.origin.url | cut -d: -f2 | cut -d/ -f1)"
IMAGE="${REGISTRY}/${REPO_NAME}:${IMAGE_TAG}"

echo "🧪 Local Deployment Pipeline Test"
echo "=================================="
echo "Repository: $REPO_NAME"
echo "Version: $VERSION"
echo "Image: $IMAGE"
echo ""

# Step 1: Run tests
echo "📋 Step 1: Running tests..."
python -m pip install -q pytest pytest-cov ruff 2>/dev/null || true
python -m pytest -q . || exit 1
echo "✅ Tests passed"
echo ""

# Step 2: Lint
echo "🔍 Step 2: Linting..."
python -m ruff check . || exit 1
echo "✅ Lint passed"
echo ""

# Step 3: Build Docker image
echo "🏗️  Step 3: Building Docker image..."
docker build -t "${IMAGE}" . || exit 1
echo "✅ Docker build succeeded"
echo ""

# Step 4: Container health check
echo "💊 Step 4: Container health check..."
CONTAINER_ID=$(docker run -d -p 8000:8000 "${IMAGE}")
trap "docker stop ${CONTAINER_ID} && docker rm ${CONTAINER_ID}" EXIT

for i in {1..12}; do
  if curl -sf http://localhost:8000/healthz >/dev/null 2>&1; then
    echo "✅ Container health check passed"
    break
  fi
  if [ $i -eq 12 ]; then
    echo "❌ Container health check failed"
    docker logs "${CONTAINER_ID}"
    exit 1
  fi
  echo "⏳ Waiting for container... ($i/12)"
  sleep 5
done
echo ""

# Step 5: Security scan (if trivy is available)
if command -v trivy &> /dev/null; then
  echo "🔐 Step 5: Security scan..."
  trivy fs . --quiet || true
  echo "✅ Security scan completed"
else
  echo "⏭️  Step 5: Skipping security scan (trivy not installed)"
fi
echo ""

# Summary
echo "✅ All pipeline checks passed!"
echo ""
echo "Next steps:"
echo "1. Push changes to GitHub"
echo "2. GitHub Actions will run the full pipeline"
echo "3. Image will be tagged as: ${REGISTRY}/${REPO_NAME}:main-<commit-sha>"
echo "4. Deploy to staging: image will be deployed automatically"
echo "5. Create git tag (v${VERSION}) to trigger production deployment"
echo ""
echo "Create release:"
echo "  git tag v${VERSION}"
echo "  git push origin v${VERSION}"
