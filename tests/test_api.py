from __future__ import annotations

import os

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
    assert response.headers["X-Request-ID"]
    assert response.headers["X-Response-Time-Ms"]
    body = response.json()
    assert body["ok"] is True
    assert response.headers["x-agent-service"] == "agent-shell-service-runtime"
    assert response.headers["x-correlation-id"]
    assert response.headers["x-process-time-ms"]


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


<<<<<<< ours
def test_auth_mode_static_bearer_requires_token(monkeypatch):
    cfg = load_config()
    cfg["auth"]["service_boundary"]["enabled"] = True
    cfg["auth"]["service_boundary"]["mode"] = "static_bearer"
    monkeypatch.setenv("AGENT_SERVICE_BEARER_TOKEN", "secret-token")
    client = TestClient(create_app(cfg))

    missing = client.get("/health")
    assert missing.status_code == 401

    ok = client.get("/health", headers={"Authorization": "Bearer secret-token"})
    assert ok.status_code == 200
    assert ok.json()["operator"]["auth_mode"] == "static_bearer"


def test_auth_mode_trusted_proxy_oidc_requires_headers():
=======
def test_service_boundary_static_bearer_auth():
    cfg = load_config()
    cfg["auth"]["service_boundary"]["enabled"] = True
    cfg["auth"]["service_boundary"]["mode"] = "static_bearer"
    client = TestClient(create_app(cfg))
    token = "test-token"
    try:
        os.environ["AGENT_SERVICE_BEARER_TOKEN"] = token
        unauthorized = client.get("/health")
        assert unauthorized.status_code == 401
        authorized = client.get("/health", headers={"Authorization": f"Bearer {token}"})
        assert authorized.status_code == 200
        assert authorized.json()["operator"]["auth_mode"] == "static_bearer"
    finally:
        os.environ.pop("AGENT_SERVICE_BEARER_TOKEN", None)


def test_service_boundary_trusted_proxy_auth():
>>>>>>> theirs
    cfg = load_config()
    cfg["auth"]["service_boundary"]["enabled"] = True
    cfg["auth"]["service_boundary"]["mode"] = "trusted_proxy_oidc"
    client = TestClient(create_app(cfg))
<<<<<<< ours

    missing = client.get("/health")
    assert missing.status_code == 401

    ok = client.get(
        "/health",
        headers={
            "X-Auth-Request-User": "ops-user",
            "X-Auth-Request-Email": "ops@example.com",
            "X-Auth-Request-Groups": "ops,platform",
        },
    )
    assert ok.status_code == 200
    assert ok.json()["operator"]["subject"] == "ops-user"
    assert ok.json()["operator"]["auth_mode"] == "trusted_proxy_oidc"


def test_auth_mode_oidc_jwt_fails_closed_when_unconfigured():
    cfg = load_config()
    cfg["auth"]["service_boundary"]["enabled"] = True
    cfg["auth"]["service_boundary"]["mode"] = "oidc_jwt"
    client = TestClient(create_app(cfg))
    response = client.get("/health", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 500
=======
    unauthorized = client.get("/health")
    assert unauthorized.status_code == 401
    authorized = client.get(
        "/health",
        headers={"x-auth-request-user": "operator-1", "x-auth-request-email": "operator@example.com"},
    )
    assert authorized.status_code == 200
    assert authorized.json()["operator"]["subject"] == "operator-1"
    assert authorized.json()["operator"]["auth_mode"] == "trusted_proxy_oidc"
>>>>>>> theirs
