$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$database = Join-Path $repoRoot "data\careerpilot.db"
$backupDirectory = Join-Path $repoRoot "data\backups"
if (-not (Test-Path -LiteralPath $database)) { throw "CareerPilot database does not exist." }
New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
$destination = Join-Path $backupDirectory "careerpilot-$(Get-Date -Format 'yyyyMMdd-HHmmss').db"
Copy-Item -LiteralPath $database -Destination $destination
Write-Output "Backup created: $destination"
