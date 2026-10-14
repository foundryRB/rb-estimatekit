<#
.SYNOPSIS
    Parse pytest output and render grouped test reports.

.DESCRIPTION
    Provides Parse-PytestVerbose (structured parsing of pytest -v output),
    Write-PytestReport (grouped table display), and Write-TestSummary
    (end-of-run aggregate report).
    Expects $script:TestResults, $script:TotalPassed, $script:TotalFailed,
    $script:AllTestCounts, and $Verbose to be set by the caller.
#>

function Parse-PytestVerbose {
    <#
    .SYNOPSIS
        Parse pytest -v output into structured per-group results.
    #>
    param([string]$RawOutput)

    $groups      = [ordered]@{}
    $failedTests = @()
    $pattern     = '^.*?engine/tests/([^/]+)/\S+::\S+\s+(PASSED|FAILED|SKIPPED|ERROR|XFAIL|XPASS)'

    foreach ($line in ($RawOutput -split "`n")) {
        if ($line -match $pattern) {
            $group  = $Matches[1]
            $status = $Matches[2]
            if (-not $groups.Contains($group)) {
                $groups[$group] = @{ Passed = 0; Failed = 0; Skipped = 0; Errors = 0; Total = 0 }
            }
            $groups[$group].Total++
            switch ($status) {
                'PASSED' { $groups[$group].Passed++ }
                'FAILED' { $groups[$group].Failed++; $failedTests += $line.Trim() }
                'XFAIL'  { $groups[$group].Passed++ }
                'XPASS'  { $groups[$group].Failed++ }
                'SKIPPED'{ $groups[$group].Skipped++ }
                'ERROR'  { $groups[$group].Errors++;  $failedTests += $line.Trim() }
            }
        }
    }

    # Summary line: "101 passed, 1 failed, 2 skipped in 1.72s"
    $summaryLine = ""
    $pytestTime  = ""
    foreach ($line in ($RawOutput -split "`n")) {
        if ($line -match '=+\s+([\d].*?)\s+in\s+([\d.]+s)') {
            $summaryLine = $Matches[1]
            $pytestTime  = $Matches[2]
        }
    }

    $sPassed = 0; $sFailed = 0; $sSkipped = 0; $sErrors = 0; $sDeselected = 0; $sWarnings = 0
    if ($summaryLine -match '(\d+)\s+passed')     { $sPassed     = [int]$Matches[1] }
    if ($summaryLine -match '(\d+)\s+failed')      { $sFailed     = [int]$Matches[1] }
    if ($summaryLine -match '(\d+)\s+skipped')     { $sSkipped    = [int]$Matches[1] }
    if ($summaryLine -match '(\d+)\s+error')       { $sErrors     = [int]$Matches[1] }
    if ($summaryLine -match '(\d+)\s+deselected')  { $sDeselected = [int]$Matches[1] }
    if ($summaryLine -match '(\d+)\s+warning')     { $sWarnings   = [int]$Matches[1] }

    return [PSCustomObject]@{
        Groups      = $groups
        FailedTests = $failedTests
        Passed      = $sPassed
        Failed      = $sFailed
        Skipped     = $sSkipped
        Errors      = $sErrors
        Deselected  = $sDeselected
        Warnings    = $sWarnings
        Total       = $sPassed + $sFailed + $sSkipped + $sErrors
        PytestTime  = $pytestTime
    }
}

