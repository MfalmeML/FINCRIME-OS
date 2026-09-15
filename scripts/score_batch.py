from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from fincrime_os.decision_engine.policy import decide
from fincrime_os.features.contracts import (
    BehavioralBaseline,
    EventSequence,
    GraphFeatures,
    TransactionFeatures,
)
from fincrime_os.features.sequence_builder import build_sequence
from fincrime_os.ingestion.replay import FileReplaySource
from fincrime_os.pipeline import Pipeline


def _transfer_amount(event) -> float:
    return float(event.payload.get("amount", 100.0))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--events", default="data/events.jsonl")
    p.add_argument("--out", default="artifacts/decisions.jsonl")
    args = p.parse_args()

    events_path = Path(args.events)
    if not events_path.exists():
        raise SystemExit(f"missing events file: {events_path}")

    events = list(FileReplaySource(events_path).stream())
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pipeline = Pipeline()
    now = datetime.now(tz=timezone.utc)
    written = 0

    with out_path.open("w", encoding="utf-8") as f:
        for e in events:
            if e.kind != "transfer":
                continue
            tx = TransactionFeatures(
                transaction_id=e.event_id,
                account_id=e.account_id,
                device_id=e.payload.get("device_id", "unknown"),
                amount=_transfer_amount(e),
                currency=e.payload.get("currency", "KES"),
                merchant_id="unknown",
                mcc="0000",
                country=e.payload.get("country", "KE"),
                channel="app",
                event_time=e.occurred_at,
                as_of=e.occurred_at,
            )
            baseline = BehavioralBaseline(
                account_id=e.account_id,
                txn_per_day=0.0,
                avg_amount=0.0,
                typical_hours=(0, 23),
                typical_countries=frozenset(),
                typical_devices=frozenset(),
                as_of=e.occurred_at,
            )
            sequence = build_sequence(e.account_id, events, e.occurred_at)
            graph = GraphFeatures(
                account_id=e.account_id,
                device_id=tx.device_id,
                connected_accounts=0,
                confirmed_fraud_neighbors=0,
                graph_ring_score=0.0,
                graph_confirmed_members=0,
                graph_snapshot_version="offline-stub",
                as_of=e.occurred_at,
            )
            bundle = pipeline.score(tx, baseline, sequence, graph)
            decision, reason = decide(
                combined_risk_score=bundle.combined_risk_score,
                graph_ring_score=bundle.graph_ring_score,
                graph_confirmed_members=bundle.graph_confirmed_members,
            )
            f.write(
                json.dumps(
                    {
                        "transaction_id": tx.transaction_id,
                        "account_id": tx.account_id,
                        "amount": tx.amount,
                        "currency": tx.currency,
                        "occurred_at": e.occurred_at.isoformat(),
                        "combined_risk_score": bundle.combined_risk_score,
                        "decision": decision,
                        "decision_reason": reason,
                        "graph_degraded": bundle.graph_degraded,
                        "sequence_events": len(sequence.events),
                        "scored_at": now.isoformat(),
                    }
                )
                + "\n"
            )
            written += 1

    print(f"wrote {written} decisions to {out_path}")


if __name__ == "__main__":
    main()