from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request

from runtime.logger import get_logger
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


class APIMiddleware:
    def __init__(self, logger, service_name: str, enabled_layers: set[str] | None = None):
        self.logger = logger
        self.service_name = service_name
        self.enabled_layers = enabled_layers or {"correlation", "logging", "timing"}

    async def __call__(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid4().hex
        correlation_id = request.headers.get("x-correlation-id") or request_id

        request.state.request_id = request_id
        request.state.auth_context = None
        if "correlation" in self.enabled_layers:
            request.state.correlation_id = correlation_id

        start = perf_counter()
        if "logging" in self.enabled_layers:
            self.logger.info(
                "api.request.start request_id=%s correlation_id=%s method=%s path=%s",
                request_id,
                correlation_id,
                request.method,
                request.url.path,
            )

        response = await call_next(request)
        duration_ms = round((perf_counter() - start) * 1000, 2)

        if "logging" in self.enabled_layers:
            auth_context = getattr(request.state, "auth_context", None) or {}
            subject = auth_context.get("subject", "anonymous")
            auth_mode = auth_context.get("auth_mode", "unknown")
            self.logger.info(
                "api.request.end request_id=%s correlation_id=%s status=%s duration_ms=%.2f subject=%s auth_mode=%s",
                request_id,
                correlation_id,
                response.status_code,
                duration_ms,
                subject,
                auth_mode,
            )

        response.headers["X-Agent-Service"] = self.service_name
        response.headers["X-Request-ID"] = request_id
        if "correlation" in self.enabled_layers:
            response.headers["X-Correlation-Id"] = correlation_id
        if "timing" in self.enabled_layers:
            # Keep both header names for backward compatibility.
            response.headers["X-Response-Time-Ms"] = str(duration_ms)
            response.headers["X-Process-Time-Ms"] = str(duration_ms)
        return response


def install_http_middleware(app: FastAPI, cfg: dict) -> None:
    service_name = cfg.get("name", "agent-shell-service-runtime")
    enabled_layers = set(cfg.get("middleware", {}).get("enabled", []))
    if not enabled_layers:
        enabled_layers = {"correlation", "logging", "timing"}
    logger = get_logger(cfg)
    app.middleware("http")(APIMiddleware(logger, service_name, enabled_layers))
