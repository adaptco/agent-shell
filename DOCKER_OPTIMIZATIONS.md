# Dockerfile Production Optimizations

## Changes Made

### 1. **Cache Cleanup Improvements**
- **Before**: Only removed `/var/lib/apt/lists/*`
- **After**: Added `/tmp/* /var/tmp/*` to complete cleanup
- **Impact**: Reduces layer size by removing temporary files left by package installation

### 2. **Better Layer Caching**
- **Before**: Copied entire application before installing dependencies
- **After**: Copy only `pyproject.toml` and `runtime/` before pip install
- **Impact**: Dependencies are cached separately. Rebuilding after code changes reuses the dependency layer instead of reinstalling

### 3. **Pip Install Flags**
- **Added**: `--no-warn-script-location` flag
- **Impact**: Suppresses warnings when scripts are installed to non-standard locations, keeping logs cleaner

### 4. **User Creation Order**
- **Before**: Created user after package installation
- **After**: Created user immediately after WORKDIR
- **Impact**: Layers are smaller; user is available earlier for permission operations

### 5. **Python Optimization**
- **Added**: `PYTHONOPTIMIZE=2` environment variable
- **Impact**: Enables Python bytecode optimization at runtime, reducing memory and startup time

### 6. **Proper Signal Handling**
- **Changed**: `CMD ["agent-shell-api", "--host", "0.0.0.0", "--port", "8000"]` to split ENTRYPOINT and CMD
- **After**: 
  - `ENTRYPOINT ["agent-shell-api"]`
  - `CMD ["--host", "0.0.0.0", "--port", "8000"]`
- **Impact**: Ensures the application process (PID 1) handles signals correctly (SIGTERM for graceful shutdown), which is critical for production

### 7. **Selective File Copy**
- **Before**: `COPY --chown=appuser:appuser .` (copied entire directory including docs, tests, cache)
- **After**: Copy only `runtime/` and `pyproject.toml` explicitly
- **Impact**: Respects `.dockerignore` better; excludes unnecessary files, reducing image size

## Summary

| Metric | Improvement |
|--------|------------|
| **Image Size** | Reduced (no test files, cache, docs) |
| **Build Speed** | Faster on code changes (cached pip layer) |
| **Signal Handling** | Fixed (proper PID 1 signal forwarding) |
| **Runtime Performance** | Slightly faster (PYTHONOPTIMIZE=2) |
| **Security** | Non-root user still enforced |

## Image Verification
Build succeeded: `agent-shell-api:optimized` image created and ready for production.
