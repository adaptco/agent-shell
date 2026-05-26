Runtime Analysis — Task A

Summary
- Focus: stabilize runtime dependencies and add defensive checks.
- Files inspected: runtime/llm.py, runtime/tools.py, runtime/hooks.py, runtime/middleware.py, runtime/server.py, runtime/cli.py, runtime/worker.py, runtime/external_ci.py

Issues found (high level)
1. File-read error handling: runtime/tools.py _file_read used path.read_text without a clear, localized error message — this can bubble up with unclear stack traces.
2. Network/credential assumptions: llm backends raise RuntimeError when API keys missing (good), but messages differ; standardize messages and ensure all backends behave similarly.
3. Potential workspace path escaping protections exist in BuiltinToolPlugin._safe_workspace_path, good — ensure all code paths use it.
4. External CI requires GitHub credentials and can fail in local dev; document as blocker for CI-run tests.

Concrete edits (prioritized)
- Tiny (apply now):
  1) Add explicit FileNotFoundError handling in runtime/tools.py _file_read (applied).
  2) Standardize "missing API key" error messages across llm backends (recommended next tiny edit).
- Medium:
  3) Centralize config/env access into runtime/config module and use a helper to read env vars with descriptive errors.
- Large:
  4) Refactor backends to use a single backend factory and uniform error/timeout handling.

Applied changes
- runtime/tools.py: added FileNotFoundError handling in _file_read to raise a clear ValueError.

Blockers / Notes
- Some tests may require real API keys or network. Documented in PR.

Next recommended task
- Task B: Implement standardized env var helper and apply to runtime/llm.py (make error messages consistent). Mark as the next small PR.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
