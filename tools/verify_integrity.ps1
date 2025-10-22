#!/usr/bin/env pwsh
# verify_integrity.ps1
# Automated integrity verification script for LINXO project
# Executes post-cleanup tests and generates verification report

param(
    [switch]$SkipVenvRecreate,
    [switch]$SkipE2E,
    [string]$TestCSV = "",
    [string]$OutputReport = "verification_report.md"
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$Results = @()

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "LINXO PROJECT - INTEGRITY VERIFICATION SCRIPT" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "Timestamp: $Timestamp" -ForegroundColor Gray
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Gray
Write-Host ""

# Helper function to add test result
function Add-TestResult {
    param(
        [string]$TestName,
        [string]$Status,  # "PASS", "FAIL", "SKIP", "WARN"
        [string]$Details = ""
    )

    $icon = switch ($Status) {
        "PASS" { "[✅]" }
        "FAIL" { "[❌]" }
        "SKIP" { "[⏭️]" }
        "WARN" { "[⚠️]" }
        default { "[?]" }
    }

    $color = switch ($Status) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "SKIP" { "Yellow" }
        "WARN" { "Yellow" }
        default { "White" }
    }

    Write-Host "$icon $TestName" -ForegroundColor $color
    if ($Details) {
        Write-Host "    $Details" -ForegroundColor Gray
    }

    $script:Results += [PSCustomObject]@{
        Test = $TestName
        Status = $Status
        Details = $Details
    }
}

# Change to project root
Set-Location $ProjectRoot

# ============================================================================
# SECTION 1: ENVIRONMENT CHECKS
# ============================================================================

Write-Host "`n=== SECTION 1: ENVIRONMENT CHECKS ===" -ForegroundColor Cyan

# 1.1 Git Status
Write-Host "`n[1.1] Git Repository Status"
$gitStatus = git status --short
if ($LASTEXITCODE -eq 0) {
    if ([string]::IsNullOrWhiteSpace($gitStatus)) {
        Add-TestResult "Git working directory clean" "PASS"
    } else {
        Add-TestResult "Git working directory has changes" "WARN" "$gitStatus"
    }
} else {
    Add-TestResult "Git repository check" "FAIL" "Not a git repository or git not available"
}

# 1.2 Git Branch
$gitBranch = git rev-parse --abbrev-ref HEAD 2>$null
if ($gitBranch) {
    Add-TestResult "Git branch: $gitBranch" "PASS"
} else {
    Add-TestResult "Git branch detection" "FAIL"
}

# 1.3 Python Version
Write-Host "`n[1.2] Python Version"
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Add-TestResult "Python version: $pythonVersion" "PASS"
} else {
    Add-TestResult "Python availability" "FAIL" "Python not found in PATH"
    Write-Host "`nCRITICAL ERROR: Python not available. Exiting." -ForegroundColor Red
    exit 1
}

# 1.4 Virtual Environment
Write-Host "`n[1.3] Virtual Environment"
if (Test-Path ".venv") {
    if ($SkipVenvRecreate) {
        Add-TestResult "Virtual environment exists" "PASS"
    } else {
        Write-Host "Recreating virtual environment for clean test..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force ".venv" -ErrorAction SilentlyContinue
        python -m venv .venv
        if ($LASTEXITCODE -eq 0) {
            Add-TestResult "Virtual environment recreated" "PASS"
        } else {
            Add-TestResult "Virtual environment creation" "FAIL"
            exit 1
        }
    }
} else {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -eq 0) {
        Add-TestResult "Virtual environment created" "PASS"
    } else {
        Add-TestResult "Virtual environment creation" "FAIL"
        exit 1
    }
}

# 1.5 Activate venv and install dependencies
Write-Host "`n[1.4] Installing Dependencies"
if ($IsWindows -or $env:OS -match "Windows") {
    $activateScript = ".venv\Scripts\Activate.ps1"
    & $activateScript
} else {
    # Linux/Mac - use bash
    $env:VIRTUAL_ENV = "$ProjectRoot/.venv"
    $env:PATH = "$ProjectRoot/.venv/bin:$env:PATH"
}

