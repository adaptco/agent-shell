# Agent Shell Enhancement Summary

**Date**: April 17, 2026
**Status**: Design Complete → Ready for Implementation
**Scope**: MCP + Desktop Automation + Skill Discovery for Long-Horizon Agent Tasks

---

## Executive Summary

The agent-shell repository is being enhanced to support **production-grade autonomous agents capable of complex, long-horizon tasks** such as:
- Learning to use software (Blender, Unity, Office) via web search and tutorials
- Controlling desktop applications (browsers, office suites) via computer usage tools
- Orchestrating workers via Model Context Protocol (MCP)
- Recursively acquiring and executing skills from multiple sources

This document summarizes the architectural design, contracts, implementation phases, and acceptance criteria.

---

## What Was Delivered

### 1. **RUNTIME_HARNESS_CONTRACTS.md** (52KB, 12 sections)
Comprehensive production-grade runtime contracts specifying:

| Component | Contracts | Details |
|-----------|-----------|---------|
| **Tool Plugin Architecture** | ToolPlugin base class, ToolRegistry refactoring | Pluggable system for tools (builtin, MCP, desktop) |
| **Computer Usage Tools** | JSON schema, execution contract, safety hooks | Desktop automation (screenshot, click, type, scroll, key press) |
| **MCP Adapter** | MCP server connection, resource discovery, tool marshaling | Connect to external tools/resources via MCP protocol |
| **Skill Discovery** | Skill metadata schema, registry, dynamic injection | Discover skills from local files, MCP, web search |
| **Long-Horizon Orchestration** | Extended decision schema, task planner | Decompose complex tasks into subtasks with learning phases |
| **Hook Extension System** | HookHandler plugins, safety policies | Externalize hook logic for safety, audit, capability negotiation |
| **Error Handling** | Error classification, recovery strategies | Transient vs permanent errors with retry/learn/skip patterns |
| **Audit & Observability** | Receipt trails, tracing, logging | Comprehensive audit for security and debugging |

**Key Features**:
- ✅ Production-ready security contracts (whitelisting, permission checks)
- ✅ Error recovery mechanisms (retry, fallback, skip)
- ✅ Backward compatible with existing agent-shell architecture
- ✅ Extensible plugin system for future tool types
- ✅ Full audit trail for all tool executions
- ✅ Comprehensive examples (long-horizon task walkthrough)

---

### 2. **IMPLEMENTATION_GUIDE.md** (33KB, 6 phases)
Step-by-step implementation instructions covering:

| Phase | Scope | Effort | Dependencies |
|-------|-------|--------|--------------|
| **Phase 1: Plugin Architecture** | Refactor tool/hook registry, ToolPlugin base class | ~300 LOC | None |
| **Phase 2: MCP Integration** | MCP server connection, resource discovery | ~600 LOC | Phase 1 |
| **Phase 3: Computer Usage Tools** | Desktop automation, vision API integration | ~800 LOC | Phase 1 |
| **Phase 4: Skill Discovery** | Dynamic skill registry, web search integration | ~500 LOC | Phases 2-3 |
| **Phase 5: Long-Horizon Tasks** | Task decomposition, recursive planning | ~400 LOC | Phases 1-4 |
| **Phase 6: Integration & Testing** | E2E tests, documentation, examples | ~500 LOC | All phases |

**Total**: ~3100 LOC, production-grade implementation

**Deliverables per Phase**:
- Concrete file paths (what to create/modify)
- Python code snippets (production-ready templates)
- JSON schemas (validation contracts)
- Configuration examples (runtime.json extensions)
- Test scenarios (verification steps)

---

### 3. **Implementation Plan** (Session State: plan.md)
High-level planning document with:
- Problem statement
- Current architecture analysis
- Design approach
- Implementation tasks breakdown
- Success criteria
- Risk mitigation strategies
- Rollout strategy

---

## Architecture Overview

