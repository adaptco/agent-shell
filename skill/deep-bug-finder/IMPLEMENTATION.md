# Deep Bug Finder - Implementation Guide

## Quick Start

This skill documents the **deep-bug-finder** agent—a systematic approach to uncovering critical correctness bugs in recent code changes.

### What This Does
- Scans commits from the last 7 days (configurable)
- Identifies high-risk code areas (concurrency, data, auth, resources)
- Traces full code paths to find real, reproducible bugs
- Fixes critical issues with minimal, high-confidence changes
- Adds tests to lock in correct behavior

### What This Does NOT Do
- Fix style issues, warnings, or minor edge cases
- Refactor unrelated code
- Report theoretical concerns without concrete trigger scenarios
- Open PRs unless >85% confident in the bug and fix

## Typical Workflow

### 1. Environment Check
```powershell
# Activate venv
. .venv/Scripts/Activate.ps1

# Install package
pip install -e .[test]

# Verify pytest
pytest --collect-only
```

### 2. Scan Recent Commits
```powershell
# List last 7 days of commits with file changes
git log --since="7 days ago" --name-status --pretty=format:"%H %s" | Select-Object -First 20
```

### 3. Identify High-Risk Changes
Look for commits that touch:
- **Data operations**: `database.py`, `cache.py`, `models.py`, `persistence.py`
- **Concurrency**: Async/await, locks, shared state, task queues
- **Auth**: Permission checks, token validation, session management
- **Resources**: File I/O, network requests, memory allocation, cleanup

### 4. Deep Review Each High-Risk File
For each risky change:

#### a) Read the diff
```powershell
git show <commit-hash> -- <file>
```

#### b) Read full file context
```powershell
# View the entire file to understand surrounding code
cat <file>
```

#### c) Find all callers
```powershell
# Search for function/class usage
grep -r "function_name" . --include="*.py" | grep -v ".pyc"
```

#### d) Check for tests
```powershell
# Find tests for this file
ls tests/ -Recurse | Select-String -Pattern (Split-Path <file> -LeafBase)
```

#### e) Simulate failure scenarios
Ask yourself:
- What if two threads call this simultaneously?
- What if a network request times out mid-operation?
- What if the database connection drops?
- What if an exception occurs during state update?
- What if a user loses authentication mid-request?

### 5. Report Findings

#### If Critical Bug Found
1. Create a minimal test that reproduces the bug:
   ```python
   def test_race_condition_in_cache_update():
       """Reproduces loss of writes under concurrent access."""
       # Test code
   ```

2. Implement a surgical fix:
   ```python
   # Minimal change that prevents the bug
   ```

3. Verify the test now passes:
   ```powershell
   pytest tests/path/to/test_file.py::test_name -v
   ```

4. Create a PR with the fix and test.

#### If No Bugs Found
Document:
- Number of commits reviewed
- Files analyzed
- Risk areas checked (concurrency, auth, data integrity, etc.)
- Any areas that warrant future review

## Red Flags (High-Risk Patterns)

### Data Corruption
- ❌ No locks around shared mutable state
- ❌ Multi-step operations without transactions
- ❌ Cache and database getting out of sync
- ❌ Writes that can be lost in concurrent access
- ❌ Silent failures during critical operations

### Race Conditions
- ❌ Check-then-act without atomic operations
- ❌ Time-of-check vs. time-of-use gaps
- ❌ Async operations without awaits
- ❌ Shared collections modified during iteration

### Null/Type Errors
- ❌ No null check before dereferencing
- ❌ Type coercion without validation
- ❌ Optional fields accessed without guards
- ❌ Exceptions not caught in critical paths

### Auth/Security
- ❌ Permission check separate from action
- ❌ State change if permission check passes but action fails
- ❌ User context not validated
- ❌ Scope confusion (user vs. org vs. global)

### Resource Leaks
- ❌ File/connection opened but not closed
- ❌ No try-finally or context manager
- ❌ Exception can escape before cleanup
- ❌ Memory allocated without free path