pip install -q -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Add-TestResult "Dependencies installed" "PASS"
} else {
    Add-TestResult "Dependencies installation" "FAIL"
    exit 1
}

# 1.6 Dependency conflicts
Write-Host "`n[1.5] Checking for conflicts"
$pipCheck = pip check 2>&1
if ($LASTEXITCODE -eq 0) {
    Add-TestResult "No dependency conflicts" "PASS"
} else {
    Add-TestResult "Dependency conflicts detected" "WARN" "$pipCheck"
}

# ============================================================================
# SECTION 2: CORE MODULE IMPORTS
# ============================================================================

Write-Host "`n=== SECTION 2: CORE MODULE IMPORTS ===" -ForegroundColor Cyan

$coreModules = @(
    "config",
    "analyzer",
    "linxo_connexion",
    "notifications",
    "report_formatter_v2",
    "agent_linxo_csv_v3_RELIABLE"
)

Set-Location "linxo_agent"

foreach ($module in $coreModules) {
    $testCode = "import $module; print('OK')"
    $result = python -c $testCode 2>&1
    if ($LASTEXITCODE -eq 0 -and $result -match "OK") {
        Add-TestResult "Import $module" "PASS"
    } else {
        Add-TestResult "Import $module" "FAIL" "$result"
    }
}

Set-Location $ProjectRoot

# ============================================================================
# SECTION 3: ENTRY POINT EXECUTION
# ============================================================================

Write-Host "`n=== SECTION 3: ENTRY POINT EXECUTION ===" -ForegroundColor Cyan

# 3.1 Main orchestrator - config check
Write-Host "`n[3.1] Main Orchestrator (linxo_agent.py)"
$output = python linxo_agent.py --config-check 2>&1
if ($LASTEXITCODE -eq 0) {
    Add-TestResult "linxo_agent.py --config-check" "PASS"
} else {
    Add-TestResult "linxo_agent.py --config-check" "FAIL" "$output"
}

# 3.2 Run analysis help
Write-Host "`n[3.2] Analysis Runner (run_analysis.py)"
Set-Location "linxo_agent"
$output = python run_analysis.py 2>&1
Set-Location $ProjectRoot
# run_analysis may fail without CSV, but should not have import errors
if ($output -match "import|ModuleNotFoundError|ImportError") {
    Add-TestResult "run_analysis.py (import check)" "FAIL" "$output"
} else {
    Add-TestResult "run_analysis.py (import check)" "PASS" "No import errors"
}

# ============================================================================
# SECTION 4: END-TO-END SCENARIO
# ============================================================================

Write-Host "`n=== SECTION 4: END-TO-END SCENARIO ===" -ForegroundColor Cyan

