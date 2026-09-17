from fastapi.testclient import TestClient

import fincrime_os.state.loader as loader
from fincrime_os.api.main import app

client = TestClient(app)


def test_drift_current_no_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    r = client.get("/drift/current")
    assert r.status_code == 200
    body = r.json()
    assert body["any_fired"] is False
    assert body["signals"] == []


def test_drift_current_with_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    loader.publish(
        "drift_signals",
        "v1",
        {
            "window_days": 30,
            "recent_fraud_rate": 0.20,
            "baseline_fraud_rate": 0.02,
            "fraud_rate_multiplier": 10.0,
            "recent_fp_rate": 0.10,
            "baseline_fp_rate": 0.05,
            "feature_score": 0.05,
            "prediction_score": 0.18,
            "graph_score": 0.0,
            "any_fired": True,
        },
    )
    r = client.get("/drift/current")
    assert r.status_code == 200
    body = r.json()
    assert body["any_fired"] is True
    fired = [s for s in body["signals"] if s["fired"]]
    components = {s["component"] for s in fired}
    assert "fraud_rate" in components