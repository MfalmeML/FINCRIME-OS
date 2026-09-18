param(
  [int]$WindowDays = 30,
  [switch]$SkipPublish,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..
. .\.venv\Scripts\Activate.ps1

$stamp = (Get-Date -AsUTC).ToString("yyyy-MM-ddTHH-mm-ssZ")
Write-Host "offline pipeline start version=$stamp window=$WindowDays"

if ($DryRun) {
  Write-Host "dry-run: skipping all steps"
  exit 0
}

if (-not $SkipPublish) {
  Write-Host "== publish_all =="
  python scripts\publish_thresholds.py --version $stamp
  python scripts\publish_models.py --version $stamp
  python scripts\publish_graph.py --version $stamp
}

Write-Host "== cost inputs =="
python scripts\build_cost_inputs.py --window-days $WindowDays --version $stamp

Write-Host "== drift =="
python scripts\compute_drift.py --window-days $WindowDays --version $stamp

Write-Host "== quality =="
python scripts\compute_quality.py --window-days $WindowDays --version $stamp

Write-Host "== thresholds =="
python scripts\optimize_thresholds.py --window-days $WindowDays --version $stamp

Write-Host "offline pipeline done version=$stamp"