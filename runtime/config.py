from pathlib import Path
from typing import Any, Dict
from runtime.utils import read_json

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HANDOFF_DIR = ".runtime-store/objects/queue/handoffs"


def load_config(root: Path | None = None) -> Dict[str, Any]:
    workspace = root or ROOT
    data = read_json(workspace / "infra" / "runtime.json")
    data["_workspace"] = str(workspace)
    return data


def resolve_path(cfg: Dict[str, Any], relative_path: str) -> Path:
    return Path(cfg["_workspace"]) / relative_path
