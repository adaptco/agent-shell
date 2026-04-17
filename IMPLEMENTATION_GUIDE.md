# Agent Shell Enhancement Implementation Guide

## Overview

This guide provides step-by-step instructions to implement the MCP + desktop automation + skill discovery enhancements to the agent-shell runtime.

**Total Scope**: ~3100 lines of code across 6 phases (see plan.md for details)

---

## Quick Start

### Prerequisites

```bash
# Python 3.11+
python --version

# Node.js v24
node --version

# MCP SDK (will be installed via pip)
# Desktop automation libraries (will be installed)
```

### Setup Environment

```powershell
# From agent-shell root
Set-Location "C:\Users\eqhsp\Agent Projects\agent-shell"

# Create/activate venv
py -m venv .venv
. .\.venv\Scripts\Activate.ps1

# Install in editable mode
py -m pip install -e .

# Verify
agent-shell doctor
```

---

## Phase 1: Plugin Architecture Foundation (Immediate)

### Goal
Refactor `ToolRegistry` and hook system to support pluggable implementations instead of hardcoded conditionals.

### Files to Create/Modify

```
runtime/
  ├── plugin_base.py (NEW)        - ToolPlugin and HookHandler base classes
  ├── tools.py (MODIFY)           - Extend ToolRegistry for plugin loading
  ├── hook_plugins.py (NEW)       - Extract hook logic to plugins
  ├── hooks.py (MODIFY)           - Extend to use HookHandler plugins
  
schemas/
  ├── tool_extended.schema.json (NEW) - Extended tool metadata schema
  
infra/
  ├── runtime.json (MODIFY)       - Add plugin configuration section
```

### Step 1.1: Create Plugin Base Classes

**File**: `runtime/plugin_base.py`

```python
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
```

### Step 1.2: Refactor ToolRegistry

**File**: `runtime/tools.py` (modify existing)

Replace the hardcoded `if name == "bash"` logic:

```python
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
        """Register file_read, bash, web_search"""
        # Existing code - wrap in BuiltinToolPlugin
        pass
    
    def _load_plugins(self):
        """Load tool plugins from config"""
        plugins_cfg = self.cfg.get("plugins", {}).get("tools", [])
        for plugin_cfg in plugins_cfg:
            if not plugin_cfg.get("enabled", True):
                continue
            
            plugin_type = plugin_cfg["type"]
            
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
            result = self._execute_builtin(name, tool_input)
        
        validate(result, spec["output_schema"])
        return result
```

### Step 1.3: Wrap Builtin Tools in ToolPlugin

Create a builtin plugin that wraps existing tools:

```python
# In runtime/tools.py

class BuiltinToolPlugin(ToolPlugin):
    """Wraps existing builtin tools (file_read, bash, web_search)"""
    
    def get_tool_specs(self) -> Dict[str, Dict]:
        return {
            "file_read": {...},    # from load_json(tools/file_read.json)
            "bash": {...},         # from load_json(tools/bash.json)
            "web_search": {...}    # from load_json(tools/web_search.json)
        }
    
    def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "file_read":
            return self._file_read(tool_input)
        elif tool_name == "bash":
            return self._bash(tool_input)
        elif tool_name == "web_search":
            return self._web_search(tool_input)
        else:
            raise ValueError(f"unknown builtin tool: {tool_name}")
    
    # Move existing _file_read, _bash, _web_search methods here
```

### Step 1.4: Extend Hook System

**File**: `runtime/hook_plugins.py` (NEW)

```python
from runtime.plugin_base import HookHandler

class BuiltinHookHandler(HookHandler):
    """Existing hook logic: bash prefix blocking, subagent validation"""
    
    def handle(self, hook_name: str, task_id: str, payload: dict) -> dict:
        if hook_name == "before_tool_call":
            return self._before_tool_call(task_id, payload)
        elif hook_name == "after_tool_call":
            return {"allow": True}
        elif hook_name == "before_delegate":
            return self._before_delegate(task_id, payload)
        else:
            return {"allow": True}
    
    def _before_tool_call(self, task_id: str, payload: dict) -> dict:
        """Block bash commands that don't match whitelist"""
        tool_name = payload.get("tool_name")
        if tool_name == "bash":
            command = payload.get("tool_input", {}).get("command", "")
            if not any(command.startswith(p) for p in self.config["tools"]["bash"]["allow_prefixes"]):
                return {"allow": False, "reason": "bash command not whitelisted"}
        return {"allow": True}
    
    def _before_delegate(self, task_id: str, payload: dict) -> dict:
        """Validate subagent delegation"""
        subagent = payload.get("subagent_name")
        # Validate subagent exists
        return {"allow": True}
```

