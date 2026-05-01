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

# Install runtime dependencies (like curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy from builder
COPY --from=builder /root/.local /root/.local

# Copy necessary configuration and asset directories
COPY infra ./infra
COPY tools ./tools
COPY configs ./configs
COPY skill ./skill

# Ensure the installed package scripts are in the PATH
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Use exec form for proper signal handling
ENTRYPOINT ["agent-shell-api"]
CMD ["--host", "0.0.0.0", "--port", "8000"]