### Current State (agent-shell)
```
┌─────────────────────────────────────────┐
│ FastAPI Service Layer                   │
├─────────────────────────────────────────┤
│ AgentLoop (reasoning loop)              │
│ ├─ Tool Dispatch (file_read, bash, ...) │
│ ├─ Hook System (before/after_call)      │
│ ├─ Memory Management                    │
│ └─ Subagent Delegation                  │
├─────────────────────────────────────────┤
│ Filesystem-Backed Storage               │
│ ├─ .runtime-store/objects/queue         │
│ ├─ .runtime-store/objects/memory        │
│ ├─ .runtime-store/objects/receipts      │
│ └─ .runtime-store/objects/state         │
└─────────────────────────────────────────┘
```

### Enhanced Architecture (with MCP + Desktop + Skills)
```
┌──────────────────────────────────────────────────────────┐
│ FastAPI Service Layer                                    │
├──────────────────────────────────────────────────────────┤
│ AgentLoop (reasoning loop with long-horizon planning)    │
│ ├─ Plugin-Based Tool Dispatch                            │
│ │  ├─ ToolPlugin: Builtin (file_read, bash, web_search) │
│ │  ├─ ToolPlugin: MCP (external tools/resources)        │
│ │  ├─ ToolPlugin: Desktop (computer_use)                │
│ │  └─ ToolPlugin: Custom (user-defined)                 │
│ ├─ Hook System (externalized plugins)                    │
│ │  ├─ HookHandler: Builtin                              │
│ │  ├─ HookHandler: Safety (whitelist, audit)            │
│ │  └─ HookHandler: Custom                               │
│ ├─ Skill Discovery & Registry                           │
│ │  ├─ Local skills (skill/*.md)                         │
│ │  ├─ MCP resources                                      │
│ │  ├─ Web search results                                │
│ │  └─ Agent-generated skills                            │
│ ├─ Task Planner (decomposition + learning phases)        │
│ ├─ Memory Management                                     │
│ └─ Subagent Delegation                                  │
├──────────────────────────────────────────────────────────┤
│ Filesystem-Backed Storage (unchanged)                    │
└──────────────────────────────────────────────────────────┘
```

### Plugin Architecture (New)

**Tool Dispatch Flow**:
```
LLM Decision → ToolRegistry.execute(tool_name, input)
                │
                ├─→ Lookup tool_specs[tool_name]
                ├─→ Validate input schema
                ├─→ Dispatch to plugin.execute()
                │   ├─ BuiltinToolPlugin (file_read, bash, web_search)
                │   ├─ MCPToolPlugin (MCP resources)
                │   ├─ ComputerUseTool (desktop automation)
                │   └─ CustomPlugin (user-defined)
                ├─→ Validate output schema
                └─→ Return result
```

**Hook Extension Flow**:
```
before_tool_call hook
  ├─ BuiltinHookHandler (bash whitelist, delegation validation)
  ├─ SafetyHookHandler (desktop whitelist, rate limiting)
  └─ CustomHandler (user-defined policies)

Result: Aggregated allow/deny + modified payload
```

---

## Key Design Decisions

### 1. **Plugin Architecture**
✅ **Decision**: Pluggable ToolPlugin system instead of hardcoded tools
- **Rationale**: Extensibility, clean separation of concerns, testability
- **Trade-off**: Slight overhead for dynamic loading (negligible for agent workloads)
- **Benefit**: Can add new tool types without modifying core ToolRegistry

### 2. **MCP as Plugin**
✅ **Decision**: MCP integrated as ToolPlugin, not at runtime core level
- **Rationale**: MCP is optional, doesn't need to be core infrastructure
- **Trade-off**: MCP discovery happens at startup (not dynamic)
- **Benefit**: Can disable MCP entirely without affecting core execution

### 3. **Computer Usage as Sandboxed Tool**
✅ **Decision**: Desktop automation accessed only via computer_use tool with safety policies
- **Rationale**: Security-first approach, all desktop actions are auditable
- **Trade-off**: Slightly more verbose than direct pyautogui calls
- **Benefit**: Whitelist enforcement, permission checks, full audit trail

### 4. **Skill Discovery Multi-Source**
✅ **Decision**: Skills can come from local files, MCP resources, or web search
- **Rationale**: Flexibility, enables self-improving agents
- **Trade-off**: Need to validate/cache web search results
- **Benefit**: Agent can acquire skills on-demand for unknown domains

