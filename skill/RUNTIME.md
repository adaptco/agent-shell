# Runtime Skill

## Triggering the loop
Use the CLI:
- `python -m runtime.cli queue-add --task "..."` to create a queued task
- `python -m runtime.cli run-next --backend mock` to process one queued task
- `python -m runtime.cli run-task --task "..." --backend mock` to bypass the queue
- `python -m runtime.cli worker --backend mock --count 10` to run repeated polling cycles
- `python -m runtime.cli heartbeat` to update liveness and runtime status

## Decision types
The reasoning loop accepts exactly three decision types:
- `tool_call`
- `delegate`
- `final`

## Hook order
1. `before_model_call`
2. model decision generation
3. `after_model_call`
4. if tool:
   - `before_tool_call`
   - tool execution
   - `after_tool_call`
5. if delegate:
   - `before_delegate`
   - sub-agent spawn
   - `after_delegate`
6. if compaction is needed:
   - `before_memory_compact`
   - compaction
   - `after_memory_compact`

## Memory
The journal is append-only until the configured threshold is hit. When compaction runs, the runtime writes a summary, archives the full journal, keeps the configured tail, and writes a compaction marker back into the live journal.
