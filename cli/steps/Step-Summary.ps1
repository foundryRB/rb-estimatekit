<#
.SYNOPSIS
    Show a lightweight project summary via the engine.
#>

function Step-Summary {
    Write-Header "Project Summary"

    $success = Invoke-Engine -Command "summary" -Arguments @($ProjectDir) -Label "Project summary"

    if (-not $success) {
        Write-Host "  Could not load project summary." -ForegroundColor Yellow
    }
}
