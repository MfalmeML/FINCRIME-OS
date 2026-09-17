from __future__ import annotations
from fastapi import APIRouter

from fincrime_os.api.schemas import (
    CanaryRequest,
    CanaryResponse,
    CostInputsOut,
    DriftRequest,
    DriftResponse,
    DriftSignalOut,
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