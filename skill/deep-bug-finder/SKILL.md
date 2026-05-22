---
name: deep-bug-finder
description: Automated deep bug-finding for critical correctness issues. Inspects recent commits to identify data loss, race conditions, null dereferences, auth bypasses, resource leaks, and other high-severity bugs that escape review.
---

# Deep Bug Finder

## Purpose
Perform static and behavioral analysis on recent commits to surface critical correctness bugs that:
- Cause data loss or corruption
- Trigger crashes or infinite loops
- Introduce race conditions that lose writes
- Bypass authentication or permissions
- Leak resources (memory, file handles, connections)
- Silently truncate or drop data
- Dereference null/undefined in critical paths

This agent focuses on **real, reproducible bugs** with concrete trigger scenarios—not theoretical concerns or style issues.

## Confidence Bar
- **High confidence (report + fix)**: You can construct a plausible trigger scenario that causes observable breakage.
- **Medium confidence (report in Slack, no PR)**: Bug is likely but hard to trigger or impact unclear.
- **Low confidence (skip)**: Theoretical or requires implausible preconditions.

## Investigation Strategy

### Phase 1: Scope Recent Changes
1. Fetch commits from the last N days (default: 7 days, configurable).
2. Group changes by area: core logic, data handling, concurrency, auth, resource management.
3. Identify files with highest risk (e.g., database, cache, sync primitives, auth).

### Phase 2: Trace Behavioral Changes
For each high-risk file:
1. **Read the diff**: Understand what changed and why.
2. **Trace the caller chain**: Who calls this code? What are the preconditions?
3. **Check error paths**: Does the code handle errors, timeouts, and edge cases?
4. **Look for state mutations**: Are there shared mutable objects? Ordering dependencies?
5. **Simulate the trigger**: Construct a scenario where the bug manifests.

### Phase 3: Analyze Patterns
Look for:
- **Data corruption**: Writes that can be lost or overwritten (e.g., missing locks, wrong transaction scope).
- **Race conditions**: Concurrent access without synchronization (e.g., check-then-act, lost updates).
- **Null/undefined dereference**: Accessing fields without null checks in critical paths.
- **Auth bypasses**: Permission checks that can be skipped or scope confusion.
- **Resource leaks**: Objects not properly released (files, connections, memory).
- **Infinite loops**: Conditions that never exit or exit after timeout.
- **Silent failures**: Operations that fail but don't propagate errors.
- **State inconsistency**: Distributed state (DB + cache) getting out of sync.

### Phase 4: Validate and Fix
1. **Confirm the trigger scenario**: Can you construct a test that reproduces it?
2. **Analyze the fix**: Is the fix minimal and high-confidence?
3. **Add tests**: Lock in the correct behavior with unit or integration tests.
4. **Avoid refactors**: Don't bundle unrelated cleanups.

## Workflow

### Step 1: Fetch and Parse Recent Commits
```bash
# Get the last 7 days of commits
git log --since="7 days ago" --oneline --name-status --pretty=format:"%H %s"
```

Extract:
- Commit hash, message
- Files changed (A=added, M=modified, D=deleted)
- Diff content for each file

### Step 2: Identify High-Risk Changes
Filter for:
- Database/cache operations
- Concurrency primitives (locks, async/await)
- Authentication or permission checks
- Resource allocation (file/network I/O)
- State synchronization

### Step 3: Deep Code Review
For each high-risk file:
1. **Read the full context**: Not just the diff, the surrounding code and call sites.
2. **Check invariants**:
   - Are preconditions documented and validated?
   - Can the code handle concurrent calls?
   - Are error cases handled?
3. **Simulate failure modes**:
   - Network timeout during write
   - Two threads racing to update the same object
   - Out-of-memory during allocation
   - User loses session/token mid-operation

### Step 4: Report Findings
If you find a critical bug:
- **Description**: Concrete scenario that triggers it, observable symptoms.
- **Root cause**: Why it happens and where in the code.
- **Impact**: What data/users/systems are affected?
- **Fix**: Minimal change that prevents the bug.
- **Tests**: New or updated tests that verify the fix.

If no critical bugs:
- Post a short "no critical bugs found" summary.
- Include number of commits reviewed and files analyzed.

## Critical Rules

1. **Don't open a PR unless you are highly confident.**
   - If the bug is likely but edge-casey, report in Slack without a PR.
   - If you can't construct a trigger scenario, don't file it.

2. **Avoid broad refactors.**
   - Fix the bug with minimal, surgical changes.
   - If the code is messy, note it for future cleanup—don't fix it in this PR.

3. **Add tests.**
   - For each fix, add a test that reproduces the original bug and verifies the fix.
   - Tests should be tight and focused (unit tests preferred).

4. **Trace the full path.**
   - Don't assume something is safe because the immediate code looks okay.
   - Check where it's called from, what state precedes it, what happens after.

5. **Be skeptical of refactors.**
   - If the original author "cleaned up" or "optimized" a critical path, check for unintended behavior changes.
   - Compare old and new semantics carefully.

