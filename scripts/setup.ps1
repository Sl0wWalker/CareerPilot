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
$venvRoot = Join-Path $apiRoot ".venv"
$venvPython = Join-Path $venvRoot "Scripts\python.exe"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$CommandArguments
    )

    & $FilePath @CommandArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed ($LASTEXITCODE): $FilePath $($CommandArguments -join ' ')"
    }
}

Write-Host "Creating the Python environment..."
if (Test-Path $venvPython) {
    & $venvPython -c "import pip._internal.cli"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "The existing Python environment is incomplete. Rebuilding it..."
        $resolvedVenv = (Resolve-Path $venvRoot).Path
        $expectedVenv = Join-Path (Resolve-Path $apiRoot).Path ".venv"
        if ($resolvedVenv -ne $expectedVenv) {
            throw "Refusing to remove an unexpected environment path: $resolvedVenv"
        }
        Remove-Item -LiteralPath $resolvedVenv -Recurse -Force
    }
}

if (-not (Test-Path $venvPython)) {
    if (-not (Test-Path $python312)) {
        throw "Python 3.12 was not found. Install it before running setup."
    }
    Invoke-Checked -FilePath $python312 -CommandArguments @("-3.12", "-m", "venv", $venvRoot)
}
Invoke-Checked -FilePath $venvPython -CommandArguments @("-m", "ensurepip", "--upgrade")
Invoke-Checked -FilePath $venvPython -CommandArguments @("-m", "pip", "install", "--upgrade", "pip")
Invoke-Checked -FilePath $venvPython -CommandArguments @(
    "-m", "pip", "install", "-e", "$apiRoot[dev]"
)
Invoke-Checked -FilePath $venvPython -CommandArguments @(
    "-m", "playwright", "install", "chromium"
)

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
