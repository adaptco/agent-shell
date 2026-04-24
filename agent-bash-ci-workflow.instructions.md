---
name: agent-bash-ci-workflow
version: 1.0.0
scope: [ci-automation, code-review, pre-push-validation, merge-conflict-resolution]
applies-to: [tool-registry, skill-execution, github-workflows, bash-scripts]
---

# Agent Bash CI Workflow Instructions

These instructions guide the agent to execute bash scripts within the `/agent-shell` environment as part of the tool registry, automating linting, CI testing, code reviews, and merge conflict resolution workflows.

## Core Principles

1. **Environment**: Always execute bash scripts in the `.venv`-activated `/agent-shell` workspace root
2. **Tool Registry Integration**: Use the `bash` tool registered in `tools/bash.json` for all shell command execution
3. **Pre-Push Validation**: Run linting and tests before allowing commit operations
4. **Post-Push Automation**: Perform code reviews and status checks after push to GitHub
5. **Fail-Fast Pattern**: Stop and diagnose on first failure; report root cause before retry
6. **State Preservation**: Never allow bash scripts to leave the workspace in an inconsistent state

## Pre-Push Workflow (Before Commits)

### Phase 1: Lint Validation

When the agent detects uncommitted changes or receives a pre-commit instruction:

1. **Execute Linting**:
   ```bash
   .venv\Scripts\python -m ruff check .
   ```
   - Expected: Exit code 0 (no violations)
   - On Failure: Parse `ruff` output for specific violations and auto-fix using:
     ```bash
     .venv\Scripts\python -m ruff check . --fix
     ```

2. **Verify Linting Fixes**:
   ```bash
   .venv\Scripts\python -m ruff check .
   ```
   - If still fails after auto-fix: Report specific violations to user (e.g., unused imports, docstring issues, import ordering)

### Phase 2: Test Execution

After linting passes, run comprehensive test suite:

1. **Execute Tests with Coverage**:
   ```bash
   .venv\Scripts\python -m pytest --cov=runtime
   ```
   - Expected: All tests pass (30+ items), coverage >= threshold
   - On Failure: 
     - Capture test output and identify failed test names
     - Do NOT proceed to commit until all tests pass
     - Report specific test failures (assertion errors, exceptions) to user

2. **Validate Coverage**:
   - Check that `runtime` module has adequate coverage (>80% recommended)
   - If below threshold: Flag for user review before commit

### Phase 3: Commit Readiness

Only permit commit operations after both Phase 1 and Phase 2 succeed:

- All linting checks pass
- All tests pass with acceptable coverage
- No uncommitted changes remain after fixes

## Post-Push Workflow (After Push/PR Creation)

### Phase 1: GitHub Actions Status Check

After code is pushed and a PR is created, monitor CI status:

1. **Check PR Status**:
   ```bash
   gh pr checks <pr-number>
   ```
   - Expected: All 4 checks green:
     1. `test / test (3.13)`
     2. `test / docker-build`
     3. `test / security-scan`
     4. `Trivy`

2. **Poll Mechanism**:
   - Check status immediately after push (GitHub Actions starts ~10-30 seconds after push)
   - Retry every 15 seconds for up to 5 minutes
   - Report partial completion progress to user

### Phase 2: Test Log Analysis

When GitHub Actions completes, retrieve and analyze logs:

1. **Get Test Results**:
   ```bash
   gh pr view <pr-number> --json "statusCheckRollup"
   ```

2. **Extract Failed Test Details**:
   - Parse GitHub Actions output to identify specific test failures
   - If tests failed: Use `gh pr view <pr-number> --comments` to fetch code review feedback

3. **Retrieve Full Logs** (if available via GitHub API):
   - Download artifacts from failed jobs
   - Search for assertion messages, stack traces, stderr output
   - Provide specific failure context to user (not just "tests failed")

### Phase 3: Code Review Processing

When code reviews or security scans flag issues:

1. **Fetch Review Comments**:
   ```bash
   gh pr view <pr-number> --comments
   ```

2. **Analyze Issues**:
   - Parse each comment for actionable feedback
   - Identify patterns (e.g., "remove unused import", "deprecated API usage", "security vulnerability")
   - Categorize by: critical (blocks merge), warning (should fix), info (nice-to-have)

