# Phase 1 Bootstrap Kernel Pack

## Status
Frozen and committed as a kernel pack document.

## Checkpoint
- `phase1-bootstrap-complete`

## Scope
Phase 1 establishes the bootstrap kernel boundary:
- schema-first contracts
- typed runtime models
- gate policy
- receipt chain
- daily loop runner
- policy enforcement
- registry-driven routing
- skill configs
- bootstrap tests
- Docker packaging
- Kubernetes CronJob manifest
- CI skeleton
- bootstrap runbook

## Canonical file set

```text
schemas/
  dailyrun.schema.json
  dailybrief.schema.json
  tool_contract.schema.json

configs/
  policy/gates.yaml
  tool_registry.json
  skills/auto_researcher.json
  skills/orchestrator.json

app/
  control/run_daily.py
  control/gates.py
  control/receipts.py
  models/contracts.py
  tools/router.py
  tools/policies.py

tests/
  test_contracts.py
  test_gates.py
  test_receipts.py
  test_run_daily.py

.github/workflows/ci.yml
README.md
deploy/docker/Dockerfile
deploy/k8s/daily-cronjob.yaml
```

## Phase 1 exit criteria
- daily dry-run works end to end
- schema, gate, receipt, and run tests pass
- tool dispatch is registry-driven
- scheduler manifest exists
- CI bootstrap exists
- promotion remains gated and auditable

## Boundary
Phase 1 does **not** hydrate real evaluators or real promotion runtime. Those belong to Phase 2 and Phase 3.
