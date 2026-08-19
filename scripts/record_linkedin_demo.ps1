<#
Starts the NEXUS demonstrator and records the entire desktop to a local MP4.

Before running: close personal windows and disable notifications. Press Ctrl+C in this terminal
to finish recording. The video remains local and is ignored by Git.
#>

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$videoDirectory = Join-Path $projectRoot "artifacts\videos"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outputPath = Join-Path $videoDirectory "nexus-ai-ops-demo-$timestamp.mp4"
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$ffmpeg = "ffmpeg.exe"

if (-not (Test-Path $python)) {
    throw "Python virtual environment not found at $python"
}

New-Item -ItemType Directory -Force -Path $videoDirectory | Out-Null

Push-Location $projectRoot
try {
    docker compose up -d postgres
    & $python scripts\run_demo.py
    docker compose --profile observability up -d

    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$projectRoot'; & '$python' -m uvicorn nexus.api.app:app --reload"
    )
    Start-Sleep -Seconds 4
    Start-Process "http://localhost:3000/d/nexus-api-overview"
    Start-Process "http://localhost:8000/docs"

    Write-Host "Recording started: $outputPath"
    Write-Host "Show the terminal, Grafana, and FastAPI docs. Press Ctrl+C here to stop."
    & $ffmpeg -f gdigrab -framerate 30 -i desktop -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p $outputPath
}
finally {
    Pop-Location
}
