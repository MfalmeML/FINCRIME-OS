param(
  [string]$Base = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

function Post-Decision($body) {
  Invoke-RestMethod -Uri "$Base/decision" -Method Post -ContentType "application/json" -Body ($body | ConvertTo-Json -Depth 8)
}

$fraud = @{
  transaction_id = "tx_smoke_fraud"
  account_id = "cust_smoke_fraud"
  device_id = "D912"
  event_sequence_ref = "seq_smoke_fraud"
  transaction_risk = 0.0
  behavioral_anomaly_score = 0.0
  sequence_risk_score = 0.0
  graph_ring_score = 0.0
  graph_confirmed_members = 0
  combined_risk_score = 0.0
  segment = @{
    customer_tier = "default"
    channel = "web"
    merchant_category = "6051"
    geography = "NG"
  }
  transaction_amount = 8700
  currency = "USD"
  connected_accounts = 0
  confirmed_fraud_neighbors = 0
  customer_avg_amount = 0
}

$legit = @{
  transaction_id = "tx_smoke_legit"
  account_id = "cust_smoke_legit"
  device_id = "D1"
  event_sequence_ref = "seq_smoke_legit"
  transaction_risk = 0.0
  behavioral_anomaly_score = 0.0
  sequence_risk_score = 0.0
  graph_ring_score = 0.0
  graph_confirmed_members = 0
  combined_risk_score = 0.0
  segment = @{
    customer_tier = "default"
    channel = "pos"
    merchant_category = "5411"
    geography = "KE"
  }
  transaction_amount = 80
  currency = "KES"
  connected_accounts = 1
  confirmed_fraud_neighbors = 0
  customer_avg_amount = 120
}

$override = @{
  transaction_id = "tx_smoke_override"
  account_id = "cust_1"
  device_id = "D912"
  event_sequence_ref = "seq_smoke_override"
  transaction_risk = 0.0
  behavioral_anomaly_score = 0.0
  sequence_risk_score = 0.0
  graph_ring_score = 0.99
  graph_confirmed_members = 5
  combined_risk_score = 0.0
  segment = @{
    customer_tier = "default"
    channel = "web"
    merchant_category = "6051"
    geography = "NG"
  }
  transaction_amount = 8700
  currency = "USD"
  connected_accounts = 14
  confirmed_fraud_neighbors = 4
  customer_avg_amount = 0
}

Write-Host "== fraud-shaped =="
$r1 = Post-Decision $fraud
$r1 | ConvertTo-Json -Depth 8
Write-Host "decision=$($r1.decision) reason=$($r1.decision_reason)"

Write-Host "== legit-shaped =="
$r2 = Post-Decision $legit
$r2 | ConvertTo-Json -Depth 8
Write-Host "decision=$($r2.decision) reason=$($r2.decision_reason)"

Write-Host "== graph override =="
$r3 = Post-Decision $override
$r3 | ConvertTo-Json -Depth 8
Write-Host "decision=$($r3.decision) reason=$($r3.decision_reason)"

if ($r1.decision -eq "APPROVE") { Write-Host "WARN: fraud-shaped was APPROVE" -ForegroundColor Yellow }
if ($r2.decision -eq "DECLINE") { Write-Host "WARN: legit-shaped was DECLINE" -ForegroundColor Yellow }
if ($r3.decision -ne "DECLINE" -or $r3.decision_reason -ne "graph_override") {
  Write-Host "FAIL: graph override did not fire" -ForegroundColor Red
  exit 1
}
Write-Host "smoke_full OK"