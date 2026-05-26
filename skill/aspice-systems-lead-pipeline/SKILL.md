---
name: aspice-systems-lead-pipeline
description: >-
  Explores the codebase, parses ASPICE requirements (docx/xlsx/csv), and run validation checks using ruff, pytest, and deep correctness scanning. Bridges backend changes to the Codebeamer MCP Server and the WebAssembly frontend dashboard.
---

# ASPICE Systems Technical Lead Pipeline

## Overview
This skill provides capabilities for a Systems Technical Lead Agent to parse ASPICE requirement artifacts (in `.docx`, `.xlsx`, or `.csv` formats), extract system metadata, map requirements to target code components, and perform architectural validation before committing Git changes. It integrates the Codebeamer MCP Server for tracking integration and WebSocket gateways to update the browser-based dashboard.

## Dependencies
- `ci-ready-review`: Used to run local style linting (`ruff check`) and verification tests (`pytest`).
- `deep-bug-finder`: Used to scan for correctness issues like race conditions or lost writes in critical system components before commits.

## Quick Start
To start the pipeline WebSocket server on the default port `8765`:
```bash
.venv\Scripts\python scripts/artifact_pipeline.py serve-websocket --port 8765
```

To run the mock Codebeamer MCP Server:
```bash
.venv\Scripts\python scripts/mcp_codebeamer_server.py
```

## Utility Scripts

The `scripts/artifact_pipeline.py` utility supports the following subcommands:

### 1. Parse Requirements
Parses a requirement document or template, extracting requirements, descriptions, and ASPICE references.
```bash
.venv\Scripts\python scripts/artifact_pipeline.py parse --file Database/requirements.xlsx --output Database/parsed_requirements.json
```
- **Inputs**: `--file` (path to artifact)
- **Outputs**: `--output` (path to write output JSON)
- **Fallback**: If parsing fails (e.g., libraries missing or corrupt document), it automatically attempts a fallback zip-based metadata extraction to recover author, creator, dates, and plain text fragments.

### 2. Validate Architecture
Runs the style and tests suite to ensure changes maintain the system architecture.
```bash
.venv\Scripts\python scripts/artifact_pipeline.py validate --repo-path . --output Database/validation_results.json
```
- **Inputs**: `--repo-path` (workspace root path)
- **Outputs**: `--output` (path to write output JSON results)

### 3. Run WebSocket Gateway Server
Exposes a WebSocket connection on a custom port (default: 8765) for WebAssembly and front-end dashboard clients to trigger parse/validate tasks and stream live logs.
```bash
.venv\Scripts\python scripts/artifact_pipeline.py serve-websocket --port 8765
```

## Common Mistakes

1. **Skipping Validation Before Staging**: Always run validation (`validate` command or trigger from dashboard) before staging/committing changes to ensure no linting or test regressions are introduced.
2. **Missing Dependency Packages**: Ensure the virtual environment `.venv` is updated with `pip install -e .` so that parser packages (`python-docx`, `openpyxl`) are accessible.
3. **Not Specifying Output Paths**: CLI parser and validator subcommands require an explicit `--output` target path to write JSON payloads.
