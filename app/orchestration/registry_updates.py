from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.utils import sha256_hex, utc_now, write_json

CANDIDATE_REGISTRY_FILE = "candidate_tool_registry.json"
CANDIDATE_SKILLS_FILE = "candidate_skills.json"


def _version_for(prefix: str, run_id: str, ids: list[str]) -> str:
    digest = sha256_hex({"run_id": run_id, "ids": ids})[:10]
    return f"{prefix}-{run_id}-{digest}"


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def stage_candidate_registry_bundle(
    *,
    run_id: str,
    proposal_bundle: dict[str, Any],
    active_registry_state: dict[str, Any],
    artifact_root: Path,
) -> dict[str, Any]:
    promoted_tool_ids = _coerce_string_list(proposal_bundle.get("tool_ids", []))
    candidate_registry_version = _version_for("registry", run_id, promoted_tool_ids)
    candidate_registry_path = str(Path(artifact_root) / CANDIDATE_REGISTRY_FILE)
    candidate_registry = {
        "schema_version": "0.3.0",
        "run_id": run_id,
        "candidate_registry_version": candidate_registry_version,
        "base_registry_version": active_registry_state.get("active_registry_version"),
        "candidate_registry_path": candidate_registry_path,
        "promoted_tool_ids": promoted_tool_ids,
        "created_at": utc_now(),
    }
    write_json(Path(candidate_registry_path), proposal_bundle.get("registry", {}))
    write_json(Path(artifact_root) / "candidate_registry_bundle.json", candidate_registry)
    return candidate_registry


def stage_candidate_skills_bundle(
    *,
    run_id: str,
    proposal_bundle: dict[str, Any],
    active_skills_state: dict[str, Any],
    artifact_root: Path,
) -> dict[str, Any]:
    promoted_skill_ids = _coerce_string_list(proposal_bundle.get("skill_ids", []))
    candidate_skills_version = _version_for("skills", run_id, promoted_skill_ids)
    candidate_skill_paths = [str(Path(artifact_root) / CANDIDATE_SKILLS_FILE)]
    candidate_skills = {
        "schema_version": "0.3.0",
        "run_id": run_id,
        "candidate_skills_version": candidate_skills_version,
        "base_skills_version": active_skills_state.get("active_skills_version"),
        "candidate_skill_paths": candidate_skill_paths,
        "promoted_skill_ids": promoted_skill_ids,
        "created_at": utc_now(),
    }
    write_json(Path(candidate_skill_paths[0]), proposal_bundle.get("skills", []))
    write_json(Path(artifact_root) / "candidate_skills_bundle.json", candidate_skills)
    return candidate_skills


def patch_active_registry_state(
    *,
    run_id: str,
    candidate_registry_bundle: dict[str, Any],
    active_registry_state: dict[str, Any],
    active_registry_path: Path,
) -> dict[str, Any]:
    patched = {
        "schema_version": "0.3.0",
        "active_registry_version": candidate_registry_bundle.get("candidate_registry_version"),
        "active_registry_path": candidate_registry_bundle.get("candidate_registry_path"),
        "prior_registry_version": active_registry_state.get("active_registry_version"),
        "prior_registry_path": active_registry_state.get("active_registry_path"),
        "activated_at": utc_now(),
        "activation_run_id": run_id,
    }
    write_json(Path(active_registry_path), patched)
    return patched


def patch_active_skills_state(
    *,
    run_id: str,
    candidate_skills_bundle: dict[str, Any],
    active_skills_state: dict[str, Any],
    active_skills_path: Path,
) -> dict[str, Any]:
    patched = {
        "schema_version": "0.3.0",
        "active_skills_version": candidate_skills_bundle.get("candidate_skills_version"),
        "active_skill_paths": _coerce_string_list(candidate_skills_bundle.get("candidate_skill_paths", [])),
        "prior_skills_version": active_skills_state.get("active_skills_version"),
        "prior_skill_paths": _coerce_string_list(active_skills_state.get("active_skill_paths", [])),
        "activated_at": utc_now(),
        "activation_run_id": run_id,
    }
    write_json(Path(active_skills_path), patched)
    return patched
