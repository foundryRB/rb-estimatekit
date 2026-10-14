<#
.SYNOPSIS
    Scaffold a new EstimateKit project from templates via the engine.
#>

function Step-Init {
    if (-not $script:PythonCmd) {
        Write-Host "  ! Python not found" -ForegroundColor Yellow
        return
    }

    $slug = Read-Host "  Project slug (e.g. my-new-project)"
    if (-not $slug) {
        Write-Host "  ERROR: No slug provided" -ForegroundColor Red
        return
    }

    $projectsRoot = Join-Path $ModernRoot "projects"
    $success = Invoke-Engine -Command "scaffold" -Arguments @($projectsRoot, $slug) -Label "Scaffold project '$slug'"

    if ($success) {
        Write-Host ""
        Write-Host "  Project created at: projects/$slug/" -ForegroundColor Green
        Write-Host "  Next: ./Start -Project projects/$slug" -ForegroundColor DarkGray
    }
}
