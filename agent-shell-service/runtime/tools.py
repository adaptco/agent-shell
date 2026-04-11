from __future__ import annotations
import json
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path
from runtime.config import resolve_path
from runtime.utils import read_json
from runtime.validation import validate


class ToolRegistry:
    def __init__(self, cfg):
        self.cfg = cfg
        self.registry = {}
        tool_dir = resolve_path(cfg, cfg["tools"]["registry_dir"])
        for path in sorted(tool_dir.glob("*.json")):
            spec = read_json(path)
            self.registry[spec["name"]] = spec

    def execute(self, name: str, tool_input: dict) -> dict:
        spec = self.registry[name]
        validate(tool_input, spec["input_schema"])
        if name == "file_read":
            result = self._file_read(tool_input)
        elif name == "bash":
            result = self._bash(tool_input)
        elif name == "web_search":
            result = self._web_search(tool_input)
        else:
            raise ValueError(f"unknown tool: {name}")
        validate(result, spec["output_schema"])
        return result

    def _safe_workspace_path(self, relative: str) -> Path:
        root = Path(self.cfg["_workspace"]).resolve()
        candidate = (root / relative).resolve()
        if root not in [candidate, *candidate.parents]:
            raise ValueError("path escapes workspace")
        return candidate

    def _file_read(self, tool_input: dict) -> dict:
        path = self._safe_workspace_path(tool_input["path"])
        max_bytes = int(tool_input.get("max_bytes", 65536))
        content = path.read_text(encoding="utf-8")[:max_bytes]
        return {"path": str(path.relative_to(Path(self.cfg["_workspace"]))), "content": content, "bytes_read": len(content.encode('utf-8'))}

    def _bash(self, tool_input: dict) -> dict:
        command = tool_input["command"]
        timeout = int(self.cfg["tools"]["bash"]["timeout_seconds"])
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=self.cfg["_workspace"],
            timeout=timeout,
        )
        return {"stdout": completed.stdout, "stderr": completed.stderr, "exit_code": int(completed.returncode)}

    def _web_search(self, tool_input: dict) -> dict:
        provider = self.cfg["tools"]["web_search"]["provider"]
        query = tool_input["query"]
        limit = int(tool_input.get("limit", 5))
        if provider == "mock":
            results = self.cfg["tools"]["web_search"]["mock_results"][:limit]
            return {"query": query, "results": results}
        if provider == "duckduckgo":
            base = self.cfg["tools"]["web_search"]["duckduckgo_url"]
            params = urllib.parse.urlencode({"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"})
            with urllib.request.urlopen(base + "?" + params, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
            results = []
            if data.get("AbstractText"):
                results.append({"title": data.get("Heading", query), "url": data.get("AbstractURL", ""), "snippet": data["AbstractText"]})
            for item in data.get("RelatedTopics", []):
                if isinstance(item, dict) and item.get("Text"):
                    results.append({"title": item["Text"][:80], "url": item.get("FirstURL", ""), "snippet": item["Text"]})
                    if len(results) >= limit:
                        break
            return {"query": query, "results": results[:limit]}
        raise ValueError(f"unsupported web search provider: {provider}")
