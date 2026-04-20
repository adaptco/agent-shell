# Gemini Project Mandates

This file contains foundational mandates for Gemini CLI when working in this repository. These instructions take absolute precedence over general defaults.

## Environment & Runtime
- **Python Version**: Minimum 3.13.0.
- **Virtual Environment**: Use the local `.venv` directory.
- **Package Management**: Managed via `pyproject.toml` using `setuptools`.
- **Installation**: Use `pip install -e .[test]` to set up the development environment.

## Testing Standards
- **Framework**: `pytest` is the primary testing framework.
- **Coverage**: Use `pytest-cov` for coverage reporting.
- **Command**: Run tests using `.venv\Scripts\pytest --cov=runtime`.
- **Validation**: All PRs and changes must pass the existing test suite before completion.

## Architecture
- **Package Structure**: The core logic resides in the `runtime/` package.
- **Entry Points**:
  - `agent-shell` -> `runtime.cli:main`
  - `agent-shell-api` -> `runtime.server:main`
