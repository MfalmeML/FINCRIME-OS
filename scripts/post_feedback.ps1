param(
  [string]$Base = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

function Post-Decision($body) {
  Invoke-RestMethod -Uri "$Base/decision" -Method Post -ContentType "application/json" -Body ($body | ConvertTo-Json -Depth 8)
}

function Post-Outcome($body) {
  Invoke-RestMethod -Uri "$Base/outcome" -Method Post -ContentType "application/json" -Body ($body | ConvertTo-Json -Depth 8)
}

$now = (Get-Date).ToUniversalTime()
$observed = $now.ToString("o")
$decided  = $now.AddSeconds(-5).ToString("o")

$cases = @(
  @{
    label = "fraud-shape"
    body = @{
      transaction_id = "tx_fb_fraud"
      account_id = "cust_fb_fraud"
      device_id = "D912"
      event_sequence_ref = "seq_fb_fraud"
      transaction_risk = 0.0; behavioral_anomaly_score = 0.0
      sequence_risk_score = 0.0; graph_ring_score = 0.0
      graph_confirmed_members = 0; combined_risk_score = 0.0
      segment = @{ customer_tier = "default"; channel = "web"; merchant_category = "6051"; geography = "NG" }
      transaction_amount = 8700; currency = "USD"
      connected_accounts = 0; confirmed_fraud_neighbors = 0; customer_avg_amount = 0
    }
    is_fraud = $true; is_ring_member = $true
    is_false_decline = $false; churned = $false; inv = "confirmed_fraud"
  },
  @{
    label = "legit-shape"
    body = @{
      transaction_id = "tx_fb_legit"
      account_id = "cust_fb_legit"
      device_id = "D1"
      event_sequence_ref = "seq_fb_legit"
      transaction_risk = 0.0; behavioral_anomaly_score = 0.0
      sequence_risk_score = 0.0; graph_ring_score = 0.0
      graph_confirmed_members = 0; combined_risk_score = 0.0
      segment = @{ customer_tier = "default"; channel = "pos"; merchant_category = "5411"; geography = "KE" }
      transaction_amount = 80; currency = "KES"
      connected_accounts = 1; confirmed_fraud_neighbors = 0; customer_avg_amount = 120
    }
    is_fraud = $false; is_ring_member = $false
    is_false_decline = $false; churned = $false; inv = "inconclusive"
  },
  @{
    label = "override-shape"
    body = @{
      transaction_id = "tx_fb_override"
      account_id = "cust_1"
      device_id = "D912"
      event_sequence_ref = "seq_fb_override"
      transaction_risk = 0.0; behavioral_anomaly_score = 0.0
      sequence_risk_score = 0.0; graph_ring_score = 0.99
      graph_confirmed_members = 5; combined_risk_score = 0.0
      segment = @{ customer_tier = "default"; channel = "web"; merchant_category = "6051"; geography = "NG" }
      transaction_amount = 8700; currency = "USD"
      connected_accounts = 14; confirmed_fraud_neighbors = 4; customer_avg_amount = 0
    }
    is_fraud = $true; is_ring_member = $true
    is_false_decline = $false; churned = $false; inv = "confirmed_fraud"
  }
)

foreach ($case in $cases) {
  Write-Host "== $($case.label) =="
  $r = Post-Decision $case.body
  Write-Host "decision=$($r.decision) reason=$($r.decision_reason) tx=$($r.transaction_id)"

  $outcome = @{
    transaction_id = $case.body.transaction_id
    account_id = $case.body.account_id
    decision = $r.decision
    decided_at = $decided
    observed_at = $observed
    is_fraud = $case.is_fraud
    is_ring_member = $case.is_ring_member
    is_false_decline = $case.is_false_decline
    churned_after_decline = $case.churned
    investigation_outcome = $case.inv
    transaction_amount = $case.body.transaction_amount
    segment = $case.body.segment
  }
  Post-Outcome $outcome | Out-Null
  Start-Sleep -Milliseconds 100
}

Write-Host "posted $($cases.Count) decisions and outcomes"