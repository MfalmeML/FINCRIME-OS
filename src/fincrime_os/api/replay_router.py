from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from fincrime_os.api.schemas import ReplaySequenceResponse
from fincrime_os.features.sequence_builder import (
    DEFAULT_WINDOW_MINUTES,
    build_sequence,
)
from fincrime_os.ingestion.replay import FileReplaySource

router = APIRouter(tags=["replay"])

REPLAY_PATH = Path("data/events.jsonl")


def _load_events():
    if not REPLAY_PATH.exists():
        return []
    return list(FileReplaySource(REPLAY_PATH).stream())


@router.get("/replay/sequence/{account_id}", response_model=ReplaySequenceResponse)
def replay_sequence(
    account_id: str,
    window_minutes: int = Query(default=DEFAULT_WINDOW_MINUTES, ge=1, le=1440),
) -> ReplaySequenceResponse:
    events = _load_events()
    if not events:
        raise HTTPException(status_code=404, detail="no replayed events available")
    decision_time = datetime.now(tz=UTC)
    seq = build_sequence(
        account_id=account_id,
        events=events,
        decision_time=decision_time,
        window_minutes=window_minutes,
    )
    return ReplaySequenceResponse(
        account_id=seq.account_id,
        as_of=seq.as_of.isoformat(),
        window_minutes=window_minutes,
        events=seq.events,
    )