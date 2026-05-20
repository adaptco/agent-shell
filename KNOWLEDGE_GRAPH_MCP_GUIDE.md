# Knowledge Graph MCP System for Agent-Shell

## Overview

The Knowledge Graph MCP System is a comprehensive solution for semantic document analysis and multi-agent orchestration. It enables the Agent-Shell runtime to:

1. **Parse requirements documents** into semantic tokens and domain clusters
2. **Build knowledge graphs** representing expertise domains and relationships
3. **Generate sub-agent task assignments** based on semantic clustering
4. **Orchestrate complex workflows** by delegating tasks to specialized sub-agents

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Web UI (Port 3000)                 │
│          Document Upload | Graph Visualization              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Web Backend (FastAPI, Port 8001)               │
│    Document Management | Graph Operations | Analysis       │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────────┐   ┌────────────────────────┐
│ Local Server     │   │ Remote MCP Server      │
│ (Optional)       │   │ (Port 5100)            │
│                  │   │                        │
│ Semantic         │   │ Semantic Analysis      │
│ Analysis         │   │ Knowledge Graph        │
│ Orchestration    │   │ Sub-Agent Assignment   │
└──────────────────┘   └────────────────────────┘
        │                         │
        └────────────┬────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Agent-Shell Runtime (Port 8000)                │
│     Knowledge Graph Plugin | Task Queue | Sub-Agents        │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. MCP Knowledge Graph Server (`app/mcp_knowledge_graph/`)

**Semantic Analyzer** (`semantic_analyzer.py`)
- Extract semantic tokens from documents
- Classify domains (backend, frontend, devops, data, ml, security, testing, documentation)
- Create domain expertise clusters
- Build knowledge graphs with embeddings

**Orchestrator** (`orchestrator.py`)
- Generate sub-agent task assignments from clusters
- Create delegation contracts
- Determine task execution order
- Map expertise to sub-agent roles

**MCP Server** (`server.py`)
- FastAPI-based MCP endpoint (Port 5100)
- Tools: `parse_requirements`, `create_knowledge_graph`, `assign_expertise_clusters`
- REST API for tool execution
- Graph storage and retrieval

### 2. Web Application (`app/web_ui/`)

**Backend** (`backend/app.py`)
- FastAPI server (Port 8001)
- Document upload and management
- Graph creation and visualization
- Task generation
- Analysis endpoints

**Frontend** (`frontend/`)
- React + Vite SPA
- Document upload UI
- Graph visualization
- Task list and management
- Real-time analysis

### 3. Runtime Integration (`runtime/knowledge_graph_plugin.py`)

- Tool plugin for Agent-Shell runtime
- Local or remote MCP server support
- Seamless integration with task queue
- Sub-agent delegation via knowledge graph

## Deployment

### Local Development (Recommended for Testing)

#### Prerequisites
- Python 3.13+
- Node.js 24+
- Docker & Docker Compose (optional)

#### Step 1: Install Python Dependencies

```bash
cd path/to/agent-shell
python -m venv .venv
source .venv/Scripts/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
pip install fastapi uvicorn httpx  # Additional for web app
```

#### Step 2: Start MCP Server

```bash
python -m app.mcp_knowledge_graph.server .
# Server running on http://127.0.0.1:5100
```

#### Step 3: Start Web Backend

```bash
python -m app.web_ui.backend.app .
# Backend running on http://127.0.0.1:8001
```

#### Step 4: Start Web Frontend

```bash
cd app/web_ui/frontend
npm install
npm run dev
# Frontend running on http://127.0.0.1:3000
```

#### Step 5: Start Agent-Shell API (Optional)

```bash
uvicorn runtime.api:create_app --factory --host 127.0.0.1 --port 8000
# API running on http://127.0.0.1:8000
```

### Docker Deployment

```bash
# Build and run all services
docker-compose -f docker-compose.knowledge-graph.yml up --build

# Services:
# - MCP Server: http://127.0.0.1:5100
# - Web Backend: http://127.0.0.1:8001
# - Web Frontend: http://127.0.0.1:3000
# - Agent-Shell API: http://127.0.0.1:8000
```

