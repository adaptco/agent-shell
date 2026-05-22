#!/usr/bin/env bash
# Quick start script for Knowledge Graph MCP System (macOS/Linux)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Starting Knowledge Graph MCP System..."
echo

# Check Python version
echo "📦 Checking Python version..."
python_version=$(python3 --version | cut -d' ' -f2)
echo "   Python $python_version"

# Create/activate venv
echo "📦 Setting up Python environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -q -r requirements.txt
pip install -q fastapi uvicorn httpx

# Check Node version
echo "📦 Checking Node.js version..."
node_version=$(node --version)
echo "   Node $node_version"

# Start services in background
echo
echo "🎯 Starting services..."
echo

# Start MCP Server
echo "   Starting MCP Server (Port 5100)..."
python -m app.mcp_knowledge_graph.server . &
MCP_PID=$!
sleep 2

# Start Web Backend
echo "   Starting Web Backend (Port 8001)..."
python -m app.web_ui.backend.app . &
BACKEND_PID=$!
sleep 2

# Start Web Frontend
echo "   Starting Web Frontend (Port 3000)..."
cd app/web_ui/frontend
if [ ! -d "node_modules" ]; then
    npm install -q
fi
npm run dev &
FRONTEND_PID=$!
sleep 2

# Start Agent-Shell API (optional)
echo "   Starting Agent-Shell API (Port 8000)..."
uvicorn runtime.api:create_app --factory --host 127.0.0.1 --port 8000 &
API_PID=$!

echo
echo "✨ All services started!"
echo
echo "Access points:"
echo "  🧠 Web UI:        http://127.0.0.1:3000"
echo "  🔌 Web Backend:   http://127.0.0.1:8001"
echo "  🛠️  MCP Server:    http://127.0.0.1:5100"
echo "  🔗 Agent-Shell:   http://127.0.0.1:8000"
echo
echo "Press Ctrl+C to stop all services"
echo

# Wait for interrupt
trap "
  echo
  echo '⛔ Stopping services...'
  kill $MCP_PID $BACKEND_PID $FRONTEND_PID $API_PID 2>/dev/null || true
  echo '✅ All services stopped'
  exit 0
" SIGINT

wait