### 5. **Synchronous Execution Only**
✅ **Decision**: No async tool execution (maintain file-based queue properties)
- **Rationale**: Current queue is file-based, not designed for concurrent execution
- **Trade-off**: Can't parallelize independent tool calls
- **Benefit**: Strong consistency guarantees, simpler error handling, auditability

### 6. **Backward Compatibility**
✅ **Decision**: All enhancements are opt-in via plugin configuration
- **Rationale**: Minimize risk, allow gradual rollout
- **Trade-off**: Must maintain old and new code paths temporarily
- **Benefit**: Existing workflows continue to work without modification

---

## Safety & Security Contracts

### Computer Usage Whitelist
```json
{
  "desktop_automation": {
    "safety_policy": "whitelist",
    "whitelist_apps": ["chrome.exe", "msword.exe", "excel.exe"],
    "whitelist_actions": ["screenshot", "click", "type", "scroll"],
    "timeout_seconds": 30
  }
}
```

**Enforcement**: `before_tool_call` hook validates action against whitelist

### MCP Server Trust
- Explicit configuration required (no auto-discovery)
- Connection pooling with timeout protection
- Resource discovery cached to reduce repeated MCP calls

### Skill Acquisition Validation
- Web search results cached with confidence scores
- Skills require explicit approval before adding to context
- Learning phase has step budget limit

### Audit Trail
Every tool execution produces immutable receipt:
```json
{
  "receipt_id": "uuid",
  "task_id": "uuid",
  "tool_name": "computer_use",
  "action": "click",
  "inputs": {...},
  "output": {...},
  "timestamp": "ISO8601",
  "worker_id": "worker-001"
}
```

---

## Integration Points

### With Existing Systems
| System | Integration Point | Impact |
|--------|------------------|--------|
| **Tool Registry** | ToolPlugin base class, plugin loading | Transparent to existing tools |
| **Hook System** | HookHandler plugins, plugin loading | Transparent to existing hooks |
| **Context Builder** | Skill discovery injection | Additional skills in context |
| **Agent Loop** | Extended decision schema | New decision types (decompose, learn) |
| **Memory System** | Unchanged | No modifications needed |
| **Queue System** | Unchanged | No modifications needed |
| **Receipts** | Enhanced audit logging | Additional receipt fields for tool metadata |

### With External Systems
| System | Protocol | Usage |
|--------|----------|-------|
| **MCP Servers** | Stdio/HTTP | Tool resource discovery |
| **Vision API** | HTTP | Screenshot OCR/element detection |
| **Web Search** | HTTP | Skill discovery queries |
| **Office/Browser** | Desktop GUI | Computer usage automation |

---

## Example: Long-Horizon Task Execution

### Task
```
"Learn to use Blender and create a simple 3D model"
```

### Execution Flow

```
Step 1: DECOMPOSE
  → Identify subtasks:
    1. Search web for Blender tutorial
    2. Install Blender
    3. Launch Blender
    4. Create 3D cube with material
    5. Export model

Step 2: LEARN
  → Search: "Blender modeling tutorial beginner"
  → Cache: Tutorial links, installation guide
  → Acquire skill: "blender_modeling_basics"

Step 3: INSTALL
  → tool: bash
  → Execute Blender installer
  → Verify installation

Step 4: CONTROL
  → tool: computer_use
  → screenshot() → see desktop
  → find_element("Blender") → locate app
  → click() → launch

Step 5: EXECUTE
  → Follow tutorial via computer_use
  → Loop:
    - Take screenshot
    - Search web for next tutorial step
    - Execute step via click/type
    - Verify result

Step 6: EXPORT
  → computer_use: Save file
  → Return: Model artifact + learned skills

RESULT:
  ✅ Model created and saved
  ✅ Skills acquired and cached for reuse
  ✅ Audit trail: Every step recorded
```

---

## Success Criteria

### Functional
- ✅ MCP servers (≥2) successfully connected and used as tools
- ✅ Computer usage tool controls desktop apps (screenshot, click, type)
- ✅ Skill discovery works across local/MCP/web sources
- ✅ Agent decomposes complex tasks into subtasks
- ✅ Agent learns skills via web search
- ✅ End-to-end example works (Blender or Unity scenario)

