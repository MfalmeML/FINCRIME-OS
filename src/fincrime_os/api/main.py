from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
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
    BehavioralBaseline,
    EventSequence,
    GraphFeatures,
    TransactionFeatures,
)
from fincrime_os.features.sequence_builder import build_sequence
from fincrime_os.ingestion.contracts import AccountEvent
from fincrime_os.ingestion.replay import FileReplaySource
from fincrime_os.logging_config import configure_logging
from fincrime_os.monitoring.runtime_metrics import get_metrics  # noqa: E402
from fincrime_os.pipeline import Pipeline
from fincrime_os.rollout.contracts import (
    SignalStage,
    stage_allows_behavioral,
    stage_allows_graph,
    stage_allows_temporal,
)
from fincrime_os.rollout.loader import load_rollout
from fincrime_os.rollout.resolver import effective_stage

configure_logging()
log = logging.getLogger("fincrime_os.api")

app = FastAPI(title="FINCRIME OS", version="0.8.1")

from fincrime_os.state.graph_snapshot import load_snapshot  # noqa: E402

CFG = default_config()
_pipeline = Pipeline()
_explainer = Explainer()
_graph_snapshot = load_snapshot()
_rollout = load_rollout()

REPLAY_PATH = Path("data/events.jsonl")
_REPLAYED: list[AccountEvent] = (
    list(FileReplaySource(REPLAY_PATH).stream()) if REPLAY_PATH.exists() else []
)


def _now() -> datetime:
    return datetime.now(tz=UTC)


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
        "graph_snapshot_version": _graph_snapshot.version,
        "graph_override": {
            "ring_score_cutoff": CFG.graph_override.ring_score_cutoff,
            "min_confirmed_members": CFG.graph_override.min_confirmed_members,
        },
        "latency_budget_ms": CFG.latency_budget_ms,
        "model_versions": _pipeline.model_versions(),
        "model_trained": _pipeline.registry.trained,
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
    snapshot_row = _graph_snapshot.for_account(req.account_id)

    def _prefer(request_val, snapshot_val):
        return request_val if request_val else snapshot_val

    connected_accounts = _prefer(req.connected_accounts, snapshot_row["connected_accounts"])
    confirmed_fraud_neighbors = _prefer(
        req.confirmed_fraud_neighbors, snapshot_row["confirmed_fraud_neighbors"]
    )
    graph_ring_score = _prefer(req.graph_ring_score, snapshot_row["graph_ring_score"])
    graph_confirmed_members = _prefer(
        req.graph_confirmed_members, snapshot_row["graph_confirmed_members"]
    )

    graph_features = GraphFeatures(
        account_id=req.account_id,
        device_id=req.device_id,
        connected_accounts=connected_accounts,
        confirmed_fraud_neighbors=confirmed_fraud_neighbors,
        graph_ring_score=graph_ring_score,
        graph_confirmed_members=graph_confirmed_members,
        graph_snapshot_version=snapshot_row["graph_snapshot_version"],
        as_of=now,
    )

    bundle = _pipeline.score(tx, baseline, sequence, graph_features)
    get_metrics().record_decision(graph_degraded=bundle.graph_degraded)

    rollout_row = _rollout.resolve(req.segment.customer_tier)
    stage = effective_stage(req.transaction_id, rollout_row)

    # Signal-stage gating: zero out signals the current stage does not include.
    # The pipeline still runs all models; gating only affects what the fusion
    # layer and decision engine consume. This is the mechanism that lets a
    # segment go from transaction-only to full rollout without redeploying.
    gated_transaction = bundle.transaction_risk
    gated_behavioral = (
        bundle.behavioral_anomaly_score if stage_allows_behavioral(stage) else 0.0
    )
    gated_sequence = (
        bundle.sequence_risk_score if stage_allows_temporal(stage) else 0.0
    )
    gated_graph = bundle.graph_ring_score if stage_allows_graph(stage) else 0.0
    gated_graph_members = (
        bundle.graph_confirmed_members if stage_allows_graph(stage) else 0
    )

    from fincrime_os.features.baseline_risk import customer_baseline_risk as _cbr

    gated_combined = _pipeline.fusion.predict(
        gated_transaction,
        gated_behavioral,
        gated_sequence,
        gated_graph,
        _cbr(baseline),
    )

    decision, reason = decide(
        combined_risk_score=gated_combined,
        graph_ring_score=gated_graph,
        graph_confirmed_members=gated_graph_members,
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

from fincrime_os.api.ops_router import router as ops_router  # noqa: E402

app.include_router(ops_router)

from fincrime_os.api.replay_router import router as replay_router  # noqa: E402

app.include_router(replay_router)

from fincrime_os.api.outcome_router import router as outcome_router  # noqa: E402

app.include_router(outcome_router)

from fastapi.responses import FileResponse  # noqa: E402

from fincrime_os.api.case_router import router as case_router  # noqa: E402

app.include_router(case_router)

_STATIC = Path(__file__).parent / "static"


@app.get("/workspace", include_in_schema=False)
def workspace() -> FileResponse:
    return FileResponse(_STATIC / "workspace.html")
from fincrime_os.monitoring.quality_router import router as quality_router  # noqa: E402

app.include_router(quality_router)