## Usage

### Via Web UI (Recommended)

1. **Upload Documents**
   - Navigate to Documents tab
   - Upload requirements.txt, architecture docs, PRD, etc.
   - Preview document content

2. **Create Knowledge Graph**
   - Click "Create Knowledge Graph"
   - System extracts semantic tokens
   - Builds clusters for each expertise domain

3. **Visualize Graph**
   - Navigate to Graph tab
   - View nodes (clusters) and edges (relationships)
   - See expertise classification

4. **Generate Sub-Agent Tasks**
   - Click "Generate Sub-Agent Tasks"
   - System creates assignments for BackendAgent, FrontendAgent, etc.
   - View task descriptions and delegation contracts

5. **Analyze Text**
   - Navigate to Analyze tab
   - Paste requirements or code snippets
   - See domain classification and extracted tokens

### Via Agent-Shell Runtime

```python
from runtime.knowledge_graph_plugin import KnowledgeGraphPlugin

# In runtime config
plugin = KnowledgeGraphPlugin({
    "mcp_server_url": "http://127.0.0.1:5100",
    "use_local_server": False,
    "_workspace": "."
})

# Use in agent loop
result = plugin.execute("build_knowledge_graph", {
    "documents": {
        "requirements.md": open("requirements.md").read(),
        "architecture.md": open("architecture.md").read()
    },
    "graph_id": "my_project_graph"
})

tasks_result = plugin.execute("generate_subtasks", {
    "graph_id": "my_project_graph",
    "parent_task": "Build software from requirements",
    "parent_task_id": "task_001"
})
```

### Via MCP API

```bash
# Parse requirements
curl -X POST http://127.0.0.1:5100/tool/parse_requirements \
  -H "Content-Type: application/json" \
  -d '{
    "document_text": "We need a REST API...",
    "document_name": "api_requirements.md"
  }'

# Create knowledge graph
curl -X POST http://127.0.0.1:5100/tool/create_knowledge_graph \
  -H "Content-Type: application/json" \
  -d '{
    "documents": {
      "requirements.md": "...content...",
      "architecture.md": "...content..."
    },
    "graph_id": "my_graph"
  }'

# Generate sub-agent tasks
curl -X POST http://127.0.0.1:5100/tool/assign_expertise_clusters \
  -H "Content-Type: application/json" \
  -d '{
    "graph_id": "my_graph",
    "parent_task": "Build the system",
    "parent_task_id": "parent_001"
  }'
```

## Semantic Domains

The system recognizes and categorizes the following expertise domains:

| Domain | Keywords | Sub-Agent | Use Case |
|--------|----------|-----------|----------|
| **backend** | api, server, database, sql, orm, auth | BackendAgent | API/service implementation |
| **frontend** | ui, react, vue, css, html, js | FrontendAgent | UI component development |
| **devops** | docker, kubernetes, ci/cd, terraform | DevOpsAgent | Infrastructure & deployment |
| **data** | analytics, data lake, etl, pipeline | DataAgent | Data processing & analysis |
| **ml** | model, training, neural, nlp | MLAgent | ML model development |
| **security** | auth, encryption, oauth, compliance | SecurityAgent | Security implementation |
| **testing** | unit test, e2e, mock, coverage | TestingAgent | Test suite development |
| **documentation** | readme, api docs, guide, spec | DocumentationAgent | Technical documentation |

## Configuration

### MCP Server Configuration

In `mcp_servers.json`:

```json
{
  "id": "knowledge-graph-mcp",
  "name": "Knowledge Graph MCP Server",
  "type": "http",
  "url": "http://127.0.0.1:5100",
  "auth": { "type": "none" },
  "trust": "explicit",
  "connection": {
    "timeout_seconds": 30,
    "pool_size": 4
  }
}
```

### Runtime Configuration

In `runtime/config.yaml` or environment:

```yaml
tools:
  knowledge_graph:
    enabled: true
    mcp_server_url: "http://127.0.0.1:5100"
    use_local_server: false
    embedding_dim: 128
```

## API Endpoints

