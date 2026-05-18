from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from runtime.utils import read_json

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HANDOFF_DIR = ".runtime-store/objects/queue/handoffs"


def _default_workspace() -> Path:
    env_workspace = os.environ.get("AGENT_SHELL_WORKSPACE")
    if env_workspace:
        return Path(env_workspace).expanduser().resolve()

    cwd = Path.cwd()
    if (cwd / "infra" / "runtime.json").exists():
        return cwd

    return ROOT


def load_config(root: Path | str | None = None) -> Dict[str, Any]:
    workspace = Path(root).expanduser().resolve() if root is not None else _default_workspace()
    data = read_json(workspace / "infra" / "runtime.json")
    data["_workspace"] = str(workspace)
    return data


def resolve_path(cfg: Dict[str, Any], relative_path: str) -> Path:
    return Path(cfg["_workspace"]) / relative_path
