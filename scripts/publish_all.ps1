$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..
. .\.venv\Scripts\Activate.ps1

$version = (Get-Date -AsUTC).ToString("yyyy-MM-ddTHH-mm-ssZ")

Write-Host "publishing all artifacts at version $version"
python scripts\publish_thresholds.py --version $version
python scripts\publish_models.py --version $version
python scripts\publish_graph.py --version $version

Write-Host "done"