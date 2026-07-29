$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$apiRoot = Join-Path $repoRoot "apps\api"
$webRoot = Join-Path $repoRoot "apps\web"
$python = Join-Path $apiRoot ".venv\Scripts\python.exe"
$nodeRoot = "$env:ProgramFiles\nodejs"

if (-not (Test-Path $python)) {
    throw "Run .\scripts\setup.ps1 first."
}

Start-Process powershell -WindowStyle Hidden -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$repoRoot'; & '$python' -m uvicorn careerpilot.main:app --app-dir '$apiRoot' --reload"
)
Start-Process powershell -WindowStyle Hidden -ArgumentList @(
    "-NoExit",
    "-Command",
    "`$env:Path = '$nodeRoot;' + `$env:Path; Set-Location '$webRoot'; & '$nodeRoot\npm.cmd' run dev"
)

Write-Host "CareerPilot is starting:"
Write-Host "Dashboard: http://localhost:5173"
Write-Host "API docs:  http://127.0.0.1:8000/docs"
