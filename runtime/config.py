from pathlib import Path
from typing import Any, Dict
from runtime.utils import read_json, write_json

ROOT = Path(__file__).resolve().parents[1]


def load_config(root: Path | None = None) -> Dict[str, Any]:
    workspace = root or ROOT
    data = read_json(workspace / "infra" / "runtime.json")
    data["_workspace"] = str(workspace)
    ensure_runtime_storage(data)
    return data


def resolve_path(cfg: Dict[str, Any], relative_path: str) -> Path:
    return Path(cfg["_workspace"]) / relative_path


def _default_runtime_state() -> Dict[str, Any]:
    return {
        "status": "idle",
        "last_heartbeat": None,
        "last_task_id": None,
        "last_worker_id": None,
        "memory": {
            "entries": 0,
            "last_compaction": None,
        },
    }


def _default_markdown_state() -> str:
    return (
        "# Agent State\n\n"
        "## Status\n"
        "idle\n\n"
        "## Last Task\n"
        "n/a\n\n"
        "## Last Result\n"
        "n/a\n\n"
        "## Last Updated\n"
        "n/a\n"
    )


def ensure_runtime_storage(cfg: Dict[str, Any]) -> None:
    dir_paths = [
        cfg["queue"]["inbox_dir"],
        cfg["queue"]["working_dir"],
        cfg["queue"]["done_dir"],
        cfg["queue"]["failed_dir"],
        cfg["queue"].get("handoff_dir", "queue/handoffs"),
        cfg["memory"]["archive_dir"],
        cfg["receipts"]["dir"],
    ]
    file_paths = [
        cfg["state"]["markdown_state"],
        cfg["state"]["runtime_state"],
        cfg["memory"]["journal_path"],
        cfg["memory"]["summary_path"],
        cfg["logging"]["path"],
    ]

    for relative in dir_paths:
        resolve_path(cfg, relative).mkdir(parents=True, exist_ok=True)
    for relative in file_paths:
        resolve_path(cfg, relative).parent.mkdir(parents=True, exist_ok=True)

    state_md_path = resolve_path(cfg, cfg["state"]["markdown_state"])
    if not state_md_path.exists():
        state_md_path.write_text(_default_markdown_state(), encoding="utf-8")

    runtime_state_path = resolve_path(cfg, cfg["state"]["runtime_state"])
    if not runtime_state_path.exists():
        write_json(runtime_state_path, _default_runtime_state())

    summary_path = resolve_path(cfg, cfg["memory"]["summary_path"])
    if not summary_path.exists():
        summary_path.write_text("# Memory Summary\n\n- No compactions yet.\n", encoding="utf-8")

    journal_path = resolve_path(cfg, cfg["memory"]["journal_path"])
    if not journal_path.exists():
        journal_path.touch()
