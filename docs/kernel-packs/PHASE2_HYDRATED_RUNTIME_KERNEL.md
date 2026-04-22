# Phase 2 Hydrated Runtime Kernel Pack

## Status
Frozen architecture with integrated implementation lanes.

## Checkpoints
- `P2-A0 contract freeze`
- `P2-D1 coordinator wired`
- `P2-R1 full Phase 2 integration complete`

## Scope
Phase 2 turns the bootstrap kernel into a first-class eval-producing runtime.

## Canonical streams
- **A** = eval-core contracts and harness
- **B** = evaluator implementations
- **C** = budget evaluator
- **D** = coordinator wiring and end-to-end runtime flow

## Frozen evaluator IDs
- `golden_tasks`
- `tool_validity`
- `replay_stability`
- `budget`

## Frozen required metrics
- `golden_task_pass_rate`
- `tool_call_validity_rate`
- `replay_stability_rate`
- `unsupported_claim_rate`
- `policy_violations`
- `safety_violations`
- `cost_delta_pct`
- `latency_delta_pct`

## Frozen artifact filenames
- `eval_harness.json`
- `eval_report.json`
- `budget_report.json`
- `golden_task_report.json`
- `replay_report.json`
- `tool_validity_report.json`

## Canonical file set
- `app/eval/models.py`
- `app/eval/harness.py`
- `app/eval/aggregate.py`
- `app/eval/golden_tasks.py`
- `app/eval/tool_validity.py`
- `app/eval/replay.py`
- `app/eval/budget.py`
- `app/control/coordinator.py`
- `app/control/run_daily.py`
- `configs/eval/evaluator_registry.json`
- `configs/eval/golden_tasks.json`
- `configs/eval/replay_tasks.json`
- `configs/eval/budget_baselines.json`
- `schemas/eval_harness.schema.json`
- `schemas/budget_report.schema.json`
- `tests/test_eval_contracts.py`
- `tests/test_eval_golden_tasks.py`
- `tests/test_eval_tool_validity.py`
- `tests/test_eval_replay.py`
- `tests/test_eval_budget.py`

## Integration decisions
- generated eval replaces borrowed `brief["eval_report"]`
- `RunCoordinator` owns orchestration
- `run_daily.py` is a thin bootstrap wrapper
- `DailyRun.artifacts` adopts the full artifact index path
- evaluator receipts are emitted in the runtime path
- `BudgetEvaluator` owns `budget_report.json` and it must not be overwritten by generic harness serialization

## Phase 2 exit criteria
- `run_daily.py` no longer forwards borrowed eval data
- `EvalHarness` generates `eval_report.json`
- `BudgetEvaluator` generates `budget_report.json`
- evaluator outputs validate against schemas
- end-to-end tests cover hold, canary-ready, and quarantine paths

## Boundary
Phase 2 stops at generated evaluation and runtime reconciliation. Governed promotion, rollback, and work-tracker updates are deferred to Phase 3.
