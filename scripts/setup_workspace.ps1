$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root


$requiredNodeMajor = 24
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
  throw "Node.js v24 is required but 'node' is not available on PATH."
}

$nodeVersionRaw = (& $node.Source -v).Trim()
$nodeVersion = $nodeVersionRaw.TrimStart('v')
$nodeMajor = [int]($nodeVersion.Split('.')[0])
if ($nodeMajor -ne $requiredNodeMajor) {
  throw "Node.js v24 is required, found $nodeVersionRaw."
}

$python = Get-Command py -ErrorAction SilentlyContinue
if (-not $python) {
  $python = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $python) {
  throw "Neither 'py' nor 'python' is available on PATH."
}

$venvPath = Join-Path $root ".venv"
if (-not (Test-Path $venvPath)) {
  & $python.Source -m venv .venv
}

$activate = Join-Path $venvPath "Scripts\Activate.ps1"
. $activate

python -m pip install --upgrade pip
python -m pip install -e .

Write-Host "Workspace is ready."
Write-Host "Run: agent-shell doctor"
Write-Host "Run: agent-shell serve-api --host 127.0.0.1 --port 8000"
Write-Host "Node.js version: $nodeVersionRaw"
