from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.utils import utc_now, write_json

CANARY_RESULT_FILE = "canary_result.json"


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def run_canary(
    *,
    run_id: str,
    candidate_registry_bundle: dict[str, Any],
    candidate_skills_bundle: dict[str, Any],
    artifact_root: Path,
) -> dict[str, Any]:
    """Run deterministic simulated canary checks and persist canary_result.json."""
    promoted_tools = _coerce_string_list(
        candidate_registry_bundle.get("promoted_tool_ids", [])
    )
    promoted_skills = _coerce_string_list(
        candidate_skills_bundle.get("promoted_skill_ids", [])
    )
    candidate_registry_version = candidate_registry_bundle.get(
        "candidate_registry_version"
    )
    candidate_skills_version = candidate_skills_bundle.get("candidate_skills_version")

    checks: list[str] = []
    failures: list[str] = []

    if (
        not isinstance(candidate_registry_version, str)
        or not candidate_registry_version
    ):
        failures.append("missing_candidate_registry_version")
    if not isinstance(candidate_skills_version, str) or not candidate_skills_version:
        failures.append("missing_candidate_skills_version")
    checks.append("candidate_versions_present")

    if len(promoted_tools) > 250:
        failures.append("promoted_tool_ids_over_limit")
    if len(promoted_skills) > 250:
        failures.append("promoted_skill_ids_over_limit")
    checks.append("promotion_sizes_within_limits")

    if not promoted_tools and not promoted_skills:
        failures.append("empty_promotion_candidate")
    checks.append("candidate_contains_changes")

    status = "pass" if not failures else "fail"
    canary_result = {
        "schema_version": "0.3.0",
        "run_id": run_id,
        "status": status,
        "checks": checks,
        "failures": failures,
        "created_at": utc_now(),
    }
    write_json(Path(artifact_root) / CANARY_RESULT_FILE, canary_result)
    return canary_result
