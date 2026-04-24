# Build Report

## Package

- Name: `agent-shell-service-runtime`
- Version: `0.5.0`

## Patch summary

Added an inbound FastAPI service layer on top of the existing runtime shell.

## Architecture diff (verified)

- **Current shell/runtime kernel (preserved):** `AgentService` continues to own queue, hooks, tools, memory, receipts, and loop execution.
- **New service boundary:** `runtime/api.py` now fronts the kernel with inbound endpoints and service-boundary auth.
- **Deployed-topology alignment:** callers now integrate through HTTP (gateway/operator/client -> FastAPI -> `AgentService`) instead of only local CLI invocation.
- **Queue topology unchanged:** filesystem inbox/working/done/failed flow remains file-backed (`runtime/queue_fs.py`).
- **Auth split retained:** provider API keys stay server-side (`OPENAI_API_KEY`, `MISTRAL_API_KEY`), while service-boundary caller auth is handled independently.

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
- API middleware header checks
- service-boundary auth mode tests (`static_bearer`, `trusted_proxy_oidc`, fail-closed `oidc_jwt` misconfiguration)
- direct task enqueue/list/get
- direct `/run` path
- heartbeat read/write

## Result

The inbound service starts through the application factory and exercises the same runtime kernel used by the CLI.
