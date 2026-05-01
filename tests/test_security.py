from __future__ import annotations
from fastapi.testclient import TestClient
from runtime.api import create_app
from runtime.config import load_config
from runtime.utils import is_valid_id


def test_is_valid_id():
    assert is_valid_id("a" * 32)
    assert is_valid_id("0123456789abcdef" * 2)
    assert not is_valid_id("*")
    assert not is_valid_id(".." * 16)
    assert not is_valid_id("a" * 31)
    assert not is_valid_id("a" * 33)
    assert not is_valid_id("G" * 32)


def test_api_glob_injection_prevention():
    cfg = load_config()
    cfg["auth"]["service_boundary"]["enabled"] = False
    client = TestClient(create_app(cfg))

    # Enqueue a task
    queued = client.post("/tasks", json={"task": "Secret task"})
    assert queued.status_code == 202

    # Try to access via glob
    resp = client.get("/tasks/*")
    assert resp.status_code == 400

    resp = client.get("/tasks/*?stream=true")  # actually /stream is separate but similar
    # Testing the stream endpoint specifically
    resp = client.get("/tasks/*/stream")
    assert resp.status_code == 400


def test_queue_fs_get_task_security():
    from runtime.queue_fs import FileTaskQueue
    from runtime.config import load_config

    cfg = load_config()
    queue = FileTaskQueue(cfg, {})  # dummy schema

    # Should not find anything with invalid ID
    assert queue.get_task("*") is None
    assert queue.get_task(".." * 16) is None
