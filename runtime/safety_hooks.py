from __future__ import annotations
import re
from runtime.plugin_base import HookHandler


class SafetyHookHandler(HookHandler):
    """
    Implements runtime safety policies for tool calls and model interactions.
    """

    def handle(self, hook_name: str, task_id: str, payload: dict) -> dict:
        if hook_name == "before_tool_call":
            return self._check_tool_call(payload)
        elif hook_name == "before_model_call":
            return self._check_model_input(payload)

        return {"allow": True, "payload": payload}

    def _check_tool_call(self, payload: dict) -> dict:
        tool_name = payload.get("tool_name")
        tool_input = payload.get("tool_input", {})

        if tool_name == "bash":
            if not self.config.get("safety", {}).get("block_dangerous_bash", True):
                return {"allow": True, "payload": payload}

            command = tool_input.get("command", "")
            # Block extremely dangerous patterns
            dangerous_patterns = [
                r"rm\s+-rf\s+/",
                r"mkfs",
                r"dd\s+if=",
                r">\s*/dev/sd",
                r":\(\){ :\|:& };:",  # Fork bomb
                r"curl.*\|.*bash",
                r"wget.*\|.*bash",
            ]
            for pattern in dangerous_patterns:
                if re.search(pattern, command):
                    return {
                        "allow": False,
                        "payload": payload,
                        "reason": f"Dangerous command pattern detected: {pattern}",
                    }

        return {"allow": True, "payload": payload}

    def _check_model_input(self, payload: dict) -> dict:
        # Placeholder for future prompt injection detection
        return {"allow": True, "payload": payload}
