from datetime import UTC, datetime, timedelta

import fincrime_os.state.loader as loader
from fincrime_os.drift.outcome_drift import compute_outcome_drift
from fincrime_os.drift.snapshot_loader import load_drift_snapshot

BASE = datetime(2026, 9, 1, tzinfo=UTC)


def _row(i, is_fraud, is_false_decline=False):
    return {
        "transaction_id": f"tx_{i}",
        "decision": "DECLINE" if is_fraud else "APPROVE",
        "is_fraud": is_fraud,
        "is_false_decline": is_false_decline,
        "observed_at": (BASE + timedelta(hours=i)).isoformat(),
    }


def test_empty_rows_multiplier_is_one():
    s = compute_outcome_drift([], version="v0", window_days=30)
    assert s.fraud_rate_multiplier == 1.0
    assert s.any_fired is False


def test_stable_rate_no_fire():
    rows = [_row(i, is_fraud=False) for i in range(20)]
    s = compute_outcome_drift(rows, version="v0", window_days=30)
    assert s.recent_fraud_rate == 0.0
    assert s.baseline_fraud_rate == 0.0
    assert s.any_fired is False


def test_fraud_spike_fires():
    rows = []
    for i in range(20):
        rows.append(_row(i, is_fraud=False))
    for i in range(20, 28):
        rows.append(_row(i, is_fraud=True))
    s = compute_outcome_drift(rows, version="v0", window_days=30)
    assert s.recent_fraud_rate > s.baseline_fraud_rate
    assert s.fraud_rate_multiplier > 1.0
    assert s.any_fired is True


def test_publish_then_load(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    rows = [_row(i, is_fraud=False) for i in range(10)]
    s = compute_outcome_drift(rows, version="v-drift", window_days=7)
    from fincrime_os.drift.outcome_drift import as_dict
    loader.publish("drift_signals", "v-drift", as_dict(s))

    loaded = load_drift_snapshot()
    assert loaded is not None
    assert loaded.version == "v-drift"
    assert loaded.window_days == 7


def test_load_returns_none_when_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    assert load_drift_snapshot() is None