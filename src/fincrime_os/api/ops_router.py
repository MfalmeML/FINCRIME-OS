from __future__ import annotations

from datetime import UTC, datetime as _dt, timedelta as _td
from pathlib import Path

from fastapi import APIRouter

from fincrime_os.api.schemas import (
    CanaryRequest,
    CanaryResponse,
    CostInputsOut,
    DriftRequest,
    DriftResponse,
    DriftSignalOut,
    ShadowDivergenceOut,
)
from fincrime_os.config import default_config
from fincrime_os.decision_engine.cost_loader import load_cost_inputs
from fincrime_os.drift.canary import (
    CanaryGate,
    CanaryOutcome,
    VersionRegistry,
    apply_gate,
)
from fincrime_os.drift.detector import DriftDetector
from fincrime_os.drift.snapshot_loader import load_drift_snapshot
from fincrime_os.monitoring.runtime_metrics import get_metrics
from fincrime_os.monitoring.shadow import read_day
from fincrime_os.state.graph_snapshot import is_fresh, load_snapshot, snapshot_age_seconds
from fincrime_os.state.loader import STATE_ROOT, load_latest
from fincrime_os.state.model_registry import load_registry

router = APIRouter(tags=["ops"])

CFG = default_config()
_detector = DriftDetector(
    feature_threshold=CFG.drift.feature_threshold,
    prediction_threshold=CFG.drift.prediction_threshold,
    graph_threshold=CFG.drift.graph_threshold,
    fraud_rate_threshold=CFG.drift.fraud_rate_threshold,
)
_gate = CanaryGate()
_registry = VersionRegistry(
    serving={
        "transaction_model": "txn-dev",
        "behavioral_model": "behav-dev",
        "temporal_model": "seq-dev",
        "graph_model": "graph-dev",
        "fusion_model": "fusion-dev",
        "threshold_table": CFG.threshold_table.version,
    }
)


@router.post("/drift/check", response_model=DriftResponse)
def drift_check(req: DriftRequest) -> DriftResponse:
    signals = _detector.check(
        feature_score=req.feature_score,
        prediction_score=req.prediction_score,
        graph_score=req.graph_score,
        fraud_rate_multiplier=req.fraud_rate_multiplier,
    )
    return DriftResponse(
        any_fired=_detector.any_fired(signals),
        signals=[
            DriftSignalOut(
                component=s.component,
                score=s.score,
                threshold=s.threshold,
                fired=s.fired,
            )
            for s in signals
        ],
    )


@router.get("/drift/current", response_model=DriftResponse)
def drift_current() -> DriftResponse:
    snapshot = load_drift_snapshot()
    if snapshot is None:
        return DriftResponse(any_fired=False, signals=[])
    signals = _detector.check(
        feature_score=snapshot.feature_score,
        prediction_score=snapshot.prediction_score,
        graph_score=snapshot.graph_score,
        fraud_rate_multiplier=snapshot.fraud_rate_multiplier,
    )
    return DriftResponse(
        any_fired=snapshot.any_fired or _detector.any_fired(signals),
        signals=[
            DriftSignalOut(
                component=s.component,
                score=s.score,
                threshold=s.threshold,
                fired=s.fired,
            )
            for s in signals
        ],
    )


@router.post("/canary/evaluate", response_model=CanaryResponse)
def canary_evaluate(req: CanaryRequest) -> CanaryResponse:
    outcome = CanaryOutcome(
        candidate_version=req.candidate_version,
        baseline_version=req.baseline_version,
        candidate_fraud_loss=req.candidate_fraud_loss,
        baseline_fraud_loss=req.baseline_fraud_loss,
        fraud_loss_ceiling=_gate.fraud_loss_ceiling,
    )
    result = apply_gate(_gate, _registry, req.component, outcome)
    serving = _registry.current(req.component) or req.baseline_version
    return CanaryResponse(
        component=req.component,
        result=result,
        serving_version=serving,
    )


