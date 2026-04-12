from pathlib import Path

import pytest

from runtime.external_ci import (
    ExternalCIError,
    _parse_repo_from_origin_url,
    _run_external_command,
    _trim_description,
)


def test_parse_repo_from_https_origin() -> None:
    assert _parse_repo_from_origin_url("https://github.com/adaptco/agent-shell.git") == "adaptco/agent-shell"


def test_parse_repo_from_ssh_origin() -> None:
    assert _parse_repo_from_origin_url("git@github.com:adaptco/agent-shell.git") == "adaptco/agent-shell"


def test_trim_description_when_over_limit() -> None:
    text = "x" * 200
    trimmed = _trim_description(text, limit=20)
    assert len(trimmed) == 20
    assert trimmed.endswith("…")


def test_run_external_command_executes_without_shell(tmp_path) -> None:
    exit_code = _run_external_command("python -c \"print('ok')\"", tmp_path)
    assert exit_code == 0


def test_run_external_command_rejects_empty() -> None:
    with pytest.raises(ExternalCIError):
        _run_external_command("   ", Path("."))
