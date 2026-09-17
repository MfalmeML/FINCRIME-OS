from fastapi.testclient import TestClient

import fincrime_os.state.loader as loader
from fincrime_os.api.main import app
from fincrime_os.monitoring.quality import build_report
from fincrime_os.monitoring.quality_loader import load_quality_report

client = TestClient(app)


def _row(segment, decision, is_fraud=None, is_false_decline=None, churned=None):
    return {
        "segment": {"customer_tier": segment},
        "decision": decision,
        "is_fraud": is_fraud,
        "is_false_decline": is_false_decline,
        "churned_after_decline": churned,
    }


def test_empty_report():
    r = build_report([], version="v0", window_days=30)
    assert r.total_outcomes == 0
    assert r.overall_miss_rate == 0.0
    assert r.overall_false_decline_rate == 0.0
    assert r.segments == {}


def test_missed_detection_counted():
    rows = [
        _row("default", "APPROVE", is_fraud=True),
        _row("default", "APPROVE", is_fraud=False),
        _row("default", "DECLINE", is_fraud=True),
    ]
    r = build_report(rows, version="v1", window_days=30)
    s = r.segments["default"]
    assert s.approves == 2
    assert s.missed_detections == 1
    assert s.detection_miss_rate == 0.5


def test_false_decline_counted():
    rows = [
        _row("vip", "DECLINE", is_false_decline=True, churned=True),
        _row("vip", "CHALLENGE", is_false_decline=True, churned=False),
        _row("vip", "DECLINE", is_false_decline=False),
    ]
    r = build_report(rows, version="v1", window_days=30)
    s = r.segments["vip"]
    assert s.declines_and_challenges == 3
    assert s.false_declines == 2
    assert abs(s.false_decline_rate - 2 / 3) < 1e-9
    assert s.churn_after_decline == 1
    assert abs(s.churn_rate - 1 / 3) < 1e-9


def test_per_segment_isolation():
    rows = [
        _row("vip", "APPROVE", is_fraud=True),
        _row("default", "APPROVE", is_fraud=False),
    ]
    r = build_report(rows, version="v1", window_days=30)
    assert r.segments["vip"].missed_detections == 1
    assert r.segments["default"].missed_detections == 0


def test_publish_and_load(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    rows = [
        _row("default", "APPROVE", is_fraud=True),
        _row("default", "DECLINE", is_false_decline=True),
    ]
    from fincrime_os.monitoring.quality import as_dict
    r = build_report(rows, version="v-q", window_days=7)
    loader.publish("quality_metrics", "v-q", as_dict(r))
    loaded = load_quality_report()
    assert loaded is not None
    assert loaded.version == "v-q"
    assert loaded.total_outcomes == 2
    assert "default" in loaded.segments


def test_endpoint_available_false_when_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    r = client.get("/metrics/quality")
    assert r.status_code == 200
    assert r.json()["available"] is False


def test_endpoint_returns_published(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    from fincrime_os.monitoring.quality import as_dict
    rows = [
        _row("default", "APPROVE", is_fraud=True),
        _row("default", "APPROVE", is_fraud=False),
    ]
    report = build_report(rows, version="v-endpoint", window_days=7)
    loader.publish("quality_metrics", "v-endpoint", as_dict(report))

    r = client.get("/metrics/quality")
    assert r.status_code == 200
    body = r.json()
    assert body["available"] is True
    assert body["version"] == "v-endpoint"
    assert body["total_outcomes"] == 2
    assert len(body["segments"]) == 1
    seg = body["segments"][0]
    assert seg["segment_key"] == "default"
    assert seg["detection_miss_rate"] == 0.5