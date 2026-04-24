---
name: ci-ready-review
description: Standardized code review and CI validation process. Use this skill to ensure Pull Requests are "green" and ready for merge by verifying linting, tests, Docker builds, and security scans.
---

# CI Ready Review

This skill provides a structured workflow for performing code reviews and ensuring that Pull Requests (PRs) pass all project-specific CI checks before being considered ready for merge.

## Prerequisites
- Python >= 3.13.0
- Virtual environment at `.venv`
- Package installed with `pip install -e .[test]`

## Validation Workflow

Follow these steps in order. If any step fails, diagnose the root cause and apply a targeted fix before proceeding.

### 1. Linting (Ruff)
Verify code style and common errors.
- **Command**: `.venv\Scripts\python -m ruff check .`
- **Common Fixes**: Remove unused imports, fix docstrings, ensure imports are at the top of the file.

### 2. Testing & Coverage (Pytest)
Ensure all tests pass and coverage is reported.
- **Command**: `.venv\Scripts\pytest --cov=runtime`
- **Ready Criteria**: All tests must pass (30+ items).

### 3. Docker Build & Health Check
Verify the container builds and starts correctly.
- **Command**: `docker build -t agent-shell:test .`
- **Health Check**: `docker run -d --name test-container -p 8000:8000 agent-shell:test` followed by `curl -f http://localhost:8000/healthz`
- **Common Fixes**: Ensure `Dockerfile` base image matches Python requirement (3.13-slim).

### 4. Security Scanning
Check for vulnerabilities in dependencies.
- **Tool**: Trivy (if available) or review GitHub Security tab.
- **Local Proxy**: `trivy fs .`

## Pull Request Lifecycle

### Status Check
Before finalizing a review, verify the GitHub Actions status:
```bash
gh pr checks <pr-number>
```
All 4 checks must be green:
1. `test / test (3.13)`
2. `test / docker-build`
3. `test / security-scan`
4. `Trivy`

### Review Loop
If GitHub Code Scanning or Reviewers flag issues:
1. **Analyze**: Use `gh pr view <pr-number> --comments` to get specific feedback.
2. **Refactor**: Perform targeted fixes (e.g., replace deprecated calls, inject secrets via env vars).
3. **Verify**: Run `pytest` and `ruff check .` locally to ensure the fix doesn't break state.
4. **Iterate**: Commit and push the fixes; the CI will automatically trigger a new check cycle.

### Debugging Failures
If a check fails in GitHub Actions but passes locally:
1. **Fetch Logs**: `gh run view <run-id> --log`
2. **Environment**: Check if CI is using the correct Python version (>=3.13) or if `Dockerfile` is stale.
3. **Paths**: Verify health check endpoints (`/healthz`).

## "Ready to Merge" Criteria
A PR is considered ready when:
- [ ] Linting passes locally and in CI.
- [ ] All tests pass with adequate coverage.
- [ ] Docker image builds and passes health checks.
- [ ] Security scans are clean.
- [ ] No merge conflicts with `main`.
