<#
.SYNOPSIS
    Build, test, and serve an EstimateKit project.

.DESCRIPTION
    Orchestrates artifact generation, test execution, and slide serving
    by consuming the engine's Python CLI adapter (estimatekit).

    Run with -Help to see all available modes and options.

    Infrastructure modules live in lib/, step functions in steps/.
    This file is the thin orchestrator that wires everything together.

.PARAMETER Project
    Path to the project directory (must contain project.yaml).
    Defaults to the first project found under projects/.

.PARAMETER Phase
    The phase the slide deck sells (for example P2). A project with one phase
    needs none; a project with several refuses to generate slides without it.

.NOTES
    EstimateKit CLI — Build & Validation
    Version: 1.0
#>

param(
    [string]$Project,
    [string]$Phase,
    [switch]$Help,
    [switch]$Init,
    [switch]$Test,
    [switch]$Build,
    [switch]$Full,
    [switch]$Run,
    [switch]$Summary,
    [switch]$Verbose,
    [switch]$StopOnError
)

# Paths — everything else derives from these
$ModernRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$EngineRoot = Join-Path $ModernRoot "engine"
$LibDir     = Join-Path $PSScriptRoot "lib"
$StepsDir   = Join-Path $PSScriptRoot "steps"

# Load infrastructure (lib/Common.ps1 sources all lib/* modules)
. (Join-Path $LibDir "Common.ps1")

# Load step functions
. (Join-Path $StepsDir "Step-Generate.ps1")
. (Join-Path $StepsDir "Step-Test.ps1")
. (Join-Path $StepsDir "Step-Init.ps1")
. (Join-Path $StepsDir "Step-Serve.ps1")
. (Join-Path $StepsDir "Step-Summary.ps1")

# Load registry (after steps, so dispatch table can reference Step-* functions)
. (Join-Path $LibDir "Registry.ps1")

# --- Dispatch ---------------------------------------------------------------

if ($Help) { Show-Help; exit 0 }

if ($Init) {
    Write-Banner
    Write-Header "Initialize New Project"
    Step-Init
    exit 0
}

# Mode selection (mutually exclusive)
$selected = @()
if ($Build)   { $selected += "Build" }
if ($Test)    { $selected += "Test" }
if ($Run)     { $selected += "Run" }
if ($Summary) { $selected += "Summary" }
if ($Full)    { $selected += "Full" }

if ($selected.Count -gt 1) {
    Write-Host ""
    Write-Host "  ERROR: Only one mode at a time. You specified: $($selected -join ', ')" -ForegroundColor Red
    Write-Host ""
    Show-Help
    exit 1
}

$activeModeName = if ($selected.Count -eq 1) { $selected[0] } else { "(default)" }
$activeMode     = $Modes[$activeModeName]
$stepsToRun     = $activeMode.Steps

Write-Banner
Write-ModeHint $activeModeName

# Split off Serve (blocking) so test summary can print first
$hasServe      = $stepsToRun -contains "Serve"
$nonBlockSteps = $stepsToRun | Where-Object { $_ -ne "Serve" }

foreach ($key in $nonBlockSteps) {
    & $StepFunctions[$key]
}

if ($script:TestResults.Count -gt 0) {
    Write-TestSummary
}

if ($hasServe) {
    & $StepFunctions["Serve"]
}

if ($script:TotalFailed -gt 0) { exit 1 } else { exit 0 }
