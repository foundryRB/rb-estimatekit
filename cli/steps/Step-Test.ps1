<#
.SYNOPSIS
    Run fast pytest tests (excludes slow + overflow markers).
#>

function Step-Test {
    Write-Header "Tests (fast) — pytest"

    if (-not $script:PythonCmd) {
        Write-Host "  ERROR: Python not found" -ForegroundColor Red
        return
    }

    $name  = "pytest (fast)"
    $start = Get-Date

    Write-TestStart $name

    try {
        $verboseFlag = if ($Verbose) { "-v" } else { "-q" }
        $testsDir    = Join-Path $EngineRoot "tests"
        $env:ESTIMATEKIT_PROJECT = $ProjectDir
        Push-Location $ModernRoot
        $out      = & $script:PythonCmd -m pytest $testsDir $verboseFlag --tb=short -m "not slow and not overflow" 2>&1 | Out-String
        $exitCode = $LASTEXITCODE
    } catch {
        $out      = $_.Exception.Message
        $exitCode = 1
    } finally {
        Pop-Location -ErrorAction SilentlyContinue
    }

    $passed = ($exitCode -eq 0)

    # Display output
    $out -split "`n" | ForEach-Object {
        if ($_.Trim()) {
            $c = if ($_ -match 'passed')                 { "Green" }
                 elseif ($_ -match 'FAILED|failed|ERROR') { "Red" }
                 elseif ($_ -match 'warning|WARNING')     { "Yellow" }
                 elseif ($_ -match 'SKIPPED|skipped')     { "DarkYellow" }
                 else                                     { "DarkGray" }
            Write-Host "    $_" -ForegroundColor $c
        }
    }

    $dur = [math]::Round(((Get-Date) - $start).TotalSeconds, 2)
    Write-TestResult $name $passed $dur

    # Track results
    if ($passed) { $script:TotalPassed++ } else { $script:TotalFailed++ }
    $script:TestResults += [PSCustomObject]@{
        Name = $name; Passed = $passed; Duration = $dur; Output = $out
    }

    # Parse verbose output for grouped report if available
    if ($Verbose -and $out) {
        $parsed = Parse-PytestVerbose $out
        Write-PytestReport $parsed $out $Verbose
        $script:AllTestCounts += [PSCustomObject]@{
            Passed  = $parsed.Passed
            Failed  = $parsed.Failed
            Skipped = $parsed.Skipped
            Errors  = $parsed.Errors
        }
    }

    if ($StopOnError -and -not $passed) {
        Write-Host "  Stopping on first error (-StopOnError)" -ForegroundColor Yellow
    }
}
