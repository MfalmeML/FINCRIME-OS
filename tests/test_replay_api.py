import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

import fincrime_os.api.replay_router as replay_router
from fincrime_os.api.main import app

client = TestClient(app)


def test_replay_returns_filtered_sequence(tmp_path, monkeypatch):
    now = datetime.now(tz=timezone.utc)
    rows = [
        {
            "event_id": "e1",
            "account_id": "cust_1",
            "kind": "login",
            "occurred_at": (now - timedelta(minutes=10)).isoformat(),
            "payload": {},
        },
        {
            "event_id": "e2",
            "account_id": "cust_1",
            "kind": "transfer",
            "occurred_at": (now - timedelta(minutes=5)).isoformat(),
            "payload": {"amount": 500},
        },
        {
            "event_id": "e3",
            "account_id": "cust_2",
            "kind": "login",
            "occurred_at": (now - timedelta(minutes=5)).isoformat(),
            "payload": {},
        },
    ]
    p = tmp_path / "events.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")

    monkeypatch.setattr(replay_router, "REPLAY_PATH", p)

    r = client.get("/replay/sequence/cust_1", params={"window_minutes": 30})
    assert r.status_code == 200
    body = r.json()
    assert body["account_id"] == "cust_1"
    assert [e["event_id"] for e in body["events"]] == ["e1", "e2"]


def test_replay_404_when_no_events(tmp_path, monkeypatch):
    monkeypatch.setattr(replay_router, "REPLAY_PATH", tmp_path / "missing.jsonl")
    r = client.get("/replay/sequence/cust_1")
    assert r.status_code == 404