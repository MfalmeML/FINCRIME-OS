from __future__ import annotations
from datetime import datetime, timezone
from fastapi import FastAPI

from fincrime_os.api.schemas import (
    DecisionRequest,
    DecisionResponse,
    ExplanationOut,
    ReasonCodeOut,
)
from fincrime_os.decision_engine.policy import decide
from fincrime_os.explainability.explainer import Explainer
from fincrime_os.features.contracts import (
    TransactionFeatures,
    BehavioralBaseline,
    EventSequence,
    GraphFeatures,
)
from fincrime_os.pipeline import Pipeline

app = FastAPI(title="FINCRIME OS", version="0.0.3")

THRESHOLD_TABLE_VERSION = "2026-09-15T00:00Z-v0"
_pipeline = Pipeline()
_explainer = Explainer()


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
        avg_amount=req.customer_avg_amount,
        typical_hours=(0, 23),
        typical_countries=frozenset(),
        typical_devices=frozenset(),
        as_of=now,
    )
    sequence = EventSequence(account_id=req.account_id, events=[], as_of=now)
    graph_features = GraphFeatures(
        account_id=req.account_id,
        device_id=req.device_id,
        connected_accounts=req.connected_accounts,
        confirmed_fraud_neighbors=req.confirmed_fraud_neighbors,
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

    explanation = _explainer.build(
        transaction_id=req.transaction_id,
        decision=decision,
        amount=req.transaction_amount,
        avg_amount=req.customer_avg_amount,
        connected_accounts=req.connected_accounts,
        confirmed_fraud_neighbors=req.confirmed_fraud_neighbors,
        graph_ring_score=req.graph_ring_score,
        graph_confirmed_members=req.graph_confirmed_members,
        sequence_risk_score=req.sequence_risk_score,
        behavioral_anomaly_score=req.behavioral_anomaly_score,
        transaction_risk=req.transaction_risk,
    )

    return DecisionResponse(
        transaction_id=req.transaction_id,
        decision=decision,
        decision_reason=reason,
        graph_degraded=bundle.graph_degraded,
        threshold_table_version=THRESHOLD_TABLE_VERSION,
        model_versions=bundle.model_versions,
        explanation_ref=f"exp_{req.transaction_id}",
        explanation=ExplanationOut(
            transaction_id=explanation.transaction_id,
            decision=explanation.decision,
            reason_codes=[
                ReasonCodeOut(
                    code=c.code,
                    text=c.text,
                    evidence_value=c.evidence_value,
                    source=c.source,
                )
                for c in explanation.reason_codes
            ],
            counterfactual=explanation.counterfactual,
            complete=explanation.complete,
        ),
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}