---
name: runtime-artifact-worker-upgrade
description: >-
  Guides the agent through upgrading the runtime with artifact-capable workers
  and creating a reusable `SKILL.md` for the bootstrap workflow that installs
  runtime dependencies, configures XLSX/DOCX workers, and validates the repo.
---

# Runtime Artifact Worker Upgrade

## Overview

This skill captures the workflow for upgrading the `agent-shell` runtime to
support artifact processing by installing runtime dependencies, creating XLSX
and DOCX worker plugins, and validating the workspace with lint and tests.

It is designed to map a bootstrap script into a structured `SKILL.md` that can
be reused by agents and contributors.

## Prerequisites

- Git repository cloned at the target path
- Python 3.13 available as `python3.13` or equivalent
- A virtual environment is created and activated under `.venv`
- Package dependencies installed with `pip install -e .[test]`

## Workflow

### 1. Sync repository

- Confirm the target directory contains a `.git` repository.
- Fetch latest updates from `origin`.
- Checkout the target branch.
- Rebase against the remote branch.

### 2. Create and activate the virtual environment

- If `.venv` does not exist, create it with Python 3.13.
- Activate the environment.
- Upgrade `pip`, `setuptools`, and `wheel`.

### 3. Install runtime and worker dependencies

- Install the package in editable mode with test dependencies.
- Install additional artifact manipulation libraries:
  - `openpyxl`
  - `python-docx`
  - `pandas`
  - `pillow`
  - `lxml`

### 4. Prepare workflow directories

Create the following workspace directories if they do not already exist:
- `workspace`
- `workspace/artifacts`
- `workspace/receipts`
- `workspace/state`
- `workspace/queue`
- `runtime/plugins`
- `runtime/workers`
- `runtime/artifacts`

### 5. Create the capability manifest

Write `runtime/artifacts/capabilities.json` with worker definitions for:
- `xlsx_worker`
- `docx_worker`

Include boolean enablement flags for `XLSX_TOOL_ENABLED` and `DOCX_TOOL_ENABLED`.

### 6. Install XLSX and DOCX workers

Create the following worker modules:
- `runtime/workers/xlsx_worker.py`
- `runtime/workers/docx_worker.py`

Each worker should expose a `process(artifact_path, operations)` method and
support operations such as:
- `update_cell`, `append_row`, `create_sheet` for XLSX
- `append_paragraph`, `replace_text`, `add_heading` for DOCX

### 7. Install the artifact dispatcher

Create `runtime/plugins/artifact_dispatcher.py` with a class that:
- imports both workers
- dispatches on `artifact_type`
- raises a clear error for unsupported artifact types

### 8. Create an example workflow job

Add `examples/workflow_artifact_job.json` describing:
- a workflow ID
- an XLSX artifact update step
- a DOCX artifact mutation step

### 9. Validate the upgrade

Run linting and tests to confirm the workspace is healthy.
- `ruff check .`
- `pytest -q`

If either step fails, fix the reported issues before finishing the upgrade.

## Decision Points

- If the repository path is missing or not a Git repo, abort immediately.
- If `.venv` already exists, reuse it but still upgrade pip/setuptools.
- Use environment flags to enable or disable XLSX and DOCX workers.
- If artifact type is unsupported in the dispatcher, the code should fail fast,
  not silently ignore the request.

## Validation Criteria

A successful upgrade meets these conditions:
- Repository is on the correct branch and rebased cleanly.
- `.venv` exists and dependencies install successfully.
- `runtime/artifacts/capabilities.json` exists with both workers.
- Worker files and dispatcher file are present and syntactically valid.
- `ruff check .` passes without critical issues.
- `pytest -q` passes all tests.

## Example Commands

```bash
git fetch origin
git checkout main
git pull --rebase origin main
python3.13 -m venv .venv
.venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -e ".[test]"
pip install openpyxl python-docx pandas pillow lxml
ruff check .
pytest -q
```

## Common Mistakes

- Forgetting to install the extra artifact libraries (`openpyxl`, `python-docx`).
- Writing worker modules with incorrect method signatures.
- Using the wrong JSON boolean values in `capabilities.json`.
- Skipping validation steps after creating artifact worker files.
- Not using a virtual environment, which can lead to inconsistent dependency versions.
