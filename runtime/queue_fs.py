from __future__ import annotations
import os
from pathlib import Path
from uuid import uuid4
from runtime.config import resolve_path
from runtime.utils import utc_now, read_json, write_json
from runtime.validation import validate


class FileTaskQueue:
    def __init__(self, cfg, task_schema: dict):
        self.cfg = cfg
        self.task_schema = task_schema
        self.inbox = resolve_path(cfg, cfg["queue"]["inbox_dir"])
        self.working = resolve_path(cfg, cfg["queue"]["working_dir"])
        self.done = resolve_path(cfg, cfg["queue"]["done_dir"])
        self.failed = resolve_path(cfg, cfg["queue"]["failed_dir"])
        for path in [self.inbox, self.working, self.done, self.failed]:
            path.mkdir(parents=True, exist_ok=True)

    def enqueue(self, task_text: str, parent_task_id: str | None = None, assigned_subagent: str | None = None) -> Path:
        task_id = uuid4().hex
        task = {
            "task_id": task_id,
            "task": task_text,
            "status": "queued",
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }
        if parent_task_id:
            task["parent_task_id"] = parent_task_id
        if assigned_subagent:
            task["assigned_subagent"] = assigned_subagent
        validate(task, self.task_schema)
        path = self.inbox / f"{task_id}.json"
        write_json(path, task)
        return path

    def claim_next(self, worker_id: str):
        for path in sorted(self.inbox.glob("*.json")):
            target = self.working / f"{worker_id}--{path.name}"
            try:
                os.replace(path, target)
            except FileNotFoundError:
                continue
            task = read_json(target)
            task["status"] = "working"
            task["worker_id"] = worker_id
            task["updated_at"] = utc_now()
            write_json(target, task)
            return task, target
        return None, None

    def complete(self, task: dict, working_path: Path, result: dict) -> Path:
        task["status"] = "done"
        task["updated_at"] = utc_now()
        task["result"] = result
        write_json(working_path, task)
        target = self.done / working_path.name.split("--", 1)[-1]
        os.replace(working_path, target)
        return target

    def fail(self, task: dict, working_path: Path, error: dict) -> Path:
        task["status"] = "failed"
        task["updated_at"] = utc_now()
        task["error"] = error
        write_json(working_path, task)
        target = self.failed / working_path.name.split("--", 1)[-1]
        os.replace(working_path, target)
        return target

    def _dirs(self) -> dict[str, Path]:
        return {
            "queued": self.inbox,
            "working": self.working,
            "done": self.done,
            "failed": self.failed,
        }

    def list_tasks(self, limit: int = 100) -> dict:
        items: list[dict] = []
        counts = {status: 0 for status in self._dirs()}
        for status, directory in self._dirs().items():
            for path in sorted(directory.glob("*.json")):
                counts[status] += 1
                if len(items) >= limit:
                    continue
                data = read_json(path)
                data["queue_state"] = status
                data["path"] = str(path)
                items.append(data)
        items.sort(key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)
        return {"counts": counts, "items": items[:limit]}

    def get_task(self, task_id: str) -> dict | None:
        suffix = f"{task_id}.json"
        for status, directory in self._dirs().items():
            for path in directory.glob(f"*{suffix}"):
                data = read_json(path)
                data["queue_state"] = status
                data["path"] = str(path)
                return data
        return None
