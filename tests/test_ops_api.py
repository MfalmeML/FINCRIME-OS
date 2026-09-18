from fastapi.testclient import TestClient

from fincrime_os.api.main import app

client = TestClient(app)


def test_drift_check_fires_on_fraud_rate_spike():
    r = client.post(
        "/drift/check",
        json={
            "feature_score": 0.05,
            "prediction_score": 0.05,
            "graph_score": 0.05,
            "fraud_rate_multiplier": 6.8,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["any_fired"] is True
    fired = [s for s in body["signals"] if s["fired"]]
    assert fired[0]["component"] == "fraud_rate"


def test_drift_check_silent_when_stable():
    r = client.post(
        "/drift/check",
        json={
            "feature_score": 0.01,
            "prediction_score": 0.01,
            "graph_score": 0.01,
            "fraud_rate_multiplier": 1.0,
        },
    )
    assert r.status_code == 200
    assert r.json()["any_fired"] is False


def test_canary_promotes_better_candidate():
    r = client.post(
        "/canary/evaluate",
        json={
            "component": "fusion_model",
            "candidate_version": "fusion-v2",
            "baseline_version": "fusion-dev",
            "candidate_fraud_loss": 0.005,
            "baseline_fraud_loss": 0.010,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["result"] == "PROMOTE"
    assert body["serving_version"] == "fusion-v2"


def test_canary_rejects_over_ceiling():
    r = client.post(
        "/canary/evaluate",
        json={
            "component": "transaction_model",
            "candidate_version": "txn-v3",
            "baseline_version": "txn-dev",
            "candidate_fraud_loss": 0.05,
            "baseline_fraud_loss": 0.01,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["result"] == "REJECT"
    assert body["serving_version"] == "txn-dev"


def test_canary_holds_worse_but_under_ceiling():
    r = client.post(
        "/canary/evaluate",
        json={
            "component": "temporal_model",
            "candidate_version": "seq-v2",
            "baseline_version": "seq-dev",
            "candidate_fraud_loss": 0.015,
            "baseline_fraud_loss": 0.010,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["result"] == "HOLD"
    assert body["serving_version"] == "seq-dev"