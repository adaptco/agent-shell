from pathlib import Path

from runtime.utils import read_json, write_json
from app.orchestration.promoter import promote_candidates


class ReceiptSpy:
    def __init__(self):
        self.events = []

    def emit(self, task_id, step, status, inputs=None, outputs=None, error=None):
        self.events.append((task_id, step, status, outputs))


def _active_states(tmp_path: Path):
    active_registry_path = tmp_path / "configs/state/active_registry.json"
    active_skills_path = tmp_path / "configs/state/active_skills.json"
    active_registry_state = {
        "schema_version": "0.3.0",
        "active_registry_version": "reg-current",
        "active_registry_path": "configs/tool_registry.json",
        "prior_registry_version": None,
        "prior_registry_path": None,
        "activated_at": None,
        "activation_run_id": None,
    }
    active_skills_state = {
        "schema_version": "0.3.0",
        "active_skills_version": "skills-current",
        "active_skill_paths": ["configs/skills/base.json"],
        "prior_skills_version": None,
        "prior_skill_paths": [],
        "activated_at": None,
        "activation_run_id": None,
    }
    write_json(active_registry_path, active_registry_state)
    write_json(active_skills_path, active_skills_state)
    return (
        active_registry_state,
        active_skills_state,
        active_registry_path,
        active_skills_path,
    )


def test_promotion_runtime_stages_and_promotes_on_pass(tmp_path: Path):
    (
        active_registry_state,
        active_skills_state,
        active_registry_path,
        active_skills_path,
    ) = _active_states(tmp_path)
    receipts = ReceiptSpy()

    result = promote_candidates(
        run_id="run-10",
        proposal_bundle={
            "registry": {"tools": []},
            "skills": [],
            "tool_ids": ["tool.x"],
            "skill_ids": ["skill.x"],
        },
        validation_result={"status": "pass"},
        active_registry_state=active_registry_state,
        active_skills_state=active_skills_state,
        artifact_root=tmp_path / "artifacts/run-10",
        active_registry_state_path=active_registry_path,
        active_skills_state_path=active_skills_path,
        receipts=receipts,
    )

    assert result["decision"]["decision"] == "promote"
    assert (tmp_path / "artifacts/run-10/candidate_registry_bundle.json").exists()
    assert (tmp_path / "artifacts/run-10/candidate_skills_bundle.json").exists()
    assert (tmp_path / "artifacts/run-10/promotion_decision.json").exists()
    assert read_json(active_registry_path)["active_registry_version"].startswith(
        "registry-run-10-"
    )
    assert read_json(active_skills_path)["active_skills_version"].startswith(
        "skills-run-10-"
    )
    assert "active_state_patched" in [event[1] for event in receipts.events]


def test_promotion_runtime_does_not_patch_on_canary_fail(tmp_path: Path):
    (
        active_registry_state,
        active_skills_state,
        active_registry_path,
        active_skills_path,
    ) = _active_states(tmp_path)

    result = promote_candidates(
        run_id="run-11",
        proposal_bundle={"registry": {}, "skills": [], "tool_ids": [], "skill_ids": []},
        validation_result={"status": "pass"},
        active_registry_state=active_registry_state,
        active_skills_state=active_skills_state,
        artifact_root=tmp_path / "artifacts/run-11",
        active_registry_state_path=active_registry_path,
        active_skills_state_path=active_skills_path,
    )

    assert result["decision"]["decision"] == "rollback"
    assert result["active_state_patched"] is False
    assert read_json(active_registry_path)["active_registry_version"] == "reg-current"
    assert read_json(active_skills_path)["active_skills_version"] == "skills-current"


def test_promotion_runtime_quarantines_when_active_pointer_files_missing(
    tmp_path: Path,
):
    (
        active_registry_state,
        active_skills_state,
        active_registry_path,
        active_skills_path,
    ) = _active_states(tmp_path)
    active_registry_path.unlink()

    result = promote_candidates(
        run_id="run-12",
        proposal_bundle={
            "registry": {},
            "skills": [],
            "tool_ids": ["a"],
            "skill_ids": ["b"],
        },
        validation_result={"status": "pass"},
        active_registry_state=active_registry_state,
        active_skills_state=active_skills_state,
        artifact_root=tmp_path / "artifacts/run-12",
        active_registry_state_path=active_registry_path,
        active_skills_state_path=active_skills_path,
    )

    assert result["decision"]["decision"] == "quarantine"
    assert result["decision"]["reason"] == "missing_active_pointer_files"
