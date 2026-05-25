import logging
from runtime.safety_hooks import SafetyHookHandler

class HookRegistry:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.handlers = {}
        self.logger = logging.getLogger("runtime.hooks")

    def register_handlers(self):
        # Fallback to empty dict if handlers key is missing
        handlers_list = self.cfg.get("runtime", {}).get("handlers", [])
        
        for handler_cfg in handlers_list:
            handler_type = handler_cfg.get("type")
            if not handler_type:
                continue
                
            if handler_type == "builtin":
                continue  # Already loaded
                
            if handler_type == "safety":
                try:
                    handler = SafetyHookHandler(self.cfg)
                    self.handlers[handler_type] = handler
                    self.logger.info("Successfully registered safety hooks handler")
                except Exception as e:
                    self.logger.error(f"Failed to initialize safety handler: {e}")
