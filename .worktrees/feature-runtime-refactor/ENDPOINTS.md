# Inbound Service Endpoints

## Purpose

This build adds an inbound FastAPI service in front of the existing runtime kernel.
The shell runtime remains the execution engine. The service is the network-facing app surface.

## Inbound endpoints

- `GET /health`
  - Returns doctor checks, runtime state, queue counts, package name/version.
- `GET /tasks?limit=100`
  - Returns queue counts and recent task records across inbox, working, done, failed.
- `POST /tasks`
  - Enqueues a task.
  - Body: `{ "task": "...", "parent_task_id": null, "assigned_subagent": null }`
- `GET /tasks/{task_id}`
  - Returns one task record if it exists.
- `POST /run`
  - Runs one task immediately through the runtime loop.
  - Body: `{ "task": "...", "backend": "mock|openai|mistral" }`
- `GET /heartbeat`
  - Returns the current runtime heartbeat state from `state/runtime.json`.
- `POST /heartbeat`
  - Emits a new heartbeat update.
  - Body: `{ "worker_id": "optional" }`

## Boundary middleware contract

Every inbound request receives response headers emitted by the FastAPI boundary middleware:

- `X-Agent-Service`: service identifier
- `X-Correlation-Id`: request correlation ID (forwarded from inbound header when provided)
- `X-Process-Time-Ms`: request duration at the boundary

## Outbound provider endpoints

The inbound service does not proxy provider credentials from the client.
It calls providers from the server process using environment variables.

- OpenAI Responses: `POST https://api.openai.com/v1/responses`
- Mistral Chat Completions: `POST https://api.mistral.ai/v1/chat/completions`
- Mock/default web search provider: `https://api.duckduckgo.com/`

## Mapping summary

- inbound REST -> `runtime/api.py`
- service facade -> `runtime/service.py`
- queue -> `runtime/queue_fs.py`
- runtime loop -> `runtime/agent_loop.py`
- provider backends -> `runtime/llm.py`
- tools -> `runtime/tools.py`
- auth boundary -> `runtime/api_auth.py`
- HTTP middleware (request ID, timing, logging, auth context) -> `runtime/middleware.py`

## Runtime topology diff (shell -> service-backed)

- previous local model: operator invoked `runtime/cli.py` commands directly on the same host as the runtime kernel.
- deployed-aligned model: operator or gateway calls FastAPI endpoints in `runtime/api.py`; API forwards to the same `AgentService` kernel in `runtime/service.py`.
- preserved internals: queue (`runtime/queue_fs.py`), hooks, tools, memory, receipts, and loop execution contracts are unchanged; only the entry boundary moved from CLI-only to CLI + HTTP.

## PowerShell operator workflow

Start local service:

```powershell
python -m runtime.cli serve-api --host 127.0.0.1 --port 8000
```

Check health:

```powershell
Invoke-RestMethod -Method GET -Uri http://127.0.0.1:8000/health
```

Queue a task:

```powershell
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/tasks `
  -ContentType "application/json" `
  -Body (@{ task = "Read agent.md" } | ConvertTo-Json)
```

Run a task immediately:

```powershell
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/run `
  -ContentType "application/json" `
  -Body (@{ task = "Read agent.md"; backend = "mock" } | ConvertTo-Json)
```
