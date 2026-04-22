from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request
from runtime.utils import utc_now


class MiddlewareStack:
    def __init__(self, logger):
        self.logger = logger

    def run(self, operation_name: str, payload: dict, handler):
        correlation_id = f"{operation_name}-{utc_now()}"
        start = utc_now()
        self.logger.info("middleware.start operation=%s correlation_id=%s", operation_name, correlation_id)
        result = handler({**payload, "_correlation_id": correlation_id, "_started_at": start})
        self.logger.info("middleware.end operation=%s correlation_id=%s", operation_name, correlation_id)
        return result


def install_http_middleware(app: FastAPI, cfg: dict) -> None:
    service_name = cfg.get("name", "agent-shell-service-runtime")
    enabled_layers = set(cfg.get("middleware", {}).get("enabled", []))
    if not enabled_layers:
        enabled_layers = {"correlation", "logging", "timing"}

    @app.middleware("http")
    async def request_boundary_middleware(request: Request, call_next):
        correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
        started = time.perf_counter()

        if "correlation" in enabled_layers:
            request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Agent-Service"] = service_name
        if "correlation" in enabled_layers:
            response.headers["X-Correlation-Id"] = correlation_id
        if "timing" in enabled_layers:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            response.headers["X-Process-Time-Ms"] = str(duration_ms)
        return response
