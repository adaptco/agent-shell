from pathlib import Path

from runtime.utils import read_json, write_json
from app.orchestration.registry_updates import patch_active_registry_state, patch_active_skills_state
from app.orchestration.registry_updates import patch_active_registry_state, patch_active_skills_state


def test_active_state_patch_preserves_prior_and_writes_run_id(tmp_path: Path):
    registry_path = tmp_path / "configs/state/active_registry.json"
    skills_path = tmp_path / "configs/state/active_skills.json"
    write_json(
        registry_path,
        {
            "active_registry_version": "reg-v1",
            "active_registry_path": "configs/tool_registry.json",
        },
    )
    write_json(
        skills_path,
        {
            "active_skills_version": "skills-v1",
            "active_skill_paths": ["configs/skills/a.json"],
        },
    )

    patched_registry = patch_active_registry_state(
        run_id="run-3",
        candidate_registry_bundle={
            "candidate_registry_version": "reg-v2",
            "candidate_registry_path": "artifacts/candidate_tool_registry.json",
        },
        active_registry_state=read_json(registry_path),
        active_registry_path=registry_path,
    )
    patched_skills = patch_active_skills_state(
        run_id="run-3",
        candidate_skills_bundle={
            "candidate_skills_version": "skills-v2",
            "candidate_skill_paths": ["artifacts/candidate_skills.json"],
        },
        active_skills_state=read_json(skills_path),
        active_skills_path=skills_path,
    )

    assert patched_registry["prior_registry_version"] == "reg-v1"
    assert patched_registry["activation_run_id"] == "run-3"
    assert patched_skills["prior_skills_version"] == "skills-v1"
    assert patched_skills["activation_run_id"] == "run-3"


def test_no_direct_mutation_of_non_pointer_files(tmp_path: Path):
    tool_registry = tmp_path / "configs/tool_registry.json"
    skill_file = tmp_path / "configs/skills/alpha.json"
    write_json(tool_registry, {"version": "source"})
    write_json(skill_file, {"skill_id": "alpha"})

    original_tool = tool_registry.read_text(encoding="utf-8")
    original_skill = skill_file.read_text(encoding="utf-8")

    patch_active_registry_state(
        run_id="run-4",
        candidate_registry_bundle={
            "candidate_registry_version": "reg-v9",
            "candidate_registry_path": "candidate.json",
        },
        active_registry_state={
            "active_registry_version": "reg-v8",
            "active_registry_path": "configs/tool_registry.json",
        },
        active_registry_path=tmp_path / "configs/state/active_registry.json",
    )
    patch_active_skills_state(
        run_id="run-4",
        candidate_skills_bundle={
            "candidate_skills_version": "skills-v9",
            "candidate_skill_paths": ["candidate_skills.json"],
        },
        active_skills_state={
            "active_skills_version": "skills-v8",
            "active_skill_paths": ["configs/skills/alpha.json"],
        },
        active_skills_path=tmp_path / "configs/state/active_skills.json",
    )

    assert tool_registry.read_text(encoding="utf-8") == original_tool
    assert skill_file.read_text(encoding="utf-8") == original_skill