## Examples of Bugs to Find

### Data Corruption
```python
# BAD: Race condition on shared list
shared_items = []

def add_item(item):
    shared_items.append(item)  # Not thread-safe

def process_all():
    for item in shared_items:  # Can miss items added during iteration
        process(item)
```
**Trigger**: Two threads calling `add_item` and `process_all` concurrently.

### Silent Data Loss
```python
# BAD: Write to cache without checking if key already exists
cache[key] = value  # If two threads race, one write is lost

# Or: Transaction not committed
db.insert(row)  # Forgot db.commit()
```
**Trigger**: High concurrency, power loss, or process crash before implicit commit.

### Null Dereference in Critical Path
```python
# BAD: User object can be None but not checked
def get_user_permissions(user_id):
    user = find_user(user_id)  # Can return None
    return user.role.permissions  # Crashes if user is None
```
**Trigger**: Request for non-existent user ID.

### Auth Bypass
```python
# BAD: Permission check before state change but state mutated after check
if user.can_delete(item):
    item.owner = None  # State change
    item.deleted = True
    db.save(item)  # Exception here leaves item in inconsistent state

# Or: Check bypassed entirely in some code path
def delete_item(item_id):
    item = db.get(item_id)
    db.delete(item)  # No permission check!
```
**Trigger**: Unauthorized user calling delete, or exception during save.

### Resource Leak
```python
# BAD: File not closed if exception occurs
def read_config():
    f = open(config_path)
    data = f.read()
    f.close()  # Never reached if exception during read()
```
**Trigger**: Corrupted config file causes exception during read.

## Prerequisites

- **Python >= 3.13.0**
- **Virtual environment** at `.venv`
- **Package installed**: `pip install -e .[test]`
- **Git**: Accessible in PATH
- **Test suite**: Running `pytest` should work

## Tools & Commands

### Git
```bash
# List recent commits with file changes
git log --since="7 days ago" --name-status --pretty=format:"%H %s"

# Get diff for a specific commit
git show <commit-hash>

# Get blame for a specific line
git blame <file> | grep <line-number>
```

### Code Review
- **Read files**: Use view/grep to inspect code.
- **Trace callers**: Search for function/class names in the codebase.
- **Check tests**: Look for existing tests that exercise the code path.

### Testing
```bash
# Run all tests
pytest --cov=runtime

# Run specific test
pytest tests/path/to/test_file.py::test_function -v

# Run with verbose output
pytest -vv
```

## Output Format

### If Bug Found and Fixed
```markdown
## Bug: [Title]

**Impact**: [Data loss / Crash / Security / Resource leak / etc.]

**Scenario**: [Concrete steps to reproduce]

**Root Cause**: [Why it happens]

**Fix**: [Changes made]

**Tests**: [New or updated tests]

**Validation**: [How you verified the fix]
```

### If Bug Found but Not Fixed
```markdown
## Potential Bug: [Title]

**Confidence**: [High / Medium / Low]

**Scenario**: [Trigger conditions]

**Root Cause**: [Why it likely happens]

**Impact**: [What could go wrong]

**Recommendation**: [Report in Slack / Add to backlog / etc.]
```

### If No Critical Bugs Found
```markdown
## Summary
No critical bugs found in [N] commits affecting [M] files.

**Coverage**: [List of areas reviewed]

**Risk Assessment**: [Any concern areas or edge cases to monitor]
```

## Safety Checklist Before Opening a PR

- [ ] You can construct a concrete scenario that reproduces the bug.
- [ ] The bug causes observable breakage (crash, data loss, wrong behavior).
- [ ] The fix is minimal and doesn't refactor unrelated code.
- [ ] Tests pass locally and verify the fix.
- [ ] You've traced the full code path from caller to downstream effects.
- [ ] You're not "just being safe"—you have evidence the bug is real.

## Session Setup

Before beginning:
1. **Activate venv**: 
   ```bash
   . .venv/Scripts/Activate.ps1  # Windows
   source .venv/bin/activate       # macOS/Linux
   ```
2. **Install package**: `pip install -e .[test]`
3. **Verify pytest works**: `pytest --collect-only`
4. **Fetch latest commits**: `git fetch origin main`

## Recommendations for Effective Bug-Finding

1. **Start with high-risk areas**: Database, concurrency, auth, resource management.
2. **Look for refactors**: When code is "reorganized," semantics can drift.
3. **Check error paths**: Try-except blocks, timeouts, missing error propagation.
4. **Trace backwards**: From the diff, find all callers and their expectations.
5. **Simulate concurrency**: Even single-threaded code can have race-like bugs if called asynchronously.
6. **Test edge cases**: Off-by-one, empty collections, null values, permission boundaries.
7. **Review dependencies**: Did the commit add a dependency? Check for known vulnerabilities.

## Notes

- **Expected outcome most days**: "No critical bugs found" is a success, not a failure.
- **High bar for fixes**: If you're not >85% confident, report in Slack instead of opening a PR.
- **Test coverage**: Existing test suite is the safety net; if new code isn't tested, it's higher risk.
