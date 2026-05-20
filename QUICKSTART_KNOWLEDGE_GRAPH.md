# Quick Start: Knowledge Graph MCP System

## 5-Minute Setup

### Option 1: PowerShell (Windows)

```powershell
cd C:\Users\eqhsp\Agent Projects\agent-shell
PowerShell -ExecutionPolicy RemoteSigned -File scripts\start-knowledge-graph.ps1
```

This will:
1. ✅ Activate Python venv
2. ✅ Install dependencies
3. ✅ Start MCP Server (Port 5100)
4. ✅ Start Web Backend (Port 8001)
5. ✅ Start Web Frontend (Port 3000)
6. ✅ Start Agent-Shell API (Port 8000)

Then open: **http://127.0.0.1:3000**

### Option 2: Bash (macOS/Linux)

```bash
cd /path/to/agent-shell
chmod +x scripts/start-knowledge-graph.sh
bash scripts/start-knowledge-graph.sh
```

Then open: **http://127.0.0.1:3000**

### Option 3: Docker (All Platforms)

```bash
cd /path/to/agent-shell
docker-compose -f docker-compose.knowledge-graph.yml up --build
```

Access:
- 🧠 Web UI: http://127.0.0.1:3000
- 🔌 Backend: http://127.0.0.1:8001
- 🛠️  MCP Server: http://127.0.0.1:5100
- 🔗 Agent-Shell: http://127.0.0.1:8000

---

## Manual Setup (For Development)

### Prerequisites
- Python 3.13+
- Node.js 24+

### Step 1: Python Environment

```bash
cd C:\Users\eqhsp\Agent Projects\agent-shell

# Create venv
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install packages
pip install -r requirements.txt
pip install fastapi uvicorn httpx
```

### Step 2: Terminal 1 - MCP Server

```bash
python -m app.mcp_knowledge_graph.server .
# Output: Uvicorn running on http://127.0.0.1:5100
```

### Step 3: Terminal 2 - Web Backend

```bash
python -m app.web_ui.backend.app .
# Output: Uvicorn running on http://127.0.0.1:8001
```

### Step 4: Terminal 3 - Web Frontend

```bash
cd app\web_ui\frontend  # or app/web_ui/frontend on Unix

npm install
npm run dev
# Output: Vite running on http://127.0.0.1:3000
```

### Step 5: Terminal 4 (Optional) - Agent-Shell API

```bash
uvicorn runtime.api:create_app --factory --host 127.0.0.1 --port 8000
# Output: Uvicorn running on http://127.0.0.1:8000
```

---

## Verify Installation

### Check All Services

```bash
# Terminal 1: MCP Server
curl http://127.0.0.1:5100/health
# Expected: {"status":"healthy","service":"knowledge-graph-mcp"}

# Terminal 2: Web Backend
curl http://127.0.0.1:8001/health
# Expected: {"status":"healthy","service":"knowledge-graph-web"}

# Terminal 3: Web Frontend
# Open browser: http://127.0.0.1:3000

# Terminal 4: Agent-Shell API
curl http://127.0.0.1:8000/tasks
# Expected: {"tasks": [], "completed_tasks": []}
```

---

## Example Workflow

### 1. Create a Test Document

Create `documents/requirements.md`:

```markdown
# SaaS Platform Requirements

## Backend Services
- REST API for user authentication (JWT)
- PostgreSQL database for user management
- Redis caching layer
- Message queue for async jobs

## Frontend Application
- React-based dashboard
- Real-time notifications with WebSocket
- Mobile-responsive design
- Dark mode support

## DevOps & Infrastructure
- Docker containerization
- Kubernetes deployment
- CI/CD pipeline with GitHub Actions
- SSL/TLS security

## Data Pipeline
- ETL jobs for analytics
- BigQuery warehouse
- Daily aggregations

## Testing
- Unit tests (Jest)
- Integration tests (Pytest)
- E2E tests (Playwright)

## Documentation
- API reference with Swagger
- Architecture decision records
- Runbook for operations
```

