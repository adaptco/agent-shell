#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
REQUIRED_PY_VERSION="3.13"

if command -v uv >/dev/null 2>&1; then
    echo "Found uv, using it for environment setup..."
    uv python install "$REQUIRED_PY_VERSION"
    uv venv "$VENV_DIR" --python "$REQUIRED_PY_VERSION"
    source "$VENV_DIR/bin/activate"
    uv pip install -e .[test]
else
    PYTHON_BIN="python$REQUIRED_PY_VERSION"
    if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
        echo "error: $PYTHON_BIN is required but not found." >&2
        exit 1
    fi
    if [ ! -d "$VENV_DIR" ]; then
        "$PYTHON_BIN" -m venv "$VENV_DIR"
    fi
    source "$VENV_DIR/bin/activate"
    python -m pip install --upgrade pip
    python -m pip install -e .[test]
fi

echo "Workspace is ready with Python $REQUIRED_PY_VERSION."
