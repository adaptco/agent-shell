from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
from runtime.config import resolve_path


class SkillDiscovery:
    """
    Logic for indexing and discovering available skills.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.skill_dir = resolve_path(config, config["skill_dir"])

    def run(self, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scan the skill directory and return metadata about available skills.
        """
        query = tool_input.get("query", "").lower()
        skills = []

        if not self.skill_dir.exists():
            return {"skills": [], "count": 0}

        for item in self.skill_dir.iterdir():
            if item.is_dir():
                skill_md = item / "SKILL.md"
                if skill_md.exists():
                    content = skill_md.read_text(encoding="utf-8")
                    # Simple extraction of title/description
                    title = item.name
                    description = content.split("\n", 1)[0].lstrip("#").strip()

                    if not query or query in title.lower() or query in description.lower():
                        skills.append(
                            {
                                "name": title,
                                "description": description,
                                "path": str(item.relative_to(Path(self.config["_workspace"]))),
                            }
                        )

        return {"skills": skills, "count": len(skills)}
