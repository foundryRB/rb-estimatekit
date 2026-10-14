<#
.SYNOPSIS
    Invoke the estimatekit Python CLI adapter.

.DESCRIPTION
    Handles Python discovery validation, working directory management,
    output capture, and exit-code propagation.
    Expects $script:PythonCmd, $ModernRoot, and $Verbose to be set.
#>

function Invoke-Engine {
    <#
    .SYNOPSIS
        Invoke the estimatekit Python CLI with the given command and arguments.
    .DESCRIPTION
        Returns $true on success, $false on failure.
    #>
    param(
        [Parameter(Mandatory)]
        [string]$Command,

        [string[]]$Arguments = @(),

        [string]$Label = ""
    )

    if (-not $script:PythonCmd) {
        Write-Host "  ! Python not found — install Python 3.10+ and ensure it's on PATH" -ForegroundColor Yellow
        return $false
    }

    $displayLabel = if ($Label) { $Label } else { $Command }
    Write-Host "  Running: $displayLabel..." -ForegroundColor Gray

    try {
        Push-Location $ModernRoot
        $allArgs = @("-m", "engine.adapters.inbound.cli", $Command) + $Arguments
        $out = & $script:PythonCmd @allArgs 2>&1 | Out-String
        $exitCode = $LASTEXITCODE
    } catch {
        $out = $_.Exception.Message
        $exitCode = 1
    } finally {
        Pop-Location -ErrorAction SilentlyContinue
    }

    if ($exitCode -eq 0) {
        Write-Host "  + $displayLabel completed" -ForegroundColor Green
        if ($Verbose -and $out.Trim()) {
            $out -split "`n" | ForEach-Object {
                if ($_.Trim()) { Write-Host "    $_" -ForegroundColor DarkGray }
            }
        }
    } else {
        Write-Host "  ! $displayLabel failed (exit code $exitCode)" -ForegroundColor Red
        $out -split "`n" | ForEach-Object {
            if ($_.Trim()) { Write-Host "    $_" -ForegroundColor DarkGray }
        }
    }

    return ($exitCode -eq 0)
}
