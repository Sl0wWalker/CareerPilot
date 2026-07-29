$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$apiRoot = Join-Path $repoRoot "apps\api"
$webRoot = Join-Path $repoRoot "apps\web"
$pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
$python312 = if ($pythonLauncher) {
    $pythonLauncher.Source
} else {
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
}
$npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $npm) {
    $npm = "$env:ProgramFiles\nodejs\npm.cmd"
}
$env:Path = "$(Split-Path -Parent $npm);$env:Path"

Write-Host "Creating the Python environment..."
if (-not (Test-Path (Join-Path $apiRoot ".venv"))) {
    if (-not (Test-Path $python312)) {
        throw "Python 3.12 was not found. Install it before running setup."
    }
    & $python312 -m venv (Join-Path $apiRoot ".venv")
}
& (Join-Path $apiRoot ".venv\Scripts\python.exe") -m pip install --upgrade pip
& (Join-Path $apiRoot ".venv\Scripts\python.exe") -m pip install -e "$apiRoot[dev]"

Write-Host "Installing dashboard dependencies..."
Push-Location $webRoot
try {
    & $npm install
    if ($LASTEXITCODE -ne 0) {
        throw "Dashboard dependency installation failed."
    }
} finally {
    Pop-Location
}

Write-Host "CareerPilot setup is complete."
