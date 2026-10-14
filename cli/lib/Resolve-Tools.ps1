<#
.SYNOPSIS
    Discover Python and npm on the PATH.

.DESCRIPTION
    Probes for Python and npm once at startup and stores the results
    in script-scoped variables shared with all other scripts.
#>

function Find-Tool {
    param([string[]]$Candidates)
    foreach ($cmd in $Candidates) {
        try { $null = & $cmd --version 2>&1; return $cmd } catch {}
    }
    return $null
}

$script:PythonCmd = Find-Tool @("python", "python3", "py")
$script:NpmCmd    = Find-Tool @("npm", "npm.cmd")
