from pathlib import Path

from runtime.utils import read_json
from app.orchestration.changelog import build_changelog


def test_changelog_summarizes_changes(tmp_path: Path):
    changelog = build_changelog(
        run_id="run-5",
        candidate_registry_bundle={"candidate_registry_version": "reg-v2", "promoted_tool_ids": ["tool.a", "tool.b"]},
        candidate_skills_bundle={"candidate_skills_version": "skills-v2", "promoted_skill_ids": ["skill.a"]},
        config_changes=["patched:configs/state/active_registry.json"],
        artifact_root=tmp_path,
    )
    assert changelog["tool_changes"] == ["promoted:tool.a", "promoted:tool.b"]
    assert changelog["skill_changes"] == ["promoted:skill.a"]
    persisted = read_json(tmp_path / "changelog.json")
    assert persisted["config_changes"] == ["patched:configs/state/active_registry.json"]