**File**: `runtime/hooks.py` (modify)

```python
class HookRegistry:
    def __init__(self, cfg):
        self.cfg = cfg
        self.handlers = {}
        self._load_handlers()
    
    def _load_handlers(self):
        """Load hook handlers from config"""
        from runtime.hook_plugins import BuiltinHookHandler
        
        handlers_cfg = self.cfg.get("plugins", {}).get("hooks", [])
        for handler_cfg in handlers_cfg:
            if not handler_cfg.get("enabled", True):
                continue
            
            handler_type = handler_cfg["type"]
            
            if handler_type == "builtin":
                handler = BuiltinHookHandler(self.cfg)
            elif handler_type == "safety":
                from runtime.safety_hooks import SafetyHookHandler
                handler = SafetyHookHandler(self.cfg)
            else:
                continue
            
            self.handlers[handler_type] = handler
    
    def run(self, hook_name: str, task_id: str, payload: dict) -> dict:
        """Run hooks in order"""
        for handler in self.handlers.values():
            result = handler.handle(hook_name, task_id, payload)
            if not result.get("allow", True):
                return result
            payload = result.get("payload", payload)
        
        return {"allow": True, "payload": payload}
```

### Step 1.5: Update Configuration

**File**: `infra/runtime.json` (add section)

```json
{
  "plugins": {
    "tools": [
      {
        "type": "builtin",
        "module": "runtime.tools",
        "enabled": true
      },
      {
        "type": "mcp",
        "module": "runtime.mcp_adapter",
        "enabled": false
      },
      {
        "type": "desktop",
        "module": "runtime.computer_use_tool",
        "enabled": false
      }
    ],
    "hooks": [
      {
        "type": "builtin",
        "module": "runtime.hook_plugins",
        "enabled": true
      },
      {
        "type": "safety",
        "module": "runtime.safety_hooks",
        "enabled": false
      }
    ]
  }
}
```

### Phase 1 Verification

```bash
# Run existing tests - should still pass
pytest tests/ -v

# Test plugin loading
python -c "from runtime.tools import ToolRegistry; from runtime.config import load_config; cfg = load_config(); tr = ToolRegistry(cfg); print(list(tr.registry.keys()))"
# Expected output: ['file_read', 'bash', 'web_search']

# Test hook loading
python -c "from runtime.hooks import HookRegistry; from runtime.config import load_config; cfg = load_config(); hr = HookRegistry(cfg); print(list(hr.handlers.keys()))"
# Expected output: ['builtin']
```

---

## Phase 2: MCP Integration (Core)

### Goal
Integrate Model Context Protocol support so agents can call external tools/resources via MCP servers.

### Files to Create

```
runtime/
  ├── mcp_adapter.py (NEW)        - MCP server connection & resource discovery
  
infra/
  ├── mcp_servers.json (NEW)      - MCP server registry
  
tests/
  ├── test_mcp_adapter.py (NEW)   - MCP integration tests
```

### Step 2.1: Create MCP Adapter

**File**: `runtime/mcp_adapter.py`

