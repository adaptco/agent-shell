---
name: Agent Bash CI Workflow - Example Prompts
description: Demonstrates how to invoke agent bash CI workflow instructions through natural language prompts
---

# Example Prompts for Agent Bash CI Workflow

These examples show how users would trigger the bash CI workflow instructions in real scenarios.

## Pre-Push Workflow Examples

### Example 1: Basic Commit with Full Validation
```
User: "Commit the changes I've made to runtime/utils.py with message 'Add new logging utility'"
```

**Expected Agent Behavior:**
1. Detects uncommitted changes via `git status`
2. Runs linting: `.venv\Scripts\python -m ruff check .`
3. If violations found, auto-fixes: `.venv\Scripts\python -m ruff check . --fix`
4. Re-checks linting
5. Runs tests: `.venv\Scripts\python -m pytest --cov=runtime`
6. Reports: "✅ All checks passed. Ready to commit."
7. Creates commit with provided message

---

### Example 2: Linting Failures That Need Manual Intervention
```
User: "I updated runtime/hooks.py. Can you lint and prepare for commit?"
```

**Expected Agent Behavior:**
1. Runs: `.venv\Scripts\python -m ruff check .`
2. Finds: Docstring issues on lines 42-45 (error description)
3. Auto-fixes import ordering issues
4. Re-runs linting
5. Reports: "❌ Linting issues remain. Manual fixes required at runtime/hooks.py:42-45. Issue: Missing docstring for function `_process_hook`. Fix: Add docstring following project style."
6. Does NOT proceed to testing until user fixes

---

### Example 3: Test Failures Block Commit
```
User: "Push these changes"
```

**Expected Agent Behavior:**
1. Runs full pre-push validation
2. Gets to testing: `.venv\Scripts\python -m pytest --cov=runtime`
3. Finds: `FAILED tests/test_utils.py::test_get_env_missing_required`
4. Reports full failure context:
   ```
   Test: test_get_env_missing_required
   Error: AssertionError: Expected RuntimeError to be raised when MISSING_VAR not set
   Current behavior: Function returns None
   Location: runtime/utils.py line 156
   ```
5. Does NOT proceed to push until test passes

---

## Post-Push Workflow Examples

### Example 4: Monitor PR After Push
```
User: "I just pushed feature-x. Check if the PR is ready for merge."
```

**Expected Agent Behavior:**
1. Identifies PR number from recent push (or asks user)
2. Runs: `gh pr checks <pr-number>`
3. Output shows:
   - `test / test (3.13)` → RUNNING
   - `test / docker-build` → PENDING
   - `test / security-scan` → PENDING
   - `Trivy` → PENDING
4. Reports: "PR #25 checks are running. test/test (3.13) is 45% complete. I'll check again in 15 seconds."
5. Polls every 15 seconds until all complete (max 5 minutes)
6. When all pass: "✅ All PR checks passed!"
7. When some fail: "❌ test/security-scan failed. Analyzing logs..."

---

### Example 5: Extract Code Review Feedback
```
User: "What did the code reviewers say about PR #24?"
```

**Expected Agent Behavior:**
1. Runs: `gh pr view 24 --comments`
2. Parses review comments
3. Reports findings:
   ```
   Reviewer feedback on PR #24:
   
   🔴 CRITICAL (blocks merge):
   - Line 89: Remove hardcoded API key. Use environment variable GITHUB_TOKEN instead.
   
   🟡 WARNING:
   - Line 156: Function `parse_webhook` has no error handling for invalid JSON.
   
   ℹ️ INFO:
   - Add unit test for the new retry logic in external_ci.py
   ```
4. Offers: "Shall I generate fixes for the critical issue?"

---

### Example 6: Security Scan Issues
```
User: "PR #26 shows a security warning. What's the issue?"
```

**Expected Agent Behavior:**
1. Queries: `gh pr checks 26` and `gh pr view 26 --comments`
2. Finds security scan comment
3. Reports: "Trivy scan found: 'Secret leaked in runtime/config.py:45'. Detected pattern: AWS_ACCESS_KEY_ID in plaintext."
4. Proposes fix: "Remove secret from source. Configure via environment variable instead."

---

## Merge Conflict Workflow Examples

### Example 7: Automatic Conflict Resolution
```
User: "Rebase on main and resolve any conflicts"
```

**Expected Agent Behavior:**
1. Runs: `git rebase main`
2. Gets: Conflict in `runtime/utils.py` and `schemas/task.schema.json`
3. For Python file:
   - Analyzes both sides of conflict marker
   - Identifies that both sides add different functions (no overlap)
   - Keeps both functions
   - Runs: `ruff check runtime/utils.py` → passes
4. For JSON schema:
   - Uses main branch as baseline
   - Merges in new keys from feature branch
   - Validates: `.venv\Scripts\python -c "import json; json.load(open('schemas/task.schema.json'))"`
