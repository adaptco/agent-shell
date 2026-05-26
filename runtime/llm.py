from __future__ import annotations
import json
import urllib.request
from runtime.utils import sha256_hex, get_env


class BaseBackend:
    name = "base"

    def decide(self, context: dict, decision_schema: dict, depth: int = 0) -> dict:
        raise NotImplementedError


class MockBackend(BaseBackend):
    name = "mock"

    def decide(self, context: dict, decision_schema: dict, depth: int = 0) -> dict:
        task_text = context["task"]["task"].lower()
        history = context["history"]
        subagent_md = context.get("subagent_md")
        if subagent_md:
            if history and history[-1].get("event_type") == "tool_result":
                return {
                    "decision_type": "final",
                    "reasoning_summary": "Sub-agent completed after one tool step.",
                    "final_response": f"Sub-agent completed task: {context['task']['task']}",
                }
            if "file" in task_text or "read" in task_text:
                return {
                    "decision_type": "tool_call",
                    "reasoning_summary": "Sub-agent will read the root agent file.",
                    "tool_name": "file_read",
                    "tool_input": {"path": "agent.md", "max_bytes": 1200},
                }
            return {
                "decision_type": "final",
                "reasoning_summary": "Sub-agent can answer directly.",
                "final_response": f"Sub-agent completed task: {context['task']['task']}",
            }
        if not history:
            if "delegate" in task_text or "subagent" in task_text:
                return {
                    "decision_type": "delegate",
                    "reasoning_summary": "This task is bounded and can be delegated.",
                    "subagent_name": "file_worker",
                    "subtask": "Read agent.md and summarize the operating rules.",
                }
            if "search" in task_text or "web" in task_text:
                return {
                    "decision_type": "tool_call",
                    "reasoning_summary": "Use web search first.",
                    "tool_name": "web_search",
                    "tool_input": {"query": context["task"]["task"], "limit": 3},
                }
            if (
                "list" in task_text
                or "workspace" in task_text
                or "directory" in task_text
            ):
                return {
                    "decision_type": "tool_call",
                    "reasoning_summary": "Use bash to list the workspace.",
                    "tool_name": "bash",
                    "tool_input": {"command": "ls -1"},
                }
            return {
                "decision_type": "tool_call",
                "reasoning_summary": "Read agent.md before answering.",
                "tool_name": "file_read",
                "tool_input": {"path": "agent.md", "max_bytes": 2000},
            }
        return {
            "decision_type": "final",
            "reasoning_summary": "Enough context has been gathered.",
            "final_response": f"Completed task '{context['task']['task']}' with {len(history)} history events.",
        }


def _build_decision_prompt(context: dict) -> tuple[str, str]:
    system_prompt = (
        "You are the decision layer for an agent shell runtime. "
        "Return only a JSON object matching the supplied schema."
    )
    user_prompt = json.dumps(
        {
            "task": context["task"],
            "history": context["history"],
            "agent_md_sha256": sha256_hex(context["agent_md"]),
            "skills": [item["name"] for item in context["skills"]],
            "state_excerpt": context["state_md"][:2000],
            "memory_summary_excerpt": context["memory_summary"][:2000],
            "subagent_md": context.get("subagent_md"),
        },
        ensure_ascii=False,
    )
    return system_prompt, user_prompt


class OpenAIResponsesBackend(BaseBackend):
    name = "openai"

    def __init__(self, cfg):
        self.cfg = cfg
        self.endpoint = cfg["llm"]["openai"]["endpoint"]
        self.model = cfg["llm"]["openai"]["model"]
        self.api_key = get_env(
            cfg.get("auth", {})
            .get("providers", {})
            .get("openai", {})
            .get("env_var", "OPENAI_API_KEY")
        )

    def decide(self, context: dict, decision_schema: dict, depth: int = 0) -> dict:
        system_prompt, user_prompt = _build_decision_prompt(context)
        payload = {
            "model": self.model,
            "input": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "agent_decision",
                    "strict": True,
                    "schema": decision_schema,
                }
            },
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(self.endpoint, data=data, method="POST")
        request.add_header("Authorization", f"Bearer {self.api_key}")
        request.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
        if "output_text" in body and body["output_text"]:
            return json.loads(body["output_text"])
        for item in body.get("output", []):
            if item.get("type") == "message":
                for content in item.get("content", []):
                    if content.get("type") in {"output_text", "text"} and content.get(
                        "text"
                    ):
                        return json.loads(content["text"])
        raise RuntimeError(
            "Could not parse structured response from OpenAI Responses API"
        )


class MistralChatBackend(BaseBackend):
    name = "mistral"

    def __init__(self, cfg):
        self.cfg = cfg
        self.endpoint = cfg.get("llm", {}).get("endpoint", "https://api.mistral.ai")
        self.model = cfg["llm"]["mistral"]["model"]
        self.api_key = get_env(
            cfg.get("auth", {}).get("providers", {}).get("mistral", {}).get("env_var")
        )

    def decide(self, context: dict, decision_schema: dict, depth: int = 0) -> dict:
        system_prompt, user_prompt = _build_decision_prompt(context)
        schema_prompt = (
            "Return only a JSON object that matches this JSON schema exactly: "
            + json.dumps(decision_schema, ensure_ascii=False)
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "system", "content": schema_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "agent_decision",
                    "schema": decision_schema,
                },
            },
            "temperature": 0,
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(self.endpoint, data=data, method="POST")
        request.add_header("Authorization", f"Bearer {self.api_key}")
        request.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = ((body.get("choices") or [{}])[0].get("message") or {}).get("content")
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            content = "".join(text_parts)
        if not content:
            raise RuntimeError(
                "Could not parse structured response from Mistral Chat Completions API"
            )
        return json.loads(content)


def get_backend(name: str, cfg):
    if name == "mock":
        return MockBackend()
    if name == "openai":
        return OpenAIResponsesBackend(cfg)
    if name == "mistral":
        return MistralChatBackend(cfg)
    raise ValueError(f"unsupported backend: {name}")