## Example: Finding & Fixing a Data Loss Bug

### Scenario
Commit modifies `cache.py` to add background expiration:

```python
# BEFORE: Safe, single-threaded
def set_cache(key, value):
    cache[key] = value

# AFTER: Bug—no locking on concurrent access
def set_cache_with_expiry(key, value, ttl):
    cache[key] = value
    schedule_expiry(key, ttl)  # Expiry runs in background thread
```

### Investigation
1. **Identify issue**: Background expiry runs async, but cache dict is not thread-safe.
2. **Trace callers**: `set_cache_with_expiry` is called from request handlers (concurrent).
3. **Simulate**: Thread 1 calls `set_cache_with_expiry("x", "a")`, Thread 2 calls `set_cache_with_expiry("x", "b")`. Race condition means one write is lost.
4. **Construct test**:
   ```python
   import threading
   
   def test_concurrent_cache_writes():
       cache.clear()
       results = []
       
       def write_cache(key, val):
           cache_module.set_cache_with_expiry(key, val, 60)
       
       threads = [
           threading.Thread(target=write_cache, args=("key1", f"value{i}"))
           for i in range(100)
       ]
       
       for t in threads:
           t.start()
       for t in threads:
           t.join()
       
       # All 100 writes should be present
       assert len(cache) == 100
   ```

### Fix
```python
import threading

_cache_lock = threading.Lock()
cache = {}

def set_cache_with_expiry(key, value, ttl):
    with _cache_lock:
        cache[key] = value
    schedule_expiry(key, ttl)
```

### Validation
```powershell
pytest tests/test_cache.py::test_concurrent_cache_writes -v
# Test passes ✓
```

## Command Reference

### Inspection
```powershell
# List changed files in last 7 days
git log --since="7 days ago" --name-only --pretty=format: | sort | uniq

# Get full diff for a commit
git show <hash>

# View specific line blame
git blame <file> -L 50,60

# Show what changed in a function
git log -S "function_name" --oneline -- <file>
```

### Testing
```powershell
# Run all tests with coverage
pytest --cov=runtime

# Run tests in a file
pytest tests/test_file.py -v

# Run a single test
pytest tests/test_file.py::test_name -v

# Run with output capture disabled (see print statements)
pytest -s tests/test_file.py

# Run with verbose traceback
pytest -vv tests/test_file.py
```

### Code Review Tools
```powershell
# Find all references to a name
grep -r "name" . --include="*.py" | grep -v test | grep -v ".pyc"

# Count files changed
git diff --name-only main..HEAD | wc -l

# List file with number of changes
git diff --stat main..HEAD
```

## When to Report Without Fixing

**Medium confidence** bugs should be reported in Slack instead of opening a PR if:
- Bug is likely but hard to trigger reliably
- Impact is unclear without more analysis
- Fix requires significant refactoring
- You're >70% but <85% confident

**Example Slack message**:
```
Found potential data race in cache.py (commit abc123):
- Race between set_cache_with_expiry and expiry cleanup
- Two threads writing same key → one write lost
- Impact: Cache inconsistency, incorrect user data
- Confidence: High (~90%)
- Recommendation: Add lock around cache dict access
```

## Safety Checklist

Before opening a PR:
- [ ] I can describe exactly how to reproduce the bug
- [ ] The bug causes observable, harmful breakage (not theoretical)
- [ ] My fix is minimal and surgical (no unrelated refactors)
- [ ] Tests pass and specifically verify the fix
- [ ] I've traced the full code path (callers, error paths, downstream effects)
- [ ] I'm >85% confident this is a real bug, not an edge case

## Next Steps

To use this agent:

1. **As a Copilot skill** (future): Load the `deep-bug-finder` skill and invoke during code review.
2. **As a manual workflow**: Follow this guide for systematic bug-finding on each sprint.
3. **As a subagent**: Delegate to a specialized agent with these instructions during automated reviews.

## Reference

See `SKILL.md` for the complete deep-bug-finder specification, pattern examples, and detailed investigation phases.
