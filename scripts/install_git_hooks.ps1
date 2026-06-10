# Install SmartCRM git hooks (pre-commit SESSION_STATE guard)
$ErrorActionPreference = "Stop"
$Root = git rev-parse --show-toplevel
if (-not $Root) { throw "Not a git repository" }
$GitDir = git rev-parse --git-dir
$HooksDir = Join-Path $GitDir "hooks"
$Source = Join-Path $Root "scripts\git-hooks\pre-commit"
$Dest = Join-Path $HooksDir "pre-commit"
New-Item -ItemType Directory -Force -Path $HooksDir | Out-Null
Copy-Item -Force $Source $Dest
Write-Host "Installed: $Dest"
