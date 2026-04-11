# Agent Shell Service Runtime

This package keeps the file-backed runtime kernel and adds an inbound FastAPI app surface.

## Topology

- **Runtime shell model**
  - local CLI entrypoint
  - file queue
  - worker loop
  - tools and model calls
  - state, memory, receipts

- **Runtime deployment topology model**
  - gateway / auth boundary
  - FastAPI app surface
  - service interface layer
  - runtime kernel
  - queue / workers
  - tools / models
  - state stores
  - observability / audit

## Local PowerShell usage

```powershell
Set-Location "C:\Users\eqhsp\Agent Projects\agent-shell-service"
py -m venv .venv
. .\.venv\Scripts\Activate.ps1
py -m pip install -e .
agent-shell doctor
agent-shell serve-api --host 127.0.0.1 --port 8000
```

## Direct uvicorn usage

```powershell
uvicorn runtime.api:create_app --factory --host 127.0.0.1 --port 8000
```

## Useful endpoints

- `GET http://127.0.0.1:8000/health`
- `POST http://127.0.0.1:8000/tasks`
- `GET http://127.0.0.1:8000/tasks`
- `POST http://127.0.0.1:8000/run`
- `GET http://127.0.0.1:8000/heartbeat`
