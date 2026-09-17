from fastapi.testclient import TestClient

import fincrime_os.state.loader as loader
from fincrime_os.api.main import app
from fincrime_os.decision_engine.cost_model import build_inputs

client = TestClient(app)


def test_build_inputs_empty():
    c = build_inputs([], version="v0", window_days=30)
    assert c.total_outcomes == 0
    assert c.p_false_decline == 0.0
    assert c.p_churn_given_decline == 0.0


def test_build_inputs_mixed():
    rows = [
        {"decision": "DECLINE", "is_false_decline": True, "churned_after_decline": True, "is_fraud": False, "transaction_amount": 100.0},
        {"decision": "DECLINE", "is_false_decline": False, "churned_after_decline": False, "is_fraud": True, "transaction_amount": 200.0},
        {"decision": "APPROVE", "is_fraud": True, "transaction_amount": 300.0},
        {"decision": "APPROVE", "is_fraud": False, "transaction_amount": 400.0},
    ]
    c = build_inputs(rows, version="v1", window_days=30)
    assert c.declines_observed == 2
    assert c.false_declines == 1
    assert c.churned_after_decline == 1
    assert c.p_false_decline == 0.5
    assert c.p_churn_given_decline == 0.5
    assert c.avg_transaction_amount == 250.0
    assert c.confirmed_fraud_rate == 0.5


def test_cost_inputs_endpoint_default(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    r = client.get("/cost/inputs")
    assert r.status_code == 200
    body = r.json()
    assert body["version"] == "unversioned-dev"
    assert body["p_false_decline"] == 0.0


def test_cost_inputs_endpoint_published(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    loader.publish(
        "cost_model_inputs",
        "v-cost",
        {
            "window_days": 7,
            "total_outcomes": 10,
            "declines_observed": 4,
            "false_declines": 1,
            "churned_after_decline": 2,
            "p_false_decline": 0.25,
            "p_churn_given_decline": 0.5,
            "avg_transaction_amount": 123.4,
            "confirmed_fraud_rate": 0.3,
        },
    )
    r = client.get("/cost/inputs")
    assert r.status_code == 200
    body = r.json()
    assert body["version"] == "v-cost"
    assert body["p_churn_given_decline"] == 0.5