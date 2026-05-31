from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from runtime.config import load_config, resolve_path
from runtime.service import AgentService
from runtime.utils import is_valid_id

MAX_TASK_LIMIT = 100


def _sanitize_task(task: dict[str, Any] | None) -> dict[str, Any] | None:
    if task is None:
        return None
    return {key: value for key, value in task.items() if key != "path"}


def _sanitize_task_list(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "counts": result.get("counts", {}),
        "items": [_sanitize_task(item) for item in result.get("items", [])],
    }


def _subagent_name(path: Path) -> str:
    return path.stem


def _list_subagents(cfg: dict[str, Any]) -> list[dict[str, str]]:
    subagent_dir = resolve_path(cfg, cfg["subagent_dir"])
    if not subagent_dir.exists():
        return []
    subagents = []
    for path in sorted(subagent_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        first_heading = next(
            (line.lstrip("#").strip() for line in text.splitlines() if line.startswith("#")),
            _subagent_name(path),
        )
        subagents.append(
            {
                "name": _subagent_name(path),
                "title": first_heading,
                "description": text[:500],
            }
        )
    return subagents


def _ensure_known_subagent(cfg: dict[str, Any], assigned_subagent: str | None) -> None:
    if assigned_subagent is None:
        return
    known = {subagent["name"] for subagent in _list_subagents(cfg)}
    if assigned_subagent not in known:
        raise ValueError(f"unknown subagent: {assigned_subagent}")


def build_workspace_mcp_server(
    cfg: dict[str, Any] | None = None,
    service: AgentService | None = None,
) -> FastMCP:
    cfg = cfg or load_config()
    service = service or AgentService(cfg)
    mcp_cfg = cfg.get("mcp", {})
    server = FastMCP(
        cfg.get("name", "agent-shell-service-runtime"),
        instructions=(
            "Agent Shell exposes workspace orchestration tools for queueing, "
            "inspecting, and running agent work. Use mutating tools only when the "
            "operator intends to create or execute workspace tasks."
        ),
        host=cfg.get("service", {}).get("host", "127.0.0.1"),
        streamable_http_path="/",
        stateless_http=bool(mcp_cfg.get("stateless_http", True)),
        json_response=bool(mcp_cfg.get("json_response", True)),
    )

    read_only = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
    mutating = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    )
    execution = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    )

    @server.tool(
        name="agent_workspace_health",
        title="Agent Workspace Health",
        description="Use this when you need the current Agent Shell workspace health, queue counts, and runtime status.",
        annotations=read_only,
        meta={
            "openai/toolInvocation/invoking": "Checking workspace",
            "openai/toolInvocation/invoked": "Workspace checked",
        },
    )
    def agent_workspace_health() -> dict[str, Any]:
        return service.health()

    @server.tool(
        name="agent_workspace_list_tasks",
        title="List Agent Workspace Tasks",
        description="Use this when you need recent queued, working, completed, or failed tasks for the active workspace.",
        annotations=read_only,
        meta={
            "openai/toolInvocation/invoking": "Listing tasks",
            "openai/toolInvocation/invoked": "Tasks listed",
        },
    )
    def agent_workspace_list_tasks(limit: int = 20) -> dict[str, Any]:
        bounded_limit = max(1, min(int(limit), MAX_TASK_LIMIT))
        return _sanitize_task_list(service.list_tasks(limit=bounded_limit))

    @server.tool(
        name="agent_workspace_get_task",
        title="Get Agent Workspace Task",
        description="Use this when you need details for one task by its 32-character task ID.",
        annotations=read_only,
        meta={
            "openai/toolInvocation/invoking": "Getting task",
            "openai/toolInvocation/invoked": "Task loaded",
        },
    )
    def agent_workspace_get_task(task_id: str) -> dict[str, Any]:
        if not is_valid_id(task_id):
            raise ValueError("task_id must be a 32-character lowercase hex string")
        return {"task": _sanitize_task(service.get_task(task_id))}

    @server.tool(
        name="agent_workspace_list_subagents",
        title="List Agent Workspace Subagents",
        description="Use this when you need the available specialist subagents and their local role descriptions.",
        annotations=read_only,
        meta={
            "openai/toolInvocation/invoking": "Listing subagents",
            "openai/toolInvocation/invoked": "Subagents listed",
        },
    )
    def agent_workspace_list_subagents() -> dict[str, Any]:
        return {"subagents": _list_subagents(cfg)}

    @server.tool(
        name="agent_workspace_enqueue_task",
        title="Enqueue Agent Workspace Task",
        description="Use this when the operator wants to create a durable queued task for later worker execution.",
        annotations=mutating,
        meta={
            "openai/toolInvocation/invoking": "Queueing task",
            "openai/toolInvocation/invoked": "Task queued",
        },
    )
    def agent_workspace_enqueue_task(
        task: str,
        parent_task_id: str | None = None,
        assigned_subagent: str | None = None,
    ) -> dict[str, Any]:
        if parent_task_id is not None and not is_valid_id(parent_task_id):
            raise ValueError("parent_task_id must be a 32-character lowercase hex string")
        _ensure_known_subagent(cfg, assigned_subagent)
        queued = service.queue_add(
            task,
            parent_task_id=parent_task_id,
            assigned_subagent=assigned_subagent,
        )
        return {"queued": True, "task_id": queued["task_id"]}

    @server.tool(
        name="agent_workspace_run_task",
        title="Run Agent Workspace Task",
        description="Use this when the operator wants to execute a task immediately through the Agent Shell runtime loop.",
        annotations=execution,
        meta={
            "openai/toolInvocation/invoking": "Running task",
            "openai/toolInvocation/invoked": "Task run complete",
        },
    )
    def agent_workspace_run_task(
        task: str,
        backend: str = "mock",
        assigned_subagent: str | None = None,
    ) -> dict[str, Any]:
        _ensure_known_subagent(cfg, assigned_subagent)
        return service.run_task(task, backend, subagent_name=assigned_subagent)

    return server
