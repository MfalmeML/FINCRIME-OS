$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..
if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
  Write-Error "venv missing"
  exit 1
}
. .\.venv\Scripts\Activate.ps1

Write-Host "== ruff =="
ruff check src tests

Write-Host "== pytest =="
pytest -q

Write-Host "== OK =="