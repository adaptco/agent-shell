#!/usr/bin/env bash
#
# Ralph Wiggum Stateless Loop Orchestrator (Linux / macOS)
#
# Usage:
#   chmod +x ralph.sh
#   ./ralph.sh
#
# This wrapper runs Ralph in a completely fresh process every iteration,
# eliminating accumulated context memory and ensuring deterministic behavior.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROGRESS_FILE="${SCRIPT_DIR}/PROGRESS.md"

# Colors for terminal output
BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'  # No Color

echo -e "${BOLD}${GREEN}🚀 Ralph Wiggum Stateless Loop Orchestrator${NC}"
echo -e "${CYAN}Booting infinite iteration cycle...${NC}"
echo ""

ITERATION=0
while true; do
    ITERATION=$((ITERATION + 1))
    echo -e "${BOLD}${CYAN}🔄 Iteration #${ITERATION}${NC}"
    echo ""

    # Run Ralph in a completely isolated process
    # The Python interpreter exits entirely, shedding all context memory
    if python3 "${SCRIPT_DIR}/ralph.py" --progress "${PROGRESS_FILE}" --verbose; then
        STATUS=0
    else
        STATUS=$?
    fi

    echo ""

    # Check exit status
    if [ $STATUS -ne 0 ]; then
        echo -e "${BOLD}${YELLOW}🛑 Loop interrupted or task queue completed.${NC}"
        echo -e "${CYAN}Final state persisted in Git. Ralph is clocking out.${NC}"
        break
    fi

    # Clean context reset between iterations
    echo -e "${CYAN}♻️  Iteration clean. Dumping process memory cache...${NC}"
    sleep 1
    echo ""
done

echo ""
echo -e "${BOLD}${GREEN}✨ Ralph Loop Orchestrator Finished${NC}"
echo -e "${CYAN}Check Git log for full execution history:${NC}"
echo -e "  ${YELLOW}git log --oneline --grep 'ralph-loop'${NC}"
echo ""
