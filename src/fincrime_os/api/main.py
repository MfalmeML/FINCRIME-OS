from __future__ import annotations
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request

from fincrime_os.api.schemas import (
    DecisionRequest,
    DecisionResponse,
    ExplanationOut,
    ReasonCodeOut,
)
from fincrime_os.config import default_config
from fincrime_os.decision_engine.policy import decide
from fincrime_os.explainability.explainer import Explainer
from fincrime_os.features.contracts import (
    TransactionFeatures,
    BehavioralBaseline,
    EventSequence,
    GraphFeatures,
)
from fincrime_os.features.sequence_builder import build_sequence
from fincrime_os.ingestion.contracts import AccountEvent
from fincrime_os.ingestion.replay import FileReplaySource
from fincrime_os.logging_config import configure_logging
from fincrime_os.pipeline import Pipeline

configure_logging()
log = logging.getLogger("fincrime_os.api")

app = FastAPI(title="FINCRIME OS", version="0.0.6")

CFG = default_config()
_pipeline = Pipeline()
_explainer = Explainer()

REPLAY_PATH = Path("data/events.jsonl")
_REPLAYED: list[AccountEvent] = (
    list(FileReplaySource(REPLAY_PATH).stream()) if REPLAY_PATH.exists() else []
)


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _sequence_for(account_id: str, decision_time: datetime) -> EventSequence:
    if not _REPLAYED:
        return EventSequence(account_id=account_id, events=[], as_of=decision_time)
    return build_sequence(account_id, _REPLAYED, decision_time)


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    response.headers["X-Latency-Ms"] = f"{elapsed_ms:.2f}"
    if request.url.path == "/decision":
        log.info("decision_request", extra={"latency_ms": round(elapsed_ms, 2)})
    return response


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict:
    return {
        "platform_version": app.version,
        "threshold_table_version": CFG.threshold_table.version,
        "graph_override": {
            "ring_score_cutoff": CFG.graph_override.ring_score_cutoff,
            "min_confirmed_members": CFG.graph_override.min_confirmed_members,
        },
        "latency_budget_ms": CFG.latency_budget_ms,
        "model_versions": _pipeline.model_versions(),
        "replayed_events": len(_REPLAYED),
    }


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
    sequence = _sequence_for(req.account_id, now)
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
        combined_risk_score=req.combined_risk_score,
        graph_ring_score=req.graph_ring_score,
        graph_confirmed_members=req.graph_confirmed_members,
        segment_key=req.segment.customer_tier,
        graph_cfg=CFG.graph_override,
        threshold_table=CFG.threshold_table,
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

    log.info(
        "decision",
        extra={
            "transaction_id": req.transaction_id,
            "decision": decision,
            "decision_reason": reason,
            "graph_degraded": bundle.graph_degraded,
        },
    )

    return DecisionResponse(
        transaction_id=req.transaction_id,
        decision=decision,
        decision_reason=reason,
        graph_degraded=bundle.graph_degraded,
        threshold_table_version=CFG.threshold_table.version,
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


from fincrime_os.api.queue_router import router as investigation_router  # noqa: E402

app.include_router(investigation_router)