
from datetime import UTC

import fincrime_os.state.loader as loader
import fincrime_os.state.outcomes as outcomes_mod
from fincrime_os.pipeline.auto_rebuild import (
    AutoRebuildThrottle,
    auto_rebuild_enabled,
)
from fincrime_os.pipeline.rebuild import rebuild_all


def _write_outcome(rows_mod_path, day: str, record: dict) -> None:
    import json
    path = rows_mod_path / f"{day}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def test_auto_rebuild_disabled_by_env():
    # conftest.py sets FINCRIME_AUTO_REBUILD=0 by default
    assert auto_rebuild_enabled() is False


def test_throttle_blocks_within_interval():
    t = AutoRebuildThrottle(min_interval_seconds=60.0)
    assert t.should_run() is True
    assert t.should_run() is False
    assert t.should_run() is False


def test_throttle_reset_allows_rerun():
    t = AutoRebuildThrottle(min_interval_seconds=60.0)
    assert t.should_run() is True
    assert t.should_run() is False
    t.reset()
    assert t.should_run() is True


def test_rebuild_all_publishes_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path / "state")
    monkeypatch.setattr(outcomes_mod, "OUTCOMES_ROOT", tmp_path / "outcomes")

    day = "2026-09-18"
    _write_outcome(
        outcomes_mod.OUTCOMES_ROOT,
        day,
        {
            "transaction_id": "tx_1",
            "account_id": "cust_1",
            "decision": "DECLINE",
            "decided_at": "2026-09-18T10:00:00+00:00",
            "observed_at": "2026-09-18T10:05:00+00:00",
            "is_fraud": True,
            "is_ring_member": None,
            "is_false_decline": False,
            "churned_after_decline": False,
            "investigation_outcome": "confirmed_fraud",
            "transaction_amount": 500.0,
            "segment": {"customer_tier": "default"},
        },
    )

    # Override today so _read_window picks up our test day
    from datetime import date as _date

    import fincrime_os.pipeline.rebuild as rebuild_mod

    class _FixedDate(_date):
        @classmethod
        def today(cls):
            return cls(2026, 9, 18)

    monkeypatch.setattr(rebuild_mod, "datetime", type("D", (), {
        "now": staticmethod(lambda tz=None: __import__("datetime").datetime(2026, 9, 18, tzinfo=tz))
    }))
    # Simpler: force window day by directly writing today's date file too.
    from datetime import datetime
    today = datetime.now(tz=UTC).strftime("%Y-%m-%d")
    _write_outcome(
        outcomes_mod.OUTCOMES_ROOT,
        today,
        {
            "transaction_id": "tx_2",
            "account_id": "cust_2",
            "decision": "APPROVE",
            "decided_at": f"{today}T10:00:00+00:00",
            "observed_at": f"{today}T10:05:00+00:00",
            "is_fraud": False,
            "is_false_decline": None,
            "churned_after_decline": None,
            "investigation_outcome": None,
            "transaction_amount": 100.0,
            "segment": {"customer_tier": "default"},
        },
    )

    result = rebuild_all(window_days=1, version="v-auto")
    assert result.version == "v-auto"
    assert result.rows >= 1
    assert "cost_model_inputs" in result.published
    assert "drift_signals" in result.published
    assert "quality_metrics" in result.published
    assert "threshold_tables" in result.published

    for kind in result.published:
        a = loader.load_version(kind, "v-auto")
        assert a is not None
        assert a.version == "v-auto"
