from abc import ABC, abstractmethod
from typing import Dict, Any

class ToolPlugin(ABC):
    """Base class for tool implementations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def get_tool_specs(self) -> Dict[str, Dict]:
        """Return {tool_name: {description, input_schema, output_schema}}"""
        pass
    
    @abstractmethod
    def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool and return result"""
        pass


class HookHandler(ABC):
    """Base class for hook implementations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def handle(self, hook_name: str, task_id: str, payload: dict) -> dict:
        """Handle hook and return {allow, payload, reason}"""
        pass
