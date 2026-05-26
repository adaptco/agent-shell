# Deep Bug Finder - Complete Guide

## Overview

The **deep-bug-finder** agent is a comprehensive system for identifying and fixing critical correctness bugs in recent code commits. It's designed to surface real, reproducible issues that would cause:

- **Data loss or corruption** (writes lost, inconsistency)
- **Crashes** (null dereferences, unhandled exceptions)
- **Race conditions** (concurrent access without synchronization)
- **Security vulnerabilities** (auth bypasses, permission leaks)
- **Resource leaks** (files, connections, memory not released)
- **Silent failures** (operations fail but errors ignored)

## Files in This Skill

| File | Purpose |
|------|---------|
| **SKILL.md** | Complete specification, patterns, investigation phases, output formats |
| **IMPLEMENTATION.md** | Practical guide with workflow steps and example findings |
| **QUICK_REFERENCE.md** | One-page checklist, command reference, red flags, decision tree |
| **INVESTIGATION_TEMPLATE.md** | Step-by-step template for investigating each commit |
| **README.md** | This file—overview and navigation |

## Quick Start (5 minutes)

1. **Read** `QUICK_REFERENCE.md` to understand high-risk patterns
2. **Setup** your environment (`.venv`, `pip install -e .[test]`)
3. **Use** `INVESTIGATION_TEMPLATE.md` for each commit
4. **Create PR** only if >85% confident, with test

## Core Workflow

```
Scope Commits (last 7 days)
    ↓
Identify High-Risk Changes (data, concurrency, auth, resources)
    ↓
Deep Code Review (read full context, trace callers, check errors)
    ↓
Simulate Failure Scenarios (What could go wrong?)
    ↓
Rate Confidence (HIGH / MEDIUM / LOW)
    ↓
├─ HIGH (>85%) → Write test, fix, PR
├─ MEDIUM (70-85%) → Report in Slack
└─ LOW (<70%) → Skip, monitor
```

## High-Risk Patterns

### 🔴 Data Corruption
```python
# Missing locks on shared state
cache[key] = value  # Concurrent writes → one is lost

# Multi-step ops without atomicity
if key in cache:
    value = cache[key]  # Another thread can delete here
    process(value)
```

### 🔴 Race Conditions
```python
# Check-then-act without atomicity
if cache[key] exists:  # Check
    cache[key] = new_value  # Race! Another thread might have deleted it

# Async without proper await
task = async_operation()  # Oops, forgot await!
continue_synchronously()  # Runs before task completes
```

### 🔴 Null Dereference
```python
# No null check
user = find_user(id)  # Can be None
return user.email  # Crash!

# Fix:
user = find_user(id)
if not user:
    return None
return user.email
```

### 🔴 Auth Bypass
```python
# Permission check separate from action
if user.can_delete(item):
    db.delete(item)  # If exception here, inconsistency
    # Exception here leaves item in weird state

# No permission check
def delete(item_id):
    db.get(item_id)
    db.delete(item_id)  # Missing permission check!
```

### 🔴 Resource Leak
```python
# File not closed on exception
f = open(file)
data = f.read()  # Exception here → file never closes
f.close()

# Fix: Use context manager
with open(file) as f:
    data = f.read()  # Auto-closes even on exception
```

## Confidence Levels

| Level | Criteria | Action |
|-------|----------|--------|
| **HIGH** (>85%) | Concrete trigger scenario; observable, harmful breakage | Write test, fix, create PR |
| **MEDIUM** (70-85%) | Likely bug; trigger may be edge-casey or impact unclear | Report in Slack; add to backlog |
| **LOW** (<70%) | Theoretical or requires implausible preconditions | Skip; note for monitoring |

**Key**: You must be able to **construct a test scenario** that reproduces the bug. If you can't, it's not HIGH confidence.

## Investigation Process (Per Commit)

### 1. Read the Diff
```powershell
git show <hash>
```
- What changed?
- Why was it changed?
- Does the commit message explain intent?

### 2. Read Full Context
```powershell
cat <file>
```
- How does this fit into the broader codebase?
- What preconditions must exist?
- What postconditions should exist?

### 3. Find Callers
```powershell
grep -r "function_name" . --include="*.py"
```
- Who calls this?
- From concurrent or single-threaded contexts?
- What do they expect?

### 4. Check Error Paths
```powershell
# Look for try-except, error handling
cat <file> | grep -E "(try:|except|raise|assert)"
```
- Are errors caught?
- Are they propagated correctly?
- What if an operation fails mid-way?

### 5. Simulate Failure Scenarios
For each high-risk area, ask:

**Concurrency**
- What if two threads call this simultaneously?
- What if callbacks race?

