$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$apiRoot = Join-Path $repoRoot "apps\api"
$webRoot = Join-Path $repoRoot "apps\web"
$python = Join-Path $apiRoot ".venv\Scripts\python.exe"
$env:Path = "$env:ProgramFiles\nodejs;$env:Path"
$npm = "$env:ProgramFiles\nodejs\npm.cmd"

& $python -m pytest $apiRoot
if ($LASTEXITCODE -ne 0) { throw "Backend tests failed." }
Push-Location $webRoot
try {
    & $npm test
    if ($LASTEXITCODE -ne 0) { throw "Frontend tests failed." }
} finally {
    Pop-Location
}
