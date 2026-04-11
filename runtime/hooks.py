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
        validate(result, spec["output_schema"])
        return result
