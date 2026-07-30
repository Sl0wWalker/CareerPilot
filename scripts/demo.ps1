$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot "apps\api\.venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Run powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1 first."
}

Push-Location $repoRoot
try {
    & $python -m alembic -c apps\api\alembic.ini upgrade head
    if ($LASTEXITCODE -ne 0) { throw "Database migration failed." }
    $env:PYTHONPATH = (Join-Path $repoRoot "apps\api")
    & $python .\scripts\seed_demo.py
    if ($LASTEXITCODE -ne 0) { throw "Demo seed failed." }
    & powershell -ExecutionPolicy Bypass -File .\scripts\dev.ps1
} finally {
    Pop-Location
}
