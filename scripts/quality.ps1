$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

& (Join-Path $PSScriptRoot "test.ps1")
& (Join-Path $PSScriptRoot "lint.ps1")

$trackedSensitive = git -C $repoRoot ls-files |
    Select-String -Pattern '(^|/)(\.env$|.*\.db$|.*\.sqlite3?$|resumes?/|browser_sessions?/|.*\.pem$)'
if ($trackedSensitive) {
    throw "Potentially sensitive tracked files found:`n$trackedSensitive"
}

Write-Host "CareerPilot quality gates passed."

