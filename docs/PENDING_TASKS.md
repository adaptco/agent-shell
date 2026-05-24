# Pending Tasks Report: Agent Shell

This document formalizes the pending tasks identified in the project documentation (`PROGRESS.md`, `PRD.md`, and `IMPLEMENTATION_GUIDE.md`).

## Phase 2: MCP Integration
- [ ] **Implement `mcp_adapter.py`**: Create the adapter to interface with Model Context Protocol servers.
- [ ] **Define `infra/mcp_servers.json`**: Configure the list of trusted MCP servers.
- [ ] **Test Connection**: Verify connectivity and tool discovery with a sample MCP server.

## Phase 3: Computer Usage Tools
- [ ] **Implement `computer_use_tool.py`**: Add the core tool for desktop automation (screenshot, click, type, etc.).
- [ ] **Define `tools/computer_use.json`**: Create the JSON schema for the computer usage tool.
- [ ] **Verify UI Automation Safety Hooks**: Ensure `SafetyHookHandler` correctly enforces whitelists for desktop actions.
- [ ] **Implement OCR/Vision-based Element Detection**: Add capability to detect UI elements from screenshots (TODO in `IMPLEMENTATION_GUIDE.md`).

## Phase 4: Skill Discovery System
- [ ] **Implement SkillDiscovery System**: Create a system to index and discover skills from local, MCP, and web-based resources.

## Phase 5: Long-Horizon Orchestration
- [ ] **Enhance AgentLoop**: Add support for multi-step planning, task decomposition, and learning phases.

## Phase 6: Integration & Verification
- [ ] **Full E2E Task Execution**: Verify the complete flow from task decomposition to execution with telemetry.
- [ ] **Telemetry Verification**: Ensure all new tool executions produce audit-ready receipts.

## Milestones
- [ ] **Milestone 2**: First successful MCP tool execution.
- [ ] **Milestone 3**: Successful desktop automation task.
- [ ] **Milestone 4**: Full E2E task execution with telemetry.
