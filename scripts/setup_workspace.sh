#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
NODE_BIN="${NODE_BIN:-node}"
REQUIRED_NODE_MAJOR="24"

if ! command -v "$NODE_BIN" >/dev/null 2>&1; then
  echo "error: required node executable '$NODE_BIN' was not found" >&2
  exit 1
fi

NODE_VERSION_RAW="$($NODE_BIN -v)"
NODE_MAJOR="${NODE_VERSION_RAW#v}"
NODE_MAJOR="${NODE_MAJOR%%.*}"
if [ "$NODE_MAJOR" != "$REQUIRED_NODE_MAJOR" ]; then
  echo "error: Node.js v${REQUIRED_NODE_MAJOR} is required, found ${NODE_VERSION_RAW}" >&2
  exit 1
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "error: required python executable '$PYTHON_BIN' was not found" >&2
  exit 1
fi

cd "$ROOT_DIR"

if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install -e .[test]

echo "Workspace is ready."
echo "Run: source .venv/bin/activate && agent-shell doctor"
echo "Node.js version: ${NODE_VERSION_RAW}"
