from pathlib import Path

from runtime.utils import read_json
from app.orchestration.canary import run_canary


def test_canary_pass_path(tmp_path: Path):
    result = run_canary(
        run_id="run-1",
        candidate_registry_bundle={
            "candidate_registry_version": "reg-v1",
            "promoted_tool_ids": ["t1"],
        },
        candidate_skills_bundle={
            "candidate_skills_version": "sk-v1",
            "promoted_skill_ids": ["s1"],
        },
        artifact_root=tmp_path,
    )
    assert result["status"] == "pass"
    persisted = read_json(tmp_path / "canary_result.json")
    assert persisted["status"] == "pass"


def test_canary_fail_path(tmp_path: Path):
    result = run_canary(
        run_id="run-2",
        candidate_registry_bundle={
            "candidate_registry_version": "",
            "promoted_tool_ids": [],
        },
        candidate_skills_bundle={
            "candidate_skills_version": "",
            "promoted_skill_ids": [],
        },
        artifact_root=tmp_path,
    )
    assert result["status"] == "fail"
    assert "missing_candidate_registry_version" in result["failures"]
