import unittest
import json
from pathlib import Path
from runtime.safety_hooks import SafetyHookHandler
from runtime.receipts import ReceiptWriter
from runtime.mcp_adapter import MCPToolPlugin
from runtime.skill_discovery import SkillDiscovery


class TestV1Features(unittest.TestCase):
    def setUp(self):
        self.cfg = {
            "_workspace": ".",
            "skill_dir": "skill",
            "receipts": {"dir": "receipts"},
            "tools": {"registry_dir": "tools", "bash": {"allow_prefixes": ["ls"]}}
        }

    def test_safety_hook_blocks_dangerous_bash(self):
        handler = SafetyHookHandler(self.cfg)
        payload = {
            "tool_name": "bash",
            "tool_input": {"command": "rm -rf /"}
        }
        result = handler.handle("before_tool_call", "task-1", payload)
        self.assertFalse(result["allow"])
        self.assertIn("Dangerous command", result["reason"])

    def test_receipt_scrubbing(self):
        writer = ReceiptWriter(self.cfg)
        # Mocking write_json to avoid filesystem side effects
        import runtime.receipts as receipts
        original_write = receipts.write_json
        receipts.write_json = lambda p, d: None 
        
        try:
            inputs = {"api_key": "sk-12345", "query": "test"}
            receipt_path = writer.emit("task-1", "step-1", "ok", inputs=inputs)
            
            # Since we can't easily read what lambda did, let's test _scrub directly
            scrubbed = writer._scrub(inputs)
            self.assertEqual(scrubbed["api_key"], "[REDACTED]")
            self.assertEqual(scrubbed["query"], "test")
        finally:
            receipts.write_json = original_write

    def test_skill_discovery(self):
        discovery = SkillDiscovery(self.cfg)
        result = discovery.run({"query": ""})
        self.assertIn("skills", result)
        self.assertIsInstance(result["skills"], list)
        # Verify it found the existing ci-ready-review skill
        skill_names = [s["name"] for s in result["skills"]]
        self.assertIn("ci-ready-review", skill_names)


if __name__ == "__main__":
    unittest.main()
