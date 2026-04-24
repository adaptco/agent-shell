Implementation Plan: runtime dependency refactor

Goal
- Fix and harden runtime dependencies within /runtime, create a clear `runtime` module API, and ensure imports/configs are robust for Phase 2 (MCP integration).

Approach (phases)
1. Analyze
- Audit runtime files for fragile imports, env usage, and external network calls.
- Identify failing or brittle dependency points (LLM backends, urllib usage, jwt, subprocess, uvicorn).

2. Stabilize module surface (small PRs)
- Create `runtime/core.py` (or `runtime/_runtime.py`) to centralize common helpers: load_config, get_logger, safe_http_request, env access.
- Replace fragile direct imports with runtime API (eg. runtime.get_backend()) where appropriate.

3. Dependency isolation
- Add fallbacks and clear errors when env vars are missing (raise descriptive RuntimeError).
- Add `requirements.txt` entries if missing and update import paths.

4. Tests & verification
- Add unit tests targeting refactored functions (config load, backend selection, tool registry dispatch).
- Run existing tests and fix failures.

5. Iteration & chunking
- Implement work as 3 small tasks: (A) analysis + small fixes, (B) core API and refactor, (C) tests and CI fixups.
- Each task: spawn an executor to implement, then a reviewer to validate.

Deliverables
- Committed feature/runtime-refactor branch with incremental PRs + IMPLEMENTATION_PLAN.md
- Passing unit tests locally or clear CI notes if external secrets block runs

Next steps
- Implement Task A (analysis + list of concrete code edits). Spawn executor to modify runtime files per findings.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
