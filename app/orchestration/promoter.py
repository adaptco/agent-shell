from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.utils import utc_now, write_json

from app.orchestration.canary import run_canary
from app.orchestration.changelog import build_changelog
from app.orchestration.registry_updates import (
    patch_active_registry_state,
    patch_active_skills_state,
    stage_candidate_registry_bundle,
    stage_candidate_skills_bundle,
)

ALLOWED_DECISIONS = {"promote", "hold", "quarantine", "rollback"}


def _emit(receipts: Any, run_id: str, step: str, status: str, outputs: dict[str, Any]) -> None:
    if receipts is None:
        return
    receipts.emit(run_id, step, status, {"run_id": run_id}, outputs)


def _write_decision(artifact_root: Path, run_id: str, decision: str, reason: str) -> dict[str, Any]:
    if decision not in ALLOWED_DECISIONS:
        raise ValueError(f"unsupported decision: {decision}")
    payload = {
        "schema_version": "0.3.0",
        "run_id": run_id,
        "decision": decision,
        "reason": reason,
        "created_at": utc_now(),
    }
    write_json(Path(artifact_root) / "promotion_decision.json", payload)
    return payload


def promote_candidates(
    *,
    run_id: str,
    proposal_bundle: dict[str, Any],
    validation_result: dict[str, Any],
    active_registry_state: dict[str, Any],
    active_skills_state: dict[str, Any],
    artifact_root: Path,
    active_registry_state_path: Path,
    active_skills_state_path: Path,
    receipts: Any = None,
) -> dict[str, Any]:
    artifact_root = Path(artifact_root)
    artifact_root.mkdir(parents=True, exist_ok=True)

    validation_status = validation_result.get("status")
    if validation_status not in {"pass", "warn"}:
        decision = _write_decision(artifact_root, run_id, "quarantine", f"invalid_validation_status:{validation_status}")
        _emit(receipts, run_id, "promotion_decision_written", "blocked", decision)
        return {"decision": decision, "canary_result": None, "active_state_patched": False}

    required_registry = {"active_registry_version", "active_registry_path"}
    required_skills = {"active_skills_version", "active_skill_paths"}
    if not required_registry.issubset(active_registry_state) or not required_skills.issubset(active_skills_state):
        decision = _write_decision(artifact_root, run_id, "quarantine", "missing_active_state_fields")
        _emit(receipts, run_id, "promotion_decision_written", "blocked", decision)
        return {"decision": decision, "canary_result": None, "active_state_patched": False}

    candidate_registry_bundle = stage_candidate_registry_bundle(
        run_id=run_id,
        proposal_bundle=proposal_bundle,
        active_registry_state=active_registry_state,
        artifact_root=artifact_root,
    )
    candidate_skills_bundle = stage_candidate_skills_bundle(
        run_id=run_id,
        proposal_bundle=proposal_bundle,
        active_skills_state=active_skills_state,
        artifact_root=artifact_root,
    )
    _emit(receipts, run_id, "candidate_state_staged", "ok", {
        "candidate_registry_version": candidate_registry_bundle["candidate_registry_version"],
        "candidate_skills_version": candidate_skills_bundle["candidate_skills_version"],
    })

    hold_decision = _write_decision(artifact_root, run_id, "hold", "awaiting_canary")
    _emit(receipts, run_id, "promotion_decision_written", "ok", hold_decision)

    _emit(receipts, run_id, "canary_started", "ok", {"run_id": run_id})
    canary_result = run_canary(
        run_id=run_id,
        candidate_registry_bundle=candidate_registry_bundle,
        candidate_skills_bundle=candidate_skills_bundle,
        artifact_root=artifact_root,
    )
    _emit(receipts, run_id, "canary_completed", "ok", canary_result)

    if canary_result["status"] == "pass":
        patch_active_registry_state(
            run_id=run_id,
            candidate_registry_bundle=candidate_registry_bundle,
            active_registry_state=active_registry_state,
            active_registry_path=active_registry_state_path,
        )
        patch_active_skills_state(
            run_id=run_id,
            candidate_skills_bundle=candidate_skills_bundle,
            active_skills_state=active_skills_state,
            active_skills_path=active_skills_state_path,
        )
        _emit(receipts, run_id, "active_state_patched", "ok", {"run_id": run_id})

        rollback_token = {
            "schema_version": "0.3.0",
            "run_id": run_id,
            "registry": {
                "version": active_registry_state.get("active_registry_version"),
                "path": active_registry_state.get("active_registry_path"),
            },
            "skills": {
                "version": active_skills_state.get("active_skills_version"),
                "paths": active_skills_state.get("active_skill_paths", []),
            },
            "created_at": utc_now(),
        }
        write_json(artifact_root / "rollback_token.json", rollback_token)
        _emit(receipts, run_id, "rollback_token_written", "ok", rollback_token)

        changelog = build_changelog(
            run_id=run_id,
            candidate_registry_bundle=candidate_registry_bundle,
            candidate_skills_bundle=candidate_skills_bundle,
            config_changes=[
                "patched:configs/state/active_registry.json",
                "patched:configs/state/active_skills.json",
            ],
            artifact_root=artifact_root,
        )
        _emit(receipts, run_id, "changelog_written", "ok", changelog)
        decision = _write_decision(artifact_root, run_id, "promote", "canary_passed")
    else:
        decision = _write_decision(artifact_root, run_id, "rollback", "canary_failed")

    _emit(receipts, run_id, "promotion_decision_written", "ok", decision)
    return {"decision": decision, "canary_result": canary_result, "active_state_patched": canary_result["status"] == "pass"}
