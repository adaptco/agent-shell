from __future__ import annotations

import asyncio
from urllib.parse import urlparse

from fastapi.testclient import TestClient

from runtime.api import create_app
from runtime.config import ROOT, load_config
from runtime.mcp_server import build_workspace_mcp_server
from runtime.tools import ToolRegistry
from runtime.utils import read_json


def _enable_mcp_plugin(cfg: dict) -> dict:
    for plugin in cfg["plugins"]["tools"]:
        if plugin["type"] == "mcp":
            plugin["enabled"] = True
    return cfg


def test_mcp_tools_are_disabled_by_default() -> None:
    registry = ToolRegistry(load_config())

    assert "discover_skills" not in registry.registry


def test_mcp_discover_skills_registers_and_executes_when_enabled() -> None:
    registry = ToolRegistry(_enable_mcp_plugin(load_config()))

    result = registry.execute("discover_skills", {"query": "ci-ready"})

    assert "discover_skills" in registry.registry
    assert result["count"] == 1
    assert result["skills"][0]["name"] == "ci-ready-review"


def test_mcp_server_registry_is_explicitly_trusted_and_local_only_without_auth() -> (
    None
):
    servers = read_json(ROOT / "infra" / "mcp_servers.json")
    ids = [server["id"] for server in servers]

    assert ids
    assert len(ids) == len(set(ids))

    for server in servers:
        parsed_url = urlparse(server["url"])
        assert server["trust"] == "explicit"
        assert server["type"] in {"http", "mock"}
        assert server["connection"]["timeout_seconds"] > 0
        assert server["connection"]["pool_size"] > 0

        if server["auth"]["type"] == "none":
            assert parsed_url.hostname in {"127.0.0.1", "localhost"}


def test_workspace_mcp_server_exposes_production_tool_contract() -> None:
    async def list_tools():
        server = build_workspace_mcp_server(load_config())
        return await server.list_tools()

    tools = {tool.name: tool for tool in asyncio.run(list_tools())}

    assert {
        "agent_workspace_health",
        "agent_workspace_list_tasks",
        "agent_workspace_get_task",
        "agent_workspace_list_subagents",
        "agent_workspace_enqueue_task",
        "agent_workspace_run_task",
    }.issubset(tools)
    assert tools["agent_workspace_health"].annotations.readOnlyHint is True
    assert tools["agent_workspace_enqueue_task"].annotations.readOnlyHint is False
    assert tools["agent_workspace_run_task"].annotations.openWorldHint is True
    assert tools["agent_workspace_health"].meta["openai/toolInvocation/invoking"]


def test_workspace_mcp_list_tasks_sanitizes_server_paths() -> None:
    class FakeService:
        def list_tasks(self, limit: int = 100) -> dict:
            return {
                "counts": {"queued": 1, "working": 0, "done": 0, "failed": 0},
                "items": [
                    {
                        "task_id": "a" * 32,
                        "task": "demo",
                        "status": "queued",
                        "path": "C:/server/secret/queue/inbox/task.json",
                    }
                ],
            }

    async def call_list_tasks():
        server = build_workspace_mcp_server(load_config(), service=FakeService())
        _content, structured = await server.call_tool(
            "agent_workspace_list_tasks", {"limit": 5}
        )
        return structured

    structured = asyncio.run(call_list_tasks())

    assert structured["items"][0]["task_id"] == "a" * 32
    assert "path" not in structured["items"][0]


def test_fastapi_mounts_streamable_http_mcp_endpoint() -> None:
    cfg = load_config()
    cfg["auth"]["service_boundary"]["enabled"] = False
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "pytest", "version": "0"},
        },
    }

    with TestClient(create_app(cfg), base_url="http://127.0.0.1:8000") as client:
        response = client.post(
            "/mcp/",
            json=request,
            headers={"accept": "application/json, text/event-stream"},
        )
        tools_response = client.post(
            "/mcp/",
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            headers={"accept": "application/json, text/event-stream"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["serverInfo"]["name"] == "agent-shell-service-runtime"
    assert "tools" in body["result"]["capabilities"]
    assert tools_response.status_code == 200
    tool_names = {tool["name"] for tool in tools_response.json()["result"]["tools"]}
    assert "agent_workspace_health" in tool_names
