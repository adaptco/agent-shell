# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

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
FROM python:3.11-slim

WORKDIR /app

# Create non-root user first (layers are smaller this way)
RUN useradd -m -u 1000 appuser

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create runtime storage directories with proper permissions
RUN mkdir -p .runtime-store/objects/{queue,logs,memory,receipts,state} && \
    chown -R appuser:appuser .runtime-store

# Copy installed Python packages from builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser runtime ./runtime
COPY --chown=appuser:appuser infra ./infra
COPY --chown=appuser:appuser schemas ./schemas
COPY --chown=appuser:appuser tools ./tools
COPY --chown=appuser:appuser hooks ./hooks
COPY --chown=appuser:appuser subagents ./subagents
COPY --chown=appuser:appuser skill ./skill
COPY --chown=appuser:appuser configs ./configs
COPY --chown=appuser:appuser agent.md .
COPY --chown=appuser:appuser pyproject.toml .

# Set environment variables (production-optimized)
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:$PYTHONPATH \
    PYTHONOPTIMIZE=2

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Expose port
EXPOSE 8000

# Use exec form for proper signal handling
ENTRYPOINT ["agent-shell-api"]
CMD ["--host", "0.0.0.0", "--port", "8000"]
