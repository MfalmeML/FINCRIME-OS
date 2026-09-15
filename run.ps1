param(
  [string]$Host = "127.0.0.1",
  [int]$Port = 8000
)

Set-Location $PSScriptRoot
if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
  Write-Error "venv missing. Create with: python -m venv .venv"
  exit 1
}

. .\.venv\Scripts\Activate.ps1
python -m uvicorn fincrime_os.api.main:app --host $Host --port $Port --reload