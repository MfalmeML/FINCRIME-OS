from fastapi.testclient import TestClient
from fincrime_os.api.main import app

client = TestClient(app)


def _payload(combined=0.10, ring=0.0, members=0, amount=8700.0, avg=120.0,
             connected=0, fraud_neighbors=0):
    return {
        "transaction_id": "tx_88213",
        "account_id": "cust_456",
        "device_id": "D912",
        "event_sequence_ref": "seq_88213",
        "transaction_risk": 0.73,
        "behavioral_anomaly_score": 0.94,
        "sequence_risk_score": 0.91,
        "graph_ring_score": ring,
        "graph_confirmed_members": members,
        "combined_risk_score": combined,
        "segment": {
            "customer_tier": "default",
            "channel": "app",
            "merchant_category": "electronics",
            "geography": "cross_border",
        },
        "transaction_amount": amount,
        "currency": "KES",
        "connected_accounts": connected,
        "confirmed_fraud_neighbors": fraud_neighbors,
        "customer_avg_amount": avg,
    }


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_decision_approve():
    r = client.post("/decision", json=_payload(0.10))
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "APPROVE"
    assert body["graph_degraded"] is False
    assert body["model_versions"]["fusion_model"] == "fusion-dev"
    assert body["explanation"]["complete"] is True


def test_decision_graph_override():
    r = client.post("/decision", json=_payload(0.10, ring=0.99, members=5))
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "DECLINE"
    assert body["decision_reason"] == "graph_override"


def test_decision_challenge_band():
    r = client.post("/decision", json=_payload(0.55))
    assert r.status_code == 200
    assert r.json()["decision"] == "CHALLENGE"


def test_response_shape_is_stable():
    r = client.post("/decision", json=_payload(0.10))
    body = r.json()
    expected = {
        "transaction_id",
        "decision",
        "decision_reason",
        "graph_degraded",
        "threshold_table_version",
        "model_versions",
        "explanation_ref",
        "explanation",
    }
    assert set(body.keys()) == expected


def test_end_to_end_explanation_populated():
    r = client.post(
        "/decision",
        json=_payload(combined=0.10, ring=0.97, members=4, amount=8700.0,
                      avg=120.0, connected=14, fraud_neighbors=4),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "DECLINE"
    codes = {rc["code"] for rc in body["explanation"]["reason_codes"]}
    assert "AMOUNT_DEVIATION" in codes
    assert "DEVICE_CONNECTIVITY" in codes
    assert "RING_OVERRIDE" in codes
    assert body["explanation"]["counterfactual"] != ""
    assert body["explanation"]["complete"] is True


def test_explanation_ref_matches_transaction():
    r = client.post("/decision", json=_payload(0.10))
    body = r.json()
    assert body["explanation_ref"] == "exp_tx_88213"