### MCP Server (Port 5100)

- `GET /health` - Health check
- `GET /tools` - List available tools
- `POST /tool/{tool_name}` - Execute tool
- `GET /graphs` - List all graphs
- `GET /graphs/{graph_id}` - Get specific graph

### Web Backend (Port 8001)

- `POST /api/documents/upload` - Upload document
- `GET /api/documents` - List documents
- `GET /api/documents/{filename}` - Get document
- `POST /api/graph/create` - Create graph
- `GET /api/graphs` - List graphs
- `GET /api/graphs/{graph_id}` - Get graph
- `POST /api/orchestrate` - Generate tasks
- `POST /api/analyze` - Analyze text
- `GET /health` - Health check

## Example Workflow

### Scenario: Build a Multi-Feature SaaS Application

1. **Upload Requirements**
   - `requirements.md` - Features and acceptance criteria
   - `architecture.md` - System design and components
   - `database_schema.sql` - Data model
   - `api_spec.yaml` - REST API specification

2. **Create Graph**
   - System extracts ~200 semantic tokens
   - Creates clusters: backend (API), frontend (UI), devops (k8s), data (queries)
   - Identifies relationships: API depends on database, UI calls API

3. **Generate Tasks**
   - BackendAgent: "Implement REST API endpoints for user management"
   - FrontendAgent: "Build authentication UI components"
   - DataAgent: "Design and optimize database queries"
   - DevOpsAgent: "Configure Kubernetes deployments"
   - TestingAgent: "Create integration tests for API"
   - DocumentationAgent: "Write API documentation"

4. **Orchestrate**
   - Tasks assigned with priorities and dependencies
   - DevOpsAgent runs first (infrastructure)
   - DataAgent runs second (schema)
   - BackendAgent and FrontendAgent run in parallel
   - TestingAgent runs after services are ready
   - DocumentationAgent runs last

## Performance Considerations

### Embedding Model
- Uses lightweight hash-based embeddings (no ML dependencies)
- Configurable dimension (default: 128)
- Deterministic and reproducible
- Fast computation (<1ms per token)

### Scalability
- In-memory graph storage (suitable for documents up to 100MB)
- Supports clustering merge to reduce node count
- Token extraction uses regex patterns (optimized)

### Optimization Tips
1. **Split large documents** into smaller files (< 5MB each)
2. **Use descriptive filenames** to preserve context
3. **Reuse graphs** when analyzing related documents
4. **Monitor task count** to avoid sub-agent overload

## Troubleshooting

### MCP Server Won't Start
```bash
# Check Python version
python --version  # Should be 3.13+

# Verify imports
python -c "from app.mcp_knowledge_graph import MCPKnowledgeGraphServer"

# Check port availability
netstat -an | grep 5100
```

### Web Backend Connection Issues
```bash
# Test MCP connectivity
curl http://127.0.0.1:5100/health

# Check environment variables
echo $MCP_SERVER_URL
```

### Frontend Not Rendering
```bash
# Clear cache and reinstall
cd app/web_ui/frontend
rm -rf node_modules package-lock.json
npm install

# Check Vite config
cat vite.config.js
```

## Future Enhancements

1. **Advanced Embeddings**
   - Integrate sentence-transformers
   - Fine-tune on domain-specific corpora
   - Support multi-language documents

2. **Graph Visualization**
   - D3.js or Cytoscape.js integration
   - Interactive node exploration
   - Real-time graph updates

3. **Persistent Storage**
   - PostgreSQL/MongoDB for graphs
   - Document versioning
   - Audit trail of modifications

4. **Advanced Orchestration**
   - Dynamic task adjustment based on results
   - Cost optimization (monetary or computational)
   - Parallel task batching

5. **Integration with Agent-Shell**
   - Automatic MCP registration
   - Hook system for knowledge graph events
   - Task feedback loop to refine assignments

## References

- [Agent-Shell Runtime](../RUNTIME_HARNESS_CONTRACTS.md)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Docker Compose Reference](https://docs.docker.com/compose/)

## License

Part of the Agent-Shell project. See main LICENSE file.