3. **Generate Fix Plan**:
   - For each critical issue: Propose specific code change
   - Verify the fix locally before pushing:
     ```bash
     .venv\Scripts\python -m pytest --cov=runtime -xvs
     .venv\Scripts\python -m ruff check .
     ```
   - Commit and push fixes; CI re-runs automatically

## Merge Conflict Resolution Workflow

When `git merge` or `git rebase` results in conflicts:

### Conflict Detection

1. **Detect Conflict State**:
   ```bash
   git status
   ```
   - Look for "both modified", "both added", or "both deleted" markers
   - Parse conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)

2. **Identify Conflicting Files**:
   ```bash
   git diff --name-only --diff-filter=U
   ```

### Conflict Resolution Strategy

**For Python files** (.py):
1. Open conflicted file and examine both sides of the conflict
2. Prefer changes that:
   - Keep both code versions if non-overlapping (e.g., different functions)
   - Keep the version with more recent modifications if overlapping
   - Preserve test coverage (prefer changes that add tests)
3. Run linting and tests after resolution to validate:
   ```bash
   .venv\Scripts\python -m ruff check <file>
   .venv\Scripts\python -m pytest -xvs
   ```

**For Configuration/Schema files** (.json, .schema.json, .yml):
1. Prefer the `main` branch version as baseline
2. Manually merge in new keys/values from the feature branch if non-conflicting
3. Validate schema files:
   ```bash
   .venv\Scripts\python -c "import json; json.load(open('<file>'))"
   ```

**For Markdown/Documentation** (.md):
1. Keep both sections if both are informative
2. Use section headings to separate different aspects
3. No validation needed; commit after manual review

### Conflict Completion

1. **Stage Resolved Files**:
   ```bash
   git add <resolved-file>
   ```

2. **Verify All Resolved**:
   ```bash
   git status
   ```
   - Confirm no files still show "both modified" status

3. **Complete Merge**:
   ```bash
   git commit -m "Merge branch with conflict resolution"
   ```
   or
   ```bash
   git rebase --continue
   ```

4. **Re-run Validation** (same as Pre-Push Phase 1-2):
   ```bash
   .venv\Scripts\python -m ruff check .
   .venv\Scripts\python -m pytest --cov=runtime
   ```

## Tool Registry Integration

### Bash Tool Usage Pattern

All bash commands MUST be invoked through the registered `bash` tool:

```json
{
  "tool": "bash",
  "input": {
    "command": "<command-string>"
  }
}
```

### Command Execution Rules

1. **Workspace Root**: All paths relative to `/agent-shell` root
2. **Environment Activation**: Assume `.venv` is already activated (pre-condition)
3. **Stdout/Stderr Capture**: 
   - Parse `stdout` for expected output or data
   - Parse `stderr` for error messages, warnings
   - Use `exit_code` to determine success (0 = success, non-zero = failure)
4. **Timeout Handling**: If bash tool times out (>30s for most commands):
   - Treat as tool failure, not command success
   - Report timeout to user; retry is up to user's discretion

### Command Categories

| Category | Command Pattern | Timeout | Exit Code | Output Parsing |
|----------|---|---|---|---|
| Linting | `ruff check .` | 10s | 0=pass, 1=violations | Parse violation lines |
| Testing | `pytest --cov=runtime` | 30s | 0=pass, 1=failures | Parse "PASSED", "FAILED", coverage summary |
| Git Ops | `git status`, `git diff` | 5s | 0=success | Parse status output for file states |
| GitHub CLI | `gh pr checks`, `gh pr view` | 10s | 0=success | Parse JSON output (when using `--json`) |

## Error Handling & Recovery

### Linting Failures

- **Violation Type**: `Unused imports`
  - Action: Run auto-fix `ruff check . --fix`
  - Verify: Re-run linting
  
- **Violation Type**: `Docstring issues`
  - Action: Manual review required; report to user with specific line numbers
  - Do NOT auto-fix; these require semantic understanding

- **Violation Type**: `Import ordering`
  - Action: Run auto-fix `ruff check . --fix`
  - Verify: Re-run linting

### Test Failures

