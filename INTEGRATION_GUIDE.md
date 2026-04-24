---
name: Integration Guide - Agent Bash CI Workflow with CI Ready Review Skill
description: How the new agent instructions integrate with existing project skills
---

# Integration Guide

## Relationship to Existing Skills

### CI Ready Review Skill
**Location**: [skill/ci-ready-review/SKILL.md](skill/ci-ready-review/SKILL.md)

| Aspect | CI Ready Review Skill | Agent Bash CI Workflow Instructions |
|--------|---|---|
| **Purpose** | Manual PR validation checklist | Automated bash execution for workflows |
| **Trigger** | User performs code review manually | Agent triggers via natural language prompts |
| **Validation Steps** | 1. Linting (Ruff) 2. Testing 3. Docker Build 4. Security Scan | Same 4 steps, automated in sequence |
| **Error Reporting** | Human-readable checklist format | Structured error context with line numbers and suggestions |
| **PR Lifecycle** | Post-push review workflow | Post-push polling + status analysis |
| **Scope** | Read-only validation checklist | Execute bash commands + modify state (commits, pushes) |

**Integration**:
- Agent instructions **automate** the manual steps described in CI Ready Review
- Agent uses the same validation commands (ruff, pytest, docker, trivy)
- Agent follows the same "Ready to Merge" criteria from the skill
- Skill remains as human reference; agent is automated version

---

## Tool Registry Integration

### Bash Tool Schema
**File**: [tools/bash.json](tools/bash.json)

```json
{
  "name": "bash",
  "description": "Run an allowlisted shell command and return stdout, stderr, and exit code.",
  "input_schema": {
    "type": "object",
    "required": ["command"],
    "properties": {
      "command": { "type": "string" }
    }
  },
  "output_schema": {
    "type": "object",
    "required": ["stdout", "stderr", "exit_code"],
    "properties": {
      "stdout": { "type": "string" },
      "stderr": { "type": "string" },
      "exit_code": { "type": "integer" }
    }
  }
}
```

**How Agent Instructions Use It**:
```
When agent needs to run `ruff check .`:
1. Invokes bash tool with input: { "command": ".venv\Scripts\python -m ruff check ." }
2. Tool executes command in workspace
3. Tool returns { "stdout": "...", "stderr": "", "exit_code": 0 }
4. Agent parses exit_code (0 = pass, 1 = violations)
5. Agent optionally parses stdout for specific violations
```

---

## External CI Integration

### External CI System
**File**: [runtime/external_ci.py](runtime/external_ci.py)

The existing `external_ci.py` module provides infrastructure for running CI commands and reporting to GitHub. Agent instructions align with this:

**`external_ci.py` Capabilities**:
- Parse repo from git origin URL
- Resolve commit SHA
- Post status checks to GitHub API
- Run arbitrary CI commands

**Agent Bash Workflow Alignment**:
- Agent uses **same command patterns** as `external_ci.py`
- Agent queries GitHub via `gh` CLI (higher level than `external_ci.py`)
- Agent respects **same error handling** (ExternalCIError patterns)
- Example: `_run_external_command()` in `external_ci.py` matches agent's bash execution pattern

---

## Workspace Environment

### Prerequisites Assumed by Agent Instructions

1. **Python Virtual Environment**
   ```bash
   .venv/  (location: workspace root)
   ```
   - Activation: Pre-condition before agent workflow starts
   - Python version: 3.13.0+

2. **Package Installation**
   ```bash
   pip install -e .[test]  # includes pytest, pytest-cov, ruff
   ```

3. **Git Configuration**
   ```bash
   git config user.name "..."
   git config user.email "..."
   ```

4. **GitHub CLI**
   ```bash
   gh auth login  # must be authenticated before using `gh pr` commands
   ```

5. **Docker** (for Docker build validation)
   ```bash
   docker --version  # optional but required for PR checks to pass
   ```

---

## File Structure Impact

### New Files Added
```
agent-shell/
├── agent-bash-ci-workflow.instructions.md  ← Main instruction set
├── AGENT_BASH_CI_EXAMPLES.md              ← Example prompts (13 scenarios)
└── INTEGRATION_GUIDE.md                   ← This file
```

