"""
Web App Backend: FastAPI server for Knowledge Graph visualization and document upload
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List
import httpx
import asyncio

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.mcp_knowledge_graph import MCPKnowledgeGraphServer, SemanticAnalyzer


class DocumentUploadRequest(BaseModel):
    """Request model for document upload"""
    content: str
    filename: str


class OrchestrationRequest(BaseModel):
    """Request for sub-agent task generation"""
    graph_id: str
    parent_task: str
    parent_task_id: str


class GraphResponse(BaseModel):
    """Response model for graph data"""
    graph_id: str
    node_count: int
    edge_count: int
    cluster_count: int
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


def create_web_app(
    workspace: str = ".",
    mcp_server_url: str = "http://127.0.0.1:5100"
) -> FastAPI:
    """Create FastAPI web app backend"""
    app = FastAPI(
        title="Knowledge Graph Web UI",
        version="1.0.0",
        description="Web interface for knowledge graph creation and sub-agent orchestration"
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    workspace_path = Path(workspace)
    documents_dir = workspace_path / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)

    # Initialize local server instance for fallback
    local_server = MCPKnowledgeGraphServer(workspace)
    app.state.local_server = local_server
    app.state.mcp_server_url = mcp_server_url
    app.state.documents_dir = documents_dir

    # ==================== Health & Info ====================
    @app.get("/health")
    async def health():
        """Health check"""
        return {
            "status": "healthy",
            "service": "knowledge-graph-web",
            "mcp_server_url": mcp_server_url
        }

    # ==================== Document Management ====================
    @app.post("/api/documents/upload")
    async def upload_document(
        file: UploadFile = File(...),
    ):
        """Upload a requirements document"""
        try:
            # Read file content
            content = await file.read()
            text_content = content.decode("utf-8")

            # Save file to documents directory
            doc_path = documents_dir / file.filename
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write(text_content)

            # Parse document locally
            analyzer = SemanticAnalyzer()
            tokens = analyzer.extract_semantic_tokens(text_content, context=file.filename)
            domains = analyzer.classify_domains(tokens)

            return {
                "status": "success",
                "filename": file.filename,
                "size": len(text_content),
                "token_count": len(tokens),
                "domains": domains,
                "tokens_preview": [t.to_dict() for t in tokens[:10]]
            }

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing document: {str(e)}")

    @app.get("/api/documents")
    async def list_documents():
        """List uploaded documents"""
        docs = []
        if documents_dir.exists():
            for doc_path in documents_dir.glob("*"):
                if doc_path.is_file():
                    docs.append({
                        "filename": doc_path.name,
                        "size": doc_path.stat().st_size,
                        "modified": doc_path.stat().st_mtime
                    })

        return {"documents": docs, "count": len(docs)}

    @app.get("/api/documents/{filename}")
    async def get_document(filename: str):
        """Get document content"""
        doc_path = documents_dir / filename

        if not doc_path.exists():
            raise HTTPException(status_code=404, detail=f"Document not found: {filename}")

        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()

        return {
            "filename": filename,
            "content": content,
            "size": len(content)
        }

    # ==================== Knowledge Graph Operations ====================
    @app.post("/api/graph/create")
    async def create_graph(request: Dict[str, Any]):
        """Create knowledge graph from documents"""
        try:
            documents = request.get("documents", {})
            graph_id = request.get("graph_id", "default")

            if not documents:
                raise ValueError("No documents provided")

            # Use local server instance
            analyzer = app.state.local_server.semantic_analyzer
            graph = analyzer.build_knowledge_graph(documents)

            # Store in local server
            app.state.local_server.graphs[graph_id] = graph

            return {
                "status": "success",
                "graph_id": graph_id,
                "node_count": len(graph["nodes"]),
                "edge_count": len(graph["edges"]),
                "cluster_count": len(graph["clusters"])
            }

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error creating graph: {str(e)}")

    @app.get("/api/graphs")
    async def list_graphs():
        """List all knowledge graphs"""
        graphs = []
        for graph_id, graph in app.state.local_server.graphs.items():
            graphs.append({
                "graph_id": graph_id,
                "node_count": len(graph["nodes"]),
                "edge_count": len(graph["edges"]),
                "cluster_count": len(graph["clusters"])
            })

        return {"graphs": graphs, "count": len(graphs)}

    @app.get("/api/graphs/{graph_id}")
    async def get_graph(graph_id: str):
        """Get graph visualization data"""
        if graph_id not in app.state.local_server.graphs:
            raise HTTPException(status_code=404, detail=f"Graph not found: {graph_id}")

        graph = app.state.local_server.graphs[graph_id]

        return {
            "graph_id": graph_id,
            "nodes": graph["nodes"],
            "edges": graph["edges"],
            "clusters": list(graph["clusters"].keys()),
            "node_count": len(graph["nodes"]),
            "edge_count": len(graph["edges"])
        }

    # ==================== Sub-Agent Orchestration ====================
    @app.post("/api/orchestrate")
    async def orchestrate_tasks(request: OrchestrationRequest):
        """Generate sub-agent task assignments from graph"""
        try:
            if request.graph_id not in app.state.local_server.graphs:
                raise ValueError(f"Graph not found: {request.graph_id}")

            graph = app.state.local_server.graphs[request.graph_id]
            orchestrator = app.state.local_server.orchestrator

            # Generate tasks
            tasks = orchestrator.generate_subtasks(graph, request.parent_task)
            ordered_tasks = orchestrator.assign_task_order(tasks)

            # Create delegation contracts
            delegations = []
            for task in ordered_tasks:
                contract = orchestrator.create_delegation_contract(task, request.parent_task_id)
                delegations.append({
                    "task": task.to_dict(),
                    "delegation_contract": contract
                })

            return {
                "status": "success",
                "parent_task_id": request.parent_task_id,
                "graph_id": request.graph_id,
                "task_count": len(delegations),
                "tasks": delegations
            }

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error generating tasks: {str(e)}")

    @app.get("/api/tasks")
    async def list_tasks():
        """List all generated tasks"""
        tasks = []
        for graph_id, graph in app.state.local_server.graphs.items():
            for cluster_id, cluster in graph["clusters"].items():
                tasks.append({
                    "cluster_id": cluster_id,
                    "label": cluster["label"],
                    "confidence": cluster["confidence"],
                    "token_count": len(cluster["tokens"])
                })

        return {"tasks": tasks, "count": len(tasks)}

    # ==================== Analysis & Parsing ====================
    @app.post("/api/analyze")
    async def analyze_text(request: Dict[str, Any]):
        """Analyze text for semantic tokens and domains"""
        try:
            text = request.get("text", "")
            context = request.get("context", "")

            analyzer = app.state.local_server.semantic_analyzer
            tokens = analyzer.extract_semantic_tokens(text, context)
            domains = analyzer.classify_domains(tokens)

            return {
                "status": "success",
                "token_count": len(tokens),
                "tokens": [t.to_dict() for t in tokens[:15]],
                "domains": domains
            }

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error analyzing text: {str(e)}")

    return app


# Entry point
if __name__ == "__main__":
    import uvicorn
    import sys

    workspace = sys.argv[1] if len(sys.argv) > 1 else "."
    app = create_web_app(workspace)
    uvicorn.run(app, host="127.0.0.1", port=8001)