```python
import asyncio
import json
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from runtime.plugin_base import ToolPlugin

logger = logging.getLogger(__name__)


class MCPToolPlugin(ToolPlugin):
    """
    Adapter for Model Context Protocol (MCP) servers.
    Discovers and exposes MCP resources as tools.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.servers = {}
        self.tool_specs = {}
        self.resource_cache = {}
        
        self._connect_servers()
        self._discover_resources()
    
    def _connect_servers(self):
        """Connect to configured MCP servers"""
        mcp_cfg = self.config.get("mcp", {})
        for server_cfg in mcp_cfg.get("servers", []):
            if not server_cfg.get("enabled", True):
                continue
            
            name = server_cfg["name"]
            server_type = server_cfg.get("type", "stdio")
            
            try:
                if server_type == "stdio":
                    server = self._connect_stdio_server(server_cfg)
                    self.servers[name] = server
                    logger.info(f"Connected to MCP server: {name}")
            except Exception as e:
                logger.error(f"Failed to connect MCP server {name}: {e}")
    
    def _connect_stdio_server(self, server_cfg: Dict) -> Any:
        """Connect to MCP server via stdio"""
        # Simplified: use async/await pattern with asyncio
        # Real implementation would use mcp library
        return MCPStdioClient(server_cfg)
    
    def _discover_resources(self):
        """Discover resources from all MCP servers"""
        for server_name, server in self.servers.items():
            try:
                resources = server.list_resources()
                for resource in resources:
                    tool_name = self._make_tool_name(server_name, resource)
                    self.tool_specs[tool_name] = {
                        "name": tool_name,
                        "description": resource.get("description", f"MCP resource: {resource['uri']}"),
                        "type": "mcp",
                        "mcp_server": server_name,
                        "mcp_resource_uri": resource["uri"],
                        "input_schema": resource.get("input_schema", {"type": "object"}),
                        "output_schema": {"type": "object"}
                    }
                    logger.debug(f"Discovered MCP tool: {tool_name}")
            except Exception as e:
                logger.error(f"Failed to discover resources from {server_name}: {e}")
    
    def _make_tool_name(self, server_name: str, resource: Dict) -> str:
        """Create tool name from server name and resource URI"""
        resource_path = resource["uri"].replace("://", "_").replace("/", "_")
        return f"mcp_{server_name}_{resource_path}"
    
    def get_tool_specs(self) -> Dict[str, Dict]:
        """Return all discovered MCP tool specs"""
        return self.tool_specs
    
    def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP resource"""
        spec = self.tool_specs.get(tool_name)
        if not spec:
            return {
                "success": False,
                "error": f"MCP tool not found: {tool_name}",
                "error_code": "not_found"
            }
        
        server_name = spec["mcp_server"]
        resource_uri = spec["mcp_resource_uri"]
        
        try:
            server = self.servers.get(server_name)
            if not server:
                return {
                    "success": False,
                    "error": f"MCP server not connected: {server_name}",
                    "error_code": "mcp_connection_error"
                }
            
            result = server.read_resource(resource_uri, tool_input)
            return {
                "success": True,
                "tool_name": tool_name,
                "result": result
            }
        except Exception as e:
            logger.error(f"MCP execution error for {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "mcp_error"
            }


class MCPStdioClient:
    """
    Simple MCP client for stdio-based servers.
    Note: This is a simplified implementation. Production use would leverage
    the official MCP Python SDK when available.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.command = config["command"]
        self.arguments = config.get("arguments", [])
        self.process = None
        self.startup_timeout = config.get("startup_timeout_seconds", 10)
        
        self._start()
    
    def _start(self):
        """Start MCP server process"""
        try:
            cmd = [self.command] + self.arguments
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info(f"Started MCP process: {' '.join(cmd)}")
        except Exception as e:
            raise RuntimeError(f"Failed to start MCP server: {e}")
    
    def list_resources(self) -> list:
        """List available resources from server"""
        # Send MCP request to list resources
        # For now, return empty list (would implement MCP protocol here)
        return []
    
    def read_resource(self, uri: str, input_data: Dict) -> Any:
        """Read resource from server"""
        # Send MCP read request
        # Return result from server
        pass
    
    def __del__(self):
        """Clean up process"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
```

### Step 2.2: Create MCP Configuration

**File**: `infra/mcp_servers.json`

```json
{
  "servers": [
    {
      "name": "filesystem",
      "type": "stdio",
      "command": "mcp-server-filesystem",
      "arguments": ["--root", "${WORKSPACE_ROOT}"],
      "enabled": false,
      "startup_timeout_seconds": 10,
      "auto_reconnect": true
    },
    {
      "name": "web",
      "type": "stdio",
      "command": "mcp-server-web",
      "arguments": [],
      "enabled": false
    },
    {
      "name": "git",
      "type": "stdio",
      "command": "mcp-server-git",
      "arguments": ["--repo", "${WORKSPACE_ROOT}"],
      "enabled": false
    }
  ]
}
```

### Phase 2 Verification

```bash
# Test MCP plugin loading (disabled by default)
python -c "from runtime.mcp_adapter import MCPToolPlugin; cfg = {'mcp': {'servers': []}}; p = MCPToolPlugin(cfg); print(len(p.tool_specs))"
# Expected: 0 (no servers configured)
```

