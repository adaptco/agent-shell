# Build Report

## Package

- Name: `agent-shell-service-runtime`
- Version: `0.5.0`

## Patch summary

Added an inbound FastAPI service layer on top of the existing runtime shell.

### New/updated components

- `runtime/api.py`
- `runtime/api_auth.py`
- `runtime/server.py`
- `runtime/service.py`
- `runtime/queue_fs.py`
- `runtime/cli.py`
- `infra/runtime.json`
- `AUTH.md`
- `ENDPOINTS.md`

## Validation performed in container

- CLI doctor
- smoke tests
- API tests using FastAPI `TestClient`
- direct task enqueue/list/get
- direct `/run` path
- heartbeat read/write

## Result

The inbound service starts through the application factory and exercises the same runtime kernel used by the CLI.
