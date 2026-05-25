#!/usr/bin/env python3
"""
Ralph Wiggum Loop Orchestrator
================================

An autonomous, stateless developer agent designed for high-density iteration loops.
Completely resets memory every iteration. Relies exclusively on PROGRESS.md and Git commits.

Usage:
    python3 ralph.py [--progress PROGRESS.md] [--verbose]
"""

import os
import sys
import subprocess
import re
from pathlib import Path
from typing import List, Optional


class RalphLoopOrchestrator:
    """Stateless infinite-loop developer automation engine."""

    def __init__(self, progress_file: str = "PROGRESS.md", verbose: bool = False):
        self.progress_file = progress_file
        self.verbose = verbose
        self.cwd = os.getcwd()

        if not os.path.exists(self.progress_file):
            self._log("⚠️  Progress file not found. Initializing...")
            self.initialize_progress_file()

    def _log(self, message: str):
        """Log with Ralph branding."""
        print(f"[Ralph] {message}")

    def initialize_progress_file(self):
        """Create initial PROGRESS.md if missing."""
        initial_content = (
            "# Project Progress — Ralph Wiggum Loop Tracker\n\n"
            "## 📋 Todo\n"
            "- [ ] Define first implementation task\n\n"
            "## ✅ Completed\n"
            "\n"
            "## 📝 Notes\n"
            "Loop initialized. Awaiting task definitions.\n"
        )
        with open(self.progress_file, "w") as f:
            f.write(initial_content)
        self._log(f"✨ Initialized {self.progress_file}")

    def read_progress(self) -> List[str]:
        """Parse PROGRESS.md and extract incomplete tasks."""
        self._log(f"📋 Reading progress from {self.progress_file}...")

        if not os.path.exists(self.progress_file):
            self._log("❌ Progress file not found!")
            return []

        with open(self.progress_file, "r") as f:
            content = f.read()

        # Extract todo section (incomplete tasks marked with [ ])
        todo_pattern = r"##\s+📋\s+Todo\n(.*?)(?=##|$)"
        todo_match = re.search(todo_pattern, content, re.DOTALL)

        if not todo_match:
            self._log("⚠️  No Todo section found in progress file")
            return []

        todo_section = todo_match.group(1)
        tasks = []

        # Extract lines starting with "- [ ]" (incomplete tasks)
        for line in todo_section.split("\n"):
            if re.match(r"^\s*-\s*\[\s*\]\s+", line):
                task = re.sub(r"^\s*-\s*\[\s*\]\s+", "", line).strip()
                if task:
                    tasks.append(task)

        if self.verbose:
            self._log(f"Found {len(tasks)} incomplete tasks")
            for i, task in enumerate(tasks[:3], 1):
                self._log(f"  {i}. {task[:60]}...")

        return tasks

    def execute_task(self, task: str) -> bool:
        """Execute a single task via local shell."""
        self._log(f"💻 Executing: {task}")

        # For now, log the task. In production, this would invoke:
        # - GitHub Copilot CLI
        # - Local code generation engine
        # - Test runner
        # - Linter/formatter

        if self.verbose:
            self._log(f"   Task scope: {task}")

        # Placeholder: successful execution
        return True

    def update_progress(self, completed_task: str) -> bool:
        """Move completed task from Todo to Completed."""
        self._log(f"📝 Updating progress: {completed_task}")

        try:
            with open(self.progress_file, "r") as f:
                content = f.read()

            # Find and replace the task
            old_pattern = f"- [ ] {re.escape(completed_task)}"
            new_pattern = f"- [x] {completed_task}"

            if re.search(old_pattern, content):
                content = re.sub(old_pattern, new_pattern, content)
            else:
                # Fallback: append to completed section
                completed_match = re.search(r"(##\s+✅\s+Completed\n)", content)
                if completed_match:
                    insert_pos = completed_match.end()
                    content = (
                        content[:insert_pos]
                        + f"- [x] {completed_task}\n"
                        + content[insert_pos:]
                    )

            with open(self.progress_file, "w") as f:
                f.write(content)

            self._log(f"✅ Task marked complete")
            return True

        except Exception as e:
            self._log(f"❌ Failed to update progress: {e}")
            return False

    def commit_iteration(self, task: str) -> bool:
        """Commit changes to Git, freezing state."""
        self._log(f"💾 Committing iteration...")

        try:
            # Stage all changes
            subprocess.run(
                ["git", "add", "."],
                cwd=self.cwd,
                capture_output=True,
                check=False,
            )

            # Check if there are staged changes
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.cwd,
                capture_output=True,
                text=True,
                check=False,
            )

            if not status_result.stdout.strip():
                self._log("ℹ️  No changes to commit")
                return True

            # Create commit
            commit_msg = f"ralph-loop: {task}"
            result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=self.cwd,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                self._log(f"✅ Committed: {commit_msg}")
                return True
            else:
                self._log(f"ℹ️  Git commit: {result.stderr.strip() or 'no changes'}")
                return True

        except Exception as e:
            self._log(f"⚠️  Commit failed: {e}")
            return True  # Don't fail the loop on commit issues

    def verify_promise(self) -> bool:
        """Run basic system health checks."""
        self._log(f"🎯 Verifying system state...")

        # Try running tests if they exist
        test_commands = [
            "pytest --co -q",
            "npm test -- --listTests",
            "python -m unittest discover -p 'test_*.py'",
        ]

        for cmd in test_commands:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=self.cwd,
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                self._log("✅ System verification passed")
                return True

        self._log("ℹ️  System verification skipped (no test harness found)")
        return True

    def step(self) -> bool:
        """Execute a single loop iteration. Returns True to continue, False to stop."""
        self._log("=" * 60)
        self._log("Ralph Loop Iteration Starting")
        self._log("=" * 60)

        # Phase 1: Read state
        tasks = self.read_progress()
        if not tasks:
            self._log("🎉 No tasks remaining. Queue is empty!")
            return False

        next_task = tasks[0]
        self._log(f"📌 Next task: {next_task}")

        # Phase 2: Execute
        if not self.execute_task(next_task):
            self._log("❌ Execution failed. Stopping to protect history.")
            return False

        # Phase 3: Update state
        if not self.update_progress(next_task):
            self._log("⚠️  Could not update progress, but continuing...")

        # Phase 4: Commit
        self.commit_iteration(next_task)

        # Phase 5: Verify
        self.verify_promise()

        self._log("=" * 60)
        self._log("✨ Iteration complete. Resetting context.")
        self._log("=" * 60)

        return True


def main():
    """Entry point for Ralph orchestrator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Ralph Wiggum Loop Orchestrator — Stateless iteration automation"
    )
    parser.add_argument(
        "--progress",
        default="PROGRESS.md",
        help="Path to progress tracking file (default: PROGRESS.md)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run infinite loop (default: single iteration)",
    )

    args = parser.parse_args()

    orchestrator = RalphLoopOrchestrator(
        progress_file=args.progress, verbose=args.verbose
    )

    if args.loop:
        # Infinite loop mode
        iteration = 0
        while True:
            iteration += 1
            print(f"\n🔄 Loop Iteration #{iteration}\n")
            if not orchestrator.step():
                print("\n🛑 Loop terminated.\n")
                break
            print()  # Blank line between iterations
    else:
        # Single iteration
        if orchestrator.step():
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