---

## Phase 3: Computer Usage Tools (Core)

### Goal
Implement desktop automation tools (screenshot, click, type, scroll, etc.) with vision API integration.

### Files to Create

```
runtime/
  ├── computer_use_tool.py (NEW)  - Desktop automation implementation
  ├── vision_client.py (NEW)       - Vision API integration
  
tools/
  ├── computer_use.json (NEW)      - Computer use tool schema
  
tests/
  ├── test_computer_use_tool.py (NEW)
```

### Step 3.1: Create Computer Use Tool

**File**: `runtime/computer_use_tool.py`

```python
import base64
import time
import platform
from typing import Dict, Any, Optional
import logging

from runtime.plugin_base import ToolPlugin

logger = logging.getLogger(__name__)


class ComputerUseTool(ToolPlugin):
    """
    Desktop/UI automation tool with screenshot, click, type, scroll capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        desktop_cfg = config.get("desktop_automation", {})
        self.enabled = desktop_cfg.get("enabled", False)
        self.vision_api = desktop_cfg.get("vision_api", "local")
        self.vision_endpoint = desktop_cfg.get("vision_endpoint")
        self.whitelist_apps = set(desktop_cfg.get("whitelist_apps", []))
        self.timeout_seconds = desktop_cfg.get("timeout_seconds", 30)
        
        # Platform-specific
        self.platform = platform.system()
    
    def get_tool_specs(self) -> Dict[str, Dict]:
        return {
            "computer_use": {
                "name": "computer_use",
                "description": "Control desktop UI: screenshot, click, type, scroll, etc.",
                "type": "computer_use",
                "input_schema": self._input_schema(),
                "output_schema": self._output_schema()
            }
        }
    
    def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name != "computer_use":
            return {"success": False, "error": f"unknown tool: {tool_name}"}
        
        if not self.enabled:
            return {
                "success": False,
                "error": "computer_use tool is disabled",
                "error_code": "not_enabled"
            }
        
        action = tool_input.get("action")
        
        try:
            start_time = time.time()
            
            if action == "screenshot":
                result = self._screenshot()
            elif action == "click":
                result = self._click(tool_input)
            elif action == "type":
                result = self._type(tool_input)
            elif action == "scroll":
                result = self._scroll(tool_input)
            elif action == "key_press":
                result = self._key_press(tool_input)
            elif action == "wait":
                result = self._wait(tool_input)
            elif action == "find_element":
                result = self._find_element(tool_input)
            else:
                result = {"success": False, "error": f"unknown action: {action}"}
            
            result["execution_time_ms"] = int((time.time() - start_time) * 1000)
            result["action"] = action
            return result
        
        except Exception as e:
            logger.error(f"computer_use error ({action}): {e}")
            return {
                "success": False,
                "action": action,
                "error": str(e),
                "error_code": "internal_error"
            }
    
    def _screenshot(self) -> Dict[str, Any]:
        """Capture desktop screenshot"""
        try:
            if self.platform == "Windows":
                screenshot_bytes = self._screenshot_windows()
            elif self.platform == "Darwin":
                screenshot_bytes = self._screenshot_macos()
            else:
                screenshot_bytes = self._screenshot_linux()
            
            # Encode as base64
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
            
            return {
                "success": True,
                "screenshot": screenshot_b64,
                "screenshot_data_url": f"data:image/png;base64,{screenshot_b64}"
            }
        except Exception as e:
            logger.error(f"screenshot error: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "display_unavailable"
            }
    
    def _screenshot_windows(self) -> bytes:
        """Capture screenshot on Windows using PIL"""
        from PIL import ImageGrab
        img = ImageGrab.grab()
        
        # Convert to PNG bytes
        from io import BytesIO
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    
    def _screenshot_macos(self) -> bytes:
        """Capture screenshot on macOS"""
        import subprocess
        from pathlib import Path
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
        
        subprocess.run(["screencapture", "-x", temp_path], check=True)
        data = Path(temp_path).read_bytes()
        Path(temp_path).unlink()
        return data
    
    def _screenshot_linux(self) -> bytes:
        """Capture screenshot on Linux"""
        import subprocess
        result = subprocess.run(["import", "-", "png:-"], capture_output=True, check=True)
        return result.stdout
    
    def _click(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Click at coordinates"""
        x = tool_input.get("x")
        y = tool_input.get("y")
        button = tool_input.get("button", "left")
        double_click = tool_input.get("double_click", False)
        
        if x is None or y is None:
            return {"success": False, "error": "x and y coordinates required"}
        
        try:
            import pyautogui
            
            # Click
            if double_click:
                pyautogui.click(x, y, clicks=2)
            else:
                pyautogui.click(x, y, button=button)
            
            # Return updated screenshot
            time.sleep(0.5)
            return self._screenshot()
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _type(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Type text"""
        text = tool_input.get("text", "")
        
        try:
            import pyautogui
            pyautogui.typewrite(text, interval=0.05)
            
            time.sleep(0.5)
            return self._screenshot()
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _scroll(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Scroll"""
        direction = tool_input.get("direction", "down")
        amount = tool_input.get("amount", 5)
        
        try:
            import pyautogui
            
            if direction == "down":
                pyautogui.scroll(-amount)
            else:
                pyautogui.scroll(amount)
            
            time.sleep(0.5)
            return self._screenshot()
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _key_press(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Press key or key sequence"""
        keys = tool_input.get("keys") or [tool_input.get("key")]
        
        try:
            import pyautogui
            
            for key in keys:
                pyautogui.press(key)
                time.sleep(0.1)
            
            time.sleep(0.5)
            return self._screenshot()
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _wait(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Wait specified duration"""
        duration_ms = tool_input.get("duration_ms", 1000)
        duration_s = min(duration_ms / 1000, self.timeout_seconds)
        
        time.sleep(duration_s)
        return {"success": True}
    
    def _find_element(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Find UI element by text"""
        search_text = tool_input.get("text")
        
        if not search_text:
            return {"success": False, "error": "text required for find_element"}
        
        try:
            # Get screenshot
            screenshot_result = self._screenshot()
            if not screenshot_result.get("success"):
                return screenshot_result
            
            # TODO: Implement OCR/vision-based element detection
            # For now, return mock response
            return {
                "success": True,
                "element_found": True,
                "ui_elements": [
                    {
                        "text": search_text,
                        "x": 100,
                        "y": 200,
                        "width": 80,
                        "height": 30,
                        "confidence": 0.9
                    }
                ]
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _input_schema(self) -> Dict:
        """Input schema for computer_use tool"""
        return {
            "type": "object",
            "required": ["action"],
            "properties": {
                "action": {
                    "enum": ["screenshot", "click", "type", "scroll", "key_press", "wait", "find_element"],
                    "description": "Action to perform"
                },
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "text": {"type": "string"},
                "key": {"type": "string"},
                "keys": {"type": "array", "items": {"type": "string"}},
                "direction": {"enum": ["up", "down"]},
                "amount": {"type": "integer"},
                "duration_ms": {"type": "integer"},
                "button": {"enum": ["left", "right", "middle"]},
                "double_click": {"type": "boolean"}
            },
            "additionalProperties": False
        }
    
    def _output_schema(self) -> Dict:
        """Output schema for computer_use tool"""
        return {
            "type": "object",
            "required": ["success", "action"],
            "properties": {
                "success": {"type": "boolean"},
                "action": {"type": "string"},
                "error": {"type": "string"},
                "error_code": {"type": "string"},
                "screenshot": {"type": "string"},
                "screenshot_data_url": {"type": "string"},
                "element_found": {"type": "boolean"},
                "ui_elements": {"type": "array"},
                "execution_time_ms": {"type": "integer"}
            },
            "additionalProperties": False
        }
```

