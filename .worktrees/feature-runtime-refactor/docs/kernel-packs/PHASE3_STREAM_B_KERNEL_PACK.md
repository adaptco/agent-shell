# Phase 3 Stream B Kernel Pack

## Status
Frozen proposal extraction and validation pack.

## Scope
This pack defines the exact file contents for the Phase 3 proposal-extraction lane.
It does **not** mutate active state. It only:
- extracts canonical proposal bundles from `dailybrief.json`
- validates proposal structure
- applies policy checks against the frozen Phase 3 mutation boundary
- materializes proposal-stage artifacts suitable for later promotion wiring

## Mutation boundary
Validation and extraction do not patch:
- `configs/tool_registry.json`
- `configs/skills/*.json`
- `configs/state/active_registry.json`
- `configs/state/active_skills.json`

They only read source artifacts and write:
- `proposal_bundle.json`
- `proposal_validation_result.json`

---

## `schemas/proposal_bundle.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.local/schemas/proposal_bundle.schema.json",
  "title": "ProposalBundle",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "run_id",
    "tool_proposals",
    "skill_proposals",
    "config_proposals",
    "proposal_ids",
    "candidate_registry_version",
    "candidate_skills_version",
    "created_at"
  ],
  "properties": {
    "schema_version": {"type": "string", "const": "0.3.0"},
    "run_id": {"type": "string", "minLength": 1},
    "tool_proposals": {"type": "array", "items": {"$ref": "#/$defs/proposalItem"}},
    "skill_proposals": {"type": "array", "items": {"$ref": "#/$defs/proposalItem"}},
    "config_proposals": {"type": "array", "items": {"$ref": "#/$defs/proposalItem"}},
    "proposal_ids": {"type": "array", "items": {"type": "string"}},
    "candidate_registry_version": {"type": ["string", "null"]},
    "candidate_skills_version": {"type": ["string", "null"]},
    "created_at": {"type": "string", "format": "date-time"}
  },
  "$defs": {
    "proposalItem": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "proposal_id",
        "proposal_type",
        "action",
        "target_id",
        "candidate_version",
        "payload",
        "source_run_id",
        "source_artifact",
        "risk_tier"
      ],
      "properties": {
        "proposal_id": {"type": "string", "minLength": 1},
        "proposal_type": {"type": "string", "enum": ["tool", "skill", "config"]},
        "action": {"type": "string", "enum": ["add", "update", "remove", "replace"]},
        "target_id": {"type": "string", "minLength": 1},
        "candidate_version": {"type": ["string", "null"]},
        "payload": {"type": "object"},
        "source_run_id": {"type": "string", "minLength": 1},
        "source_artifact": {"type": "string", "minLength": 1},
        "risk_tier": {"type": "string", "enum": ["low", "moderate", "high", "critical"]}
      }
    }
  }
}
```

---

## `schemas/proposal_validation_result.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.local/schemas/proposal_validation_result.schema.json",
  "title": "ProposalValidationResult",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "run_id",
    "status",
    "validated_proposal_ids",
    "errors",
    "warnings",
    "created_at"
  ],
  "properties": {
    "schema_version": {"type": "string", "const": "0.3.0"},
    "run_id": {"type": "string", "minLength": 1},
    "status": {"type": "string", "enum": ["pass", "warn", "fail", "hold"]},
    "validated_proposal_ids": {"type": "array", "items": {"type": "string"}},
    "errors": {"type": "array", "items": {"type": "string"}},
    "warnings": {"type": "array", "items": {"type": "string"}},
    "created_at": {"type": "string", "format": "date-time"}
  }
}
```

---

## `app/orchestration/proposals.py`

```python
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class ProposalItem:
    proposal_id: str
    proposal_type: str
    action: str
    target_id: str
    candidate_version: str | None
    payload: dict[str, Any]
    source_run_id: str
    source_artifact: str
    risk_tier: str


@dataclass(frozen=True)
class ProposalBundle:
    schema_version: str
    run_id: str
    tool_proposals: list[ProposalItem]
    skill_proposals: list[ProposalItem]
    config_proposals: list[ProposalItem]
    proposal_ids: list[str]
    candidate_registry_version: str | None
    candidate_skills_version: str | None
    created_at: str


