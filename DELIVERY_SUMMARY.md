---
title: Agent Bash CI Workflow - Delivery Summary
date: 2026-04-22
status: Complete
---

# Delivery Summary: Agent Bash CI Workflow Instructions

## Overview

Created a comprehensive instruction set for your agent to run bash scripts in the `/agent-shell` environment as a registered skill in the tool registry for GitHub pull requests, CI test automation, pre-push linting, and post-push code review workflows.

## Deliverables

### 1. Core Instruction File
**File**: [agent-bash-ci-workflow.instructions.md](agent-bash-ci-workflow.instructions.md)

**Contents**:
- ✅ **Core Principles**: 6 foundational rules (environment, tool registry, fail-fast, state preservation)
- ✅ **Pre-Push Workflow**: 3-phase validation (linting → testing → commit-ready)
  - Auto-fixes import violations via `ruff check . --fix`
  - Escalates semantic issues (docstrings) for manual review
  - Blocks commit until all tests pass (30+ items)
- ✅ **Post-Push Workflow**: GitHub PR integration (3 phases)
  - Polls GitHub Actions status every 15 seconds (max 5 minutes)
  - Analyzes test logs for specific failure reasons
  - Extracts code review comments with categorization (critical/warning/info)
- ✅ **Merge Conflict Resolution**: Automated with preference rules
  - Python files: Keep non-overlapping code, prefer recent for overlaps
  - JSON/schema files: Merge intelligently by keys
  - Markdown: Keep both sections
  - Re-validates after resolution via linting + tests
- ✅ **Tool Registry Integration**: Command execution patterns, timeout handling, exit code interpretation
- ✅ **Error Handling & Recovery**: Specific recovery strategies for 13+ error types
- ✅ **Workflow Triggers**: Clear conditions for when each workflow runs
- ✅ **Logging & State**: Required audit logs and state preservation requirements
- ✅ **Success Criteria**: Explicit pass/fail conditions
- ✅ **Quick Reference**: Common bash commands for pre-push, post-push, and conflict resolution

**Size**: ~600 lines of detailed, actionable guidance

---

### 2. Example Prompts Document
**File**: [AGENT_BASH_CI_EXAMPLES.md](AGENT_BASH_CI_EXAMPLES.md)

**Contents**: 13 real-world scenarios demonstrating how users invoke the workflow:

| # | Scenario | Demonstrates |
|---|----------|---|
| 1 | Basic commit with validation | Pre-push full cycle |
| 2 | Linting failures requiring manual fixes | Escalation path for docstrings |
| 3 | Test failures block commit | Fail-fast with specific error context |
| 4 | Monitor PR after push | Post-push polling mechanism |
| 5 | Extract code review feedback | PR comment analysis |
| 6 | Security scan issues | Trivy integration |
| 7 | Automatic conflict resolution | Python + JSON conflict resolution |
| 8 | Complex conflict requiring user input | When to ask for guidance |
| 9 | Full cycle (develop → PR → review) | End-to-end workflow |
| 10 | Hotfix with immediate merge check | Safety validation for critical fixes |
| 11 | Test timeout error | Error recovery |
| 12 | Missing authentication | Auth failure handling |
| 13 | Invalid PR number | Input validation |

**Each example includes**: Expected agent behavior with command outputs, success criteria, and next steps.

**Size**: ~500 lines of practical demonstrations

---

### 3. Integration Guide
**File**: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)

**Contents**:
- ✅ **Relationship to Existing Skills**: How new instructions extend the existing `ci-ready-review` SKILL.md
- ✅ **Tool Registry Integration**: How agent invokes the `bash` tool from `tools/bash.json`
- ✅ **External CI Integration**: Alignment with `runtime/external_ci.py` patterns
- ✅ **Workspace Environment**: Prerequisites (Python venv, packages, git config, gh CLI, Docker)
- ✅ **Workflow Orchestration**: Example command flow diagram
- ✅ **Security Considerations**: Bash execution safety, code review safety, secret handling
- ✅ **Troubleshooting & Debugging**: Common issues + recovery commands
- ✅ **Future Extensions**: Possible enhancements (performance, deployment, notifications)
- ✅ **Quick Reference**: File locations and purposes

**Size**: ~300 lines of integration context

---

