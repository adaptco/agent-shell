from pathlib import Path
from runtime.config import resolve_path
from runtime.utils import read_json


class ContextBuilder:
    def __init__(self, cfg):
        self.cfg = cfg
        self.workspace = Path(cfg["_workspace"])

    def _load_skills(self) -> list[dict]:
        skill_dir = resolve_path(self.cfg, self.cfg["skill_dir"])
        items = []
        for path in sorted(skill_dir.glob("*.md")):
            items.append(
                {"name": path.name, "content": path.read_text(encoding="utf-8")}
            )
        return items

    def _load_subagent_prompt(self, subagent_name: str | None) -> str | None:
        if not subagent_name:
            return None
        path = resolve_path(self.cfg, self.cfg["subagent_dir"]) / f"{subagent_name}.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def build(
        self, task: dict, history: list[dict], subagent_name: str | None = None
    ) -> dict:
        agent_text = resolve_path(self.cfg, self.cfg["agent_file"]).read_text(
            encoding="utf-8"
        )
        state_md = resolve_path(
            self.cfg, self.cfg["state"]["markdown_state"]
        ).read_text(encoding="utf-8")
        runtime_state = read_json(
            resolve_path(self.cfg, self.cfg["state"]["runtime_state"])
        )
        summary_path = resolve_path(self.cfg, self.cfg["memory"]["summary_path"])
        memory_summary = (
            summary_path.read_text(encoding="utf-8") if summary_path.exists() else ""
        )
        return {
            "task": task,
            "agent_md": agent_text,
            "skills": self._load_skills(),
            "state_md": state_md,
            "runtime_state": runtime_state,
            "memory_summary": memory_summary,
            "history": history,
            "subagent_md": self._load_subagent_prompt(subagent_name),
        }
