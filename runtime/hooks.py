from runtime.config import resolve_path
from runtime.utils import read_json
from runtime.validation import validate
from runtime.hook_plugins import BuiltinHookHandler


class HookRegistry:
    def __init__(self, cfg):
        self.cfg = cfg
        self.registry = {}
        self.handlers = {}
        
        # Load legacy hook specs for validation
        hook_dir = resolve_path(cfg, cfg["hooks"]["registry_dir"])
        for path in sorted(hook_dir.glob("*.json")):
            data = read_json(path)
            self.registry[data["name"]] = data

        # Load handlers
        self._load_handlers()

    def _load_handlers(self):
        """Load hook handlers from config"""
        # Always load builtin handler for backward compatibility
        self.handlers["builtin"] = BuiltinHookHandler(self.cfg)
        
        handlers_cfg = self.cfg.get("plugins", {}).get("hooks", [])
        for handler_cfg in handlers_cfg:
            if not handler_cfg.get("enabled", True):
                continue
            
            handler_type = handler_cfg["type"]
            if handler_type == "builtin":
                continue # Already loaded

            continue
    def run(self, name: str, task_id: str, payload: dict) -> dict:
        """Run all registered hook handlers for a given hook name"""
        spec = self.registry.get(name)
        if spec:
            validate({"task_id": task_id, "payload": payload}, spec["input_schema"])
        
        final_result = {"allow": True, "payload": payload}
        
        for handler in self.handlers.values():
            result = handler.handle(name, task_id, payload)
            if not result.get("allow", True):
                final_result = result
                break
            payload = result.get("payload", payload)
            final_result["payload"] = payload
        
        if spec:
            validate(final_result, spec["output_schema"])
            
        return final_result
