from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from fincrime_os.state.loader import load_latest


@dataclass(frozen=True)
class GraphSnapshot:
    version: str
    ring_scores: dict[str, float] = field(default_factory=dict)
    confirmed_members: dict[str, int] = field(default_factory=dict)
    connected_accounts: dict[str, int] = field(default_factory=dict)
    confirmed_fraud_neighbors: dict[str, int] = field(default_factory=dict)

    def for_account(self, account_id: str) -> dict:
        return {
            "graph_ring_score": self.ring_scores.get(account_id, 0.0),
            "graph_confirmed_members": self.confirmed_members.get(account_id, 0),
            "connected_accounts": self.connected_accounts.get(account_id, 0),
            "confirmed_fraud_neighbors": self.confirmed_fraud_neighbors.get(account_id, 0),
            "graph_snapshot_version": self.version,
        }


def load_snapshot() -> GraphSnapshot:
    artifact = load_latest("graph_snapshots")
    if artifact is None:
        return GraphSnapshot(version="unversioned-dev")
    p = artifact.payload
    return GraphSnapshot(
        version=artifact.version,
        ring_scores={k: float(v) for k, v in (p.get("ring_scores") or {}).items()},
        confirmed_members={k: int(v) for k, v in (p.get("confirmed_members") or {}).items()},
        connected_accounts={k: int(v) for k, v in (p.get("connected_accounts") or {}).items()},
        confirmed_fraud_neighbors={
            k: int(v) for k, v in (p.get("confirmed_fraud_neighbors") or {}).items()
        },
    )


def snapshot_age_seconds(version: str) -> float | None:
    from fincrime_os.state.loader import STATE_ROOT

    path = STATE_ROOT / "graph_snapshots" / f"{version}.json"
    if not path.exists():
        return None
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    return (datetime.now(tz=UTC) - mtime).total_seconds()


def is_fresh(version: str, max_age_seconds: int) -> bool:
    age = snapshot_age_seconds(version)
    if age is None:
        return False
    return age <= max_age_seconds