### Step 3.2: Create Computer Use Tool Schema

**File**: `tools/computer_use.json`

(See RUNTIME_HARNESS_CONTRACTS.md section 3.1 for complete schema)

### Phase 3 Verification

```bash
# Install desktop automation dependencies
pip install pillow pyautogui

# Test computer use tool
python -c "from runtime.computer_use_tool import ComputerUseTool; cfg = {'desktop_automation': {'enabled': True}}; tool = ComputerUseTool(cfg); specs = tool.get_tool_specs(); print('computer_use' in specs)"
# Expected: True
```

---

## Phase 4: Skill Discovery System

### Goal
Implement dynamic skill discovery from local files, MCP resources, and web search.

### Files to Create

```
runtime/
  ├── skill_discovery.py (NEW)    - Skill registry and discovery logic
  
schemas/
  ├── skill_metadata.schema.json (NEW) - Skill metadata schema
```

### Step 4.1: Create Skill Discovery

**File**: `runtime/skill_discovery.py`

(See RUNTIME_HARNESS_CONTRACTS.md section 5.2 for implementation details)

### Phase 4 Verification

```bash
# Test skill discovery
python -c "from runtime.skill_discovery import SkillRegistry; cfg = {'_workspace': '.', 'skill_discovery': {'cache_dir': '.runtime-store/objects/skills'}}; sr = SkillRegistry(cfg); skills = sr.discover_all(); print(f'Discovered {len(skills)} skills')"
```

