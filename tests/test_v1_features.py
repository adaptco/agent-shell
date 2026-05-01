import pytest
import json
from pathlib import Path
from runtime.safety_hooks import SafetyHookHandler
from runtime.receipts import ReceiptWriter
from runtime.mcp_adapter import MCPToolPlugin
from runtime.skill_discovery import SkillDiscovery


@pytest.fixture
def cfg():
    return {
        "_workspace": ".",
        "skill_dir": "skill",
        "receipts": {"dir": "receipts"},
        "tools": {"registry_dir": "tools", "bash": {"allow_prefixes": ["ls"]}},
        "safety": {"block_dangerous_bash": True}
    }


def test_safety_hook_blocks_dangerous_bash(cfg):
    handler = SafetyHookHandler(cfg)
    payload = {
        "tool_name": "bash",
        "tool_input": {"command": "rm -rf /"}
    }
    result = handler.handle("before_tool_call", "task-1", payload)
    assert result["allow"] is False
    assert "Dangerous command" in result["reason"]


def test_safety_hook_respects_config_flag(cfg):
    cfg["safety"]["block_dangerous_bash"] = False
    handler = SafetyHookHandler(cfg)
    payload = {
        "tool_name": "bash",
        "tool_input": {"command": "rm -rf /"}
    }
    result = handler.handle("before_tool_call", "task-1", payload)
    assert result["allow"] is True


def test_receipt_scrubbing(cfg, monkeypatch):
    writer = ReceiptWriter(cfg)
    
    # Mocking write_json to avoid filesystem side effects
    import runtime.receipts as receipts
    monkeypatch.setattr(receipts, "write_json", lambda p, d: None)
    
    inputs = {"api_key": "sk-12345", "query": "test"}
    # Test _scrub directly as in previous version
    scrubbed = writer._scrub(inputs)
    assert scrubbed["api_key"] == "[REDACTED]"
    assert scrubbed["query"] == "test"


def test_skill_discovery(cfg):
    discovery = SkillDiscovery(cfg)
    result = discovery.run({"query": ""})
    assert "skills" in result
    assert isinstance(result["skills"], list)
    # Verify it found the existing ci-ready-review skill
    skill_names = [s["name"] for s in result["skills"]]
    assert "ci-ready-review" in skill_names
