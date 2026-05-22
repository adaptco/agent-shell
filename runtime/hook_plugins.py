from __future__ import annotations

from runtime.plugin_base import HookHandler
from runtime.config import resolve_path

class BuiltinHookHandler(HookHandler):
    """Existing hook logic: bash prefix blocking, subagent validation, and webhooks"""
    
    def handle(self, hook_name: str, task_id: str, payload: dict) -> dict:
        result = {"allow": True, "payload": payload}
        
        if hook_name == "before_tool_call":
            result = self._before_tool_call(task_id, payload)
        elif hook_name == "before_delegate":
            result = self._before_delegate(task_id, payload)
        
        # Webhook logic (global for all builtin hooks)
        self._trigger_webhook(hook_name, task_id, payload, result)
        
        return result
    
    def _before_tool_call(self, task_id: str, payload: dict) -> dict:
        """Block bash commands that don't match whitelist"""
        tool_name = payload.get("tool_name")
        if tool_name == "bash":
            command = payload.get("tool_input", {}).get("command", "")
            token = command.strip().split(" ", 1)[0]
            allow = token in self.config["tools"]["bash"]["allow_prefixes"]
            if not allow:
                return {"allow": False, "payload": payload, "reason": f"command prefix not allowed: {token}"}
        return {"allow": True, "payload": payload}
    
    def _before_delegate(self, task_id: str, payload: dict) -> dict:
        """Validate subagent existence"""
        subagent_name = payload.get("subagent_name")
        subagent_path = resolve_path(self.config, self.config["subagent_dir"]) / f"{subagent_name}.md"
        if not subagent_path.exists():
            return {"allow": False, "payload": payload, "reason": f"unknown subagent: {subagent_name}"}
        return {"allow": True, "payload": payload}

    def _trigger_webhook(self, hook_name: str, task_id: str, payload: dict, result: dict):
        webhooks = self.config.get("webhooks", {})
        webhook_url = webhooks.get("url")
        webhook_events = webhooks.get("events", [])
        if webhook_url and (hook_name in webhook_events or "*" in webhook_events):
            try:
                import urllib.request
                import json
                req = urllib.request.Request(
                    webhook_url,
                    data=json.dumps({"name": hook_name, "task_id": task_id, "payload": payload, "result": result}).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(req, timeout=1.0)
            except Exception:
                pass