if ($SkipE2E) {
    Add-TestResult "E2E scenario" "SKIP" "Skipped by user flag"
} else {
    # Find test CSV
    $testCSVPath = ""
    if ($TestCSV -and (Test-Path $TestCSV)) {
        $testCSVPath = $TestCSV
    } elseif (Test-Path "data/latest.csv") {
        $testCSVPath = "data/latest.csv"
    } elseif (Test-Path "Downloads/operations.csv") {
        $testCSVPath = "Downloads/operations.csv"
    } else {
        # Try to find any CSV
        $csvFiles = Get-ChildItem -Path "data", "Downloads" -Filter "*.csv" -ErrorAction SilentlyContinue
        if ($csvFiles) {
            $testCSVPath = $csvFiles[0].FullName
        }
    }

    if ($testCSVPath) {
        Write-Host "Using test CSV: $testCSVPath" -ForegroundColor Gray

        # Execute analysis
        $output = python linxo_agent.py --csv-file $testCSVPath --skip-notifications 2>&1

        # Check for success indicators
        $hasTransactions = $output -match "Transactions:"
        $hasDepenses = $output -match "Depenses variables:"
        $hasBudget = $output -match "Budget:"
        $hasSuccess = $output -match "SUCCESS|terminee avec succes"
        $hasError = $output -match "ERROR|ERREUR|Exception|Traceback"

        if ($hasSuccess -and $hasTransactions -and !$hasError) {
            Add-TestResult "E2E analysis execution" "PASS" "CSV processed successfully"
        } elseif ($hasError) {
            Add-TestResult "E2E analysis execution" "FAIL" "Errors detected in output"
        } else {
            Add-TestResult "E2E analysis execution" "WARN" "Completed but with warnings"
        }

        # Check if report was generated
        $recentReports = Get-ChildItem -Path "reports" -Filter "rapport_*.txt" -ErrorAction SilentlyContinue |
                        Sort-Object LastWriteTime -Descending |
                        Select-Object -First 1

        if ($recentReports) {
            $reportAge = (Get-Date) - $recentReports.LastWriteTime
            if ($reportAge.TotalMinutes -lt 5) {
                Add-TestResult "Report generation" "PASS" "Report created: $($recentReports.Name)"
            } else {
                Add-TestResult "Report generation" "WARN" "Report exists but may be old"
            }
        } else {
            Add-TestResult "Report generation" "WARN" "No report found in reports/"
        }

    } else {
        Add-TestResult "E2E scenario" "SKIP" "No test CSV file found"
    }
}

# ============================================================================
# SECTION 5: FILE INTEGRITY
# ============================================================================

Write-Host "`n=== SECTION 5: FILE INTEGRITY ===" -ForegroundColor Cyan

# Essential files that must exist
$essentialFiles = @(
    "requirements.txt",
    ".env.example",
    ".gitignore",
    "README.md",
    "linxo_agent/config.py",
    "linxo_agent/analyzer.py",
    "linxo_agent/notifications.py",
    "linxo_agent/linxo_connexion.py",
    "linxo_agent/report_formatter_v2.py",
    "linxo_agent/config_linxo.json",
    "linxo_agent/depenses_recurrentes.json",
    "deploy/install_vps.sh",
    "deploy/setup_ssl.sh"
)

