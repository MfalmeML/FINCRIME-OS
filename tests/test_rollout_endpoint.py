from fastapi.testclient import TestClient

import fincrime_os.state.loader as loader
from fincrime_os.api.main import app

client = TestClient(app)


def test_rollout_current_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    r = client.get("/rollout/current")
    assert r.status_code == 200
    body = r.json()
    assert body["version"] == "unversioned-dev"
    assert body["default_stage"] == "full"
    assert body["segments"] == []


def test_rollout_current_reflects_published(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    loader.publish(
        "rollout_table",
        "v-roll-endpoint",
        {
            "default_stage": "add_temporal",
            "default_percentage": 0.5,
            "segments": {"vip": {"stage": "full", "percentage": 0.1}},
        },
    )
    r = client.get("/rollout/current")
    body = r.json()
    assert body["version"] == "v-roll-endpoint"
    assert body["default_stage"] == "add_temporal"
    assert body["default_percentage"] == 0.5
    keys = {s["segment_key"] for s in body["segments"]}
    assert "vip" in keys