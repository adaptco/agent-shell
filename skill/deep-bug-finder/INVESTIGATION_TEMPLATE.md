# Deep Bug Finder - Investigation Template

Use this template to systematically investigate recent code changes for critical bugs.

## Session Setup

```powershell
# 1. Activate venv
. .venv/Scripts/Activate.ps1

# 2. Install package
pip install -e .[test]

# 3. Verify test suite
pytest --collect-only

# 4. Fetch latest
git fetch origin main
```

## Phase 1: Scope Recent Changes

### Get Recent Commits
```powershell
$days = 7  # Investigate last N days
git log --since="$days days ago" --oneline --name-status --pretty=format:"%H|%s"
```

### Categorize Changes
Create a list of commits and their risk areas:

| Commit | Message | Files | Risk Area | Risk Level |
|--------|---------|-------|-----------|-----------|
| abc123 | Cache expiry | cache.py, queue.py | Concurrency | HIGH |
| def456 | Auth refactor | auth.py, models.py | Auth/Permission | HIGH |
| ghi789 | UI fixes | frontend.py | UI | LOW |

**High-Risk Areas**: 
- Database/persistence operations
- Concurrency primitives and async code
- Authentication and permission checks
- Resource management (files, network, memory)
- State synchronization

## Phase 2: Deep Dive Per High-Risk Commit

### For each HIGH/MEDIUM risk commit:

#### Step 1: Understand the Change
```powershell
git show <commit-hash>
```

**Document**:
- [ ] What was changed?
- [ ] Why was it changed?
- [ ] Does the commit message explain the intent?

#### Step 2: Read Full Context
```powershell
# View the entire modified file(s)
cat <file-path>
```

**Document**:
- [ ] How does this code fit into the larger module?
- [ ] What preconditions must be true for this to work?
- [ ] What are the postconditions (what state should exist after)?

#### Step 3: Trace Callers
```powershell
# Find everywhere this function/class is used
grep -r "function_name" . --include="*.py" | grep -v "def function_name" | head -20
```

**Document**:
- [ ] Who calls this code?
- [ ] From what contexts? (Single-threaded? Async? Concurrent?)
- [ ] What do callers expect to happen?

#### Step 4: Analyze Error Paths
```powershell
# Check for try-except, error handling, timeouts
cat <file-path> | grep -E "(try:|except|finally:|raise|timeout|assert)"
```

**Document**:
- [ ] Are errors caught and handled?
- [ ] Are error cases propagated correctly?
- [ ] What happens if an operation fails mid-way?

#### Step 5: Check for Tests
```powershell
# Find tests for this module
ls tests/ -Recurse | Select-String -Pattern (Split-Path <file> -LeafBase)
```

**Document**:
- [ ] Are there existing tests?
- [ ] Do they cover the changed code path?
- [ ] Are concurrent/edge cases tested?

### Step 6: Simulate Failure Scenarios
For each high-risk change, ask:

#### Concurrency
- What if two threads call this simultaneously?
- What if async code doesn't await properly?
- What if a callback fires while state is being modified?
- **Scenario**: [Describe]
- **Outcome**: [What goes wrong]

#### State Management
- What if this operation fails halfway through?
- What if power/network fails mid-operation?
- What if something changes the state before this completes?
- **Scenario**: [Describe]
- **Outcome**: [What goes wrong]

#### Resource Management
- What if a resource runs out mid-operation?
- What if a file/connection is closed mid-operation?
- What if cleanup code doesn't run?
- **Scenario**: [Describe]
- **Outcome**: [What goes wrong]

#### Auth/Permission
- What if permissions change mid-operation?
- What if a user loses auth between check and action?
- What if a different user can call this code?
- **Scenario**: [Describe]
- **Outcome**: [What goes wrong]

### Step 7: Risk Assessment

**For this commit, rate the bug confidence:**

| Confidence | Description | Action |
|-----------|-------------|--------|
| HIGH (>85%) | Concrete scenario, observable breakage | Create test + fix → PR |
| MEDIUM (70-85%) | Likely but edge-casey or unclear impact | Report in Slack, add to backlog |
| LOW (<70%) | Theoretical or requires implausible conditions | Skip, monitor |

**Confidence Score**: [HIGH / MEDIUM / LOW]
**Reasoning**: [Your assessment]

---

## Phase 3: Report Findings

### If HIGH Confidence Bug Found

