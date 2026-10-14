<#
.SYNOPSIS
    Infrastructure loader (cli/lib/).

.DESCRIPTION
    Dot-sourced by Start.ps1 to initialize shared state and load the
    focused helper modules that live alongside it in cli/lib/:

        Resolve-Project.ps1    — project discovery + encoding setup
        Resolve-Tools.ps1      — Python/npm discovery
        Write-UI.ps1           — terminal UI helpers + Show-Help
        Invoke-Engine.ps1      — estimatekit CLI invocation
        Format-TestReport.ps1  — pytest parsing and reporting
        Registry.ps1           — step / mode / dispatch data

    Step functions live separately in cli/steps/.

    Expects $ModernRoot and $Project to be set by the caller.
    After sourcing, $ProjectDir, $SlidesDir, $Steps, $Modes,
    $StepFunctions, and tool paths are available.
#>

# Shared test-tracking state (script-scoped, visible to all modules)
if (-not (Get-Variable -Name TestResults -Scope Script -ErrorAction SilentlyContinue)) {
    $script:TestResults   = @()
    $script:TotalPassed   = 0
    $script:TotalFailed   = 0
    $script:AllTestCounts = @()
}

# Load focused modules
$_dir = Split-Path $MyInvocation.MyCommand.Path -Parent
. (Join-Path $_dir "Resolve-Project.ps1")
. (Join-Path $_dir "Resolve-Tools.ps1")
. (Join-Path $_dir "Write-UI.ps1")
. (Join-Path $_dir "Invoke-Engine.ps1")
. (Join-Path $_dir "Format-TestReport.ps1")