function Write-PytestReport {
    <#
    .SYNOPSIS
        Display a compact, grouped test report from parsed pytest output.
    #>
    param(
        [PSCustomObject]$Parsed,
        [string]$RawOutput,
        [bool]$ShowVerbose = $false
    )

    if ($ShowVerbose) {
        $RawOutput -split "`n" | ForEach-Object {
            if ($_.Trim()) {
                $c = if ($_ -match 'PASSED')                { "Green" }
                     elseif ($_ -match 'FAILED|ERROR')      { "Red" }
                     elseif ($_ -match 'SKIPPED')            { "DarkYellow" }
                     elseif ($_ -match 'warning|WARNING')    { "Yellow" }
                     else                                    { "DarkGray" }
                Write-Host "    $_" -ForegroundColor $c
            }
        }
        Write-Host ""
    }

    # Grouped summary table
    Write-Host ""
    $nameWidth = 16
    Write-Host "  $("Group".PadRight($nameWidth))  Pass  Fail  Skip  Total" -ForegroundColor DarkGray
    Write-Host "  $("-" * $nameWidth)  ----  ----  ----  -----" -ForegroundColor DarkGray

    foreach ($key in $Parsed.Groups.Keys) {
        $g       = $Parsed.Groups[$key]
        $label   = $key.PadRight($nameWidth)
        $pStr    = "$($g.Passed)".PadLeft(4)
        $fStr    = "$($g.Failed + $g.Errors)".PadLeft(4)
        $sStr    = "$($g.Skipped)".PadLeft(4)
        $tStr    = "$($g.Total)".PadLeft(5)

        Write-Host "  " -NoNewline
        if ($g.Failed -gt 0 -or $g.Errors -gt 0) {
            Write-Host $label -NoNewline -ForegroundColor Red
        } else {
            Write-Host $label -NoNewline -ForegroundColor Green
        }
        Write-Host "  $pStr" -NoNewline -ForegroundColor Green
        if ($g.Failed -gt 0 -or $g.Errors -gt 0) {
            Write-Host "  $fStr" -NoNewline -ForegroundColor Red
        } else {
            Write-Host "  $fStr" -NoNewline -ForegroundColor DarkGray
        }
        if ($g.Skipped -gt 0) {
            Write-Host "  $sStr" -NoNewline -ForegroundColor DarkYellow
        } else {
            Write-Host "  $sStr" -NoNewline -ForegroundColor DarkGray
        }
        Write-Host "  $tStr" -ForegroundColor White
    }

    # Totals row
    $allP = 0; $allF = 0; $allS = 0; $allT = 0
    foreach ($g in $Parsed.Groups.Values) {
        $allP += $g.Passed
        $allF += $g.Failed + $g.Errors
        $allS += $g.Skipped
        $allT += $g.Total
    }
    Write-Host "  $("-" * $nameWidth)  ----  ----  ----  -----" -ForegroundColor DarkGray
    Write-Host "  $("TOTAL".PadRight($nameWidth))" -NoNewline -ForegroundColor White
    Write-Host "  $("$allP".PadLeft(4))" -NoNewline -ForegroundColor Green
    if ($allF -gt 0) {
        Write-Host "  $("$allF".PadLeft(4))" -NoNewline -ForegroundColor Red
    } else {
        Write-Host "  $("$allF".PadLeft(4))" -NoNewline -ForegroundColor DarkGray
    }
    Write-Host "  $("$allS".PadLeft(4))" -NoNewline -ForegroundColor DarkGray
    Write-Host "  $("$allT".PadLeft(5))" -NoNewline -ForegroundColor White
    Write-Host "  ($($Parsed.PytestTime))" -ForegroundColor DarkGray

    $notes = @()
    if ($Parsed.Deselected -gt 0) { $notes += "$($Parsed.Deselected) deselected" }
    if ($Parsed.Warnings -gt 0)   { $notes += "$($Parsed.Warnings) warnings" }
    if ($notes.Count -gt 0) {
        Write-Host "  ($($notes -join ', '))" -ForegroundColor DarkYellow
    }

    if ($Parsed.FailedTests.Count -gt 0 -and -not $ShowVerbose) {
        Write-Host ""
        Write-Host "  Failed:" -ForegroundColor Red
        foreach ($ft in $Parsed.FailedTests) {
            $short = $ft -replace '.*?::', ''
            Write-Host "    x $short" -ForegroundColor Red
        }
    }

    Write-Host ""
}

function Write-TestSummary {
    $stepCount   = $script:TestResults.Count
    $stepsPassed = $script:TotalPassed
    $stepsFailed = $script:TotalFailed
    $duration    = ($script:TestResults | Measure-Object -Property Duration -Sum).Sum

    $realPassed  = ($script:AllTestCounts | Measure-Object -Property Passed -Sum).Sum
    $realFailed  = ($script:AllTestCounts | Measure-Object -Property Failed -Sum).Sum
    $realSkipped = ($script:AllTestCounts | Measure-Object -Property Skipped -Sum).Sum
    $realErrors  = ($script:AllTestCounts | Measure-Object -Property Errors -Sum).Sum
    $realTotal   = $realPassed + $realFailed + $realSkipped + $realErrors
    if ($realTotal -eq 0) { $realTotal = $stepCount }

    Write-Header "Results"
    Write-Host ""

    if ($stepsFailed -eq 0) {
        Write-Host "                    +=======================+" -ForegroundColor Green
        Write-Host "                    |   ALL TESTS PASSED!   |" -ForegroundColor Green
        Write-Host "                    +=======================+" -ForegroundColor Green
    } else {
        Write-Host "                    +=======================+" -ForegroundColor Red
        Write-Host "                    |   SOME TESTS FAILED   |" -ForegroundColor Red
        Write-Host "                    +=======================+" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "  Tests:    " -NoNewline -ForegroundColor Gray
    Write-Host "$realPassed passed" -NoNewline -ForegroundColor Green
    if ($realFailed -gt 0) {
        Write-Host ", $realFailed failed" -NoNewline -ForegroundColor Red
    }
    if ($realErrors -gt 0) {
        Write-Host ", $realErrors errors" -NoNewline -ForegroundColor Red
    }
    if ($realSkipped -gt 0) {
        Write-Host ", $realSkipped skipped" -NoNewline -ForegroundColor DarkYellow
    }
    Write-Host " / $realTotal total" -ForegroundColor White

    Write-Host "  Suites:   " -NoNewline -ForegroundColor Gray
    Write-Host "$stepsPassed passed" -NoNewline -ForegroundColor Green
    if ($stepsFailed -gt 0) {
        Write-Host ", $stepsFailed failed" -NoNewline -ForegroundColor Red
    }
    Write-Host " / $stepCount total" -ForegroundColor White

    Write-Host "  Duration: " -NoNewline -ForegroundColor Gray
    Write-Host "$([math]::Round($duration, 2))s" -ForegroundColor White
    Write-Host ""

    $failures = $script:TestResults | Where-Object { -not $_.Passed }
    if ($failures.Count -gt 0 -and -not $Verbose) {
        Write-SubHeader "Failed Test Output (last 25 lines per suite)"
        foreach ($f in $failures) {
            Write-Host ""
            Write-Host "  [X] " -NoNewline -ForegroundColor Red
            Write-Host $f.Name -ForegroundColor White
            Write-Host ""
            $f.Output -split "`n" | Select-Object -Last 25 | ForEach-Object {
                if ($_.Trim()) { Write-Host "      $_" -ForegroundColor DarkGray }
            }
        }
        Write-Host ""
    }
}
