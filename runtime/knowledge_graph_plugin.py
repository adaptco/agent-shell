"""
Knowledge Graph Tool Plugin for Agent Shell Runtime
Integrates semantic analysis and sub-agent orchestration into agent tool registry.
"""

from __future__ import annotations
from typing import Dict, Any
import httpx

from runtime.plugin_base import ToolPlugin
from app.mcp_knowledge_graph import MCPKnowledgeGraphServer


class KnowledgeGraphPlugin(ToolPlugin):
    """
    Tool plugin that provides semantic analysis and knowledge graph capabilities
    to the Agent Shell runtime. Can use either local server or remote MCP endpoint.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.mcp_server_url = config.get("mcp_server_url", "http://127.0.0.1:5100")
        self.use_local = config.get("use_local_server", False)

        if self.use_local:
            workspace = config.get("_workspace", ".")
            self.local_server = MCPKnowledgeGraphServer(workspace)
        else:
            self.local_server = None

    def get_tool_specs(self) -> Dict[str, Dict]:
        """Return available tool specifications"""
        return {
            "parse_requirements_document": {
                "name": "parse_requirements_document",
                "description": "Parse a requirements document and extract semantic tokens and domain expertise",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "document_text": {"type": "string", "description": "The requirements document text"},
                        "document_name": {"type": "string", "description": "Name/identifier for the document"},
                    },
                    "required": ["document_text", "document_name"],
                },
            },
            "build_knowledge_graph": {
                "name": "build_knowledge_graph",
                "description": "Build a knowledge graph from requirements documents",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "documents": {
                            "type": "object",
                            "description": "Dict of document_name -> document_text",
                            "additionalProperties": {"type": "string"},
                        },
                        "graph_id": {"type": "string", "description": "Identifier for this graph"},
                    },
                    "required": ["documents", "graph_id"],
                },
            },
            "generate_subtasks": {
                "name": "generate_subtasks",
                "description": "Generate sub-agent task assignments from a knowledge graph",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "graph_id": {"type": "string", "description": "ID of the knowledge graph"},
                        "parent_task": {"type": "string", "description": "Description of the parent task"},
                        "parent_task_id": {"type": "string", "description": "ID of the parent task"},
                    },
                    "required": ["graph_id", "parent_task", "parent_task_id"],
                },
            },
        }

    def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a knowledge graph tool"""
        if tool_name == "parse_requirements_document":
            return self._parse_requirements(
                tool_input.get("document_text", ""), tool_input.get("document_name", "document")
            )

        elif tool_name == "build_knowledge_graph":
            return self._build_graph(tool_input.get("documents", {}), tool_input.get("graph_id", "default"))

        elif tool_name == "generate_subtasks":
            return self._generate_tasks(
                tool_input.get("graph_id", "default"),
                tool_input.get("parent_task", ""),
                tool_input.get("parent_task_id", ""),
            )

        else:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}

    def _parse_requirements(self, document_text: str, document_name: str) -> Dict[str, Any]:
        """Parse requirements and extract semantic tokens"""
        if self.use_local and self.local_server:
            return self.local_server._parse_requirements(document_text, document_name)
        else:
            return self._call_remote_tool(
                "parse_requirements", {"document_text": document_text, "document_name": document_name}
            )

    def _build_graph(self, documents: Dict[str, str], graph_id: str) -> Dict[str, Any]:
        """Build knowledge graph from documents"""
        if self.use_local and self.local_server:
            return self.local_server._create_knowledge_graph(documents, graph_id)
        else:
            return self._call_remote_tool("create_knowledge_graph", {"documents": documents, "graph_id": graph_id})

    def _generate_tasks(self, graph_id: str, parent_task: str, parent_task_id: str) -> Dict[str, Any]:
        """Generate sub-agent task assignments"""
        if self.use_local and self.local_server:
            return self.local_server._assign_expertise_clusters(graph_id, parent_task, parent_task_id)
        else:
            return self._call_remote_tool(
                "assign_expertise_clusters",
                {"graph_id": graph_id, "parent_task": parent_task, "parent_task_id": parent_task_id},
            )

    def _call_remote_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on remote MCP server"""
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(f"{self.mcp_server_url}/tool/{tool_name}", json=tool_input)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"status": "error", "message": f"Remote call failed: {str(e)}"}
