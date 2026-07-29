param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9]{4}$')]
    [string]$Number,
    [Parameter(Mandatory = $true)]
    [string]$Title
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$slug = ($Title.ToLowerInvariant() -replace '[^a-z0-9]+', '-').Trim('-')
$target = Join-Path $repoRoot "docs\adr\$Number-$slug.md"
if (Test-Path $target) { throw "ADR already exists: $target" }

$template = Get-Content -Raw (Join-Path $repoRoot "docs\adr\0000-template.md")
$content = $template.Replace("ADR-NNNN: Short decision title", "ADR-$Number`: $Title").
    Replace("YYYY-MM-DD", (Get-Date -Format "yyyy-MM-dd"))
Set-Content -Path $target -Value $content -Encoding utf8
Write-Host "Created $target"

