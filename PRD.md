# Product Requirements Document (PRD): Production-Grade Agent Harness

## 1. Vision & Objectives
The goal is to enhance the `agent-shell` runtime into a production-grade autonomous agent environment. This includes integrating the Model Context Protocol (MCP), providing desktop automation capabilities, and enabling dynamic skill discovery.

### Key Objectives:
- **Extensibility**: Transition from hardcoded tools/hooks to a plugin-based architecture.
- **Interoperability**: Enable seamless integration with external MCP servers.
- **Capability Expansion**: Implement secure, high-fidelity desktop automation (Computer Usage).
- **Self-Evolution**: Support dynamic discovery and injection of skills from local, MCP, and web sources.
- **Observability**: Ensure every step, decision, and memory change is logged with immutable telemetry.

## 2. Core Requirements

### 2.1 Plugin Architecture (Phase 1)
- Define `ToolPlugin` and `HookPlugin` base classes.
- Refactor `ToolRegistry` and `HookRegistry` to load plugins dynamically.
- Maintain 100% backward compatibility with existing hardcoded tools.

### 2.2 MCP Integration (Phase 2)
- Implement `MCPAdapter` to connect to remote MCP servers.
- Dynamically generate tool schemas from MCP resource definitions.
- Support secure connection pooling and timeout management.

### 2.3 Computer Usage Tools (Phase 3)
- Provide tools for `screenshot`, `click`, `type`, `scroll`, and `key_press`.
- Implement a whitelist-based safety policy for target applications.
- Audit all desktop interactions with high-resolution telemetry.

### 2.4 Skill Discovery (Phase 4)
- Create a `SkillDiscovery` system to index local, MCP, and web-based resources.
- Support dynamic injection of validated skills into the active runtime.

### 2.5 Long-Horizon Orchestration (Phase 5)
- Enhance the `AgentLoop` to handle multi-step planning and learning phases.
- Implement task decomposition for complex, underspecified requests.

## 3. Telemetry & Observability
- Every execution step must emit a **Receipt** containing:
  - `task_id`, `step_id`, `status`.
  - Input/Output payloads and their SHA-256 hashes.
  - **Memory Snapshot**: The state of the agent's memory journal at the time of execution.
- Telemetry artifacts must be stored in the `.runtime-store` as immutable JSON files.

## 4. Security & Compliance
- **Permission Boundary**: All tool calls must pass through a `HookRegistry` for policy validation.
- **Auditability**: Maintain a complete, unalterable trail of all actions and state changes.
- **Credential Protection**: Ensure provider API keys are never exposed in receipts or logs.

## 5. Success Criteria
- [ ] Successful execution of complex, multi-step tasks (e.g., "Install Unity and set up a basic scene").
- [ ] 100% pass rate on all existing and new unit/integration tests.
- [ ] Zero manual intervention required for tool discovery and connection.
- [ ] Complete telemetry coverage for all runtime artifacts.
