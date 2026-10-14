<#
.SYNOPSIS
    Resolve the active project directory and set encoding defaults.

.DESCRIPTION
    Populates $ProjectDir (and derived $SlidesDir) from, in priority order:
      1. -Project parameter
      2. $env:ESTIMATEKIT_PROJECT
      3. First directory under projects/ containing project.yaml

    Also forces UTF-8 on the console, $OutputEncoding, and PYTHONIOENCODING.

    Expects $ModernRoot and $Project to be set by the caller.
#>

if ($Project) {
    $ProjectDir = (Resolve-Path $Project).Path
} elseif ($env:ESTIMATEKIT_PROJECT) {
    $ProjectDir = $env:ESTIMATEKIT_PROJECT
} else {
    $projectsRoot = Join-Path $ModernRoot "projects"
    $first = Get-ChildItem $projectsRoot -Directory -ErrorAction SilentlyContinue |
             Where-Object { Test-Path (Join-Path $_.FullName "project.yaml") } |
             Select-Object -First 1
    if ($first) { $ProjectDir = $first.FullName }
    else {
        Write-Host "  ERROR: No project found in projects/. Use -Project <path>." -ForegroundColor Red
        exit 1
    }
}

$SlidesDir = Join-Path (Join-Path $ProjectDir "output") "slides"

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding           = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING     = "utf-8"
