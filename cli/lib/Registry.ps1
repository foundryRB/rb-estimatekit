<#
.SYNOPSIS
    Step, mode, and dispatch registry.

.DESCRIPTION
    Declares the data structures that drive mode selection and
    step dispatch in Start.ps1:

      $Steps          — ordered table of step metadata (labels)
      $Modes          — ordered table mapping mode names to flags, descriptions, and step lists
      $StepFunctions  — dispatch table mapping step keys to script blocks

    Expects the Step-* functions to already be defined (dot-sourced
    from steps/ before this file runs).
#>

$Steps = [ordered]@{
    Generate = @{ Label = "Generate all outputs (roadmap, excel, slides)" }
    Test     = @{ Label = "Run tests (fast)"                              }
    Summary  = @{ Label = "Show project summary"                          }
    Serve    = @{ Label = "Launch Slidev dev server"                      }
}

$Modes = [ordered]@{
    "(default)" = @{
        Flag        = "(none)"
        Description = "Generate all outputs, run fast tests, launch slides"
        Steps       = @("Generate", "Test", "Serve")
    }
    "Build" = @{
        Flag        = "-Build"
        Description = "Generate all outputs, no tests"
        Steps       = @("Generate")
    }
    "Test" = @{
        Flag        = "-Test"
        Description = "Run fast tests only"
        Steps       = @("Test")
    }
    "Run" = @{
        Flag        = "-Run"
        Description = "Launch the Slidev dev server (no build)"
        Steps       = @("Serve")
    }
    "Summary" = @{
        Flag        = "-Summary"
        Description = "Show project summary"
        Steps       = @("Summary")
    }
    "Full" = @{
        Flag        = "-Full"
        Description = "Everything: generate, test, launch slides"
        Steps       = @("Generate", "Test", "Serve")
    }
}

$StepFunctions = @{
    Generate = { Step-Generate }
    Test     = { Step-Test     }
    Summary  = { Step-Summary  }
    Serve    = { Step-Serve    }
}
