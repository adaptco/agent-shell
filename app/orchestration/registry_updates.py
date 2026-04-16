from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.utils import utc_now, write_json


def stage_candidate_registry_bundle(
    *,
    run_id: str,
    proposal_bundle: dict[str, Any],
    active_registry_state: dict[str, Any],
    artifact_root: Path,
) -> dict[str, Any]:
    candidate_registry_path = str(Path(artifact_root) / "candidate_tool_registry.json")
    candidate_registry = {
        "schema_version": "0.3.0",
        "run_id": run_id,
        "candidate_registry_version": f"{run_id}-registry-v1",
        "base_registry_version": active_registry_state.get("active_registry_version"),
        "candidate_registry_path": candidate_registry_path,
        "promoted_tool_ids": [str(v) for v in proposal_bundle.get("tool_ids", [])],
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
    candidate_skill_paths = [str(Path(artifact_root) / "candidate_skills.json")]
    candidate_skills = {
        "schema_version": "0.3.0",
        "run_id": run_id,
        "candidate_skills_version": f"{run_id}-skills-v1",
        "base_skills_version": active_skills_state.get("active_skills_version"),
        "candidate_skill_paths": candidate_skill_paths,
        "promoted_skill_ids": [str(v) for v in proposal_bundle.get("skill_ids", [])],
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
        "active_skill_paths": candidate_skills_bundle.get("candidate_skill_paths", []),
        "prior_skills_version": active_skills_state.get("active_skills_version"),
        "prior_skill_paths": active_skills_state.get("active_skill_paths", []),
        "activated_at": utc_now(),
        "activation_run_id": run_id,
    }
    write_json(Path(active_skills_path), patched)
    return patched
