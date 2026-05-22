#!/usr/bin/env bash
# Trigger the issue_to_fix_workflow subagent

set -euo pipefail

# Get the root directory of the agent-shell
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Check if arguments are provided
if [ $# -lt 2 ]; then
  echo "Usage: $0 <title> <description> [backend]"
  echo "Example: $0 'Fix bug in login' 'The login button is unresponsive' openai"
  exit 1
fi

TITLE="$1"
DESCRIPTION="$2"
BACKEND="${3:-mock}"

# Activate venv if it exists
if [ -d ".venv" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

# Run the task using the agent-shell CLI
# We use the subagent 'issue_to_fix_workflow' which maps to subagents/issue_to_fix_workflow.md
TASK="Create an issue titled '$TITLE' and have a PR generated to fix it. The issue description is: $DESCRIPTION"

echo "🚀 Triggering issue-to-fix workflow..."
echo "📝 Title: $TITLE"
echo "🤖 Backend: $BACKEND"
echo ""

agent-shell run-task --task "$TASK" --subagent "issue_to_fix_workflow" --backend "$BACKEND"
