from runtime.config import resolve_path
from runtime.utils import read_json
from runtime.validation import validate


class HookRegistry:
    def __init__(self, cfg):
        self.cfg = cfg
        self.registry = {}
        hook_dir = resolve_path(cfg, cfg["hooks"]["registry_dir"])
        for path in sorted(hook_dir.glob("*.json")):
            data = read_json(path)
            self.registry[data["name"]] = data

    def run(self, name: str, task_id: str, payload: dict) -> dict:
        spec = self.registry[name]
        validate({"task_id": task_id, "payload": payload}, spec["input_schema"])
        result = {"allow": True, "payload": payload}
        if name == "before_tool_call":
            tool_name = payload.get("tool_name")
            if tool_name == "bash":
                command = payload.get("tool_input", {}).get("command", "")
                token = command.strip().split(" ", 1)[0]
                allow = token in self.cfg["tools"]["bash"]["allow_prefixes"]
                if not allow:
                    result = {"allow": False, "payload": payload, "reason": f"command prefix not allowed: {token}"}
        if name == "before_delegate":
            subagent_name = payload.get("subagent_name")
            subagent_path = resolve_path(self.cfg, self.cfg["subagent_dir"]) / f"{subagent_name}.md"
            if not subagent_path.exists():
                result = {"allow": False, "payload": payload, "reason": f"unknown subagent: {subagent_name}"}
        
        webhooks = self.cfg.get("webhooks", {})
        webhook_url = webhooks.get("url")
        webhook_events = webhooks.get("events", [])
        if webhook_url and (name in webhook_events or "*" in webhook_events):
            try:
                import urllib.request
                import json
                req = urllib.request.Request(
                    webhook_url,
                    data=json.dumps({"name": name, "task_id": task_id, "payload": payload, "result": result}).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(req, timeout=1.0)
            except Exception:
                pass

        validate(result, spec["output_schema"])
        return result

