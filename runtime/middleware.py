from __future__ import annotations

<<<<<<< ours
from time import perf_counter
from uuid import uuid4

=======
import time
import uuid

from fastapi import FastAPI, Request
>>>>>>> theirs
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


<<<<<<< ours
class APIMiddleware:
    def __init__(self, logger, service_name: str):
        self.logger = logger
        self.service_name = service_name

    async def __call__(self, request, call_next):
        request_id = request.headers.get("x-request-id") or uuid4().hex
        request.state.request_id = request_id
        request.state.auth_context = None
        start = perf_counter()

        self.logger.info(
            "api.request.start request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )
        response = await call_next(request)
        duration_ms = round((perf_counter() - start) * 1000, 2)

        auth_context = getattr(request.state, "auth_context", None) or {}
        subject = auth_context.get("subject", "anonymous")
        auth_mode = auth_context.get("auth_mode", "unknown")
        self.logger.info(
            "api.request.end request_id=%s status=%s duration_ms=%.2f subject=%s auth_mode=%s",
            request_id,
            response.status_code,
            duration_ms,
            subject,
            auth_mode,
        )
        response.headers["X-Agent-Service"] = self.service_name
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(duration_ms)
=======
def install_http_middleware(app: FastAPI, cfg: dict) -> None:
    service_name = cfg.get("name", "agent-shell-service-runtime")

    @app.middleware("http")
    async def request_boundary_middleware(request: Request, call_next):
        correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Agent-Service"] = service_name
        response.headers["X-Correlation-Id"] = correlation_id
        response.headers["X-Process-Time-Ms"] = str(duration_ms)
>>>>>>> theirs
        return response
