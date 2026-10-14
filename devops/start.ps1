# estimatekit - local native launcher (no Docker).
#
# Starts the FastAPI backend (127.0.0.1:8000) and the Vite frontend (localhost:3000)
# in their own PowerShell windows, each with a descriptive title. First run creates
# the backend venv + installs deps, and installs the frontend deps.
#
# The Vite dev server proxies /api to the backend, so both must run. For a one-shot
# containerised run instead, use devops/docker-compose.yml.
#
# Run by double-clicking start.bat, or:
#   powershell -ExecutionPolicy Bypass -File devops\start.ps1

$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $PSScriptRoot
$web = Join-Path $repo 'web'
$py = Join-Path $repo '.venv\Scripts\python.exe'

Write-Host '== estimatekit (FastAPI + Vite, native) ==' -ForegroundColor Cyan

# Backend venv + deps (first run only).
if (-not (Test-Path $py)) {
    Write-Host 'First run: creating backend venv and installing deps...'
    python -m venv (Join-Path $repo '.venv')
    & $py -m pip install --quiet -e "$repo[http,dev]"
}

# Frontend deps (first run only).
if (-not (Test-Path (Join-Path $web 'node_modules'))) {
    Write-Host 'First run: installing frontend deps...'
    Push-Location $web
    npm install
    Pop-Location
}

Write-Host 'Backend  -> http://127.0.0.1:8000   (/api, /docs)' -ForegroundColor Green
Start-Process pwsh -ArgumentList '-NoExit', '-Command',
    "`$Host.UI.RawUI.WindowTitle = 'estimatekit backend (:8000)'; & '$py' -m uvicorn engine.adapters.inbound.http.app:create_app --factory --port 8000 --reload" `
    -WorkingDirectory $repo

Write-Host 'Frontend -> http://localhost:3000' -ForegroundColor Green
Start-Process pwsh -ArgumentList '-NoExit', '-Command',
    "`$Host.UI.RawUI.WindowTitle = 'estimatekit frontend (:3000)'; npm run dev" `
    -WorkingDirectory $web

Start-Sleep -Seconds 5
Start-Process 'http://localhost:3000'
Write-Host 'Started. Two PowerShell windows host the servers; close them to stop.' -ForegroundColor Green
