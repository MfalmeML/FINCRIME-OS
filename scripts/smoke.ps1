$base = "http://127.0.0.1:8000"

Write-Host "health:"
Invoke-RestMethod -Uri "$base/health" -Method Get | ConvertTo-Json -Depth 4

$body = @{
  transaction_id = "tx_smoke_1"
  account_id = "cust_1"
  device_id = "D912"
  event_sequence_ref = "seq_1"
  transaction_risk = 0.73
  behavioral_anomaly_score = 0.94
  sequence_risk_score = 0.91
  graph_ring_score = 0.97
  graph_confirmed_members = 4
  combined_risk_score = 0.96
  segment = @{
    customer_tier = "default"
    channel = "app"
    merchant_category = "electronics"
    geography = "cross_border"
  }
  transaction_amount = 8700
  currency = "KES"
  connected_accounts = 14
  confirmed_fraud_neighbors = 4
  customer_avg_amount = 120
} | ConvertTo-Json -Depth 6

Write-Host "decision:"
Invoke-RestMethod -Uri "$base/decision" -Method Post -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 8