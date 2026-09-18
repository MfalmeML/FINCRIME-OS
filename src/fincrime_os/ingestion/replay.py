from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from fincrime_os.ingestion.contracts import AccountEvent


def _parse(payload: dict) -> AccountEvent:
    return AccountEvent(
        event_id=payload["event_id"],
        account_id=payload["account_id"],
        kind=payload["kind"],
        occurred_at=datetime.fromisoformat(payload["occurred_at"]),
        payload=payload.get("payload", {}),
    )


class FileReplaySource:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def stream(self) -> Iterator[AccountEvent]:
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield _parse(json.loads(line))