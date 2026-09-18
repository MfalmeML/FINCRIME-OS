from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

EventKind = Literal[
    "login",
    "password_change",
    "device_registration",
    "beneficiary_addition",
    "transfer",
]


@dataclass(frozen=True)
class AccountEvent:
    event_id: str
    account_id: str
    kind: EventKind
    occurred_at: datetime
    payload: dict


class EventSource(Protocol):
    def stream(self) -> Iterator[AccountEvent]: ...