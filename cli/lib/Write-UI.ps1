<#
.SYNOPSIS
    Terminal UI helpers — headers, banners, mode hints, help screen, test indicators.

.DESCRIPTION
    Pure presentation functions. No business logic, no I/O beyond
    Write-Host. Expects $ProjectDir, $Modes, and $Steps to be set by the caller.
#>

function Write-Header {
    param([string]$Title)
    $line = "=" * 70
    Write-Host ""
    Write-Host $line -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host $line -ForegroundColor Cyan
}

function Write-SubHeader {
    param([string]$Title)
    $line = "-" * 70
    Write-Host ""
    Write-Host $line -ForegroundColor DarkGray
    Write-Host "  $Title" -ForegroundColor White
    Write-Host $line -ForegroundColor DarkGray
}

function Write-Banner {
    Clear-Host
    Write-Host ""
    Write-Host "  _____ _   _                 _       _  ___ _   " -ForegroundColor Magenta
    Write-Host " | ____| |_(_)_ __ ___   __ _| |_ ___| |/ (_) |_ " -ForegroundColor Magenta
    Write-Host " |  _| / __| | '_ ' _ \ / _' | __/ _ \ ' /| | __|" -ForegroundColor Magenta
    Write-Host " | |___\__ \ | | | | | | (_| | ||  __/ . \| | |_ " -ForegroundColor Magenta
    Write-Host " |_____|___/_|_| |_| |_|\__,_|\__\___|_|\_\_|\__|" -ForegroundColor Magenta
    Write-Host ""
    $projName = Split-Path $ProjectDir -Leaf
    Write-Host "  Project: $projName" -ForegroundColor DarkGray
    Write-Host ""
}

function Write-ModeHint {
    param([string]$ActiveMode)

    $flags = foreach ($key in $Modes.Keys) {
        if ($key -ne "(default)") { $Modes[$key].Flag }
    }

    Write-Host "  Mode:    " -NoNewline -ForegroundColor DarkGray
    Write-Host $ActiveMode -ForegroundColor White
    Write-Host "  Options: " -NoNewline -ForegroundColor DarkGray
    Write-Host ($flags -join "  ") -ForegroundColor DarkGray
    Write-Host "           -Phase <id>  -Verbose  -StopOnError  -Help" -ForegroundColor DarkGray
    Write-Host ""
}

function Write-TestStart {
    param([string]$Name)
    Write-Host ""
    Write-Host "  >> " -NoNewline -ForegroundColor Yellow
    Write-Host "Running: " -NoNewline -ForegroundColor Gray
    Write-Host $Name -ForegroundColor White
    Write-Host ""
}

function Write-TestResult {
    param([string]$Name, [bool]$Passed, [double]$Duration)

    if ($Passed) {
        Write-Host "  [PASS] " -NoNewline -ForegroundColor Green
        Write-Host "$Name " -NoNewline -ForegroundColor White
        Write-Host "PASSED" -NoNewline -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] " -NoNewline -ForegroundColor Red
        Write-Host "$Name " -NoNewline -ForegroundColor White
        Write-Host "FAILED" -NoNewline -ForegroundColor Red
    }
    Write-Host " (${Duration}s)" -ForegroundColor DarkGray
}

function Show-Help {
    <#
    .SYNOPSIS
        Render the help screen from the $Steps and $Modes registries.
    #>
    Write-Banner

    Write-Host "  Usage: ./Start [mode] [options]" -ForegroundColor White
    Write-Host ""
    Write-Host "  MODES" -ForegroundColor Cyan
    Write-Host "  -----" -ForegroundColor Cyan

    foreach ($key in $Modes.Keys) {
        $m    = $Modes[$key]
        $flag = $m.Flag.PadRight(14)
        Write-Host "    $flag " -NoNewline -ForegroundColor Yellow
        Write-Host $m.Description -ForegroundColor Gray

        $labels = ($m.Steps | ForEach-Object { $Steps[$_].Label }) -join " -> "
        Write-Host "                   $labels" -ForegroundColor DarkGray
    }

    Write-Host ""
    Write-Host "  OPTIONS" -ForegroundColor Cyan
    Write-Host "  -------" -ForegroundColor Cyan
    Write-Host "    -Project <path>" -NoNewline -ForegroundColor Yellow
    Write-Host "  Path to project directory" -ForegroundColor Gray
    Write-Host "    -Phase <id>    " -NoNewline -ForegroundColor Yellow
    Write-Host "  Phase the slide deck sells (needed when the project defines several)" -ForegroundColor Gray
    Write-Host "    -Verbose       " -NoNewline -ForegroundColor Yellow
    Write-Host "  Show full output from builds and tests" -ForegroundColor Gray
    Write-Host "    -StopOnError   " -NoNewline -ForegroundColor Yellow
    Write-Host "  Stop on first test failure" -ForegroundColor Gray
    Write-Host "    -Help          " -NoNewline -ForegroundColor Yellow
    Write-Host "  Show this help" -ForegroundColor Gray
    Write-Host ""
}