- **Pattern**: `AssertionError` or `FAILED test_*.py`
  - Action: Report the assertion message and test name
  - Do NOT proceed until user investigates and commits fix

- **Pattern**: `ImportError` or `ModuleNotFoundError`
  - Action: Likely missing dependency; suggest `pip install -e .[test]`
  - Do NOT proceed; user must install dependencies

- **Pattern**: `timeout` or `TIMEOUT`
  - Action: Report specific slow test; suggest user optimize or increase timeout

### GitHub CLI Failures

- **Error**: `authentication required` or `not authenticated`
  - Action: User must run `gh auth login`
  - Do NOT proceed; authentication is prerequisite

- **Error**: `PR not found` or `could not find pull request`
  - Action: Verify PR number is correct and PR exists
  - Do NOT proceed; user must provide valid PR number

### Merge Conflict Failures

- **Error**: `git merge` exits with code 1 and conflict markers present
  - Action: Enter Conflict Resolution Workflow
  - Report: List of conflicting files to user

- **Error**: `git rebase --continue` fails
  - Action: Check for remaining conflict markers
  - Action: User may need to abort with `git rebase --abort` and try merge instead

## Workflow Triggers & Conditions

### When to Run Pre-Push Workflow

Agent MUST run pre-push workflow when:
- User requests "commit changes" or "push code"
- User provides a commit message (indicating intent to commit)
- Uncommitted changes are detected with `git status`
- User explicitly requests "lint" or "test" commands

Agent SHOULD NOT run pre-push workflow when:
- User is only viewing code or asking questions
- User explicitly requests to skip checks
- Running tests/linting in isolation for diagnostic purposes (user can skip commit)

### When to Run Post-Push Workflow

Agent MUST run post-push workflow when:
- User creates or updates a PR
- User pushes to a branch that has an open PR
- User explicitly requests "check PR status" or "review PR"

Agent SHOULD NOT run post-push workflow when:
- PR is still running CI (unless explicitly requested to poll)
- User has not yet pushed changes

### When to Run Merge Conflict Workflow

Agent MUST run merge conflict workflow when:
- `git merge` or `git rebase` command fails
- Conflicting files are detected with `git status` or `git diff --name-only --diff-filter=U`
- User explicitly requests "resolve conflicts"

Agent SHOULD NOT attempt automatic conflict resolution without:
- Informing user of conflict discovery
- Explaining the conflict (which files, which sections)
- Offering to resolve or asking user for guidance

## Logging & State

### Required Logging

The agent SHOULD log (for debugging and audit):

1. **Command Execution**:
   - Bash command invoked
   - Start timestamp
   - Exit code and duration

2. **Validation Results**:
   - Linting status (pass/fail + violation count)
   - Test status (pass/fail + test count)
   - Coverage percentage

3. **Workflow Transitions**:
   - Pre-push phase completion
   - Post-push status check results
   - Conflict resolution steps

### State Preservation

Agent MUST preserve workspace state:
- No uncommitted changes after linting auto-fixes (either staged or committed)
- No dangling containers or processes after Docker health checks
- No temporary files left behind

## Success Criteria

A bash script execution is **successful** when:

1. **Pre-Push**: All linting + tests pass, ready to commit
2. **Post-Push**: PR status shows all 4 checks green, code review has no blockers
3. **Merge Conflict**: All conflicts resolved, tests + linting pass, ready to push

A bash script execution **fails** when:
- Exit code is non-zero and not handled by recovery logic
- Output indicates unrecoverable error (e.g., missing dependency, authentication failure)
- User terminates operation or requests abort

---

## Quick Reference: Common Commands

```bash
# Pre-Push
.venv\Scripts\python -m ruff check .
.venv\Scripts\python -m ruff check . --fix
.venv\Scripts\python -m pytest --cov=runtime

# Post-Push
gh pr checks <pr-number>
gh pr view <pr-number> --comments
gh pr view <pr-number> --json "statusCheckRollup"

# Merge Conflict Resolution
git status
git diff --name-only --diff-filter=U
git add <resolved-file>
git commit -m "Merge branch with conflict resolution"
git rebase --continue

# Diagnostics
git log --oneline -n 5
git branch -vv
git remote -v
```
