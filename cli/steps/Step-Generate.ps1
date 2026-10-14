<#
.SYNOPSIS
    Generate all project outputs (roadmap, excel, slides) via the engine.

.DESCRIPTION
    The slide deck sells one phase. $Phase (the -Phase parameter) names it;
    a single-phase project needs none, and the engine refuses slides on a
    multi-phase project without it, listing the phases to choose from.
#>

function Step-Generate {
    Write-Header "Generate Outputs"

    $args = @($ProjectDir)
    if ($Phase) { $args += @("--phase", $Phase) }
    if ($Verbose) { $args = @("--verbose") + $args }

    $label = if ($Phase) { "Generate all outputs (deck for $Phase)" } else { "Generate all outputs" }
    $success = Invoke-Engine -Command "generate" -Arguments $args -Label $label

    if (-not $success -and $StopOnError) {
        Write-Host "  Stopping on error (-StopOnError)" -ForegroundColor Yellow
        exit 1
    }
}
