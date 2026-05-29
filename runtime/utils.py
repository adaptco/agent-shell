from __future__ import annotations
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


def utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(value: Any) -> str:
    if not isinstance(value, str):
        value = canonical_json(value)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def append_jsonl(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False) + "\n")


<<<<<<< ours
<<<<<<< ours
# Environment helper: centralize env var access and consistent error messaging


def get_env(
    name: str, required: bool = False, message: str | None = None
) -> str | None:
=======
def get_env(name: str, required: bool = True, message: str | None = None) -> str | None:
>>>>>>> theirs
=======
def get_env(name: str, required: bool = True, message: str | None = None) -> str | None:
>>>>>>> theirs
    """Return the environment variable value or raise RuntimeError when required and missing."""
    val = os.environ.get(name)
    if required and (val is None or val == ""):
        raise RuntimeError(message or f"Missing required environment variable: {name}")
    return val
<<<<<<< ours
<<<<<<< ours


def is_valid_id(id_str: str) -> bool:
    """Check if the string is a valid hexadecimal task ID (32 chars)."""
    return bool(isinstance(id_str, str) and re.fullmatch(r"[0-9a-f]{32}", id_str))
=======
>>>>>>> theirs
=======
>>>>>>> theirs
