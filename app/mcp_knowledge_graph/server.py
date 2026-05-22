"""
MCP Server: Knowledge Graph MCP Server
Implements Model Context Protocol tools for semantic analysis and knowledge graph creation.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
import uvicorn

from app.mcp_knowledge_graph.semantic_analyzer import SemanticAnalyzer
from app.mcp_knowledge_graph.orchestrator import SubAgentOrchestrator


class MCPKnowledgeGraphServer:
    """MCP Server providing knowledge graph and orchestration tools"""

    def __init__(self, workspace: str = "."):
        self.workspace = Path(workspace)
        self.documents_dir = self.workspace / "documents"
        self.documents_dir.mkdir(parents=True, exist_ok=True)

        self.semantic_analyzer = SemanticAnalyzer(embedding_dim=128)
        self.orchestrator = SubAgentOrchestrator()

        # Store graphs in memory
        self.graphs: Dict[str, Dict[str, Any]] = {}

    def get_tool_specs(self) -> list[Dict[str, Any]]:
        """Return MCP tool specifications"""
        return [
            {
                "name": "parse_requirements",
                "description": "Parse a requirements document and extract semantic tokens",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "document_text": {"type": "string", "description": "The requirements document text to analyze"},
                        "document_name": {"type": "string", "description": "Name/identifier for the document"},
                    },
                    "required": ["document_text", "document_name"],
                },
            },
            {
                "name": "create_knowledge_graph",
                "description": "Create a knowledge graph from one or more documents",
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
            {
                "name": "assign_expertise_clusters",
                "description": "Generate sub-agent task assignments from knowledge graph",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "graph_id": {"type": "string", "description": "ID of the knowledge graph to use"},
                        "parent_task": {"type": "string", "description": "Description of the parent task"},
                        "parent_task_id": {"type": "string", "description": "ID of the parent task"},
                    },
                    "required": ["graph_id", "parent_task", "parent_task_id"],
                },
            },
            {
                "name": "get_graph_visualization",
                "description": "Get graph data for visualization",
                "inputSchema": {
                    "type": "object",
                    "properties": {"graph_id": {"type": "string", "description": "ID of the knowledge graph"}},
                    "required": ["graph_id"],
                },
            },
        ]

    async def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool"""
        try:
            if tool_name == "parse_requirements":
                return self._parse_requirements(
                    tool_input.get("document_text", ""), tool_input.get("document_name", "document")
                )

            elif tool_name == "create_knowledge_graph":
                return self._create_knowledge_graph(
                    tool_input.get("documents", {}), tool_input.get("graph_id", "default_graph")
                )

            elif tool_name == "assign_expertise_clusters":
                return self._assign_expertise_clusters(
                    tool_input.get("graph_id", "default_graph"),
                    tool_input.get("parent_task", ""),
                    tool_input.get("parent_task_id", ""),
                )

            elif tool_name == "get_graph_visualization":
                return self._get_graph_visualization(tool_input.get("graph_id", "default_graph"))

            else:
                return {"status": "error", "message": f"Unknown tool: {tool_name}"}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _parse_requirements(self, document_text: str, document_name: str) -> Dict[str, Any]:
        """Tool: Parse requirements document"""
        tokens = self.semantic_analyzer.extract_semantic_tokens(document_text, context=document_name)

        return {
            "status": "success",
            "document_name": document_name,
            "token_count": len(tokens),
            "tokens": [t.to_dict() for t in tokens[:20]],  # Return top 20
            "domain_classification": self.semantic_analyzer.classify_domains(tokens),
        }

    def _create_knowledge_graph(self, documents: Dict[str, str], graph_id: str) -> Dict[str, Any]:
        """Tool: Create knowledge graph"""
        if not documents:
            return {"status": "error", "message": "No documents provided"}

        graph = self.semantic_analyzer.build_knowledge_graph(documents)
        self.graphs[graph_id] = graph

        return {
            "status": "success",
            "graph_id": graph_id,
            "node_count": len(graph["nodes"]),
            "edge_count": len(graph["edges"]),
            "cluster_count": len(graph["clusters"]),
            "nodes": graph["nodes"],
            "edges": graph["edges"],
        }

    def _assign_expertise_clusters(self, graph_id: str, parent_task: str, parent_task_id: str) -> Dict[str, Any]:
        """Tool: Assign expertise clusters to sub-agents"""
        if graph_id not in self.graphs:
            return {"status": "error", "message": f"Graph not found: {graph_id}"}

        graph = self.graphs[graph_id]
        tasks = self.orchestrator.generate_subtasks(graph, parent_task)
        ordered_tasks = self.orchestrator.assign_task_order(tasks)

        # Create delegation contracts
        delegations = []
        for task in ordered_tasks:
            contract = self.orchestrator.create_delegation_contract(task, parent_task_id)
            delegations.append({"task": task.to_dict(), "delegation_contract": contract})

        return {
            "status": "success",
            "graph_id": graph_id,
            "parent_task_id": parent_task_id,
            "task_count": len(delegations),
            "tasks": delegations,
        }

    def _get_graph_visualization(self, graph_id: str) -> Dict[str, Any]:
        """Tool: Get graph visualization data"""
        if graph_id not in self.graphs:
            return {"status": "error", "message": f"Graph not found: {graph_id}"}

        graph = self.graphs[graph_id]

        return {
            "status": "success",
            "graph_id": graph_id,
            "visualization": {"nodes": graph["nodes"], "edges": graph["edges"]},
        }


# FastAPI Application for MCP Server
def create_mcp_app(workspace: str = ".") -> FastAPI:
    """Create FastAPI app for MCP server"""
    app = FastAPI(
        title="Knowledge Graph MCP Server",
        version="1.0.0",
        description="MCP server for semantic analysis and knowledge graph creation",
    )

    server = MCPKnowledgeGraphServer(workspace)
    app.state.server = server

    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "knowledge-graph-mcp"}

    @app.get("/tools")
    async def list_tools():
        """List available MCP tools"""
        return {"tools": app.state.server.get_tool_specs()}

    @app.post("/tool/{tool_name}")
    async def execute_tool(tool_name: str, payload: Dict[str, Any]):
        """Execute a tool"""
        result = await app.state.server.execute_tool(tool_name, payload)
        return result

    @app.get("/graphs")
    async def list_graphs():
        """List all knowledge graphs"""
        return {"graphs": list(app.state.server.graphs.keys()), "count": len(app.state.server.graphs)}

    @app.get("/graphs/{graph_id}")
    async def get_graph(graph_id: str):
        """Get a specific graph"""
        if graph_id not in app.state.server.graphs:
            raise HTTPException(status_code=404, detail=f"Graph not found: {graph_id}")

        graph = app.state.server.graphs[graph_id]
        return {
            "graph_id": graph_id,
            "nodes": graph["nodes"],
            "edges": graph["edges"],
            "clusters": list(graph["clusters"].keys()),
        }

    return app


# Entry point
if __name__ == "__main__":
    import sys

    workspace = sys.argv[1] if len(sys.argv) > 1 else "."
    app = create_mcp_app(workspace)
    uvicorn.run(app, host="127.0.0.1", port=5100)
