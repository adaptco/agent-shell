#
# Ralph Wiggum Stateless Loop Orchestrator (Windows PowerShell)
#
# Usage:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser (if needed)
#   .\ralph.ps1
#
# This wrapper runs Ralph in a completely fresh process every iteration,
# eliminating accumulated context memory and ensuring deterministic behavior.
#

param(
    [string]$ProgressFile = "PROGRESS.md",
    [switch]$Verbose = $false
)

# Color functions for terminal output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProgressPath = Join-Path $ScriptDir $ProgressFile

Write-ColorOutput "🚀 Ralph Wiggum Stateless Loop Orchestrator" -Color Green
Write-ColorOutput "Booting infinite iteration cycle..." -Color Cyan
Write-ColorOutput ""

$Iteration = 0
$ContinueLoop = $true

while ($ContinueLoop) {
    $Iteration++
    Write-ColorOutput "🔄 Iteration #$Iteration" -Color Cyan
    Write-ColorOutput ""

    # Run Ralph in a completely isolated process
    # The Python interpreter exits entirely, shedding all context memory
    $RalphScript = Join-Path $ScriptDir "ralph.py"
    $Arguments = @("$RalphScript", "--progress", "$ProgressPath")
    
    if ($Verbose) {
        $Arguments += "--verbose"
    }

    $Process = Start-Process -FilePath "python.exe" `
        -ArgumentList $Arguments `
        -Wait `
        -NoNewWindow `
        -PassThru

    $Status = $Process.ExitCode

    Write-ColorOutput ""

    # Check exit status
    if ($Status -ne 0) {
        Write-ColorOutput "🛑 Loop interrupted or task queue completed." -Color Yellow
        Write-ColorOutput "Final state persisted in Git. Ralph is clocking out." -Color Cyan
        $ContinueLoop = $false
    } else {
        # Clean context reset between iterations
        Write-ColorOutput "♻️  Iteration clean. Dumping process memory cache..." -Color Cyan
        Start-Sleep -Seconds 1
        Write-ColorOutput ""
    }
}

Write-ColorOutput ""
Write-ColorOutput "✨ Ralph Loop Orchestrator Finished" -Color Green
Write-ColorOutput "Check Git log for full execution history:" -Color Cyan
Write-ColorOutput "  git log --oneline --grep 'ralph-loop'" -Color Yellow
Write-ColorOutput ""
