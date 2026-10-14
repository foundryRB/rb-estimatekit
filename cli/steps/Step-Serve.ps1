<#
.SYNOPSIS
    Launch the Slidev dev server for the active project.
#>

function Step-Serve {
    Write-Header "Slidev Dev Server"

    if (-not $script:NpmCmd) {
        Write-Host "  ! npm not found — install Node.js and ensure npm is on PATH" -ForegroundColor Yellow
        return
    }

    if (-not (Test-Path $SlidesDir)) {
        Write-Host "  ! Slides directory not found: $SlidesDir" -ForegroundColor Yellow
        Write-Host "    Run a build first to generate slides." -ForegroundColor DarkGray
        return
    }

    Write-Host "  Starting Slidev on http://localhost:3030 ..." -ForegroundColor Gray
    Write-Host "  Press Ctrl+C to stop" -ForegroundColor DarkGray
    Write-Host ""

    try {
        Push-Location $SlidesDir
        & $script:NpmCmd run dev
    } finally {
        Pop-Location -ErrorAction SilentlyContinue
    }
}
