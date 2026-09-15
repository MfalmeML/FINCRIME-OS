from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TransactionFeatures:
    transaction_id: str
    account_id: str
    device_id: str
    amount: float
    currency: str
    merchant_id: str
    mcc: str
    country: str
    channel: str
    event_time: datetime
    as_of: datetime


@dataclass(frozen=True)
class BehavioralBaseline:
    account_id: str
    txn_per_day: float
    avg_amount: float
    typical_hours: tuple[int, int]
    typical_countries: frozenset[str]
    typical_devices: frozenset[str]
    as_of: datetime


@dataclass(frozen=True)
class EventSequence:
    account_id: str
    events: list[dict]
    as_of: datetime


@dataclass(frozen=True)
class GraphFeatures:
    account_id: str
    device_id: str
    connected_accounts: int
    confirmed_fraud_neighbors: int
    graph_ring_score: float
    graph_confirmed_members: int
    graph_snapshot_version: str
    as_of: datetime