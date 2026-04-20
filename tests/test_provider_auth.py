from __future__ import annotations

import pytest

from runtime.config import load_config
from runtime.llm import MistralChatBackend, OpenAIResponsesBackend


def test_openai_backend_uses_server_side_env_var(monkeypatch: pytest.MonkeyPatch):
    cfg = load_config()
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
    backend = OpenAIResponsesBackend(cfg)
    assert backend.api_key == "openai-test-key"


def test_mistral_backend_uses_server_side_env_var(monkeypatch: pytest.MonkeyPatch):
    cfg = load_config()
    monkeypatch.setenv("MISTRAL_API_KEY", "mistral-test-key")
    backend = MistralChatBackend(cfg)
    assert backend.api_key == "mistral-test-key"


def test_provider_backend_rejects_missing_server_side_keys(monkeypatch: pytest.MonkeyPatch):
    cfg = load_config()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    
    with pytest.raises(RuntimeError, match="Missing required environment variable: OPENAI_API_KEY"):
        OpenAIResponsesBackend(cfg)
        
    with pytest.raises(RuntimeError, match="Missing required environment variable: MISTRAL_API_KEY"):
        MistralChatBackend(cfg)
