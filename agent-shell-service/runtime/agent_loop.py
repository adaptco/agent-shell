from __future__ import annotations
from runtime.context import ContextBuilder
from runtime.validation import validate
from runtime.utils import utc_now


class AgentLoop:
    def __init__(self, cfg, backend, hooks, tools, memory, receipts, decision_schema, subagents, logger):
        self.cfg = cfg
        self.backend = backend
        self.hooks = hooks
        self.tools = tools
        self.memory = memory
        self.receipts = receipts
        self.decision_schema = decision_schema
        self.subagents = subagents
        self.logger = logger
        self.context_builder = ContextBuilder(cfg)

    def _update_markdown_state(self, task: dict, result: dict) -> None:
        from pathlib import Path
        path = Path(self.cfg["_workspace"]) / self.cfg["state"]["markdown_state"]
        path.write_text(
            "# Agent State\n\n"
            "## Status\n"
            f"{result.get('status', 'complete')}\n\n"
            "## Last Task\n"
            f"{task['task']}\n\n"
            "## Last Result\n"
            f"{result.get('final_response', result.get('summary', 'n/a'))}\n\n"
            "## Last Updated\n"
            f"{utc_now()}\n",
            encoding="utf-8",
        )
        from runtime.utils import read_json, write_json
        runtime_state_path = Path(self.cfg["_workspace"]) / self.cfg["state"]["runtime_state"]
        runtime_state = read_json(runtime_state_path)
        runtime_state["status"] = "idle"
        runtime_state["last_task_id"] = task["task_id"]
        runtime_state["last_worker_id"] = task.get("worker_id")
        write_json(runtime_state_path, runtime_state)

    def run_task(self, task: dict, subagent_name: str | None = None, depth: int = 0) -> dict:
        if depth > self.cfg["worker"]["max_delegate_depth"]:
            return {"status": "failed", "final_response": "max delegate depth exceeded"}
        history: list[dict] = []
        max_steps = self.cfg["worker"]["max_steps"]
        for step_index in range(max_steps):
            context = self.context_builder.build(task, history, subagent_name=subagent_name)
            self.hooks.run("before_model_call", task["task_id"], {"step_index": step_index, "history_length": len(history)})
            decision = self.backend.decide(context, self.decision_schema, depth=depth)
            validate(decision, self.decision_schema)
            self.hooks.run("after_model_call", task["task_id"], {"decision": decision})
            self.receipts.emit(task["task_id"], f"decision_{step_index}", "ok", {"history_length": len(history)}, decision)
            if decision["decision_type"] == "tool_call":
                hook_result = self.hooks.run(
                    "before_tool_call",
                    task["task_id"],
                    {"tool_name": decision["tool_name"], "tool_input": decision.get("tool_input", {})},
                )
                if not hook_result["allow"]:
                    error = {"status": "blocked", "reason": hook_result.get("reason", "tool blocked")}
                    self.receipts.emit(task["task_id"], f"tool_{step_index}", "blocked", decision, error)
                    return error
                tool_result = self.tools.execute(decision["tool_name"], hook_result["payload"]["tool_input"])
                tool_result = self.hooks.run(
                    "after_tool_call",
                    task["task_id"],
                    {"tool_name": decision["tool_name"], "tool_result": tool_result},
                )["payload"]
                history.append(
                    {
                        "event_type": "tool_result",
                        "tool_name": decision["tool_name"],
                        "summary": decision["reasoning_summary"],
                        "result": tool_result,
                        "created_at": utc_now(),
                    }
                )
                self.memory.append(
                    {
                        "event_type": "tool_result",
                        "tool_name": decision["tool_name"],
                        "summary": decision["reasoning_summary"],
                        "created_at": utc_now(),
                    },
                    task_id=task["task_id"],
                )
                continue
            if decision["decision_type"] == "delegate":
                hook_result = self.hooks.run(
                    "before_delegate",
                    task["task_id"],
                    {
                        "subagent_name": decision["subagent_name"],
                        "subtask": decision["subtask"],
                        "handoff_contract": decision.get("handoff_contract", {}),
                    },
                )
                if not hook_result["allow"]:
                    error = {"status": "blocked", "reason": hook_result.get("reason", "delegate blocked")}
                    self.receipts.emit(task["task_id"], f"delegate_{step_index}", "blocked", decision, error)
                    return error
                delegate_result = self.subagents.delegate(task, decision, self.backend.name, depth)
                delegate_result = self.hooks.run("after_delegate", task["task_id"], delegate_result)["payload"]
                history.append(
                    {
                        "event_type": "delegate_result",
                        "summary": decision["reasoning_summary"],
                        "result": delegate_result,
                        "created_at": utc_now(),
                    }
                )
                self.memory.append(
                    {"event_type": "delegate_result", "summary": decision["reasoning_summary"], "created_at": utc_now()},
                    task_id=task["task_id"],
                )
                continue
            final = {
                "status": "done",
                "final_response": decision["final_response"],
                "summary": decision["reasoning_summary"],
                "history_length": len(history),
            }
            self.memory.append({"event_type": "final", "summary": decision["reasoning_summary"], "created_at": utc_now()}, task_id=task["task_id"])
            self.receipts.emit(task["task_id"], "final", "ok", {"history_length": len(history)}, final)
            self._update_markdown_state(task, final)
            return final
        error = {"status": "failed", "final_response": "max steps exceeded"}
        self.receipts.emit(task["task_id"], "max_steps", "failed", {"max_steps": max_steps}, error)
        self._update_markdown_state(task, error)
        return error
