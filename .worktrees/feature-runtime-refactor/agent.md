# Agent Shell

## Purpose
Operate as a filesystem-backed agent runtime that sits above the LLM layer. The runtime owns:
- task intake
- context assembly
- reasoning loop orchestration
- hook execution
- tool dispatch
- memory management
- receipts
- sub-agent delegation

## Runtime rules
1. Always produce a typed decision object.
2. Never call a tool without the `before_tool_call` hook.
3. Append every tool result, delegate result, and final answer to history.
4. Compact memory when the configured threshold is exceeded.
5. Emit a receipt for every loop step and terminal state.
6. Prefer `file_read` before `bash` when the task is explicitly about reading a known file.
7. Use delegation for bounded subtasks that can return a structured result.