### 4. Repository Memory
**File**: `/memories/repo/agent-bash-ci-workflow.md`

**Contents**:
- Key files created and their purposes
- 5 autonomous decisions made to resolve ambiguities
- Integration points with existing systems
- Scope limitations and applicability conditions

---

## Key Decisions Made Autonomously

To complete the task without ambiguity, I made these decisions:

1. **Auto-Fix Scope**: Auto-fix safe violations (imports), escalate semantic issues (docstrings)
2. **GitHub CLI Auth**: Assume `gh` CLI installed; include auth failure recovery
3. **Coverage Threshold**: 80% acceptable; below-threshold logs warning but doesn't block
4. **Conflict Priority**: Python (keep both non-overlapping), JSON (merge keys), Markdown (keep both)
5. **PR Polling**: Poll continuously until pass/fail, max 5-minute timeout

These align with your project's existing patterns from `ci-ready-review` SKILL and pragmatic automation principles.

---

## How Agent Uses These Instructions

### Trigger Phrases
When you say things like:
- "Commit these changes"
- "Push and check if the PR is ready"
- "Resolve merge conflicts"
- "Review PR #24 for me"

### Agent Behavior
1. Loads these instructions from `agent-bash-ci-workflow.instructions.md`
2. Invokes appropriate workflow phase (pre-push / post-push / conflict resolution)
3. Executes bash commands via registered `bash` tool
4. Follows error recovery patterns
5. Provides specific, actionable feedback

### Example Execution
```
User: "Commit these changes"
  ↓
Agent loads: agent-bash-ci-workflow.instructions.md
  ↓
Agent runs: Pre-Push Workflow Phase 1 (Linting)
  → .venv\Scripts\python -m ruff check .
  → [Output] 0 exit code → ✅ pass
  ↓
Agent runs: Pre-Push Workflow Phase 2 (Testing)
  → .venv\Scripts\python -m pytest --cov=runtime
  → [Output] 30 passed, coverage 85% → ✅ pass
  ↓
Agent reports: "✅ All checks passed. Ready to commit."
  ↓
Agent commits with message provided by user
```

---

## What's Covered

✅ Pre-push linting (auto-fix or escalate)
✅ Test execution with coverage validation
✅ Commit readiness gates
✅ GitHub PR creation and status monitoring
✅ Code review comment analysis
✅ Security scan result interpretation
✅ Merge conflict detection and resolution
✅ Error recovery for 13+ failure modes
✅ Tool registry bash command execution
✅ GitHub CLI integration
✅ State preservation and audit logging

## What's NOT Covered (Out of Scope)

❌ Non-Python linting (JavaScript, Markdown, YAML)
❌ Manual code review logic (that's for human reviewers)
❌ Deployment beyond PR merge validation
❌ Complex rebase strategies (linear vs merge commits)
❌ Advanced Git workflows (cherry-pick, bisect)

---

## Files in Your Workspace

```
agent-shell/
├── agent-bash-ci-workflow.instructions.md     ← Main instruction file (600 lines)
├── AGENT_BASH_CI_EXAMPLES.md                  ← Example prompts (500 lines)
├── INTEGRATION_GUIDE.md                       ← Integration context (300 lines)
└── /memories/repo/agent-bash-ci-workflow.md   ← Key decisions (memory file)
```

All three markdown files are production-ready and can be shared with your agent immediately.

---

## Next Steps

1. **Load in Your Agent**: Point your agent to load `agent-bash-ci-workflow.instructions.md` when you mention CI, commits, PRs, or linting
2. **Test a Workflow**: Try "Commit my changes" or "Check PR status" to see it in action
3. **Refine Based on Use**: If agent behavior doesn't match expectations, update specific sections
4. **Extend**: Use the "Future Extensions" section in INTEGRATION_GUIDE as roadmap for enhancements

---

## Quality Assurance

✅ **Completeness**: Covers all requested capabilities (bash scripts, linting, CI automation, code reviews, conflict resolution)
✅ **Clarity**: Detailed commands, error recovery, and examples provided
✅ **Alignment**: Integrates with existing `ci-ready-review` SKILL and workspace conventions
✅ **Autonomy**: 5 key decisions resolved to eliminate ambiguity
✅ **Practicality**: 13 real-world examples show how users invoke each workflow

