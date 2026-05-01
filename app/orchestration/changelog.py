from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.utils import utc_now, write_json


def build_changelog(
    *,
    run_id: str,
    candidate_registry_bundle: dict[str, Any],
    candidate_skills_bundle: dict[str, Any],
    config_changes: list[str],
    artifact_root: Path,
) -> dict[str, Any]:
    changelog = {
        "schema_version": "0.3.0",
        "run_id": run_id,
        "candidate_registry_version": candidate_registry_bundle.get("candidate_registry_version"),
        "candidate_skills_version": candidate_skills_bundle.get("candidate_skills_version"),
        "tool_changes": [f"promoted:{tid}" for tid in candidate_registry_bundle.get("promoted_tool_ids", [])],
        "skill_changes": [f"promoted:{sid}" for sid in candidate_skills_bundle.get("promoted_skill_ids", [])],
        "config_changes": config_changes,
        "created_at": utc_now(),
    }
    write_json(Path(artifact_root) / "changelog.json", changelog)
    return changelog