### Existing Files Unchanged
- All runtime code continues to work
- CI Ready Review skill remains as reference
- Bash tool registry entry unchanged
- GitHub Actions workflows unchanged

### Memory Additions
```
/memories/repo/agent-bash-ci-workflow.md  ← Key decisions + integration notes
```

---

## Workflow Orchestration

### Command Flow Example: "Push and check PR status"

```
User Input: "Push my changes and check if the PR is ready"
    ↓
Agent Bash CI Workflow Instructions (Pre-Push Phase)
    ├─ Run: .venv\Scripts\python -m ruff check .
    ├─ Run: .venv\Scripts\python -m pytest --cov=runtime
    └─ Result: ✅ All pass → Ready to push
    ↓
Agent executes: git push origin feature-branch
    ↓
Agent creates PR (if not exists): gh pr create ...
    ↓
Agent Bash CI Workflow Instructions (Post-Push Phase)
    ├─ Poll: gh pr checks <pr-number>
    ├─ Check: All 4 checks green?
    ├─ Analyze: gh pr view <pr-number> --comments
    └─ Report: Status summary + blockers
    ↓
User Decision: Merge? Iterate? Continue working?
```

---

## Security Considerations

### Bash Command Execution Safety

The agent instructions assume these security safeguards:

1. **Workspace Isolation**: All commands execute in workspace root, never system-wide
2. **Tool Allowlist**: Only commands in `tools/bash.json` allowlist can execute
3. **No Secrets in Code**: Instructions explicitly remind agent to use env vars for secrets
4. **GitHub Token Handling**: Agent uses `gh` CLI (handles token securely via system keyring), never stores token in code

### Code Review Safety

Instructions include GitHub Code Scanning analysis step:
- Agent reports security findings from Trivy scan
- Agent helps resolve flagged issues (secrets leaks, CVEs)
- Agent NEVER overrides security warnings without user approval

---

## Troubleshooting & Debugging

### Common Issues & Recovery

| Issue | Root Cause | Recovery |
|-------|-----------|----------|
| `ruff check .` hangs | Circular dependency in linting rules | Run `pip install --upgrade ruff` |
| `pytest` times out | Slow test or infinite loop | Agent identifies slow test, suggests optimization |
| `gh pr checks` fails | Not authenticated | Run `gh auth login` |
| Docker health check fails | Port 8000 already in use | Kill existing container, retry |
| Merge conflict unresolvable | Complex semantic conflict | User provides resolution guidance |

### Debug Commands (Available to User)

```bash
# Verify agent bash workflow readiness
git status  # Check uncommitted changes
.venv\Scripts\python -m ruff check .  # Manual linting
.venv\Scripts\python -m pytest -xvs  # Verbose test output
gh pr checks <pr-number>  # Manual PR status check
git log --oneline -n 5  # Verify commit history
```

---

## Future Extensions

### Possible Enhancements (Not in Scope)

1. **Advanced Conflict Resolution**: Multi-pass merge strategies, 3-way merge visualization
2. **Performance Optimization**: Parallel test execution, test result caching
3. **Custom Linting Rules**: Project-specific ruff configurations
4. **Deployment Integration**: Automated deployment after PR merge
5. **Notification System**: Slack/email alerts for PR status

These would extend the instructions but maintain backward compatibility.

---

## Quick Reference: File Locations

| File | Purpose | Link |
|------|---------|------|
| Instructions | Core agent behavior | [agent-bash-ci-workflow.instructions.md](agent-bash-ci-workflow.instructions.md) |
| Examples | 13 usage scenarios | [AGENT_BASH_CI_EXAMPLES.md](AGENT_BASH_CI_EXAMPLES.md) |
| Skill Reference | Manual PR validation | [skill/ci-ready-review/SKILL.md](skill/ci-ready-review/SKILL.md) |
| Tool Registry | Bash tool schema | [tools/bash.json](tools/bash.json) |
| CI Module | External CI infrastructure | [runtime/external_ci.py](runtime/external_ci.py) |
| Repo Memory | Key decisions | `/memories/repo/agent-bash-ci-workflow.md` |