### Non-Functional
- ✅ Production-grade error handling (all error paths covered)
- ✅ Comprehensive audit logging (100% tool execution traced)
- ✅ Safety policies enforced (whitelist blocking works)
- ✅ Backward compatible (existing workflows unaffected)
- ✅ Documented (README, implementation guide, examples)
- ✅ Tested (unit + integration + E2E tests)

### Acceptance
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ E2E test: Long-horizon task executes successfully
- ✅ Code review approved
- ✅ Security audit completed
- ✅ Performance acceptable (no timeout issues)

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Desktop automation permissions denied | High | Whitelist policies, early permission check in hook |
| MCP server unavailable | Medium | Connection pooling with fallback, error recovery |
| Skill discovery returns poor results | Medium | Confidence scoring, verification hooks, manual override |
| Long-horizon task explosion | Medium | Max depth limits, step budgets, early termination |
| Context window overflow | Low | Skill summarization, dynamic pruning, tiered context |

---

## Next Steps

### Immediate (This Week)
1. ✅ **Review contracts & implementation guide** - Confirm scope with stakeholders
2. ✅ **Secure approval** - Sign off on design decisions
3. 📅 **Start Phase 1** - Plugin architecture foundation

### Short-term (Weeks 2-3)
4. 📅 Complete Phase 1 (plugin foundation)
5. 📅 Start Phases 2-3 in parallel (MCP + desktop automation)
6. 📅 Create integration tests

### Medium-term (Weeks 4-6)
7. 📅 Complete Phase 4 (skill discovery)
8. 📅 Complete Phase 5 (long-horizon tasks)
9. 📅 Phase 6 (E2E testing & documentation)

### Before Production
10. 📅 Security audit for desktop automation
11. 📅 Performance testing with large skill registries
12. 📅 Load testing with multiple workers
13. 📅 Documentation & examples
14. 📅 Team training & rollout plan

---

## Files Delivered

| File | Purpose | Size |
|------|---------|------|
| **RUNTIME_HARNESS_CONTRACTS.md** | Production contracts for all components | 52KB |
| **IMPLEMENTATION_GUIDE.md** | Step-by-step implementation instructions | 33KB |
| **plan.md** (session state) | High-level planning document | 11KB |
| **ENHANCEMENT_SUMMARY.md** (this file) | Executive summary | 8KB |

---

## Appendix: Quick Reference

### Configuration Template
```json
{
  "plugins": {
    "tools": [
      {"type": "builtin", "enabled": true},
      {"type": "mcp", "enabled": true},
      {"type": "desktop", "enabled": true}
    ]
  },
  "mcp": {
    "servers": [
      {"name": "filesystem", "type": "stdio", "command": "mcp-server-filesystem"}
    ]
  },
  "desktop_automation": {
    "enabled": true,
    "vision_api": "local",
    "whitelist_apps": ["chrome.exe", "msword.exe"]
  },
  "skill_discovery": {
    "enabled": true,
    "sources": ["local", "mcp", "web"]
  }
}
```

### Tool Plugin Template
```python
from runtime.plugin_base import ToolPlugin

class MyToolPlugin(ToolPlugin):
    def get_tool_specs(self):
        return {
            "my_tool": {
                "description": "...",
                "input_schema": {...},
                "output_schema": {...}
            }
        }
    
    def execute(self, tool_name, tool_input):
        # Implementation here
        return {"success": True, ...}
```

### Hook Handler Template
```python
from runtime.plugin_base import HookHandler

class MyHookHandler(HookHandler):
    def handle(self, hook_name, task_id, payload):
        # Handle hook here
        return {"allow": True, "payload": payload}
```

---

## Questions?

Refer to:
- **Technical details**: RUNTIME_HARNESS_CONTRACTS.md
- **Implementation steps**: IMPLEMENTATION_GUIDE.md
- **High-level planning**: plan.md (session state)
- **Architecture decisions**: This document (ENHANCEMENT_SUMMARY.md)