def _proposal_id(proposal_type: str, target_id: str, version: str | None) -> str:
    safe_version = (version or "noversion").replace(".", "_")
    safe_target = target_id.replace("/", ".")
    return f"{proposal_type}.{safe_target}.{safe_version}"


def _normalize_tool(raw: dict[str, Any], run_id: str, source_artifact: str) -> ProposalItem:
    target_id = raw["tool_name"]
    version = raw.get("version")
    return ProposalItem(
        proposal_id=_proposal_id("tool", target_id, version),
        proposal_type="tool",
        action=raw.get("action", "add"),
        target_id=target_id,
        candidate_version=version,
        payload=raw,
        source_run_id=run_id,
        source_artifact=source_artifact,
        risk_tier=raw.get("risk_tier", "moderate"),
    )


def _normalize_skill(raw: dict[str, Any], run_id: str, source_artifact: str) -> ProposalItem:
    target_id = raw["skill_id"]
    version = raw.get("version")
    return ProposalItem(
        proposal_id=_proposal_id("skill", target_id, version),
        proposal_type="skill",
        action=raw.get("action", "update"),
        target_id=target_id,
        candidate_version=version,
        payload=raw,
        source_run_id=run_id,
        source_artifact=source_artifact,
        risk_tier=raw.get("risk_tier", "moderate"),
    )


def _normalize_config(raw: dict[str, Any], run_id: str, source_artifact: str) -> ProposalItem:
    target_id = raw["config_id"]
    version = raw.get("version")
    return ProposalItem(
        proposal_id=_proposal_id("config", target_id, version),
        proposal_type="config",
        action=raw.get("action", "update"),
        target_id=target_id,
        candidate_version=version,
        payload=raw,
        source_run_id=run_id,
        source_artifact=source_artifact,
        risk_tier=raw.get("risk_tier", "moderate"),
    )


def extract_proposals(dailybrief: dict[str, Any], source_artifact: str) -> ProposalBundle:
    run_id = dailybrief["run_id"]
    proposals = dailybrief.get("proposals", {})

    tool_items = [_normalize_tool(item, run_id, source_artifact) for item in proposals.get("tools", [])]
    skill_items = [_normalize_skill(item, run_id, source_artifact) for item in proposals.get("skills", [])]
    config_items = [_normalize_config(item, run_id, source_artifact) for item in proposals.get("configs", [])]

    all_ids = [item.proposal_id for item in [*tool_items, *skill_items, *config_items]]

    candidate_registry_version = f"{run_id}.registry" if tool_items else None
    candidate_skills_version = f"{run_id}.skills" if skill_items else None

    return ProposalBundle(
        schema_version="0.3.0",
        run_id=run_id,
        tool_proposals=tool_items,
        skill_proposals=skill_items,
        config_proposals=config_items,
        proposal_ids=all_ids,
        candidate_registry_version=candidate_registry_version,
        candidate_skills_version=candidate_skills_version,
        created_at=utc_now_iso(),
    )


def write_proposal_bundle(path: Path, bundle: ProposalBundle) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(bundle), indent=2, sort_keys=True) + "\n", encoding="utf-8")
```

---

## `app/orchestration/validators.py`

```python
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class ValidationResult:
    schema_version: str
    run_id: str
    status: str
    validated_proposal_ids: list[str]
    errors: list[str]
    warnings: list[str]
    created_at: str


