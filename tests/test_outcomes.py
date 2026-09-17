from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

import fincrime_os.state.outcomes as outcomes_mod
from fincrime_os.api.main import app

client = TestClient(app)

T_DECIDED = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def isolated_outcomes(tmp_path, monkeypatch):
    root = tmp_path / "outcomes"
    monkeypatch.setattr(outcomes_mod, "OUTCOMES_ROOT", root)
    return root


def _payload(observed_offset_seconds=60, **overrides):
    observed = T_DECIDED + timedelta(seconds=observed_offset_seconds)
    base = {
        "transaction_id": "tx_1",
        "account_id": "cust_1",
        "decision": "DECLINE",
        "decided_at": T_DECIDED.isoformat(),
        "observed_at": observed.isoformat(),
        "is_fraud": True,
        "is_ring_member": True,
        "is_false_decline": False,
        "churned_after_decline": False,
        "investigation_outcome": "confirmed_fraud",
    }
    base.update(overrides)
    return base


def test_outcome_stored(isolated_outcomes):
    r = client.post("/outcome", json=_payload())
    assert r.status_code == 200
    body = r.json()
    assert body["transaction_id"] == "tx_1"
    files = list(isolated_outcomes.glob("*.jsonl"))
    assert len(files) == 1
    assert "tx_1" in files[0].read_text(encoding="utf-8")


def test_outcome_rejects_future_label(isolated_outcomes):
    r = client.post("/outcome", json=_payload(observed_offset_seconds=-10))
    assert r.status_code == 422


def test_outcome_accepts_partial_labels(isolated_outcomes):
    r = client.post(
        "/outcome",
        json=_payload(is_fraud=None, is_ring_member=None, investigation_outcome=None),
    )
    assert r.status_code == 200


def test_outcome_appends_multiple(isolated_outcomes):
    client.post("/outcome", json=_payload())
    client.post("/outcome", json=_payload(transaction_id="tx_2"))
    files = list(isolated_outcomes.glob("*.jsonl"))
    content = files[0].read_text(encoding="utf-8")
    assert content.count("\n") == 2


def test_outcome_round_trip_read(isolated_outcomes):
    client.post("/outcome", json=_payload())
    day = T_DECIDED.strftime("%Y-%m-%d")
    rows = outcomes_mod.read_outcomes(day)
    assert len(rows) == 1
    assert rows[0]["is_fraud"] is True
    assert rows[0]["investigation_outcome"] == "confirmed_fraud"