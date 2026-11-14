# Install SmartCRM git hooks (pre-commit SESSION_STATE guard + pre-commit framework)
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

# Pre-commit framework hooks (.pre-commit-config.yaml)
$PreCommitExe = Get-Command pre-commit -ErrorAction SilentlyContinue
if (-not $PreCommitExe) {
  Write-Host "pre-commit не найден — устанавливаю через pip"
  pip install pre-commit
}
pre-commit install -c .pre-commit-config.yaml
Write-Host "Pre-commit hooks installed: .pre-commit-config.yaml"
