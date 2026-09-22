param(
  [int]$TransactionN = 20000,
  [int]$BehavioralN = 20000,
  [int]$SequenceN = 20000,
  [int]$FusionN = 40000,
  [int]$GraphN = 40000,
  [int]$Seed = 42
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..
. .\.venv\Scripts\Activate.ps1

Write-Host "== generate datasets =="
python scripts\generate_transactions.py --n $TransactionN --fraud-rate 0.02 --seed $Seed
python scripts\generate_behavioral.py   --n $BehavioralN  --anomaly-rate 0.05 --seed $Seed
python scripts\generate_sequences.py    --n $SequenceN    --suspicious-rate 0.10 --seed $Seed
python scripts\generate_fusion.py       --n $FusionN      --fraud-rate 0.03 --seed $Seed
python scripts\generate_graph.py        --n $GraphN       --ring-rate 0.05 --seed $Seed

Write-Host "== train models =="
python scripts\train_transaction_model.py
python scripts\train_behavioral_model.py
python scripts\train_temporal_model.py
python scripts\train_fusion_model.py
python scripts\train_graph_model.py

Write-Host "== publish model registry =="
python scripts\publish_models.py

Write-Host "== publish graph snapshot =="
python scripts\publish_graph.py

Write-Host "== publish thresholds =="
python scripts\publish_thresholds.py

Write-Host "train_all done"