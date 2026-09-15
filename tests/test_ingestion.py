import json
from datetime import datetime, timezone
from pathlib import Path

from fincrime_os.ingestion.replay import FileReplaySource


def _write(tmp_path: Path) -> Path:
    p = tmp_path / "events.jsonl"
    lines = [
        {
            "event_id": "evt_1",
            "account_id": "cust_1",
            "kind": "login",
            "occurred_at": datetime(2026, 9, 15, 1, 51, tzinfo=timezone.utc).isoformat(),
            "payload": {"device_id": "D1"},
        },
        {
            "event_id": "evt_2",
            "account_id": "cust_1",
            "kind": "transfer",
            "occurred_at": datetime(2026, 9, 15, 1, 57, tzinfo=timezone.utc).isoformat(),
            "payload": {"amount": 8700},
        },
    ]
    p.write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")
    return p


def test_replay_streams_events(tmp_path):
    src = FileReplaySource(_write(tmp_path))
    events = list(src.stream())
    assert len(events) == 2
    assert events[0].kind == "login"
    assert events[1].kind == "transfer"
    assert events[1].payload["amount"] == 8700


def test_replay_skips_blank_lines(tmp_path):
    p = tmp_path / "events.jsonl"
    p.write_text("\n\n", encoding="utf-8")
    src = FileReplaySource(p)
    assert list(src.stream()) == []