5. Stages both: `git add runtime/utils.py schemas/task.schema.json`
6. Completes: `git rebase --continue`
7. Runs full validation:
   - `.venv\Scripts\python -m ruff check .` → ✅ pass
   - `.venv\Scripts\python -m pytest --cov=runtime` → ✅ pass
8. Reports: "✅ Rebase complete. 2 conflicts resolved. All checks pass. Ready to push."

---

### Example 8: Complex Conflict Requiring User Input
```
User: "I'm getting a merge conflict. Help me resolve it."
```

**Expected Agent Behavior:**
1. Runs: `git diff --name-only --diff-filter=U`
2. Reports conflicting files:
   - `runtime/external_ci.py` (critical infrastructure file)
   - `tests/test_external_ci.py` (test file)
3. Shows conflict sections in `runtime/external_ci.py`:
   ```
   <<<<<<< HEAD (main branch)
   def _github_api_request(...):
       # New auth logic version A
   =======
   def _github_api_request(...):
       # New auth logic version B (from feature branch)
   >>>>>>>
   ```
4. Analyzes both versions:
   - Version A: Uses JWT tokens
   - Version B: Uses Personal Access Token
5. Asks: "Version A (JWT) or Version B (PAT)? Or merge both into configurable auth?"
6. After user choice: Resolves, validates, completes rebase

---

## Combined Workflows

### Example 9: Full Cycle (Develop → Test → Push → Review → Merge)
```
User: "Complete the full workflow: validate my changes, push to GitHub, and create a PR"
```

**Expected Agent Behavior:**
1. **Pre-Push**: Runs linting + tests (as Example 1-3)
2. **Push**: `git push origin feature-branch`
3. **Create PR**: `gh pr create --title "..." --body "..."`
4. **Monitor**: Polls PR checks until complete
5. **Report**: 
   ```
   ✅ Pre-push validation: PASSED
   ✅ Pushed to: origin/feature-branch
   ✅ PR created: #27
   ⏳ PR checks: Running (est. 2 minutes)
   
   I'll monitor the checks and report back when complete.
   ```

---

### Example 10: Hotfix with Immediate Merge Check
```
User: "This is a critical bugfix. Lint, test, push, and tell me if it's safe to merge immediately."
```

**Expected Agent Behavior:**
1. **Validate locally**: `.venv\Scripts\python -m ruff check .` && `.venv\Scripts\python -m pytest --cov=runtime`
2. **Push**: Force-push if needed for hotfix: `git push -f origin hotfix-critical-bug`
3. **Verify PR**: `gh pr checks <pr-number>`
4. **Report merge readiness**:
   ```
   ✅ Local validation: PASSED
   ✅ GitHub Actions: ALL PASS (4/4 checks green)
   ✅ Code reviews: No comments yet
   ✅ Merge conflicts: None
   
   Status: SAFE TO MERGE
   Next: `gh pr merge <pr-number> --merge` or approve via GitHub UI
   ```

---

## Error Recovery Examples

### Example 11: Test Timeout
```
User: "Push my changes"
```

**Expected Agent Behavior:**
1. Runs tests
2. Test hangs for >30 seconds
3. Bash tool times out
4. Reports: "❌ Pytest timed out. Likely cause: test_async_worker.py is hanging on network call. Suggestion: Add timeout decorator or mock network calls. Manual review needed before push."
5. Does NOT push

---

### Example 12: Missing Authentication
```
User: "Check PR #30 status"
```

**Expected Agent Behavior:**
1. Tries: `gh pr checks 30`
2. Gets: `error: authentication required`
3. Reports: "❌ GitHub CLI not authenticated. Run: `gh auth login` to authenticate, then try again."
4. Does NOT proceed

---

### Example 13: Invalid PR Number
```
User: "Review PR #999 for me"
```

**Expected Agent Behavior:**
1. Tries: `gh pr view 999`
2. Gets: `error: pull request not found`
3. Reports: "❌ PR #999 not found. Verify the number is correct. Available PRs: (lists recent PRs)"
4. Asks: "Which PR should I check?"

---

## Key Behaviors Demonstrated

✅ **Auto-fix vs. Escalate**: Auto-fixes import ordering, escalates docstring issues
✅ **Fail-Fast**: Stops immediately on linting/test failures with specific context
✅ **Polling**: Continuously monitors GitHub Actions with 15-second intervals
✅ **Detailed Reporting**: Provides exact line numbers, error messages, suggestions
✅ **State Preservation**: Never leaves workspace in inconsistent state
✅ **Error Recovery**: Handles auth failures, timeouts, missing files gracefully
✅ **User Autonomy**: Asks for clarification when ambiguous (JWT vs. PAT)

