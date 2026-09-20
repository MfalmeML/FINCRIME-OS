from fastapi.testclient import TestClient

from fincrime_os.api.main import app
from fincrime_os.pipeline import Pipeline

client = TestClient(app)


def _payload(account_id="cust_1", ring=0.0, members=0, amount=8700.0):
    return {
        "transaction_id": "tx_e2e_1",
        "account_id": account_id,
        "device_id": "D912",
        "event_sequence_ref": "seq_e2e_1",
        "transaction_risk": 0.0,
        "behavioral_anomaly_score": 0.0,
        "sequence_risk_score": 0.0,
        "graph_ring_score": ring,
        "graph_confirmed_members": members,
        "combined_risk_score": 0.0,
        "segment": {
            "customer_tier": "default",
            "channel": "web",
            "merchant_category": "6051",
            "geography": "NG",
        },
        "transaction_amount": amount,
        "currency": "USD",
        "connected_accounts": 0,
        "confirmed_fraud_neighbors": 0,
        "customer_avg_amount": 0.0,
    }


def test_api_accepts_request_and_returns_full_response():
    r = client.post("/decision", json=_payload())
    assert r.status_code == 200
    body = r.json()
    assert body["transaction_id"] == "tx_e2e_1"
    assert body["decision"] in {"APPROVE", "CHALLENGE", "DECLINE"}
    assert "model_versions" in body
    assert "explanation" in body
    assert body["explanation"]["complete"] is True or body["decision"] == "APPROVE"


def test_api_decision_is_deterministic_for_same_input():
    p1 = client.post("/decision", json=_payload()).json()["decision"]
    p2 = client.post("/decision", json=_payload()).json()["decision"]
    assert p1 == p2


def test_api_respects_graph_override():
    r = client.post("/decision", json=_payload(ring=0.99, members=5))
    body = r.json()
    assert body["decision"] == "DECLINE"
    assert body["decision_reason"] == "graph_override"


def test_api_with_no_graph_signal_does_not_override():
    r = client.post("/decision", json=_payload(ring=0.0, members=0))
    body = r.json()
    assert body["decision_reason"] != "graph_override"


def test_pipeline_reports_training_state():
    p = Pipeline()
    # This test does not fail if models are untrained, it just reports.
    # The point is to confirm the pipeline exposes training state so it can
    # be checked in ops.
    assert isinstance(p.transaction.is_trained, bool)
    assert isinstance(p.behavioral.is_trained, bool)
    assert isinstance(p.temporal.is_trained, bool)
    assert isinstance(p.fusion.is_trained, bool)