def validate_proposal_bundle(bundle: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    proposal_ids = bundle.get("proposal_ids", [])
    if len(proposal_ids) != len(set(proposal_ids)):
        errors.append("duplicate proposal_id detected")

    for section_name in ("tool_proposals", "skill_proposals", "config_proposals"):
        for item in bundle.get(section_name, []):
            if not item.get("proposal_id"):
                errors.append(f"{section_name} item missing proposal_id")
            if not item.get("proposal_type"):
                errors.append(f"{section_name} item missing proposal_type")
            if not item.get("target_id"):
                errors.append(f"{section_name} item missing target_id")
            if item.get("action") in {"add", "update", "replace"} and not item.get("candidate_version"):
                errors.append(f"{item.get('proposal_id', 'unknown')} missing candidate_version")

    status = "pass" if not errors else "fail"
    return ValidationResult(
        schema_version="0.3.0",
        run_id=bundle["run_id"],
        status=status,
        validated_proposal_ids=proposal_ids,
        errors=errors,
        warnings=warnings,
        created_at=utc_now_iso(),
    )


def write_validation_result(path: Path, result: ValidationResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
```

---

## `app/orchestration/policy_checks.py`

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PolicyCheckResult:
    status: str
    errors: list[str]
    warnings: list[str]


FORBIDDEN_DIRECT_TARGETS = {
    "configs/tool_registry.json",
    "configs/state/active_registry.json",
    "configs/state/active_skills.json",
}


def check_proposal_policy(bundle: dict[str, Any]) -> PolicyCheckResult:
    errors: list[str] = []
    warnings: list[str] = []

    for section in ("tool_proposals", "skill_proposals", "config_proposals"):
        for item in bundle.get(section, []):
            payload = item.get("payload", {})
            candidate_path = payload.get("path")

            if candidate_path in FORBIDDEN_DIRECT_TARGETS:
                errors.append(f"{item['proposal_id']} targets forbidden activation path")

            if item["proposal_type"] == "tool":
                side_effect_class = payload.get("side_effect_class")
                if side_effect_class in {"write_external", "execute"}:
                    warnings.append(f"{item['proposal_id']} is high-risk: {side_effect_class}")

                scopes = payload.get("allowed_scopes", [])
                if any(scope.endswith(":admin") for scope in scopes):
                    errors.append(f"{item['proposal_id']} requests admin-like scope escalation")

    status = "pass"
    if errors:
        status = "fail"
    elif warnings:
        status = "warn"

    return PolicyCheckResult(status=status, errors=errors, warnings=warnings)
```

---

## `tests/test_proposal_extraction.py`

```python
from app.orchestration.proposals import extract_proposals


def test_extract_proposals_builds_canonical_bundle() -> None:
    brief = {
        "run_id": "2026-04-12.daily.0001",
        "proposals": {
            "tools": [
                {
                    "tool_name": "internal.noop_probe",
                    "version": "0.1.0",
                    "connector_type": "internal",
                    "risk_tier": "low"
                }
            ],
            "skills": [
                {
                    "skill_id": "orchestrator",
                    "version": "0.2.0"
                }
            ],
            "configs": [
                {
                    "config_id": "policy.gates",
                    "version": "0.3.0"
                }
            ]
        }
    }

    bundle = extract_proposals(brief, "artifacts/run/dailybrief.json")

    assert bundle.run_id == "2026-04-12.daily.0001"
    assert len(bundle.tool_proposals) == 1
    assert len(bundle.skill_proposals) == 1
    assert len(bundle.config_proposals) == 1
    assert bundle.proposal_ids
```

---

## `tests/test_proposal_validation.py`

```python
from dataclasses import asdict

from app.orchestration.policy_checks import check_proposal_policy
from app.orchestration.proposals import extract_proposals
from app.orchestration.validators import validate_proposal_bundle


def test_validation_passes_for_clean_bundle() -> None:
    brief = {
        "run_id": "2026-04-12.daily.0001",
        "proposals": {
            "tools": [
                {
                    "tool_name": "internal.noop_probe",
                    "version": "0.1.0",
                    "connector_type": "internal",
                    "risk_tier": "low",
                    "allowed_scopes": ["internal:noop"],
                    "side_effect_class": "read_only"
                }
            ],
            "skills": [],
            "configs": []
        }
    }

    bundle = asdict(extract_proposals(brief, "artifacts/run/dailybrief.json"))
    result = validate_proposal_bundle(bundle)
    policy = check_proposal_policy(bundle)

    assert result.status == "pass"
    assert policy.status == "pass"


def test_policy_fails_on_scope_escalation() -> None:
    brief = {
        "run_id": "2026-04-12.daily.0001",
        "proposals": {
            "tools": [
                {
                    "tool_name": "dangerous.tool",
                    "version": "1.0.0",
                    "connector_type": "http",
                    "risk_tier": "critical",
                    "allowed_scopes": ["github:admin"],
                    "side_effect_class": "execute"
                }
            ],
            "skills": [],
            "configs": []
        }
    }

    bundle = asdict(extract_proposals(brief, "artifacts/run/dailybrief.json"))
    policy = check_proposal_policy(bundle)

    assert policy.status == "fail"
    assert policy.errors
```

---

## Integration notes
- First land extraction and validation only.
- Do not patch active-state pointers in this lane.
- Wire receipts later with event names:
  - `proposals_extracted`
  - `proposals_validated`
- Promotion runtime should consume only validated proposal bundles.
