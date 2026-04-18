from __future__ import annotations
import json
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, Any
from runtime.config import resolve_path
from runtime.utils import read_json
from runtime.validation import validate
from runtime.plugin_base import ToolPlugin


class BuiltinToolPlugin(ToolPlugin):
    """Wraps existing builtin tools (file_read, bash, web_search)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.specs = {}
        tool_dir = resolve_path(config, config["tools"]["registry_dir"])
        for name in ["file_read", "bash", "web_search"]:
            path = tool_dir / f"{name}.json"
            if path.exists():
                self.specs[name] = read_json(path)

    def get_tool_specs(self) -> Dict[str, Dict]:
        return self.specs
    
    def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "file_read":
            return self._file_read(tool_input)
        elif tool_name == "bash":
            return self._bash(tool_input)
        elif tool_name == "web_search":
            return self._web_search(tool_input)
        else:
            raise ValueError(f"unknown builtin tool: {tool_name}")

    def _safe_workspace_path(self, relative: str) -> Path:
        root = Path(self.config["_workspace"]).resolve()
        candidate = (root / relative).resolve()
        if root not in [candidate, *candidate.parents]:
            raise ValueError("path escapes workspace")
        return candidate

    def _file_read(self, tool_input: dict) -> dict:
        path = self._safe_workspace_path(tool_input["path"])
        max_bytes = int(tool_input.get("max_bytes", 65536))
        content = path.read_text(encoding="utf-8")[:max_bytes]
        return {"path": str(path.relative_to(Path(self.config["_workspace"]))), "content": content, "bytes_read": len(content.encode('utf-8'))}

    def _bash(self, tool_input: dict) -> dict:
        command = tool_input["command"]
        timeout = int(self.config["tools"]["bash"]["timeout_seconds"])
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=self.config["_workspace"],
            timeout=timeout,
        )
        return {"stdout": completed.stdout, "stderr": completed.stderr, "exit_code": int(completed.returncode)}

    def _web_search(self, tool_input: dict) -> dict:
        provider = self.config["tools"]["web_search"]["provider"]
        query = tool_input["query"]
        limit = int(tool_input.get("limit", 5))
        if provider == "mock":
            results = self.config["tools"]["web_search"]["mock_results"][:limit]
            return {"query": query, "results": results}
        if provider == "duckduckgo":
            base = self.config["tools"]["web_search"]["duckduckgo_url"]
            params = urllib.parse.urlencode({"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"})
            with urllib.request.urlopen(base + "?" + params, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
            results = []
            if data.get("AbstractText"):
                results.append({"title": data.get("Heading", query), "url": data.get("AbstractURL", ""), "snippet": data["AbstractText"]})
            for item in data.get("RelatedTopics", []):
                if isinstance(item, dict) and item.get("Text"):
                    results.append({"title": item["Text"][:80], "url": item.get("FirstURL", ""), "snippet": item["Text"]})
                    if len(results) >= limit:
                        break
            return {"query": query, "results": results[:limit]}
        raise ValueError(f"unsupported web search provider: {provider}")


class ToolRegistry:
    def __init__(self, cfg):
        self.cfg = cfg
        self.registry = {}
        self.plugins = {}
        
        # Load builtin tools
        self._register_builtin_tools()
        
        # Load plugins
        self._load_plugins()
    
    def _register_builtin_tools(self):
        """Register file_read, bash, web_search via BuiltinToolPlugin"""
        plugin = BuiltinToolPlugin(self.cfg)
        for tool_name, spec in plugin.get_tool_specs().items():
            self.registry[tool_name] = spec
            self.plugins[tool_name] = plugin
    
    def _load_plugins(self):
        """Load tool plugins from config"""
        plugins_cfg = self.cfg.get("plugins", {}).get("tools", [])
        for plugin_cfg in plugins_cfg:
            if not plugin_cfg.get("enabled", True):
                continue
            
            plugin_type = plugin_cfg["type"]
            if plugin_type == "builtin":
                continue # Already loaded
            
            # Lazy load plugins
            if plugin_type == "mcp":
                from runtime.mcp_adapter import MCPToolPlugin
                plugin = MCPToolPlugin(self.cfg)
            elif plugin_type == "desktop":
                from runtime.computer_use_tool import ComputerUseTool
                plugin = ComputerUseTool(self.cfg)
            else:
                continue
            
            # Register all tools from plugin
            for tool_name, spec in plugin.get_tool_specs().items():
                self.registry[tool_name] = spec
                self.plugins[tool_name] = plugin
    
    def execute(self, name: str, tool_input: dict) -> dict:
        """Execute tool via plugin"""
        if name not in self.registry:
            raise ValueError(f"unknown tool: {name}")
        
        spec = self.registry[name]
        validate(tool_input, spec["input_schema"])
        
        # Dispatch to plugin
        plugin = self.plugins.get(name)
        if plugin:
            result = plugin.execute(name, tool_input)
        else:
            # Fallback (should not happen with BuiltinToolPlugin registered)
            raise ValueError(f"no plugin found for tool: {name}")
        
        validate(result, spec["output_schema"])
        return result
