import pytest
from runtime.utils import get_env


def test_get_env_present(monkeypatch):
    monkeypatch.setenv("TEST_FOO", "bar")
    assert get_env("TEST_FOO") == "bar"


def test_get_env_missing_required(monkeypatch):
    monkeypatch.delenv("TEST_BAR", raising=False)
    with pytest.raises(RuntimeError):
        get_env("TEST_BAR", required=True)


def test_get_env_missing_not_required(monkeypatch):
    monkeypatch.delenv("TEST_BAZ", raising=False)
    assert get_env("TEST_BAZ", required=False) is None