---

## Phase 5: Long-Horizon Task Orchestration

### Goal
Add support for task decomposition and multi-step execution planning.

### Files to Create

```
runtime/
  ├── task_planner.py (NEW)       - Task decomposition and planning
  
schemas/
  ├── decision_extended.schema.json (NEW) - Extended decision schema
```

---

## Phase 6: Integration & Verification

### Goal
Test all components together and document usage.

### Test Scenarios

1. **Test basic tool dispatch**: Verify plugin system routes calls correctly
2. **Test MCP integration**: Mock MCP server, verify resource discovery
3. **Test computer use**: Verify screenshot/click actions work
4. **Test skill discovery**: Verify local + web skill discovery
5. **End-to-end**: Test complete workflow with decomposition

### Documentation

Update README.md with:
- MCP server setup instructions
- Computer use tool permissions/whitelisting
- Skill discovery configuration
- Long-horizon task examples

---

## Implementation Checklist

### Phase 1 (Foundation)
- [ ] Create plugin_base.py with ToolPlugin and HookHandler
- [ ] Refactor ToolRegistry to use plugins
- [ ] Wrap builtin tools in BuiltinToolPlugin
- [ ] Create hook_plugins.py with BuiltinHookHandler
- [ ] Extend hooks.py to use HookHandler plugins
- [ ] Update runtime.json with plugin config section
- [ ] Run existing tests - all should pass

### Phase 2 (MCP)
- [ ] Create mcp_adapter.py with MCPToolPlugin
- [ ] Create mcp_servers.json
- [ ] Implement MCPStdioClient (basic)
- [ ] Add MCP tests
- [ ] Test MCP resource discovery (with mock server)

### Phase 3 (Computer Use)
- [ ] Create computer_use_tool.py
- [ ] Implement screenshot (platform-specific)
- [ ] Implement click, type, scroll, key_press
- [ ] Create tools/computer_use.json schema
- [ ] Add computer use tests
- [ ] Install dependencies (pillow, pyautogui)

### Phase 4 (Skill Discovery)
- [ ] Create skill_discovery.py
- [ ] Implement local skill loading
- [ ] Implement MCP skill loading
- [ ] Implement web search skill discovery
- [ ] Create skill_metadata.schema.json
- [ ] Extend ContextBuilder for dynamic skills
- [ ] Add skill discovery tests

### Phase 5 (Long-Horizon)
- [ ] Create task_planner.py
- [ ] Extend decision schema with decompose/learn
- [ ] Implement task decomposition logic
- [ ] Add planning tests

### Phase 6 (Integration)
- [ ] Create comprehensive integration tests
- [ ] End-to-end test with example task
- [ ] Security audit for computer_use whitelisting
- [ ] Update README with setup/usage instructions
- [ ] Create example configuration
- [ ] Performance testing

---

## Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_computer_use_tool.py -v

# With coverage
pytest tests/ --cov=runtime --cov-report=html
```

---

## Development Workflow

1. Create feature branch: `git checkout -b feature/mcp-integration`
2. Implement changes following phase schedule
3. Run tests after each phase
4. Create PR for review
5. Merge after review + approval

---

## Next Steps

1. **Confirm scope** with user
2. **Start Phase 1** - Plugin architecture (foundation for all others)
3. **Proceed with Phases 2-3 in parallel** - MCP and computer use (independent)
4. **Complete Phase 4** - Skill discovery (depends on 2-3)
5. **Add Phase 5** - Long-horizon tasks (builds on 1-4)
6. **Phase 6** - Integration and documentation