**State**
- What if power fails mid-operation?
- What if the state changes?

**Resources**
- What if a resource runs out?
- What if cleanup doesn't run?

**Auth**
- What if permissions change mid-operation?
- What if an unauthorized user calls this?

### 6. Rate Confidence
Can you construct a test? Can you observe the breakage?

## Creating a Fix

When you find a HIGH confidence bug:

### 1. Write a Test That Reproduces It
```python
def test_concurrent_writes():
    """Reproduces data loss under concurrent writes."""
    cache.clear()
    threads = [
        Thread(target=cache_set, args=(key, f"val{i}"))
        for i in range(100)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Before fix: This fails (some writes lost)
    assert len(cache) == 100
```

### 2. Run Test to Confirm It Fails
```powershell
pytest tests/test_file.py::test_concurrent_writes -v
# Expected: FAILED ✓
```

### 3. Implement Minimal Fix
```python
import threading

_lock = threading.Lock()

def cache_set(key, value):
    with _lock:
        cache[key] = value
```

### 4. Run Test to Confirm It Passes
```powershell
pytest tests/test_file.py::test_concurrent_writes -v
# Expected: PASSED ✓
```

### 5. Run Full Suite
```powershell
pytest --cov=runtime
# Expected: All tests pass ✓
```

### 6. Create PR
- Title: "Fix: [Bug title]"
- Description: Scenario, root cause, fix, test
- Reference the commit that introduced the bug

## Safety Checklist

Before opening a PR:

- [ ] Concrete scenario that reproduces the bug
- [ ] Observable, harmful breakage (crash, data loss, wrong behavior)
- [ ] Minimal, surgical fix (no unrelated refactoring)
- [ ] Test passes after fix
- [ ] All existing tests still pass
- [ ] Full code path traced and understood
- [ ] Confidence level >= 85%

## Example Session

### Commit: abc123 "Add cache expiry"

**File**: `runtime/cache.py`

**Initial Assessment**: Background expiry might race with concurrent access.

**Caller Analysis**:
- Called from request handlers (concurrent)
- Request handling is async (concurrent by design)

**Risk Scenario**:
```
1. Thread A: set_cache("x", "val_a")
2. Thread B: set_cache("x", "val_b") — races with A
3. Expiry runs in background (async, no lock)
4. One write is lost; cache has wrong value
```

**Test**:
```python
def test_concurrent_writes_with_expiry():
    cache.clear()
    threads = [
        Thread(target=set_cache_with_expiry, args=(f"k{i}", f"v{i}", 60))
        for i in range(100)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # All 100 writes should be in cache
    assert len(cache) == 100
```

**Confidence**: HIGH (>85%)
- Can construct clear trigger scenario
- Race condition is reproducible
- Causes observable data loss

**Fix**:
```python
import threading

_cache_lock = threading.Lock()
cache = {}

def set_cache_with_expiry(key, value, ttl):
    with _cache_lock:
        cache[key] = value
    schedule_expiry(key, ttl)
```

**Action**: Create PR with test and fix ✓

---

## When NOT to Report

- **Theoretical edge cases** without concrete trigger: Skip
- **Style/warning issues**: Not this tool's scope
- **Minor UX degradation**: Too low severity
- **Code that "looks wrong" but works**: Don't guess; only report observable bugs

## When to Report Without Fixing

If you're 70-85% confident:

```
Slack message to team:
"Found potential race condition in cache.py (commit abc123):
- Two threads writing same key → one write lost
- Confidence: ~80% (edge-casey concurrent access)
- Recommendation: Add lock or review with original author
```

## Expected Outcomes

### Most Days (Healthy)
"No critical bugs found in 15 commits. Reviewed concurrency, auth, data handling. No issues detected."

This is a WIN.

### Occasionally
One or two HIGH confidence bugs that need fixing.

### Rarely
Multiple critical bugs, indicating code quality concerns.

## Commands Quick Ref

```powershell
# List commits
git log --since="7 days ago" --oneline

# View diff
git show <hash>

# Find callers
grep -r "name" . --include="*.py"

# Run tests
pytest --cov=runtime

# Run one test
pytest tests/test_file.py::test_name -v
```

## Read Next

- **Quick Reference**: `QUICK_REFERENCE.md` (1 page, all key patterns)
- **Implementation Guide**: `IMPLEMENTATION.md` (step-by-step workflow)
- **Investigation Template**: `INVESTIGATION_TEMPLATE.md` (per-commit checklist)
- **Full Specification**: `SKILL.md` (complete reference with examples)

---

**Goal**: Find real bugs that would cause data loss, crashes, or security issues. Fix them with minimal, high-confidence changes. Most days, you'll find no bugs—and that's the expected, healthy outcome.
