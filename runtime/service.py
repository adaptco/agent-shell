from runtime.agent_loop import AgentLoop
from runtime.config import load_config, resolve_path
from runtime.hooks import HookRegistry
from runtime.llm import get_backend
from runtime.logger import get_logger
from runtime.memory import JournalMemory
from runtime.middleware import MiddlewareStack
from runtime.queue_fs import FileTaskQueue
from runtime.receipts import ReceiptWriter
from runtime.subagents import SubagentManager
from runtime.tools import ToolRegistry
from runtime.utils import read_json, write_json, utc_now


class AgentService:
    def __init__(self, cfg=None):
        self.cfg = cfg or load_config()
        self.logger = get_logger(self.cfg)
        self.middleware = MiddlewareStack(self.logger)
        self.decision_schema = read_json(resolve_path(self.cfg, "schemas/decision.schema.json"))
        self.task_schema = read_json(resolve_path(self.cfg, "schemas/task.schema.json"))
        self.handoff_schema = read_json(resolve_path(self.cfg, "schemas/handoff.schema.json"))
        self.hooks = HookRegistry(self.cfg)
        self.tools = ToolRegistry(self.cfg)
        self.receipts = ReceiptWriter(self.cfg)
        self.memory = JournalMemory(self.cfg, hooks=self.hooks, receipts=self.receipts)
        self.queue = FileTaskQueue(self.cfg, self.task_schema)

    def _loop_factory(self, backend_name: str):
        backend = get_backend(backend_name, self.cfg)
        subagents = SubagentManager(self.cfg, self._loop_factory, self.handoff_schema)
        return AgentLoop(
            self.cfg,
            backend,
            self.hooks,
            self.tools,
            self.memory,
            self.receipts,
            self.decision_schema,
            subagents,
            self.logger,
        )

    def doctor(self) -> dict:
        def _handler(payload):
            checks = {
                "agent_md": resolve_path(self.cfg, self.cfg["agent_file"]).exists(),
                "skills": resolve_path(self.cfg, self.cfg["skill_dir"]).exists(),
                "tools": resolve_path(self.cfg, self.cfg["tools"]["registry_dir"]).exists(),
                "hooks": resolve_path(self.cfg, self.cfg["hooks"]["registry_dir"]).exists(),
                "queue_inbox": resolve_path(self.cfg, self.cfg["queue"]["inbox_dir"]).exists(),
                "runtime_state": resolve_path(self.cfg, self.cfg["state"]["runtime_state"]).exists(),
            }
            return {"ok": all(checks.values()), "checks": checks}

        return self.middleware.run("doctor", {}, _handler)

    def health(self) -> dict:
        def _handler(payload):
            doctor = self.doctor()
            runtime_state = self.get_runtime_state()
            queue_state = self.list_tasks(limit=10)
            return {
                "ok": doctor["ok"],
                "name": self.cfg["name"],
                "version": self.cfg["version"],
                "doctor": doctor,
                "runtime_state": runtime_state,
                "queue": queue_state["counts"],
            }

        return self.middleware.run("health", {}, _handler)

    def get_runtime_state(self) -> dict:
        return read_json(resolve_path(self.cfg, self.cfg["state"]["runtime_state"]))

    def queue_add(
        self,
        task: str,
        parent_task_id: str | None = None,
        assigned_subagent: str | None = None,
    ) -> dict:
        def _handler(payload):
            path = self.queue.enqueue(task, parent_task_id=parent_task_id, assigned_subagent=assigned_subagent)
            return {"queued": True, "path": str(path), "task_id": path.stem}

        return self.middleware.run("queue_add", {"task": task}, _handler)

    def list_tasks(self, limit: int = 100) -> dict:
        def _handler(payload):
            return self.queue.list_tasks(limit=limit)

        return self.middleware.run("list_tasks", {"limit": limit}, _handler)

    def get_task(self, task_id: str) -> dict | None:
        def _handler(payload):
            return self.queue.get_task(task_id)

        return self.middleware.run("get_task", {"task_id": task_id}, _handler)

    def run_next(self, backend_name: str, worker_id: str | None = None) -> dict:
        worker_id = worker_id or self.cfg["worker"]["default_worker_id"]

        def _handler(payload):
            task, working_path = self.queue.claim_next(worker_id)
            if not task:
                return {"queued": False, "message": "no queued task"}
            loop = self._loop_factory(backend_name)
            result = loop.run_task(task, subagent_name=task.get("assigned_subagent"))
            if result.get("status") == "done":
                completed = self.queue.complete(task, working_path, result)
                return {
                    "queued": True,
                    "completed_path": str(completed),
                    "result": result,
                }
            failed = self.queue.fail(task, working_path, result)
            return {"queued": True, "failed_path": str(failed), "result": result}

        return self.middleware.run("run_next", {"backend_name": backend_name, "worker_id": worker_id}, _handler)

    def run_task(self, task: str, backend_name: str, subagent_name: str | None = None) -> dict:
        def _handler(payload):
            queued = self.queue.enqueue(task, assigned_subagent=subagent_name)
            task_obj = read_json(queued)
            queued.unlink()
            loop = self._loop_factory(backend_name)
            result = loop.run_task(task_obj, subagent_name=subagent_name)
            return {"result": result}

        return self.middleware.run("run_task", {"task": task, "backend_name": backend_name}, _handler)

    def heartbeat(self, worker_id: str | None = None) -> dict:
        worker_id = worker_id or self.cfg["worker"]["default_worker_id"]

        def _handler(payload):
            runtime_state_path = resolve_path(self.cfg, self.cfg["state"]["runtime_state"])
            runtime_state = read_json(runtime_state_path)
            runtime_state["last_heartbeat"] = utc_now()
            runtime_state["last_worker_id"] = worker_id
            runtime_state["status"] = "alive"
            write_json(runtime_state_path, runtime_state)
            self.receipts.emit("system", "heartbeat", "ok", {"worker_id": worker_id}, runtime_state)
            return runtime_state

        return self.middleware.run("heartbeat", {"worker_id": worker_id}, _handler)
