from runtime.config import resolve_path
from runtime.utils import append_jsonl, utc_now, read_json, write_json


class JournalMemory:
    def __init__(self, cfg, hooks=None, receipts=None):
        self.cfg = cfg
        self.hooks = hooks
        self.receipts = receipts
        self.journal = resolve_path(cfg, cfg["memory"]["journal_path"])
        self.summary = resolve_path(cfg, cfg["memory"]["summary_path"])
        self.archive_dir = resolve_path(cfg, cfg["memory"]["archive_dir"])
        self.runtime_state_path = resolve_path(cfg, cfg["state"]["runtime_state"])
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.journal.parent.mkdir(parents=True, exist_ok=True)
        self.journal.touch(exist_ok=True)

    def entries(self) -> list[dict]:
        if not self.journal.exists():
            return []
        lines = [
            line
            for line in self.journal.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        result = []
        for line in lines:
            try:
                import json

                result.append(json.loads(line))
            except Exception:
                result.append({"raw": line, "parse_error": True})
        return result

    def append(self, event: dict, task_id: str = "system") -> None:
        append_jsonl(self.journal, event)
        state = read_json(self.runtime_state_path)
        state["memory"]["entries"] = len(self.entries())
        write_json(self.runtime_state_path, state)
        if self.should_compact():
            self.compact(task_id)

    def should_compact(self) -> bool:
        compaction = self.cfg["memory"]["compaction"]
        return (
            compaction.get("enabled", False)
            and len(self.entries()) > compaction["max_entries"]
        )

    def compact(self, task_id: str) -> dict:
        entries = self.entries()
        payload = {"entry_count": len(entries)}
        if self.hooks:
            hook_result = self.hooks.run("before_memory_compact", task_id, payload)
            if not hook_result["allow"]:
                return {
                    "compacted": False,
                    "reason": hook_result.get("reason", "blocked"),
                }
        archive_path = (
            self.archive_dir / f"{utc_now().replace(':', '').replace('+', '_')}.jsonl"
        )
        archive_path.write_text(
            self.journal.read_text(encoding="utf-8"), encoding="utf-8"
        )
        keep_last = self.cfg["memory"]["compaction"]["keep_last"]
        retained = entries[-keep_last:]
        lines = [
            f"- {e.get('event_type', 'event')}: {e.get('summary', e.get('tool_name', 'n/a'))}"
            for e in entries[-10:]
        ]
        self.summary.write_text(
            "# Memory Summary\n\n"
            + f"- Compacted at: {utc_now()}\n"
            + f"- Entries archived: {len(entries)}\n\n## Recent Events\n"
            + "\n".join(lines)
            + "\n",
            encoding="utf-8",
        )
        self.journal.write_text("", encoding="utf-8")
        for entry in retained:
            append_jsonl(self.journal, entry)
        append_jsonl(
            self.journal,
            {
                "event_type": "compaction_marker",
                "summary": f"Archived {len(entries)} entries",
                "created_at": utc_now(),
            },
        )
        state = read_json(self.runtime_state_path)
        state["memory"]["entries"] = len(self.entries())
        state["memory"]["last_compaction"] = utc_now()
        write_json(self.runtime_state_path, state)
        result = {
            "compacted": True,
            "archive_path": str(archive_path),
            "retained": len(retained),
        }
        if self.hooks:
            self.hooks.run("after_memory_compact", task_id, result)
        if self.receipts:
            self.receipts.emit(task_id, "memory_compact", "ok", payload, result)
        return result
