from datetime import UTC, datetime, timedelta

from fincrime_os.features.sequence_builder import build_sequence
from fincrime_os.ingestion.contracts import AccountEvent

T0 = datetime(2026, 9, 15, 2, 13, tzinfo=UTC)


def _evt(eid, kind, minutes_before, account="cust_1"):
    return AccountEvent(
        event_id=eid,
        account_id=account,
        kind=kind,
        occurred_at=T0 - timedelta(minutes=minutes_before),
        payload={},
    )


def test_sequence_only_includes_window():
    events = [
        _evt("e1", "login", 22),
        _evt("e2", "device_registration", 18),
        _evt("e3", "transfer", 10),
        _evt("e4", "transfer", 500),
    ]
    seq = build_sequence("cust_1", events, T0)
    kinds = [e["kind"] for e in seq.events]
    assert kinds == ["login", "device_registration", "transfer"]


def test_sequence_excludes_future_events():
    events = [
        _evt("e1", "login", 5),
        AccountEvent(
            event_id="e_future",
            account_id="cust_1",
            kind="transfer",
            occurred_at=T0 + timedelta(seconds=1),
            payload={},
        ),
    ]
    seq = build_sequence("cust_1", events, T0)
    assert len(seq.events) == 1
    assert seq.events[0]["event_id"] == "e1"


def test_sequence_isolates_account():
    events = [
        _evt("a", "login", 5, account="cust_1"),
        _evt("b", "login", 5, account="cust_2"),
    ]
    seq = build_sequence("cust_1", events, T0)
    assert [e["event_id"] for e in seq.events] == ["a"]


def test_sequence_is_ordered_chronologically():
    events = [
        _evt("late", "transfer", 1),
        _evt("early", "login", 20),
        _evt("mid", "device_registration", 10),
    ]
    seq = build_sequence("cust_1", events, T0)
    assert [e["event_id"] for e in seq.events] == ["early", "mid", "late"]