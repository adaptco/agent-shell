from fastapi.testclient import TestClient
from runtime.api import create_app


def test_root_redirect():
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/docs"


def test_healthz_alias():
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/healthz")
        assert response.status_code == 200
        assert "ok" in response.json()


def test_task_not_found_detail():
    app = create_app()
    with TestClient(app) as client:
        task_id = "missing-task-123"
        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == 404
        assert f"Task not found: {task_id}" == response.json()["detail"]
