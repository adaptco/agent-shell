from __future__ import annotations
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from runtime.api_auth import OperatorIdentity, get_auth_dependency
from runtime.config import load_config
from runtime.middleware import install_http_middleware
from runtime.service import AgentService


class TaskCreateRequest(BaseModel):
    task: str = Field(..., min_length=1)
    parent_task_id: str | None = None
    assigned_subagent: str | None = None


class RunRequest(BaseModel):
    task: str = Field(..., min_length=1)
    backend: str = "mock"


class HeartbeatRequest(BaseModel):
    worker_id: str | None = None


def _error_content(request: Request, detail: object, error: str) -> dict[str, object]:
    return {
        "error": error,
        "detail": detail,
        "correlation_id": getattr(request.state, "correlation_id", None),
    }


def create_app(cfg: dict | None = None) -> FastAPI:
    cfg = cfg or load_config()
    service_auth = get_auth_dependency(cfg)
    service = AgentService(cfg)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.cfg = cfg
        app.state.service = service
        yield

    app = FastAPI(
        title=cfg.get("service", {}).get("title", "Agent Shell Service Runtime API"),
        version=cfg.get("version", "0.0.0"),
        lifespan=lifespan,
    )
    app.state.cfg = cfg
    app.state.service = service

    install_http_middleware(app, cfg)

    def svc(request: Request) -> AgentService:
        return request.app.state.service

    async def auth_operator(
        request: Request,
        operator: OperatorIdentity = Depends(service_auth),
    ) -> OperatorIdentity:
        request.state.auth_context = operator.__dict__
        return operator

    @app.get("/health")
    async def health(
        operator: OperatorIdentity = Depends(auth_operator),
        service: AgentService = Depends(svc),
    ):
        result = service.health()
        result["operator"] = operator.__dict__
        return result

    @app.get("/tasks")
    async def list_tasks(
        limit: int = 100,
        operator: OperatorIdentity = Depends(auth_operator),
        service: AgentService = Depends(svc),
    ):
        result = service.list_tasks(limit=limit)
        result["operator"] = operator.__dict__
        return result

    @app.post("/tasks")
    async def create_task(
        body: TaskCreateRequest,
        operator: OperatorIdentity = Depends(auth_operator),
        service: AgentService = Depends(svc),
    ):
        result = service.queue_add(
            body.task,
            parent_task_id=body.parent_task_id,
            assigned_subagent=body.assigned_subagent,
        )
        result["operator"] = operator.__dict__
        return JSONResponse(status_code=202, content=result)

    @app.get("/tasks/{task_id}")
    async def get_task(
        task_id: str,
        operator: OperatorIdentity = Depends(auth_operator),
        service: AgentService = Depends(svc),
    ):
        result = service.get_task(task_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"task": result, "operator": operator.__dict__}

    @app.post("/run")
    async def run_task(
        body: RunRequest,
        operator: OperatorIdentity = Depends(auth_operator),
        service: AgentService = Depends(svc),
    ):
        result = service.run_task(body.task, body.backend)
        result["operator"] = operator.__dict__
        return result

    @app.get("/heartbeat")
    async def heartbeat_state(
        operator: OperatorIdentity = Depends(auth_operator),
        service: AgentService = Depends(svc),
    ):
        return {"runtime_state": service.get_runtime_state(), "operator": operator.__dict__}

    @app.post("/heartbeat")
    async def emit_heartbeat(
        body: HeartbeatRequest,
        operator: OperatorIdentity = Depends(auth_operator),
        service: AgentService = Depends(svc),
    ):
        result = service.heartbeat(worker_id=body.worker_id)
        return {"runtime_state": result, "operator": operator.__dict__}

    @app.exception_handler(HTTPException)
    async def handled_http_exception(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            headers=exc.headers,
            content=_error_content(request, exc.detail, "HTTPException"),
        )

    @app.exception_handler(RequestValidationError)
    async def handled_validation_exception(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=_error_content(request, exc.errors(), "RequestValidationError"),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=_error_content(request, "Internal server error", type(exc).__name__),
        )

    return app