$missingFiles = @()
foreach ($file in $essentialFiles) {
    if (Test-Path $file) {
        # Silent pass
    } else {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -eq 0) {
    Add-TestResult "Essential files present" "PASS" "All $($essentialFiles.Count) files found"
} else {
    Add-TestResult "Essential files present" "FAIL" "Missing: $($missingFiles -join ', ')"
}

# Files that should NOT exist (removed during cleanup)
$removedFiles = @(
    "CHANGELOG_V2.md",
    "README_V2.md",
    "QUICK_START.txt",
    "linxo_agent/report_formatter.py",
    "linxo_agent/send_notifications.py"
)

$stillExists = @()
foreach ($file in $removedFiles) {
    if (Test-Path $file) {
        $stillExists += $file
    }
}

if ($stillExists.Count -eq 0) {
    Add-TestResult "Obsolete files removed" "PASS" "Verified $($removedFiles.Count) files"
} else {
    Add-TestResult "Obsolete files removed" "FAIL" "Still exist: $($stillExists -join ', ')"
}

# ============================================================================
# SECTION 6: SUMMARY & REPORT
# ============================================================================

Write-Host "`n=== VERIFICATION SUMMARY ===" -ForegroundColor Cyan

$passed = ($Results | Where-Object { $_.Status -eq "PASS" }).Count
$failed = ($Results | Where-Object { $_.Status -eq "FAIL" }).Count
$warned = ($Results | Where-Object { $_.Status -eq "WARN" }).Count
$skipped = ($Results | Where-Object { $_.Status -eq "SKIP" }).Count
$total = $Results.Count

Write-Host "`nTest Results:" -ForegroundColor White
Write-Host "  ✅ PASSED:  $passed" -ForegroundColor Green
Write-Host "  ❌ FAILED:  $failed" -ForegroundColor Red
Write-Host "  ⚠️  WARNED:  $warned" -ForegroundColor Yellow
Write-Host "  ⏭️  SKIPPED: $skipped" -ForegroundColor Gray
Write-Host "  ━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "  📊 TOTAL:   $total" -ForegroundColor White

# Determine overall status
$overallStatus = "UNKNOWN"
$exitCode = 0

if ($failed -eq 0) {
    if ($warned -eq 0) {
        $overallStatus = "SUCCESS"
        Write-Host "`n✅ VERIFICATION SUCCESSFUL - All tests passed!" -ForegroundColor Green
    } else {
        $overallStatus = "SUCCESS_WITH_WARNINGS"
        Write-Host "`n⚠️ VERIFICATION PASSED with warnings" -ForegroundColor Yellow
    }
} else {
    $overallStatus = "FAILED"
    $exitCode = 1
    Write-Host "`n❌ VERIFICATION FAILED - Some tests failed!" -ForegroundColor Red
}

# ============================================================================
# GENERATE REPORT
# ============================================================================

Write-Host "`n=== GENERATING REPORT ===" -ForegroundColor Cyan

$reportContent = @"
# LINXO PROJECT - VERIFICATION REPORT

**Generated:** $Timestamp
**Branch:** $gitBranch
**Overall Status:** $overallStatus

---

## 📊 SUMMARY

| Metric | Count |
|--------|-------|
| Total Tests | $total |
| ✅ Passed | $passed |
| ❌ Failed | $failed |
| ⚠️ Warnings | $warned |
| ⏭️ Skipped | $skipped |

**Success Rate:** $([math]::Round(($passed / $total) * 100, 2))%

---

## 📋 DETAILED RESULTS

| Test | Status | Details |
|------|--------|---------|
"@

foreach ($result in $Results) {
    $statusIcon = switch ($result.Status) {
        "PASS" { "✅" }
        "FAIL" { "❌" }
        "SKIP" { "⏭️" }
        "WARN" { "⚠️" }
        default { "?" }
    }

    $details = if ($result.Details) { $result.Details.Replace("`n", " ").Replace("|", "\|") } else { "-" }
    $reportContent += "`n| $($result.Test) | $statusIcon $($result.Status) | $details |"
}

$reportContent += @"

---

## 🎯 CONCLUSION

"@

if ($overallStatus -eq "SUCCESS") {
    $reportContent += @"
✅ **VERIFICATION SUCCESSFUL**

All tests passed. The project is in a healthy state after cleanup.

**Next Steps:**
1. Review this report
2. Commit cleanup changes
3. Create Pull Request
4. Merge to main branch
"@
} elseif ($overallStatus -eq "SUCCESS_WITH_WARNINGS") {
    $reportContent += @"
⚠️ **VERIFICATION PASSED WITH WARNINGS**

All critical tests passed, but some warnings were detected. Review warnings before proceeding.

**Next Steps:**
1. Review warnings above
2. Address any concerns
3. Proceed with commit if acceptable
"@
} else {
    $reportContent += @"
❌ **VERIFICATION FAILED**

Some tests failed. **DO NOT PROCEED** with cleanup.

**Required Actions:**
1. Review failed tests above
2. Investigate root causes
3. Fix issues
4. Re-run verification
5. Consider rollback if necessary

**Rollback Commands:**
\`\`\`bash
git reset --hard HEAD~1
git checkout main
\`\`\`
"@
}

$reportContent += @"

---

## 📞 ENVIRONMENT INFO

- **Python Version:** $pythonVersion
- **Git Branch:** $gitBranch
- **Project Root:** $ProjectRoot
- **Timestamp:** $Timestamp

---

*Report generated by verify_integrity.ps1*
"@

# Write report to file
$reportContent | Out-File -FilePath $OutputReport -Encoding UTF8
Write-Host "Report saved to: $OutputReport" -ForegroundColor Green

# ============================================================================
# EXIT
# ============================================================================

Write-Host "`n" + ("=" * 80) -ForegroundColor Cyan
Write-Host "Verification script completed." -ForegroundColor Cyan
Write-Host ("=" * 80) -ForegroundColor Cyan

exit $exitCode
