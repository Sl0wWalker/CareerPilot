param([Parameter(Mandatory = $true)][string]$BackupPath)
$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Split-Path -Parent $PSScriptRoot)).Path
$resolvedBackup = (Resolve-Path -LiteralPath $BackupPath).Path
$allowedBackupRoot = (Resolve-Path (Join-Path $repoRoot "data\backups")).Path
if (-not $resolvedBackup.StartsWith($allowedBackupRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Restore source must be inside $allowedBackupRoot"
}
$database = Join-Path $repoRoot "data\careerpilot.db"
if (Test-Path -LiteralPath $database) {
    $safetyCopy = "$database.before-restore-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item -LiteralPath $database -Destination $safetyCopy
    Write-Output "Safety copy created: $safetyCopy"
}
Copy-Item -LiteralPath $resolvedBackup -Destination $database -Force
Write-Output "Database restored from: $resolvedBackup"
