from fastapi.testclient import TestClient
from fincrime_os.api.main import app

client = TestClient(app)


def _payload(combined=0.10, ring=0.0, members=0):
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
        "transaction_amount": 8700,
        "currency": "KES",
    }


def test_health():
    r = client.get("/health")
    assert r.status_code == 200


def test_decision_approve():
    r = client.post("/decision", json=_payload(0.10))
    assert r.status_code == 200
    assert r.json()["decision"] == "APPROVE"


def test_decision_graph_override():
    r = client.post("/decision", json=_payload(0.10, ring=0.99, members=5))
    assert r.status_code == 200
    assert r.json()["decision"] == "DECLINE"
    assert r.json()["decision_reason"] == "graph_override"