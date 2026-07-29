param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z][a-z0-9-]+$')]
    [string]$Name
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$target = Join-Path $repoRoot "samples\marketplace\$Name"
if (Test-Path $target) { throw "Plugin already exists: $target" }
New-Item -ItemType Directory -Path $target | Out-Null
@{
    name = $Name
    version = "0.1.0"
    careerpilot = ">=1.0.0 <2.0.0"
    permissions = @()
    capabilities = @()
    network_access = @()
} | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $target "manifest.json") -Encoding utf8
Set-Content (Join-Path $target "README.md") "# $Name`n`nDescribe capabilities, permissions, and test instructions.`n" -Encoding utf8
Write-Host "Created plugin scaffold at $target"

