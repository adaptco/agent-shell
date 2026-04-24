# Agent Shell Runtime Harness Contracts
## Computer Usage Tools & MCP Worker Orchestration

This document specifies the production-grade runtime contracts for integrating:
- **Computer Usage Tools** (desktop automation, UI actuation)
- **MCP (Model Context Protocol)** workers (skill orchestration)
- **Dynamic Skill Discovery** (RAG + web learning)
- **Long-Horizon Task Execution** (recursive self-improvement)

---

## 1. CORE EXECUTION MODEL

### 1.1 Tool Execution Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ AgentLoop.run_task(task)                                        │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │ ContextBuilder.build(task, history)
        │ - Assemble task context
        │ - Inject available skills
        │ - Load MCP resource descriptions
        │ - Include security policies
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │ before_model_call hook
        │ - Capability negotiation
        │ - Dynamic tool injection
        │ - Security checks
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │ LLM.decide(context)
        │ Returns: TypedDecision
        │  - tool_call
        │  - delegate
        │  - final
        └───────────────────────────────────┘
                            │
                ┌───────────┼───────────┐
                │           │           │
                ▼           ▼           ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ tool_call│  │ delegate │  │ final    │
        └──────────┘  └──────────┘  └──────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │ before_tool_call hook
        │ - Safety validation
        │ - Tool authorization
        │ - Rate limiting check
        │ - Whitelist enforcement
        └───────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
    ┌────────────┐   ┌──────────────┐   ┌────────────────┐
    │ ToolPlugin │   │ ToolPlugin   │   │ ToolPlugin     │
    │ (builtin)  │   │ (MCP)        │   │ (computer_use) │
    └────────────┘   └──────────────┘   └────────────────┘
        │ file_read       │ resources         │ screenshot
        │ bash            │ subprocess        │ click
        │ web_search      │ rich_snippets     │ type
        │                 │                   │ key_press
        │                 │                   │ scroll
        └─────────────────┴───────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │ ToolRegistry.execute()
        │ - Validate input schema
        │ - Execute tool action
        │ - Validate output schema
        │ - Capture audit trail
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │ after_tool_call hook
        │ - Post-process results
        │ - Error recovery
        │ - Learning capture
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │ Memory.append(tool_result)
        │ - Journal entry
        │ - State update
        │ - Compaction check
        └───────────────────────────────────┘
                            │
                            └─────────────────────► Continue loop
