from __future__ import annotations
from fastapi import FastAPI

from fincrime_os.api.schemas import DecisionRequest, DecisionResponse
from fincrime_os.decision_engine.policy import decide

app = FastAPI(title="FINCRIME OS", version="0.0.1")

THRESHOLD_TABLE_VERSION = "unversioned-dev"
MODEL_VERSIONS = {
    "transaction_model": "txn-dev",
    "behavioral_model": "behav-dev",
    "temporal_model": "seq-dev",
    "graph_model": "graph-dev",
    "fusion_model": "fusion-dev",
}


@app.post("/decision", response_model=DecisionResponse)
def decision(req: DecisionRequest) -> DecisionResponse:
    segment_key = req.segment.customer_tier
    decision, reason = decide(
        combined_risk_score=req.combined_risk_score,
        graph_ring_score=req.graph_ring_score,
        graph_confirmed_members=req.graph_confirmed_members,
        segment_key=segment_key,
    )
    return DecisionResponse(
        transaction_id=req.transaction_id,
        decision=decision,
        decision_reason=reason,
        threshold_table_version=THRESHOLD_TABLE_VERSION,
        model_versions=MODEL_VERSIONS,
        explanation_ref=f"exp_{req.transaction_id}",
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}