from __future__ import annotations
from datetime import datetime, timezone
from fastapi import FastAPI

from fincrime_os.api.schemas import DecisionRequest, DecisionResponse
from fincrime_os.decision_engine.policy import decide
from fincrime_os.features.contracts import (
    TransactionFeatures,
    BehavioralBaseline,
    EventSequence,
    GraphFeatures,
)
from fincrime_os.pipeline import Pipeline

app = FastAPI(title="FINCRIME OS", version="0.0.2")

THRESHOLD_TABLE_VERSION = "2026-09-15T00:00Z-v0"
_pipeline = Pipeline()


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


@app.post("/decision", response_model=DecisionResponse)
def decision(req: DecisionRequest) -> DecisionResponse:
    now = _now()
    tx = TransactionFeatures(
        transaction_id=req.transaction_id,
        account_id=req.account_id,
        device_id=req.device_id,
        amount=req.transaction_amount,
        currency=req.currency,
        merchant_id="unknown",
        mcc=req.segment.merchant_category,
        country=req.segment.geography,
        channel=req.segment.channel,
        event_time=now,
        as_of=now,
    )
    baseline = BehavioralBaseline(
        account_id=req.account_id,
        txn_per_day=0.0,
        avg_amount=0.0,
        typical_hours=(0, 23),
        typical_countries=frozenset(),
        typical_devices=frozenset(),
        as_of=now,
    )
    sequence = EventSequence(
        account_id=req.account_id,
        events=[],
        as_of=now,
    )
    graph_features = GraphFeatures(
        account_id=req.account_id,
        device_id=req.device_id,
        connected_accounts=0,
        confirmed_fraud_neighbors=req.graph_confirmed_members,
        graph_ring_score=req.graph_ring_score,
        graph_confirmed_members=req.graph_confirmed_members,
        graph_snapshot_version="api-stub",
        as_of=now,
    )

    bundle = _pipeline.score(tx, baseline, sequence, graph_features)

    decision, reason = decide(
        combined_risk_score=bundle.combined_risk_score,
        graph_ring_score=bundle.graph_ring_score,
        graph_confirmed_members=bundle.graph_confirmed_members,
        segment_key=req.segment.customer_tier,
    )

    return DecisionResponse(
        transaction_id=req.transaction_id,
        decision=decision,
        decision_reason=reason,
        graph_degraded=bundle.graph_degraded,
        threshold_table_version=THRESHOLD_TABLE_VERSION,
        model_versions=bundle.model_versions,
        explanation_ref=f"exp_{req.transaction_id}",
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}