```

### 1.2 Synchronous Execution Guarantee

All tool execution **MUST** be synchronous (blocking). The current file-based queue and receipt system do not support concurrent execution.

**Property**: At any point in time, exactly **one task** is executing in the runtime (per worker instance).

---

## 2. TOOL PLUGIN ARCHITECTURE

### 2.1 ToolPlugin Base Class

```python
# runtime/plugin_base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ToolPlugin(ABC):
    """
    Abstract base class for all tool implementations.
    Plugins are registered at startup and dispatch via ToolRegistry.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize plugin with runtime config.
        
        Args:
            config: Full runtime configuration dict
        """
        self.config = config
    
    @abstractmethod
    def get_tool_specs(self) -> Dict[str, Dict]:
        """
        Return dict mapping tool names to specifications.
        
        Returns:
            {
                "tool_name": {
                    "description": "...",
                    "input_schema": {...},
                    "output_schema": {...}
                }
            }
        """
        pass
    
    @abstractmethod
    def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name with validated input.
        
        Args:
            tool_name: Name of tool to execute
            tool_input: Validated input dict (already validated against input_schema)
        
        Returns:
            Tool output dict (must validate against output_schema)
        
        Raises:
            ValueError: If tool_name not found
            ToolExecutionError: If execution fails
        """
        pass


class ToolExecutionError(Exception):
    """
    Raised when tool execution fails.
    Must include error details in output dict.
    """
    pass
```

### 2.2 ToolRegistry Refactoring

**Current** (tools.py lines 21-33):
```python
def execute(self, name: str, tool_input: dict) -> dict:
    spec = self.registry[name]
    validate(tool_input, spec["input_schema"])
    if name == "file_read":
        result = self._file_read(tool_input)
    elif name == "bash":
        result = self._bash(tool_input)
    elif name == "web_search":
        result = self._web_search(tool_input)
    else:
        raise ValueError(f"unknown tool: {name}")
    validate(result, spec["output_schema"])
    return result
```

**Refactored** (tools.py):
```python
class ToolRegistry:
    def __init__(self, cfg):
        self.cfg = cfg
        self.registry = {}           # tool specs: {name -> {description, input_schema, ...}}
        self.plugins = {}            # tool plugins: {name -> ToolPlugin instance}
        self._load_builtin_tools()   # file_read, bash, web_search
        self._load_plugins()         # MCP, desktop, custom
    
    def _load_plugins(self):
        """Load tool plugins from config"""
        plugins_cfg = self.cfg.get("plugins", {}).get("tools", [])
        for plugin_cfg in plugins_cfg:
            plugin_type = plugin_cfg.get("type")  # "builtin", "mcp", "desktop"
            if plugin_type == "mcp":
                from runtime.mcp_adapter import MCPToolPlugin
                plugin = MCPToolPlugin(self.cfg)
            elif plugin_type == "desktop":
                from runtime.computer_use_tool import ComputerUseTool
                plugin = ComputerUseTool(self.cfg)
            # Register all tools from this plugin
            for tool_name, spec in plugin.get_tool_specs().items():
                self.registry[tool_name] = spec
                self.plugins[tool_name] = plugin
    
    def execute(self, name: str, tool_input: dict) -> dict:
        """Execute tool via appropriate plugin"""
        if name not in self.registry:
            raise ValueError(f"unknown tool: {name}")
        
        spec = self.registry[name]
        
        # Validate input
        validate(tool_input, spec["input_schema"])
        
        # Dispatch to plugin
        plugin = self.plugins.get(name)
        if plugin:
            result = plugin.execute(name, tool_input)
        else:
            # Backward compatibility: builtin tools
            result = self._execute_builtin(name, tool_input)
        
        # Validate output
        validate(result, spec["output_schema"])
        
        return result
```

---

## 3. COMPUTER USAGE TOOL CONTRACTS

### 3.1 Tool Definition

**File**: `tools/computer_use.json`

```json
{
  "name": "computer_use",
  "description": "Control desktop UI: screenshot, click, type, scroll, key press, element detection",
  "type": "computer_use",
  "implementation": "runtime.computer_use_tool.ComputerUseTool",
  "requires_auth": true,
  "input_schema": {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["action"],
    "properties": {
      "action": {
        "enum": [
          "screenshot",
          "click",
          "type",
          "scroll",
          "key_press",
          "wait",
          "find_element",
          "get_clipboard",
          "set_clipboard"
        ],
        "description": "The desktop control action"
      },
      "x": {
        "type": "integer",
        "description": "X coordinate in pixels (for click, find_element near location)"
      },
      "y": {
        "type": "integer",
        "description": "Y coordinate in pixels (for click, find_element near location)"
      },
      "text": {
        "type": "string",
        "description": "Text to type (for type action) or text to find (for find_element)"
      },
      "key": {
        "type": "string",
        "description": "Key name: 'enter', 'escape', 'tab', 'backspace', 'shift', 'ctrl', 'alt', etc.",
        "enum": [
          "enter", "escape", "tab", "backspace", "shift", "ctrl", "alt", "win",
          "home", "end", "pageup", "pagedown", "up", "down", "left", "right",
          "delete", "insert", "capslock", "numlock", "printscreen",
          "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"
        ]
      },
      "keys": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Sequence of keys for key_press (e.g., ['ctrl', 'c'] for copy)"
      },
      "direction": {
        "enum": ["up", "down"],
        "description": "Scroll direction"
      },
      "amount": {
        "type": "integer",
        "description": "Scroll amount in lines (default: 5)"
      },
      "duration_ms": {
        "type": "integer",
        "minimum": 0,
        "maximum": 30000,
        "description": "Wait duration in milliseconds (max 30s)"
      },
      "search_radius": {
        "type": "integer",
        "description": "Search radius for find_element in pixels (default: 100)"
      },
      "button": {
        "enum": ["left", "right", "middle"],
        "description": "Mouse button for click (default: left)"
      },
      "double_click": {
        "type": "boolean",
        "description": "Double-click instead of single click"
      }
    },
    "additionalProperties": false
  },
  "output_schema": {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["success", "action"],
    "properties": {
      "success": {
        "type": "boolean",
        "description": "Whether action completed successfully"
      },
      "action": {
        "type": "string",
        "description": "The action that was performed"
      },
      "error": {
        "type": "string",
        "description": "Error message if success=false"
      },
      "error_code": {
        "type": "string",
        "enum": [
          "timeout",
          "not_found",
          "permission_denied",
          "invalid_coordinate",
          "display_unavailable",
          "clipboard_error"
        ],
        "description": "Error classification"
      },
      "screenshot": {
        "type": "string",
        "description": "Base64-encoded PNG screenshot (always returned for screenshot action)"
      },
      "screenshot_data_url": {
        "type": "string",
        "description": "Data URL for screenshot (format: data:image/png;base64,...)"
      },
      "ui_elements": {
        "type": "array",
        "description": "Detected UI elements (if action=find_element or screenshot with OCR)",
        "items": {
          "type": "object",
          "required": ["text", "x", "y", "width", "height"],
          "properties": {
            "text": {
              "type": "string",
              "description": "Visible text of element"
            },
            "x": { "type": "integer", "description": "X coordinate" },
            "y": { "type": "integer", "description": "Y coordinate" },
            "width": { "type": "integer" },
            "height": { "type": "integer" },
            "type": {
              "type": "string",
              "enum": ["button", "text_input", "link", "label", "image", "checkbox", "unknown"],
              "description": "Inferred element type"
            },
            "confidence": {
              "type": "number",
              "minimum": 0,
              "maximum": 1,
              "description": "Confidence of detection (0-1)"
            }
          }
        }
      },
      "clipboard_content": {
        "type": "string",
        "description": "Clipboard content (if action=get_clipboard)"
      },
      "element_found": {
        "type": "boolean",
        "description": "Whether element was found (if action=find_element)"
      },
      "matching_elements_count": {
        "type": "integer",
        "description": "Number of matching elements found"
      },
      "cursor_position": {
        "type": "object",
        "properties": {
          "x": { "type": "integer" },
          "y": { "type": "integer" }
        },
        "description": "Current cursor position"
      },
      "active_window": {
        "type": "object",
        "description": "Info about currently active window",
        "properties": {
          "title": { "type": "string" },
          "process": { "type": "string" },
          "pid": { "type": "integer" }
        }
      },
      "execution_time_ms": {
        "type": "integer",
        "description": "Time taken to execute action"
      }
    },
    "additionalProperties": false
  }
}
```

### 3.2 Implementation Contract

```python
# runtime/computer_use_tool.py

class ComputerUseTool(ToolPlugin):
    """
    Desktop/UI automation tool.
    Requires local vision API (screenshot + OCR) or remote vision service.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        desktop_cfg = config.get("desktop_automation", {})
        
        # Required: screenshot capability
        self.vision_api = desktop_cfg.get("vision_api")  # "local", "azure", "openai"
        self.vision_endpoint = desktop_cfg.get("vision_endpoint")
        
        # Optional: UI element detection
        self.ui_detection = desktop_cfg.get("ui_detection", "grid")  # "grid", "ocr", "vision"
        
        # Safety: whitelisting
        self.whitelist_apps = set(desktop_cfg.get("whitelist_apps", []))
        self.safety_policy = desktop_cfg.get("safety_policy", "whitelist")
        
        # Timeout
        self.timeout_seconds = desktop_cfg.get("timeout_seconds", 30)
    
    def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute desktop action.
        
        Contract:
        1. Validate action is allowed (whitelist check)
        2. Acquire display/screenshot
        3. Perform action
        4. Return screenshot + results
        
        All actions are synchronous and timeout-protected.
        """
        action = tool_input.get("action")
        
        try:
            if action == "screenshot":
                return self._screenshot()
            elif action == "click":
                return self._click(tool_input)
            elif action == "type":
                return self._type(tool_input)
            elif action == "scroll":
                return self._scroll(tool_input)
            elif action == "key_press":
                return self._key_press(tool_input)
            elif action == "wait":
                return self._wait(tool_input)
            elif action == "find_element":
                return self._find_element(tool_input)
            elif action == "get_clipboard":
                return self._get_clipboard()
            elif action == "set_clipboard":
                return self._set_clipboard(tool_input)
            else:
                return {"success": False, "action": action, "error": f"unknown action: {action}"}
        except Exception as e:
            return {
                "success": False,
                "action": action,
                "error": str(e),
                "error_code": "internal_error"
            }
    
    def _screenshot(self) -> Dict[str, Any]:
        """
        Capture desktop screenshot.
        
        Returns:
        - screenshot (base64 PNG)
        - ui_elements (if OCR enabled)
        - active_window info
        """
        # Implementation varies by platform:
        # Windows: Use PIL/pyautogui with win32gui
        # Linux: xdotool + scrot
        # macOS: screencapture
        pass
    
    def _click(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Click at coordinates"""
        pass
    
    def _type(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Type text at current cursor position"""
        pass
    
    def _scroll(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Scroll window"""
        pass
    
    def _key_press(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Press key or key combo"""
        pass
    
    def _wait(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Wait specified duration"""
        pass
    
    def _find_element(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find UI element by text.
        Returns list of matching elements with coordinates.
        """
        pass
    
    def _get_clipboard(self) -> Dict[str, Any]:
        """Get clipboard content"""
        pass
    
    def _set_clipboard(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Set clipboard content"""
        pass
```

### 3.3 Safety Contract: Whitelist Policy

**Hook**: `before_tool_call` for `computer_use` tool

```python
# Example hook implementation
def before_tool_call(task_id: str, payload: dict) -> dict:
    """
    Whitelist enforcement for computer_use tool.
    
    Safety properties:
    1. Only whitelisted applications can be controlled
    2. Tool use is logged and auditable
    3. Rapid consecutive clicks are throttled
    4. Clipboard operations require explicit approval
    """
    if payload["tool_name"] != "computer_use":
        return {"allow": True}
    
    action = payload.get("tool_input", {}).get("action")
    
    # Clipboard operations require whitelist approval
    if action in ["get_clipboard", "set_clipboard"]:
        # Check if task has clipboard permission
        if not is_clipboard_permitted(task_id):
            return {
                "allow": False,
                "reason": "clipboard operations not permitted for this task"
            }
    
    # Log all computer_use operations for audit
    audit_log(task_id, "computer_use", action, payload)
    
    return {"allow": True}
```

---

## 4. MCP ADAPTER CONTRACTS

### 4.1 MCP Server Connection

**Configuration** (infra/runtime.json):

```json
{
  "mcp": {
    "servers": [
      {
        "name": "filesystem",
        "type": "stdio",
        "command": "mcp-server-filesystem",
        "arguments": ["--root", "/workspace"],
        "enabled": true,
        "startup_timeout_seconds": 10,
        "resource_cache_ttl_seconds": 3600
      },
      {
        "name": "web",
        "type": "stdio",
        "command": "mcp-server-web-search",
        "arguments": [],
        "enabled": true
      },
      {
        "name": "git",
        "type": "stdio",
        "command": "mcp-server-git",
        "arguments": ["--repo", "/workspace"],
        "enabled": false
      }
    ],
    "connection_pool_size": 5,
    "reconnect_max_attempts": 3,
    "reconnect_backoff_ms": 1000
  }
}
```

### 4.2 MCP Tool Plugin

```python
# runtime/mcp_adapter.py

class MCPToolPlugin(ToolPlugin):
    """
    Adapter for Model Context Protocol (MCP) servers.
    Discovers MCP resources and exposes them as tools.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.servers = {}  # name -> MCPServer instance
        self.tool_specs = {}  # tool_name -> spec
        self._connect_servers()
        self._discover_resources()
    
    def _connect_servers(self):
        """Connect to all configured MCP servers"""
        mcp_cfg = self.config.get("mcp", {})
        for server_cfg in mcp_cfg.get("servers", []):
            if not server_cfg.get("enabled", True):
                continue
            
            name = server_cfg["name"]
            server_type = server_cfg["type"]  # "stdio", "http"
            
            try:
                if server_type == "stdio":
                    server = self._connect_stdio_server(server_cfg)
                elif server_type == "http":
                    server = self._connect_http_server(server_cfg)
                
                self.servers[name] = server
            except Exception as e:
                logger.error(f"Failed to connect MCP server {name}: {e}")
    
    def _discover_resources(self):
        """Discover all resources from MCP servers"""
        for server_name, server in self.servers.items():
            try:
                resources = server.list_resources()
                for resource in resources:
                    tool_name = f"mcp_{server_name}_{resource['uri'].replace('/', '_')}"
                    self.tool_specs[tool_name] = {
                        "name": tool_name,
                        "description": resource.get("description", "MCP resource"),
                        "mcp_server": server_name,
                        "mcp_resource_uri": resource["uri"],
                        "input_schema": resource.get("input_schema", {"type": "object"}),
                        "output_schema": {"type": "object"}
                    }
            except Exception as e:
                logger.error(f"Failed to discover resources from {server_name}: {e}")
    
    def get_tool_specs(self) -> Dict[str, Dict]:
        """Return all discovered MCP tools"""
        return self.tool_specs
    
    def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP resource"""
        spec = self.tool_specs.get(tool_name)
        if not spec:
            return {"success": False, "error": f"MCP tool not found: {tool_name}"}
        
        server_name = spec["mcp_server"]
        resource_uri = spec["mcp_resource_uri"]
        
        try:
            server = self.servers[server_name]
            result = server.read_resource(resource_uri, tool_input)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e), "error_code": "mcp_error"}
```

### 4.3 MCP Tool Schema

**Generated tool spec from MCP resource**:

```json
{
  "name": "mcp_filesystem_read_file",
  "description": "Read file contents from filesystem",
  "type": "mcp",
  "mcp_server": "filesystem",
  "mcp_resource_uri": "file://read",
  "input_schema": {
    "type": "object",
    "required": ["path"],
    "properties": {
      "path": {
        "type": "string",
        "description": "File path to read"
      },
      "max_bytes": {
        "type": "integer",
        "description": "Maximum bytes to read"
      }
    }
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "success": { "type": "boolean" },
      "content": { "type": "string" },
      "bytes_read": { "type": "integer" }
    }
  }
}
```

---

## 5. SKILL DISCOVERY CONTRACTS

### 5.1 Skill Metadata Schema

**File**: `schemas/skill_metadata.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["name", "version", "description", "source"],
  "properties": {
    "name": {
      "type": "string",
      "description": "Unique skill identifier (e.g., 'use_blender_modeling')"
    },
    "version": {
      "type": "string",
      "description": "Semantic version (e.g., '1.0.0')"
    },
    "description": {
      "type": "string",
      "description": "Human-readable skill description"
    },
    "source": {
      "enum": ["local", "mcp", "web", "model_generated"],
      "description": "Where skill originated"
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" },
      "examples": ["modeling", "3d", "blender", "automation"],
      "description": "Tags for categorization and search"
    },
    "execution_contract": {
      "type": "object",
      "properties": {
        "type": {
          "enum": ["tool", "workflow", "model_instruction", "delegation"],
          "description": "How skill is executed"
        },
        "tools_required": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Tools this skill depends on (e.g., ['computer_use', 'web_search'])"
        },
        "expected_inputs": {
          "type": "object",
          "description": "Input schema for skill"
        },
        "expected_outputs": {
          "type": "object",
          "description": "Output schema for skill"
        },
        "estimated_steps": {
          "type": "integer",
          "description": "Estimated reasoning steps required"
        },
        "estimated_time_seconds": {
          "type": "integer",
          "description": "Estimated execution time"
        },
        "learning_path": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Prerequisite skills"
        }
      }
    },
    "acquisition_method": {
      "type": "object",
      "properties": {
        "source": {
          "enum": ["manual", "web_search", "mcp_discovery", "model_generation"],
          "description": "How skill was discovered"
        },
        "search_query": {
          "type": "string",
          "description": "Query used to find skill (if web_search source)"
        },
        "confidence": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "description": "Confidence that skill is accurate"
        },
        "last_verified": {
          "type": "string",
          "format": "date-time",
          "description": "Last verification timestamp"
        }
      }
    },
    "content": {
      "type": "string",
      "description": "Skill instruction/prompt/documentation"
    }
  },
  "additionalProperties": false
}
```

### 5.2 Skill Registry

```python
# runtime/skill_discovery.py