### 2. Open Web UI

Browse to: **http://127.0.0.1:3000**

### 3. Upload Document

1. Go to "Documents" tab
2. Click file input
3. Select `documents/requirements.md`
4. Click "Upload Document"

### 4. Create Knowledge Graph

1. Click "Create Knowledge Graph"
2. Wait for completion
3. View nodes and edges

### 5. Generate Sub-Agent Tasks

1. Go to "Graph" tab
2. Select the graph
3. Click "Generate Sub-Agent Tasks"
4. Review delegation contracts

### 6. Analyze Further (Optional)

1. Go to "Analyze" tab
2. Paste any text snippet
3. See domain classification and tokens

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
netstat -ano | findstr :5100  # Windows
lsof -i :5100  # macOS/Linux

# Kill process
taskkill /PID <PID> /F  # Windows
kill -9 <PID>  # macOS/Linux
```

### Module Not Found Error

```bash
# Reinstall with editable install
pip install -e .

# Or directly
pip install -e .[test]
```

### Frontend Build Issues

```bash
# Clear cache and rebuild
cd app/web_ui/frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### MCP Server Connection Failed

```bash
# Check if server is running
curl -v http://127.0.0.1:5100/health

# Try with longer timeout
python -m app.mcp_knowledge_graph.server . --timeout 60
```

---

## Next Steps

### Integration with Agent-Shell

See [KNOWLEDGE_GRAPH_MCP_GUIDE.md](../KNOWLEDGE_GRAPH_MCP_GUIDE.md) for:
- Runtime configuration
- MCP server registration
- Tool plugin usage
- Advanced workflows

### Production Deployment

Use Docker Compose:
```bash
docker-compose -f docker-compose.knowledge-graph.yml up -d
```

### Custom Domains

Edit semantic domains in `app/mcp_knowledge_graph/semantic_analyzer.py`:

```python
DOMAIN_KEYWORDS = {
    "custom_domain": ["keyword1", "keyword2", ...],
    # ... other domains
}
```

---

## API Examples

### Via cURL

```bash
# Parse requirements
curl -X POST http://127.0.0.1:5100/tool/parse_requirements \
  -H "Content-Type: application/json" \
  -d '{
    "document_text": "Build a REST API with authentication",
    "document_name": "api_requirements.md"
  }'

# Create graph
curl -X POST http://127.0.0.1:8001/api/graph/create \
  -H "Content-Type: application/json" \
  -d '{
    "documents": {
      "req.md": "Build a REST API..."
    },
    "graph_id": "my_graph"
  }'

# Generate tasks
curl -X POST http://127.0.0.1:8001/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "graph_id": "my_graph",
    "parent_task": "Build the system",
    "parent_task_id": "task_001"
  }'
```

### Via Python

```python
import httpx

# Create client
client = httpx.Client(base_url="http://127.0.0.1:8001")

# Upload and create graph
docs = {
    "requirements.md": open("requirements.md").read(),
}

response = client.post("/api/graph/create", json={
    "documents": docs,
    "graph_id": "my_project"
})

graph = response.json()
print(f"Created graph with {graph['node_count']} nodes")

# Generate tasks
response = client.post("/api/orchestrate", json={
    "graph_id": "my_project",
    "parent_task": "Implement the system",
    "parent_task_id": "main_task"
})

tasks = response.json()
for task in tasks["tasks"]:
    print(f"- {task['task']['assigned_subagent']}: {task['task']['task_description']}")
```

---

## Support

For issues or questions:
1. Check [KNOWLEDGE_GRAPH_MCP_GUIDE.md](../KNOWLEDGE_GRAPH_MCP_GUIDE.md)
2. Review service logs (check terminal windows)
3. Test endpoints with `curl` or Postman
4. Check port availability with `netstat`

---

**Happy orchestrating! 🚀**
