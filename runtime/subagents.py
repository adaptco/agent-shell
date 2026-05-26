from __future__ import annotations
from pathlib import Path
from uuid import uuid4
from runtime.utils import write_json


class SubagentManager:
    def __init__(self, cfg, loop_factory, handoff_schema):
        self.cfg = cfg
        self.loop_factory = loop_factory
        self.handoff_schema = handoff_schema
        self.handoff_dir = Path(cfg["_workspace"]) / "queue" / "handoffs"
        self.handoff_dir.mkdir(parents=True, exist_ok=True)

    def delegate(
        self, parent_task: dict, decision: dict, backend_name: str, depth: int
    ) -> dict:
        handoff = decision.get("handoff_contract") or {
            "handoff_id": uuid4().hex,
            "parent_task_id": parent_task["task_id"],
            "subagent_name": decision["subagent_name"],
            "subtask": decision["subtask"],
            "context_files": ["agent.md", "skill/RUNTIME.md"],
            "return_contract": {"expects": "delegate_result", "max_steps": 4},
        }
        from runtime.validation import validate

        validate(handoff, self.handoff_schema)
        write_json(self.handoff_dir / f"{handoff['handoff_id']}.json", handoff)
        loop = self.loop_factory(backend_name)
        subtask = {
            "task_id": uuid4().hex,
            "task": handoff["subtask"],
            "status": "working",
            "created_at": parent_task["created_at"],
            "parent_task_id": parent_task["task_id"],
        }
        result = loop.run_task(
            subtask, subagent_name=handoff["subagent_name"], depth=depth + 1
        )
        return {"handoff": handoff, "delegate_result": result}