class SkillRegistry:
    """
    Dynamic skill discovery from multiple sources:
    - Local skill/*.md files
    - MCP resources
    - Web search for missing capabilities
    - Agent-generated skills from execution
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.skills = {}  # skill_name -> skill_metadata
        self.cache_dir = Path(config.get("skill_discovery", {}).get("cache_dir", ".runtime-store/objects/skills"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def discover_all(self) -> Dict[str, Dict]:
        """
        Discover all available skills from all sources.
        
        Returns:
            {skill_name: skill_metadata}
        """
        # Load local skills
        self._load_local_skills()
        
        # Load MCP resource skills
        self._load_mcp_skills()
        
        # Load cached web discoveries
        self._load_cached_skills()
        
        return self.skills
    
    def discover_skill(self, query: str) -> Optional[Dict]:
        """
        Search for a specific skill.
        
        Args:
            query: Skill query (e.g., "how to use blender")
        
        Returns:
            Skill metadata if found, else None
        """
        # First, try local/MCP discovery
        for skill in self.skills.values():
            if self._matches_query(skill, query):
                return skill
        
        # If not found, search web
        if self.config.get("skill_discovery", {}).get("web_search_enabled"):
            return self._web_search_skill(query)
        
        return None
    
    def _load_local_skills(self):
        """Load skills from skill/*.md files"""
        skill_dir = Path(self.config.get("_workspace")) / "skill"
        if not skill_dir.exists():
            return
        
        for md_file in skill_dir.glob("*.md"):
            content = md_file.read_text()
            metadata = self._parse_skill_metadata(content)
            if metadata:
                self.skills[metadata["name"]] = metadata
    
    def _load_mcp_skills(self):
        """Load skills from MCP resources"""
        # Get MCP tool plugin
        # For each MCP tool, create skill metadata
        pass
    
    def _load_cached_skills(self):
        """Load previously discovered skills from cache"""
        for cache_file in self.cache_dir.glob("*.json"):
            metadata = read_json(cache_file)
            self.skills[metadata["name"]] = metadata
    
    def _web_search_skill(self, query: str) -> Optional[Dict]:
        """
        Search web for skill information and cache it.
        
        Uses existing web_search tool to find tutorials, documentation, etc.
        """
        # Query: "tutorial on {query}" or "how to {query}"
        # Parse results and create skill metadata
        # Cache result
        pass
    
    def _matches_query(self, skill: Dict, query: str) -> bool:
        """Check if skill matches query"""
        query_lower = query.lower()
        
        # Check name, tags, description
        if query_lower in skill.get("name", "").lower():
            return True
        
        for tag in skill.get("tags", []):
            if query_lower in tag.lower():
                return True
        
        if query_lower in skill.get("description", "").lower():
            return True
        
        return False
    
    def _parse_skill_metadata(self, content: str) -> Optional[Dict]:
        """Parse skill metadata from markdown file"""
        # Extract YAML frontmatter or comments
        # Expected format:
        # ---
        # name: use_blender_modeling
        # version: 1.0.0
        # tags: [3d, modeling, blender]
        # ---
        pass
```

### 5.3 Dynamic Skill Injection into Context

**Extend ContextBuilder** (context.py):

```python
class ContextBuilder:
    def build(self, task: dict, history: list[dict], subagent_name: str | None = None) -> dict:
        """Build context with dynamically discovered skills"""
        context = {
            "task": task,
            "agent_md": self._load_agent_md(),
            "skills": self._discover_relevant_skills(task, history),  # DYNAMIC
            "state_md": self._load_state_md(),
            "runtime_state": self._load_runtime_state(),
            "memory_summary": self._summarize_memory(history),
            "history": history,
        }
        
        if subagent_name:
            context["subagent_md"] = self._load_subagent_md(subagent_name)
        
        return context
    
    def _discover_relevant_skills(self, task: dict, history: list[dict]) -> list[dict]:
        """
        Discover skills relevant to this task.
        
        Heuristics:
        1. Parse task description for skill keywords
        2. Extract inferred tools from history
        3. Query skill registry for matches
        4. Return top-K skills with confidence
        """
        skill_registry = SkillRegistry(self.cfg)
        all_skills = skill_registry.discover_all()
        
        # Extract keywords from task
        keywords = self._extract_task_keywords(task["task"])
        
        # Score skills based on keyword matches
        relevant_skills = []
        for skill_name, skill in all_skills.items():
            score = self._skill_relevance_score(skill, keywords, history)
            if score > 0:
                relevant_skills.append((score, skill))
        
        # Sort by score and return top-K
        relevant_skills.sort(reverse=True)
        return [skill for _, skill in relevant_skills[:10]]
```

---

## 6. LONG-HORIZON TASK ORCHESTRATION

### 6.1 Extended Decision Schema

**File**: `schemas/decision_extended.schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["decision_type", "reasoning_summary"],
  "properties": {
    "decision_type": {
      "enum": ["tool_call", "delegate", "decompose", "learn", "final"]
    },
    "reasoning_summary": { "type": "string" },
    "tool_name": { "type": "string" },
    "tool_input": { "type": "object" },
    "subagent_name": { "type": "string" },
    "subtask": { "type": "string" },
    "decompose": {
      "type": "object",
      "description": "Task decomposition for long-horizon execution",
      "properties": {
        "subtasks": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["task_id", "task", "estimated_steps"],
            "properties": {
              "task_id": { "type": "string" },
              "task": { "type": "string" },
              "estimated_steps": { "type": "integer" },
              "dependencies": {
                "type": "array",
                "items": { "type": "string" },
                "description": "task_ids of prerequisites"
              },
              "skills_required": {
                "type": "array",
                "items": { "type": "string" }
              }
            }
          }
        },
        "learning_phase": {
          "type": "boolean",
          "description": "Whether to first acquire needed skills"
        },
        "learning_queries": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Queries to search for learning materials"
        }
      }
    },
    "learn": {
      "type": "object",
      "description": "Skill learning action",
      "properties": {
        "skill_query": {
          "type": "string",
          "description": "What skill to learn (e.g., 'how to use blender')"
        },
        "search_method": {
          "enum": ["web_search", "mcp", "documentation"],
          "description": "How to discover the skill"
        },
        "expected_output": {
          "type": "string",
          "description": "What learning success looks like"
        }
      }
    },
    "final_response": { "type": "string" }
  },
  "additionalProperties": false
}
```

### 6.2 Long-Horizon Task Planner

```python
# runtime/task_planner.py

class TaskPlanner:
    """
    Decomposes complex tasks into subtasks for long-horizon execution.
    Supports:
    - Task decomposition
    - Skill acquisition planning
    - Dependency graph construction
    - Execution sequencing
    """
    
    def plan(self, task: str, skill_registry: SkillRegistry) -> Dict:
        """
        Create execution plan for complex task.
        
        Returns:
            {
                "subtasks": [...],
                "learning_phase": bool,
                "learning_queries": [...],
                "dependency_graph": {...}
            }
        """
        # Example: "Learn to use Blender and create a simple 3D model"
        
        # Step 1: Extract components
        components = self._extract_task_components(task)
        # -> ["learn blender", "create 3d model"]
        
        # Step 2: Check which skills are needed but missing
        missing_skills = self._find_missing_skills(components, skill_registry)
        # -> ["blender_modeling", "3d_design_basics"]
        
        # Step 3: Plan skill acquisition
        learning_phase = len(missing_skills) > 0
        learning_queries = [f"how to {skill}" for skill in missing_skills]
        
        # Step 4: Decompose main task into subtasks
        subtasks = self._decompose(task, missing_skills)
        # -> [{task: "acquire blender tutorial", ...},
        #     {task: "install blender", ...},
        #     {task: "follow tutorial", ...},
        #     {task: "create cube", ...},
        #     {task: "export model", ...}]
        
        # Step 5: Build dependency graph
        dependency_graph = self._build_dependencies(subtasks)
        
        return {
            "subtasks": subtasks,
            "learning_phase": learning_phase,
            "learning_queries": learning_queries,
            "dependency_graph": dependency_graph
        }
    
    def _extract_task_components(self, task: str) -> List[str]:
        """Extract high-level components from task description"""
        # Use LLM or heuristics to break down task
        pass
    
    def _find_missing_skills(self, components: List[str], skill_registry: SkillRegistry) -> List[str]:
        """Identify skills needed but not currently available"""
        pass
    
    def _decompose(self, task: str, missing_skills: List[str]) -> List[Dict]:
        """Create subtask list with dependencies"""
        pass
    
    def _build_dependencies(self, subtasks: List[Dict]) -> Dict:
        """Build dependency DAG from subtasks"""
        pass
```

---

## 7. HOOK EXTENSION CONTRACTS

### 7.1 Hook Plugin System

```python
# runtime/hook_plugins.py

class HookHandler(ABC):
    """Base class for hook implementations"""
    
    @abstractmethod
    def handle(self, hook_name: str, task_id: str, payload: dict) -> dict:
        """
        Handle hook invocation.
        
        Returns:
            {
                "allow": bool,
                "payload": dict (modified payload if needed),
                "reason": str (optional explanation)
            }
        """
        pass


class BuiltinHookHandler(HookHandler):
    """Default hooks: bash prefix blocking, subagent validation"""
    pass


class SafetyHookHandler(HookHandler):
    """
    Safety hooks for:
    - Desktop automation whitelisting
    - Rate limiting
    - Capability negotiation
    """
    
    def handle(self, hook_name: str, task_id: str, payload: dict) -> dict:
        if hook_name == "before_tool_call":
            return self._before_tool_call(task_id, payload)
        elif hook_name == "before_model_call":
            return self._before_model_call(task_id, payload)
        else:
            return {"allow": True}
    
    def _before_tool_call(self, task_id: str, payload: dict) -> dict:
        """Check tool execution safety"""
        tool_name = payload.get("tool_name")
        
        # Desktop automation whitelist
        if tool_name == "computer_use":
            # Verify action is permitted
            action = payload.get("tool_input", {}).get("action")
            if not self._is_action_permitted(action, task_id):
                return {
                    "allow": False,
                    "reason": f"computer_use action not permitted: {action}"
                }
        
        return {"allow": True}
    
    def _before_model_call(self, task_id: str, payload: dict) -> dict:
        """Dynamically inject available capabilities"""
        # This hook can modify context to announce tool availability
        # E.g., inject list of available tools, safety policies, etc.
        return {"allow": True, "payload": payload}
```

---

## 8. CONFIGURATION EXTENSION

**File**: `infra/runtime.json` (additions)

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
        "enabled": true
      },
      {
        "type": "desktop",
        "module": "runtime.computer_use_tool",
        "enabled": true
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
        "enabled": true
      }
    ]
  },
  "mcp": {
    "servers": [
      {
        "name": "filesystem",
        "type": "stdio",
        "command": "mcp-server-filesystem",
        "arguments": ["--root", "${WORKSPACE_ROOT}"],
        "enabled": true,
        "startup_timeout_seconds": 10,
        "auto_reconnect": true
      }
    ],
    "connection_pool_size": 5,
    "reconnect_max_attempts": 3,
    "reconnect_backoff_ms": 1000
  },
  "desktop_automation": {
    "enabled": true,
    "vision_api": "local",
    "vision_endpoint": "http://localhost:5000",
    "ui_detection": "grid",
    "safety_policy": "whitelist",
    "whitelist_apps": ["chrome.exe", "msword.exe", "excel.exe"],
    "whitelist_actions": ["screenshot", "click", "type", "scroll"],
    "timeout_seconds": 30,
    "max_consecutive_clicks": 5,
    "throttle_clicks_ms": 100
  },
  "skill_discovery": {
    "enabled": true,
    "sources": ["local", "mcp", "web"],
    "web_search_enabled": true,
    "cache_dir": ".runtime-store/objects/skills",
    "auto_refresh_hours": 24,
    "max_skill_context_tokens": 4000
  },
  "task_planning": {
    "enabled": true,
    "max_decomposition_depth": 3,
    "max_subtasks_per_task": 10,
    "learning_step_budget": 5
  }
}
```

---

## 9. ERROR HANDLING & RECOVERY

### 9.1 Tool Execution Error Classification

```python
class ToolError(Exception):
    """Base class for tool execution errors"""
    
    def __init__(self, error_code: str, message: str, recoverable: bool = True):
        self.error_code = error_code
        self.message = message
        self.recoverable = recoverable
        super().__init__(message)


# Desktop automation errors
class DisplayUnavailableError(ToolError):
    """Display/screenshot not available"""
    def __init__(self):
        super().__init__("display_unavailable", "Display not available", recoverable=False)


class UIElementNotFoundError(ToolError):
    """Element not found on screen"""
    def __init__(self, search_text: str):
        super().__init__("not_found", f"UI element not found: {search_text}", recoverable=True)


class PermissionDeniedError(ToolError):
    """Permission denied for action"""
    def __init__(self, action: str):
        super().__init__("permission_denied", f"Permission denied: {action}", recoverable=False)


# MCP errors
class MCPConnectionError(ToolError):
    """MCP server connection failed"""
    def __init__(self, server_name: str):
        super().__init__("mcp_connection_error", f"MCP server not available: {server_name}", recoverable=True)


class MCPResourceNotFoundError(ToolError):
    """MCP resource not found"""
    def __init__(self, resource_uri: str):
        super().__init__("mcp_resource_not_found", f"MCP resource not found: {resource_uri}", recoverable=True)
```

### 9.2 Tool Execution Recovery Hook

```python
# Hook: after_tool_call

def after_tool_call_recovery(task_id: str, payload: dict) -> dict:
    """
    Post-process tool results and attempt recovery on errors.
    
    Recovery strategies:
    1. Transient errors: Retry with backoff
    2. Not found: Suggest alternative tool or skill
    3. Permission denied: Skip and note in memory
    """
    result = payload.get("result", {})
    
    if not result.get("success"):
        error_code = result.get("error_code")
        
        if error_code in ["timeout", "mcp_connection_error"]:
            # Transient error: can retry
            return {
                "allow": True,
                "payload": {
                    "recovery_strategy": "retry",
                    "retry_backoff_ms": 1000
                }
            }
        
        elif error_code == "not_found":
            # Not found: suggest web search for skill
            return {
                "allow": True,
                "payload": {
                    "recovery_strategy": "learn",
                    "suggestion": "Try web_search to learn how to find this element"
                }
            }
        
        elif error_code == "permission_denied":
            # Permission denied: note and continue
            return {
                "allow": True,
                "payload": {
                    "recovery_strategy": "skip",
                    "note": "Action not permitted, proceeding with alternative approach"
                }
            }
    
    return {"allow": True}
```

---

## 10. AUDIT & OBSERVABILITY

### 10.1 Audit Logging for Computer Usage

All computer usage tool invocations MUST be logged:

```
.runtime-store/objects/receipts/YYYYMMDD/
  ├── {task_id}-computer_use_screenshot-001.json
  ├── {task_id}-computer_use_click-001.json
  ├── {task_id}-computer_use_click-002.json
  └── ...
```

Each receipt includes:
```json
{
  "receipt_id": "uuid",
  "task_id": "uuid",
  "step": "computer_use_click_001",
  "timestamp": "2026-04-17T12:30:00Z",
  "tool_name": "computer_use",
  "action": "click",
  "inputs": {
    "x": 100,
    "y": 200,
    "button": "left"
  },
  "inputs_sha256": "...",
  "output": {
    "success": true,
    "action": "click",
    "screenshot": "base64..."
  },
  "output_sha256": "...",
  "execution_time_ms": 150,
  "worker_id": "worker-001"
}
```

### 10.2 Tracing for MCP Integration

All MCP tool invocations include tracing:

```json
{
  "receipt_id": "uuid",
  "task_id": "uuid",
  "tool_name": "mcp_filesystem_read_file",
  "mcp_server": "filesystem",
  "mcp_resource_uri": "file://read",
  "input": { "path": "document.txt" },
  "output": { "success": true, "content": "..." },
  "mcp_latency_ms": 50,
  "error": null
}
```

---

## 11. PRODUCTION READINESS CHECKLIST

- [ ] All tool plugins implement `ToolPlugin` base class
- [ ] All tool specs validate against `tool.schema.json`
- [ ] MCP server connections include timeout handling
- [ ] Desktop automation includes screenshot+audit logging
- [ ] Skill discovery includes web search integration
- [ ] Error handling includes recovery strategies
- [ ] Whitelist policies enforced via hooks
- [ ] All tool execution is synchronous
- [ ] All receipts include audit trail
- [ ] Configuration supports enable/disable per plugin
- [ ] Documentation includes setup/usage examples
- [ ] Tests cover happy path + error paths
- [ ] Load testing for concurrent tool dispatch
- [ ] Security audit for desktop automation
- [ ] Rate limiting on web search/MCP calls

---

## 12. EXAMPLE: LONG-HORIZON TASK EXECUTION

### Task: "Learn to use Blender and create a simple 3D model"

```
Initial Task (task_id=abc123):
  "Learn to use Blender and create a simple 3D model"

Step 1: Agent decides to DECOMPOSE
  Decision: {
    "decision_type": "decompose",
    "reasoning_summary": "This is a multi-phase task requiring learning, installation, and execution",
    "decompose": {
      "subtasks": [
        {
          "task_id": "subtask_1",
          "task": "Search web for Blender tutorials and installation guide",
          "estimated_steps": 3,
          "skills_required": ["web_search"]
        },
        {
          "task_id": "subtask_2",
          "task": "Install Blender on this system",
          "estimated_steps": 2,
          "dependencies": ["subtask_1"],
          "skills_required": ["bash", "file_read"]
        },
        {
          "task_id": "subtask_3",
          "task": "Launch Blender and open tutorial project",
          "estimated_steps": 2,
          "dependencies": ["subtask_2"],
          "skills_required": ["computer_use"]
        },
        {
          "task_id": "subtask_4",
          "task": "Follow tutorial to create cube and apply material",
          "estimated_steps": 8,
          "dependencies": ["subtask_3"],
          "skills_required": ["computer_use", "web_search"]
        },
        {
          "task_id": "subtask_5",
          "task": "Export model as .blend file",
          "estimated_steps": 2,
          "dependencies": ["subtask_4"],
          "skills_required": ["computer_use"]
        }
      ],
      "learning_phase": true,
      "learning_queries": [
        "Blender 3D modeling tutorial for beginners",
        "How to install Blender on Windows"
      ]
    }
  }

Step 2: Agent learns (delegates to subagent for learning_phase)
  Subtask 1 execution:
    - Calls web_search for "Blender tutorials"
    - Discovers MCP filesystem resource
    - Caches tutorial links and installation guide
    - Returns: {"learned_skills": ["blender_basics"], "resources": [...]}

Step 3: Agent installs
  Subtask 2 execution:
    - Downloads Blender installer
    - Executes installer via bash
    - Verifies installation with file_read

Step 4: Agent launches
  Subtask 3 execution:
    - Calls computer_use screenshot → sees desktop
    - Calls computer_use to find Blender application
    - Double-clicks Blender icon
    - Waits for launch

Step 5: Agent follows tutorial
  Subtask 4 execution (loop):
    a. Take screenshot → see Blender UI
    b. Search tutorial for next step (web_search)
    c. Execute step via computer_use (click menu, type parameters, etc.)
    d. Repeat until cube is created
    - Creates cube primitive
    - Applies Principled BSDF material
    - Renders preview

Step 6: Agent exports
  Subtask 5 execution:
    - Calls computer_use to navigate File → Save As
    - Types filename and location
    - Confirms export

Final Response:
  "I successfully learned Blender basics and created a 3D model cube
   with a material applied. The model was exported to
   /workspace/my_model.blend. Key learnings:
   - Blender interface navigation
   - Primitive modeling
   - Material application
   - File export
   
   Next steps: More complex modeling, animation, rendering"

```

---

## Conclusion

This runtime harness enables production-grade computer usage agents with:

1. **Pluggable tool architecture** - Extensible via `ToolPlugin` system
2. **MCP integration** - Connect to external tools via Model Context Protocol
3. **Desktop automation** - Control UI apps via screenshot + click/type/scroll
4. **Dynamic skill discovery** - Learn from web + MCP resources
5. **Long-horizon orchestration** - Decompose and execute multi-step tasks
6. **Safety & audit** - Whitelists, hooks, receipt trails
7. **Error recovery** - Transient vs permanent error handling

All contracts are production-ready and backward-compatible with existing agent-shell architecture.
