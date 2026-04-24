from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    return subprocess.run([sys.executable, "-m", "runtime.cli", *args], cwd=ROOT, capture_output=True, text=True, check=True)


def test_doctor():
    out = run("doctor")
    data = json.loads(out.stdout)
    assert data["ok"] is True


def test_run_task_file_read():
    out = run("run-task", "--backend", "mock", "--task", "Read the agent file")
    data = json.loads(out.stdout)
    assert data["result"]["status"] == "done"


def test_run_task_bash():
    out = run("run-task", "--backend", "mock", "--task", "List the workspace directory")
    data = json.loads(out.stdout)
    assert data["result"]["status"] == "done"


def test_run_task_web_search():
    out = run("run-task", "--backend", "mock", "--task", "Search the web for runtime architecture")
    data = json.loads(out.stdout)
    assert data["result"]["status"] == "done"


def test_delegate():
    out = run("run-task", "--backend", "mock", "--task", "Delegate this bounded file task to a subagent")
    data = json.loads(out.stdout)
    assert data["result"]["status"] == "done"
