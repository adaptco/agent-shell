# Tool Skill

## File Read
Use for deterministic reads inside the workspace. The runtime rejects path traversal and returns text plus metadata.

## Bash
Use only when the command prefix is allowlisted in `infra/runtime.json`. The hook layer blocks disallowed commands before execution.

## Web Search
Use for internet lookups when a search provider is configured. In smoke tests the package uses a mock provider so the tool path can be exercised offline.