#### Create Reproducer Test
```python
# tests/test_<module>.py

def test_<bug_name>():
    """
    Reproduces: [Bug title]
    Scenario: [How to trigger the bug]
    Expected: [What should happen]
    Actual (before fix): [What goes wrong]
    """
    # Setup
    # ...
    
    # Execute
    # ...
    
    # Assert (this will fail before the fix)
    # ...
```

#### Run Test to Confirm It Fails
```powershell
pytest tests/test_<module>.py::test_<bug_name> -v
# Expected: FAILED
```

#### Implement Minimal Fix
```python
# <file>.py
# Make surgical change that prevents the bug
```

#### Verify Test Passes
```powershell
pytest tests/test_<module>.py::test_<bug_name> -v
# Expected: PASSED
```

#### Run Full Test Suite
```powershell
pytest --cov=runtime
# Expected: All tests pass
```

#### Create PR
Document:
- **Bug**: [Concrete description]
- **Impact**: [Data loss / Crash / Security / Resource leak]
- **Root Cause**: [Why it happens]
- **Trigger**: [How to reproduce]
- **Fix**: [Changes made]
- **Tests**: [New or updated tests]

### If MEDIUM Confidence Bug Found

Post to Slack:
```
Found potential bug in <file> (commit <hash>):

Scenario: <Describe trigger conditions>
Impact: <What could go wrong>
Confidence: <70-85%>

Recommendation: [Add to backlog / Needs more analysis / Low priority]
```

### If No Bugs Found

Document:
```
Deep Bug Finder Summary
- Commits reviewed: <N>
- Files analyzed: <M>
- Time period: <dates>

Areas covered:
✓ Data operations (<files>)
✓ Concurrency patterns (<files>)
✓ Auth/permissions (<files>)
✓ Resource management (<files>)

Findings: No critical bugs detected.

Edge cases to monitor:
- <Any areas that warrant future review>
```

---

## Investigation Template (Per Commit)

### Commit: [HASH] | [MESSAGE]

**File(s) Changed**: 
```
<file1>
<file2>
```

**Risk Area**: [Data / Concurrency / Auth / Resource / Other]

**Initial Assessment**: [1-2 sentence summary]

---

### Context Analysis
- What changed: 
- Why it changed: 
- Preconditions required: 
- Expected postconditions: 

### Caller Analysis
- Called from:
- Concurrency context:
- Error handling expectations:

### Scenario Analysis

#### Scenario 1: [Name]
**Trigger**: [How to make this happen]
**Expected**: [Correct behavior]
**Actual Risk**: [What could go wrong]
**Confidence**: HIGH / MEDIUM / LOW

#### Scenario 2: [Name]
**Trigger**: [How to make this happen]
**Expected**: [Correct behavior]
**Actual Risk**: [What could go wrong]
**Confidence**: HIGH / MEDIUM / LOW

---

### Verdict
- **Bug Found**: YES / NO / UNCERTAIN
- **Confidence**: HIGH / MEDIUM / LOW
- **Action**: PR / Slack Report / Monitor / Skip

---

## Tools Reference

### View Code
```powershell
# Diff for one commit
git show <hash>

# Blame for specific lines
git blame <file> -L 10,20

# Full file
cat <file>
```

### Search
```powershell
# Find function callers
grep -r "func_name" . --include="*.py"

# Find pattern
grep -r "pattern" . --include="*.py" --color=never

# Count matches
grep -r "pattern" . --include="*.py" | wc -l
```

### Test
```powershell
# Run single test
pytest tests/test_file.py::test_name -v

# Run with output
pytest tests/test_file.py -s

# Run with coverage
pytest tests/test_file.py --cov=runtime

# List what would run
pytest tests/test_file.py --collect-only
```

---

## Checklist Before Creating PR

- [ ] I have a concrete scenario that triggers the bug
- [ ] The bug causes observable, harmful breakage
- [ ] I have a test that reproduces the bug
- [ ] My fix is minimal and surgical
- [ ] The test passes after the fix
- [ ] All existing tests still pass
- [ ] No unrelated refactoring in this PR
- [ ] My confidence level is >85%

---

## Session Notes

Use this section to track your progress:

**Date**: [ISO 8601]
**Commits Reviewed**: [List hashes]
**Files Analyzed**: [Count]
**Bugs Found**: [Count and confidence levels]
**PRs Created**: [Links]
**Issues Reported**: [Slack/backlog items]
**Time Spent**: [Estimate]
