import os
import sys
import time
import json
import subprocess
from runtime.config import load_config
from runtime.llm import get_backend


def run_command(args, check=True):
    return subprocess.run(args, capture_output=True, text=True, check=check)


def fetch_comments(pr_number):
    print(f"Fetching comments for PR #{pr_number}...")
    result = run_command(["gh", "pr", "view", str(pr_number), "--json", "comments"])
    data = json.loads(result.stdout)
    return data.get("comments", [])


def extract_gemini_feedback(comments):
    feedback = []
    for comment in comments:
        if "@gemini-code-assist" in comment["body"]:
            feedback.append(comment["body"])
    return feedback


def apply_refactor(feedback, cfg):
    if not feedback:
        print("No feedback from @gemini-code-assist found.")
        return False

    print(f"Found {len(feedback)} comments. Starting refactor...")

    # Load LLM backend from config
    backend_name = cfg["llm"]["default_backend"]
    _ = get_backend(backend_name, cfg)

    # Build a prompt to refactor the code based on feedback
    # Note: A real implementation would need to identify which files to refactor.
    # For now, we'll focus on the intent and a sample file if provided in feedback.

    # [Placeholder for complex file identification logic]
    # In a real scenario, we'd loop through files mentioned or relevant to the feedback.

    print("Self-heal script: Refactoring logic would call the LLM backend here.")
    # result = backend.decide(...)

    return True


def main():
    pr_number = os.environ.get("PR_NUMBER")
    if not pr_number:
        print("PR_NUMBER not set.")
        sys.exit(1)

    print("Waiting 60 seconds for reviews to populate...")
    time.sleep(60)

    cfg = load_config()
    comments = fetch_comments(pr_number)
    feedback = extract_gemini_feedback(comments)

    if apply_refactor(feedback, cfg):
        # Commit and push changes
        print("Committing and pushing refactored code...")
        run_command(["git", "config", "--global", "user.email", "action@github.com"])
        run_command(["git", "config", "--global", "user.name", "GitHub Action"])
        run_command(["git", "add", "."])
        run_command(["git", "commit", "-m", "chore: self-heal refactor based on @gemini-code-assist feedback"])
        run_command(["git", "push", "origin", os.environ.get("GITHUB_HEAD_REF")])
        print("Refactor complete.")
    else:
        print("No action taken.")


if __name__ == "__main__":
    main()
