# Stage 1: Build dependencies
FROM python:3.13-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy only dependency files first (better layer caching)
COPY pyproject.toml .
COPY runtime ./runtime

# Install Python dependencies and package with explicit pip caching disabled
RUN pip install --user --no-cache-dir --no-warn-script-location \
    --upgrade pip setuptools wheel && \
    pip install --user --no-cache-dir --no-warn-script-location .

# Stage 2: Runtime
FROM python:3.13-slim

WORKDIR /app

# ... (omitted for brevity)

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Expose port
EXPOSE 8000

# Use exec form for proper signal handling
ENTRYPOINT ["agent-shell-api"]
CMD ["--host", "0.0.0.0", "--port", "8000"]
