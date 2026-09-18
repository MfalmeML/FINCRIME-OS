from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from fincrime_os.features.contracts import EventSequence
from fincrime_os.ingestion.contracts import AccountEvent

DEFAULT_WINDOW_MINUTES = 60


def _event_to_dict(e: AccountEvent) -> dict:
    return {
        "event_id": e.event_id,
        "kind": e.kind,
        "occurred_at": e.occurred_at.isoformat(),
        "payload": e.payload,
    }


def build_sequence(
    account_id: str,
    events: Iterable[AccountEvent],
    decision_time: datetime,
    window_minutes: int = DEFAULT_WINDOW_MINUTES,
) -> EventSequence:
    cutoff = decision_time
    window_start = decision_time - timedelta(minutes=window_minutes)
    selected = [
        e
        for e in events
        if e.account_id == account_id
        and window_start <= e.occurred_at <= cutoff
    ]
    selected.sort(key=lambda e: e.occurred_at)
    return EventSequence(
        account_id=account_id,
        events=[_event_to_dict(e) for e in selected],
        as_of=decision_time,
    )