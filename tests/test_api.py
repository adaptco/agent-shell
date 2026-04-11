from __future__ import annotations

from fastapi.testclient import TestClient

from runtime.api import create_app
from runtime.config import load_config


def _client():
    cfg = load_config()
    cfg["auth"]["service_boundary"]["enabled"] = False
    return TestClient(create_app(cfg))


def test_health_endpoint():
    client = _client()
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True


def test_tasks_endpoint_and_lookup():
    client = _client()
    queued = client.post("/tasks", json={"task": "Read agent.md"})
    assert queued.status_code == 202
    task_id = queued.json()["task_id"]
    listing = client.get("/tasks")
    assert listing.status_code == 200
    lookup = client.get(f"/tasks/{task_id}")
    assert lookup.status_code == 200
    assert lookup.json()["task"]["task_id"] == task_id


def test_run_endpoint():
    client = _client()
    response = client.post("/run", json={"task": "Read the agent file", "backend": "mock"})
    assert response.status_code == 200
    assert response.json()["result"]["status"] == "done"


def test_heartbeat_endpoints():
    client = _client()
    get_resp = client.get("/heartbeat")
    assert get_resp.status_code == 200
    post_resp = client.post("/heartbeat", json={"worker_id": "api-test"})
    assert post_resp.status_code == 200
    assert post_resp.json()["runtime_state"]["last_worker_id"] == "api-test"
