from fastapi.testclient import TestClient

from fincrime_os.api.main import app

client = TestClient(app)


def test_version_endpoint():
    r = client.get("/version")
    assert r.status_code == 200
    body = r.json()
    assert body["threshold_table_version"]
    assert body["graph_override"]["ring_score_cutoff"] == 0.90
    assert body["graph_override"]["min_confirmed_members"] == 2
    assert body["latency_budget_ms"] == 100
    assert "fusion_model" in body["model_versions"]
    assert body["platform_version"] == "0.7.0"
    assert "graph_snapshot_version" in body
    assert "replayed_events" in body


def test_decision_response_contains_latency_header():
    payload = {
        "transaction_id": "tx_lat",
        "account_id": "cust_1",
        "device_id": "D1",
        "event_sequence_ref": "seq_1",
        "transaction_risk": 0.1,
        "behavioral_anomaly_score": 0.1,
        "sequence_risk_score": 0.1,
        "graph_ring_score": 0.0,
        "graph_confirmed_members": 0,
        "combined_risk_score": 0.1,
        "segment": {
            "customer_tier": "default",
            "channel": "app",
            "merchant_category": "electronics",
            "geography": "KE",
        },
        "transaction_amount": 100.0,
        "currency": "KES",
    }
    r = client.post("/decision", json=payload)
    assert r.status_code == 200
    assert "X-Latency-Ms" in r.headers
    assert float(r.headers["X-Latency-Ms"]) < 100.0
