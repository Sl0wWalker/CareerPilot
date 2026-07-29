$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$apiRoot = Join-Path $repoRoot "apps\api"
$webRoot = Join-Path $repoRoot "apps\web"
$python = Join-Path $apiRoot ".venv\Scripts\python.exe"
$env:Path = "$env:ProgramFiles\nodejs;$env:Path"
$npm = "$env:ProgramFiles\nodejs\npm.cmd"

& $python -m ruff check $apiRoot
if ($LASTEXITCODE -ne 0) { throw "Backend linting failed." }
Push-Location $webRoot
try {
    & $npm run lint
    if ($LASTEXITCODE -ne 0) { throw "Frontend linting failed." }
    & $npm run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }
} finally {
    Pop-Location
}
