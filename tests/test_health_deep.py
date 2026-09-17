from fastapi.testclient import TestClient

import fincrime_os.state.loader as loader
from fincrime_os.api.main import app
from fincrime_os.monitoring.runtime_metrics import get_metrics

client = TestClient(app)


def test_health_deep_empty_state(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    get_metrics().reset()
    r = client.get("/health/deep")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["artifacts"]["threshold_tables"]["available"] is False
    assert body["artifacts"]["graph_snapshots"]["available"] is False
    assert body["artifacts"]["cost_model_inputs"]["available"] is False
    assert body["runtime"]["decisions_in_window"] == 0
    assert body["runtime"]["graph_degraded_rate"] == 0.0


def test_health_deep_reflects_published_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    loader.publish("threshold_tables", "v-t", {"entries": {"default": [0.4, 0.75]}})
    loader.publish("model_versions", "v-m", {"models": {"fusion_model": "fusion-v1"}})
    loader.publish(
        "graph_snapshots",
        "v-g",
        {
            "ring_scores": {"cust_1": 0.9},
            "confirmed_members": {"cust_1": 2},
            "connected_accounts": {"cust_1": 5},
            "confirmed_fraud_neighbors": {"cust_1": 2},
        },
    )
    loader.publish(
        "cost_model_inputs",
        "v-c",
        {
            "window_days": 7,
            "total_outcomes": 0,
            "declines_observed": 0,
            "false_declines": 0,
            "churned_after_decline": 0,
            "p_false_decline": 0.0,
            "p_churn_given_decline": 0.0,
            "avg_transaction_amount": 0.0,
            "confirmed_fraud_rate": 0.0,
        },
    )
    r = client.get("/health/deep")
    body = r.json()
    assert body["artifacts"]["threshold_tables"]["available"] is True
    assert body["artifacts"]["threshold_tables"]["version"] == "v-t"
    assert body["artifacts"]["model_versions"]["version"] == "v-m"
    assert body["artifacts"]["graph_snapshots"]["version"] == "v-g"
    assert body["artifacts"]["graph_snapshots"]["fresh"] is True
    assert body["artifacts"]["cost_model_inputs"]["version"] == "v-c"


def test_health_deep_tracks_graph_degraded_rate(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    get_metrics().reset()
    get_metrics().record_decision(graph_degraded=True)
    get_metrics().record_decision(graph_degraded=True)
    get_metrics().record_decision(graph_degraded=False)
    r = client.get("/health/deep")
    body = r.json()
    assert body["runtime"]["decisions_in_window"] == 3
    assert body["runtime"]["graph_degraded_count"] == 2
    assert abs(body["runtime"]["graph_degraded_rate"] - 0.6667) < 0.01