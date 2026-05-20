# Quick start script for Knowledge Graph MCP System (Windows)
# Run: PowerShell -ExecutionPolicy RemoteSigned -File scripts\start-knowledge-graph.ps1

param(
    [switch]$StopAll = $false
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir\..

Write-Host "🚀 Starting Knowledge Graph MCP System..." -ForegroundColor Green
Write-Host

# Check Python version
Write-Host "📦 Checking Python version..." -ForegroundColor Cyan
$pythonVersion = & python --version 2>&1
Write-Host "   $pythonVersion"

# Create/activate venv
Write-Host "📦 Setting up Python environment..." -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& ".venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Cyan
pip install -q -r requirements.txt
pip install -q fastapi uvicorn httpx

# Check Node version
Write-Host "📦 Checking Node.js version..." -ForegroundColor Cyan
$nodeVersion = & node --version
Write-Host "   Node $nodeVersion"

Write-Host
Write-Host "🎯 Starting services..." -ForegroundColor Green
Write-Host

# Create a helper script to run in background
$runScript = {
    param($command, $workDir)
    if ($workDir) {
        Set-Location $workDir
    }
    Invoke-Expression $command
}

# Start MCP Server
Write-Host "   Starting MCP Server (Port 5100)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$pwd'; python -m app.mcp_knowledge_graph.server ."
) -WindowStyle Normal

Start-Sleep -Seconds 2

# Start Web Backend
Write-Host "   Starting Web Backend (Port 8001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$pwd'; python -m app.web_ui.backend.app ."
) -WindowStyle Normal

Start-Sleep -Seconds 2

# Start Web Frontend
Write-Host "   Starting Web Frontend (Port 3000)..." -ForegroundColor Yellow
$frontendDir = Join-Path $pwd "app\web_ui\frontend"
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$frontendDir'; if (-not (Test-Path 'node_modules')) { npm install }; npm run dev"
) -WindowStyle Normal

Start-Sleep -Seconds 2

# Start Agent-Shell API
Write-Host "   Starting Agent-Shell API (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$pwd'; uvicorn runtime.api:create_app --factory --host 127.0.0.1 --port 8000"
) -WindowStyle Normal

Write-Host
Write-Host "✨ All services started!" -ForegroundColor Green
Write-Host
Write-Host "Access points:" -ForegroundColor Cyan
Write-Host "  🧠 Web UI:        http://127.0.0.1:3000" -ForegroundColor White
Write-Host "  🔌 Web Backend:   http://127.0.0.1:8001" -ForegroundColor White
Write-Host "  🛠️  MCP Server:    http://127.0.0.1:5100" -ForegroundColor White
Write-Host "  🔗 Agent-Shell:   http://127.0.0.1:8000" -ForegroundColor White
Write-Host
Write-Host "To stop services, close the PowerShell windows or run: Ctrl+C" -ForegroundColor Yellow
Write-Host

Read-Host "Press Enter to continue (services will keep running in separate windows)"
