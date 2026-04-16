from __future__ import annotations
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from runtime.api_auth import OperatorIdentity, get_auth_dependency
from runtime.config import load_config
<<<<<<< ours
from runtime.logger import get_logger
from runtime.middleware import APIMiddleware
=======
from runtime.middleware import install_http_middleware
>>>>>>> theirs
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


def create_app(cfg: dict | None = None) -> FastAPI:
    cfg = cfg or load_config()
    service_auth = get_auth_dependency(cfg)
    logger = get_logger(cfg)
    service_name = cfg.get("name", "agent-shell-service-runtime")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.cfg = cfg
        app.state.service = AgentService(cfg)
        yield

    app = FastAPI(
        title=cfg.get("service", {}).get("title", "Agent Shell Service Runtime API"),
        version=cfg.get("version", "0.0.0"),
        lifespan=lifespan,
    )
    app.state.cfg = cfg
    app.state.service = AgentService(cfg)

<<<<<<< ours
    app.middleware("http")(APIMiddleware(logger, service_name))
=======
    install_http_middleware(app, cfg)
>>>>>>> theirs

    def svc(request: Request) -> AgentService:
        return request.app.state.service

    def _set_auth_context(request: Request, operator: OperatorIdentity) -> None:
        request.state.auth_context = operator.__dict__

    @app.get("/health")
    async def health(request: Request, operator: OperatorIdentity = Depends(service_auth), service: AgentService = Depends(svc)):
        _set_auth_context(request, operator)
        result = service.health()
        result["operator"] = operator.__dict__
        return result

    @app.get("/tasks")
    async def list_tasks(request: Request, limit: int = 100, operator: OperatorIdentity = Depends(service_auth), service: AgentService = Depends(svc)):
        _set_auth_context(request, operator)
        result = service.list_tasks(limit=limit)
        result["operator"] = operator.__dict__
        return result

    @app.post("/tasks")
    async def create_task(request: Request, body: TaskCreateRequest, operator: OperatorIdentity = Depends(service_auth), service: AgentService = Depends(svc)):
        _set_auth_context(request, operator)
        result = service.queue_add(body.task, parent_task_id=body.parent_task_id, assigned_subagent=body.assigned_subagent)
        result["operator"] = operator.__dict__
        return JSONResponse(status_code=202, content=result)

    @app.get("/tasks/{task_id}")
    async def get_task(request: Request, task_id: str, operator: OperatorIdentity = Depends(service_auth), service: AgentService = Depends(svc)):
        _set_auth_context(request, operator)
        result = service.get_task(task_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"task": result, "operator": operator.__dict__}

    @app.post("/run")
    async def run_task(request: Request, body: RunRequest, operator: OperatorIdentity = Depends(service_auth), service: AgentService = Depends(svc)):
        _set_auth_context(request, operator)
        result = service.run_task(body.task, body.backend)
        result["operator"] = operator.__dict__
        return result

    @app.get("/heartbeat")
    async def heartbeat_state(request: Request, operator: OperatorIdentity = Depends(service_auth), service: AgentService = Depends(svc)):
        _set_auth_context(request, operator)
        return {"runtime_state": service.get_runtime_state(), "operator": operator.__dict__}

    @app.post("/heartbeat")
    async def emit_heartbeat(request: Request, body: HeartbeatRequest, operator: OperatorIdentity = Depends(service_auth), service: AgentService = Depends(svc)):
        _set_auth_context(request, operator)
        result = service.heartbeat(worker_id=body.worker_id)
        return {"runtime_state": result, "operator": operator.__dict__}

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": type(exc).__name__,
                "detail": str(exc),
                "correlation_id": getattr(request.state, "correlation_id", None),
            },
        )

    return app
