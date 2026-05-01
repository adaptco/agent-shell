from __future__ import annotations
import json
from typing import Dict, Any
from runtime.plugin_base import ToolPlugin
from runtime.config import resolve_path


class MCPToolPlugin(ToolPlugin):
    """
    Adapter for Model Context Protocol (MCP) servers.
    Provides dynamic tool registration and execution.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.specs: Dict[str, Dict] = {}
        # For now, we'll implement a built-in 'discover_skills' tool 
        # as a bridge to Phase 4, served via the MCP adapter logic.
        self._load_local_mcp_specs()

    def _load_local_mcp_specs(self):
        """Mock discovery of tools from an MCP-like registry"""
        # In a real implementation, this would connect to an MCP server
        # and fetch tool definitions via SSE or stdio.
        # For debugging, we expose the 'discover_skills' tool here.
        registry_dir = resolve_path(self.config, self.config["tools"]["registry_dir"])
        discovery_spec_path = registry_dir / "discover_skills.json"
        
        if discovery_spec_path.exists():
            from runtime.utils import read_json
            self.specs["discover_skills"] = read_json(discovery_spec_path)

    def get_tool_specs(self) -> Dict[str, Dict]:
        return self.specs

    def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "discover_skills":
            from runtime.skill_discovery import SkillDiscovery
            discovery = SkillDiscovery(self.config)
            return discovery.run(tool_input)
        
        raise ValueError(f"MCP tool not found: {tool_name}")
