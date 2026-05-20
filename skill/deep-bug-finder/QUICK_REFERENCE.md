# Deep Bug Finder - Quick Reference Card

## One-Page Checklist

### Pre-Flight
- [ ] `.venv` activated
- [ ] `pip install -e .[test]` run
- [ ] `pytest --collect-only` passes
- [ ] `git fetch origin main` done

### Investigation (Per Commit)
- [ ] Read commit message and diff
- [ ] Identify risk level: Data? Concurrency? Auth? Resource?
- [ ] Find all code that calls this
- [ ] Trace all error paths
- [ ] Simulate 3+ failure scenarios mentally
- [ ] Ask: "What could go wrong if..."?

### High-Risk Patterns to Hunt

#### Data Corruption
```
Look for: Shared state + no locks, multi-step ops without transactions,
          cache/DB out of sync, lost writes
Question: Can two threads corrupt this state?
```

#### Race Conditions
```
Look for: Check-then-act, async without await, shared collections mutated
Question: What if two requests hit this at the same time?
```

#### Null Dereference
```
Look for: No null check before .field access, optional fields
Question: What if this value is None/undefined?
```

#### Auth Bypass
```
Look for: Permission check separate from action, state change if check passes
Question: Can an unauthorized user exploit this?
```

#### Resource Leak
```
Look for: File/connection opened without try-finally, no context manager
Question: Can this resource fail to close if exception occurs?
```

### Fix Checklist
- [ ] Bug has concrete trigger scenario
- [ ] Fix is minimal (no unrelated refactors)
- [ ] New test reproduces the original bug
- [ ] Test passes after fix
- [ ] All existing tests still pass
- [ ] Confidence level: >= 85%

### Output Options
1. **Bug + Fix**: Create PR with test
2. **Bug, No Fix**: Post to Slack, add to backlog
3. **No Bugs**: Document coverage, report summary

---

## Commands at Hand

### Git
```powershell
# Recent commits
git log --since="7 days ago" --oneline

# Changed files
git log --since="7 days ago" --name-only --pretty=format: | sort -u

# Full diff
git show <hash>

# Who changed this line
git blame <file>
```

### Testing
```powershell
# All tests
pytest --cov=runtime

# One test
pytest tests/path/test_file.py::test_name -v

# With prints
pytest -s tests/test_file.py
```

### Search
```powershell
# Find callers
grep -r "func_name" . --include="*.py" | grep -v test

# Find pattern
grep -r "pattern" . --include="*.py"
```

---

## Red Flag Signals (High Confidence Bugs)

| Pattern | Risk | Trigger |
|---------|------|---------|
| No lock around shared dict/list | HIGH | Concurrent threads writing |
| Check-then-act without atomicity | HIGH | Race between check and action |
| No null check before deref | HIGH | Call with None/missing value |
| Async without await | HIGH | Execution continues before completion |
| No try-finally for cleanup | MEDIUM | Exception before cleanup |
| Cache + DB mismatch | HIGH | Updates to one but not the other |
| Silent exception swallow | MEDIUM | Error lost, wrong behavior continues |

---

## Decision Tree

```
Found unusual code change?
├─ Can I construct a concrete failure scenario?
│  ├─ YES → Is it observable/harmful breakage?
│  │  ├─ YES → High confidence? (>85%)
│  │  │  ├─ YES → Fix + Test → PR ✓
│  │  │  └─ NO → Slack, backlog
│  │  └─ NO → Edge case, skip
│  └─ NO → Theoretical, skip
└─ No, looks safe
   └─ Document coverage, move on
```

---

## Example Findings

### 🔴 Critical: Lost Writes (Data Loss)
```python
# BAD
cache[key] = value  # No lock, concurrent access

# FIX
with lock:
    cache[key] = value

# TEST
def test_concurrent_writes():
    threads = [Thread(target=set_cache, args=(key, val)) for ...]
    assert all_values_in_cache()
```

### 🔴 Critical: Null Dereference (Crash)
```python
# BAD
user = find_user(id)
return user.email  # Crash if None

# FIX
user = find_user(id)
if not user:
    return None
return user.email

# TEST
def test_missing_user_returns_none():
    assert find_email(invalid_id) is None
```

### 🔴 Critical: Auth Bypass (Security)
```python
# BAD
def delete(item_id):
    item = db.get(item_id)
    db.delete(item)  # No permission check!

# FIX
def delete(item_id, user):
    item = db.get(item_id)
    if not user.can_delete(item):
        raise Forbidden()
    db.delete(item)

# TEST
def test_unauthorized_user_cannot_delete():
    with pytest.raises(Forbidden):
        delete(item_id, unauthorized_user)
```

### 🟡 Medium: Potential Data Race
```python
# SUSPECT
items = []
async def process():
    for item in items:  # Concurrent modification?
        await handle(item)

# RECOMMEND: Use lock or copy
with lock:
    items_copy = items.copy()
for item in items_copy:
    await handle(item)
```

---

## Success Criteria

### ✅ Bug Fixed
- PR merged with test locked in
- Bug cannot regress undetected

### ✅ Bug Reported (No Fix)
- Slack message with scenario + confidence
- Added to backlog or assigned

### ✅ No Bugs Found
- Documented N commits reviewed
- Listed areas covered
- Note any edge cases to monitor
- This is a WIN—most days have no critical bugs

---

## Remember
- **High bar**: Need >85% confidence AND concrete trigger scenario
- **Test everything**: Tests are your safety net
- **Minimal fixes**: Don't refactor while fixing bugs
- **Most days**: "No critical bugs found" is the expected and healthy outcome
