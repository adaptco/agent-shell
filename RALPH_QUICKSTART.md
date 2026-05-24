# Ralph Wiggum Loop Orchestrator — Quick Start Guide

## 🎯 What is Ralph?

Ralph is a **stateless, deterministic loop orchestrator** for autonomous multi-step development tasks. Instead of maintaining massive chat histories, Ralph:

- Reads task state from `PROGRESS.md`
- Executes **one granular task** per iteration
- Commits changes to Git (creating permanent memory)
- Completely resets process memory before the next iteration
- Repeats until all tasks are done

**Key Benefit:** No accumulated context bloat. Fresh LLM window every iteration. Perfect Git history for debugging.

---

## 🚀 Getting Started

### Step 1: Create Your Task List

Create or edit `PROGRESS.md` in your project root:

```markdown
# Project Progress — Ralph Wiggum Loop Tracker

## 📋 Todo
- [ ] Implement user authentication module
- [ ] Add database connection pooling
- [ ] Write integration tests for API
- [ ] Deploy to staging environment

## ✅ Completed

## 📝 Notes
Started Ralph loop orchestration. Initial task queue defined.
```

### Step 2: Run Ralph (Single Iteration)

```bash
# Linux / macOS
python3 ralph.py

# Windows PowerShell
python.exe .\ralph.py
```

Ralph will:
1. Read the first incomplete task from `PROGRESS.md`
2. Execute it (hook into your LLM or tool)
3. Mark it complete
4. Commit changes to Git
5. Exit with status 0 (continue) or 1 (stop)

### Step 3: Run Ralph (Infinite Loop)

#### Linux / macOS

```bash
chmod +x ralph.sh
./ralph.sh
```

#### Windows PowerShell

```powershell
.\ralph.ps1
```

Ralph will repeatedly:
- Execute a single task
- Mark it complete
- Commit to Git
- **Completely reset process memory**
- Start fresh for the next iteration

---

## 📋 Command Options

### ralph.py

```bash
python3 ralph.py [--progress PROGRESS.md] [--verbose] [--loop]

Options:
  --progress FILE    Path to progress tracking file (default: PROGRESS.md)
  --verbose, -v      Show detailed task information
  --loop             Run infinite loop instead of single iteration
```

### ralph.ps1 (Windows)

```powershell
.\ralph.ps1 -ProgressFile "PROGRESS.md" -Verbose
```

---

## 🔄 The Ralph Loop: State Transition

```
Iteration N
├─ Phase 1: read_progress()
│  └─ Parse PROGRESS.md, find first incomplete task
├─ Phase 2: execute_task(task)
│  └─ Invoke LLM, run command, or execute code generation
├─ Phase 3: update_progress(completed_task)
│  └─ Move task from [ ] to [x], update PROGRESS.md on disk
├─ Phase 4: commit_iteration(task)
│  └─ git add . && git commit -m "ralph-loop: {task}"
├─ Phase 5: verify_promise()
│  └─ Run tests, linters, health checks
└─ Process exits, memory completely dumped
  
Iteration N+1
└─ Fresh process boots, repeats from Phase 1
```

---

## 💾 Git History Example

After running Ralph through 3 tasks, your git log shows perfect atomicity:

```
$ git log --oneline --grep ralph-loop
a1b2c3d ralph-loop: Implement user authentication module
f4e5d6c ralph-loop: Add database connection pooling
7g8h9i0 ralph-loop: Write integration tests for API
```

Each commit is a single completed task. Perfect for:
- Tracing exactly when features were added
- Reverting specific tasks
- Bisecting for bug introductions
- Code review per logical unit

---

## 🛠️ Customization

### Hook Ralph into Your LLM

Edit `ralph.py` in the `execute_task()` method:

```python
def execute_task(self, task: str) -> bool:
    """Execute via GitHub Copilot CLI, local model, or custom tool."""
    
    # Example: Invoke Copilot CLI
    result = subprocess.run(
        ["gh", "copilot", "suggest", "-t", "shell", task],
        capture_output=True,
        text=True
    )
    
    return result.returncode == 0
```

### Add Custom Verification

Edit the `verify_promise()` method:

```python
def verify_promise(self) -> bool:
    """Run your project's health checks."""
    
    checks = [
        ("pytest", ["pytest", "--cov"]),
        ("ruff", ["ruff", "check", "."]),
        ("mypy", ["mypy", "src/"]),
    ]
    
    for name, cmd in checks:
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            self._log(f"❌ {name} failed")
            return False
    
    return True
```

### Change Progress File Location

```bash
python3 ralph.py --progress ./docs/IMPLEMENTATION_PLAN.md
```

---

## 📊 Monitoring Ralph Execution

### View Current State

```bash
cat PROGRESS.md
```

### View Execution History

```bash
# All Ralph commits
git log --grep ralph-loop

# Last 5 iterations
git log --oneline -n 5

# Show changes in last iteration
git show HEAD
```

### Check Loop Status

```bash
# On Linux/macOS, watch the live output
tail -f PROGRESS.md

# Or check git in another terminal
watch -n 1 'git log --oneline -n 5'
```

---

## 🚨 Troubleshooting

### Ralph Loop Exits Unexpectedly

**Check:**
1. Is `PROGRESS.md` properly formatted?
2. Run single iteration with verbose: `python3 ralph.py --verbose`
3. Check Git status: `git status`

### Task Stays Incomplete

**Cause:** The task text in PROGRESS.md changed.

**Fix:** Ensure task description matches exactly:
```markdown
# In PROGRESS.md
- [ ] Exact task description

# Ralph looks for exact match to mark complete
```

### Git Commits Failing

**Check:**
```bash
git config user.email
git config user.name
```

**Set if missing:**
```bash
git config user.email "ralph@agent-shell.local"
git config user.name "Ralph Wiggum Loop"
```

### Python Not Found

**Windows:** Ensure Python is in PATH:
```powershell
python --version
# If not found, add Python to PATH or use full path:
C:\Python311\python.exe .\ralph.py
```

---

## 🎯 Best Practices

✅ **Do:**
- Keep task descriptions concise and atomic
- One logical feature per task
- Run `git log` between iterations to verify commits
- Use `--verbose` flag when debugging

❌ **Don't:**
- Make 50 tasks at once (start with 3-5)
- Forget to commit working state before running Ralph
- Leave Ralph running unattended on production code
- Modify `PROGRESS.md` while Ralph is executing

---

## 📖 Advanced Usage

### Conditional Task Execution

Modify `ralph.py` to skip tasks based on conditions:

```python
def execute_task(self, task: str) -> bool:
    if "requires-approval" in task:
        self._log("⏸️  Skipping approval-required task")
        return True  # Skip but mark complete
    
    # Normal execution
    return True
```

### Multi-File Tracking

Use separate progress files for different domains:

```bash
python3 ralph.py --progress BACKEND_PROGRESS.md &
python3 ralph.py --progress FRONTEND_PROGRESS.md &
```

### Integration with CI/CD

Trigger Ralph from GitHub Actions:

```yaml
- name: Run Ralph Loop
  run: |
    python3 ralph.py --loop
    git push origin main
```

---

## 📞 Support

For issues or custom adaptations, check:
- `ralph.py --help`
- Git commit messages for execution history
- Console output with `--verbose` flag

Happy autonomous development! 🎉

---

**Ralph Wiggum Loop Orchestrator v1.0**
*Deterministic, stateless, memory-efficient task automation.*