@router.get("/cost/inputs", response_model=CostInputsOut)
def cost_inputs() -> CostInputsOut:
    c = load_cost_inputs()
    return CostInputsOut(
        version=c.version,
        window_days=c.window_days,
        total_outcomes=c.total_outcomes,
        declines_observed=c.declines_observed,
        false_declines=c.false_declines,
        churned_after_decline=c.churned_after_decline,
        p_false_decline=c.p_false_decline,
        p_churn_given_decline=c.p_churn_given_decline,
        avg_transaction_amount=c.avg_transaction_amount,
        confirmed_fraud_rate=c.confirmed_fraud_rate,
    )


def _artifact_age_seconds(kind: str) -> float | None:
    artifact = load_latest(kind)
    if artifact is None:
        return None
    path = Path(artifact.path)
    if not path.exists():
        return None
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    return (datetime.now(tz=UTC) - mtime).total_seconds()


@router.get("/health/deep")
def health_deep() -> dict:
    cfg = default_config()
    registry = load_registry()
    cost = load_cost_inputs()
    drift = load_drift_snapshot()
    graph = load_snapshot()
    metrics = get_metrics().snapshot()

    threshold_artifact = load_latest("threshold_tables")
    cost_artifact = load_latest("cost_model_inputs")
    drift_artifact = load_latest("drift_signals")

    return {
        "status": "ok",
        "artifacts": {
            "threshold_tables": {
                "available": threshold_artifact is not None,
                "version": threshold_artifact.version if threshold_artifact else None,
                "age_seconds": _artifact_age_seconds("threshold_tables"),
            },
            "model_versions": {
                "available": load_latest("model_versions") is not None,
                "version": registry.version,
            },
            "graph_snapshots": {
                "available": graph.version != "unversioned-dev",
                "version": graph.version,
                "age_seconds": snapshot_age_seconds(graph.version),
                "fresh": is_fresh(
                    graph.version,
                    cfg.graph_freshness.max_snapshot_age_seconds,
                ),
                "max_age_seconds": cfg.graph_freshness.max_snapshot_age_seconds,
            },
            "cost_model_inputs": {
                "available": cost_artifact is not None,
                "version": cost.version,
                "age_seconds": _artifact_age_seconds("cost_model_inputs"),
            },
            "drift_signals": {
                "available": drift_artifact is not None,
                "version": drift.version if drift else None,
                "age_seconds": _artifact_age_seconds("drift_signals"),
                "any_fired": drift.any_fired if drift else False,
            },
        },
        "runtime": {
            "graph_degraded_rate": metrics["graph_degraded_rate"],
            "graph_degraded_count": metrics["graph_degraded"],
            "decisions_in_window": metrics["decisions"],
            "window_seconds": metrics["window_seconds"],
        },
        "state_root": str(STATE_ROOT),
    }


@router.get("/shadow/divergence", response_model=ShadowDivergenceOut)
def shadow_divergence(window_days: int = 1) -> ShadowDivergenceOut:
    today = _dt.now(tz=UTC).date()
    rows: list[dict] = []
    for offset in range(window_days):
        day = (today - _td(days=offset)).strftime("%Y-%m-%d")
        rows.extend(read_day(day))

    by_live: dict[str, int] = {}
    by_shadow: dict[str, int] = {}
    divergent = 0
    for r in rows:
        live = r.get("live_decision", "UNKNOWN")
        shadow = r.get("shadow_decision", "UNKNOWN")
        by_live[live] = by_live.get(live, 0) + 1
        by_shadow[shadow] = by_shadow.get(shadow, 0) + 1
        if r.get("divergence"):
            divergent += 1

    total = len(rows)
    return ShadowDivergenceOut(
        window_days=window_days,
        total=total,
        divergent=divergent,
        divergence_rate=(divergent / total) if total else 0.0,
        by_live_decision=by_live,
        by_shadow_decision=by_shadow,
    )