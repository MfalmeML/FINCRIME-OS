from __future__ import annotations
from fastapi import APIRouter, HTTPException

from fincrime_os.api.schemas import (
    CaseDetailResponse,
    CaseGraphOut,
    ExplanationOut,
    GraphEdgeOut,
    ReasonCodeOut,
    TimelineEntryOut,
)
from fincrime_os.explainability.explainer import Explainer

router = APIRouter(tags=["investigation"])
_explainer = Explainer()


_FIXTURES: dict[str, dict] = {
    "case_3": {
        "decision": "DECLINE",
        "combined_risk_score": 0.96,
        "transaction_amount": 1000.0,
        "avg_amount": 120.0,
        "graph_ring_score": 0.95,
        "graph_confirmed_members": 4,
        "connected_accounts": 14,
        "confirmed_fraud_neighbors": 4,
        "behavioral_anomaly_score": 0.94,
        "sequence_risk_score": 0.91,
        "transaction_risk": 0.73,
        "nodes": ["cust_1", "D912", "acct_A", "acct_B", "acct_C", "benef_Z"],
        "edges": [
            ("cust_1", "D912", "uses_device"),
            ("D912", "acct_A", "shared_device"),
            ("D912", "acct_B", "shared_device"),
            ("D912", "acct_C", "shared_device"),
            ("acct_A", "benef_Z", "beneficiary"),
            ("acct_B", "benef_Z", "beneficiary"),
        ],
        "timeline": [
            ("2026-09-15T01:51:00+00:00", "login", "login from new device D912"),
            ("2026-09-15T01:53:00+00:00", "password_change", "password changed"),
            ("2026-09-15T01:55:00+00:00", "device_registration", "new device registered"),
            ("2026-09-15T01:57:00+00:00", "beneficiary_addition", "new beneficiary Z added"),
            ("2026-09-15T02:01:00+00:00", "transfer", "transfer 2000 KES"),
            ("2026-09-15T02:04:00+00:00", "transfer", "transfer 5000 KES"),
            ("2026-09-15T02:13:00+00:00", "transfer", "transfer 8700 KES"),
        ],
    },
    "case_1": {
        "decision": "CHALLENGE",
        "combined_risk_score": 0.96,
        "transaction_amount": 40.0,
        "avg_amount": 40.0,
        "graph_ring_score": 0.0,
        "graph_confirmed_members": 0,
        "connected_accounts": 1,
        "confirmed_fraud_neighbors": 0,
        "behavioral_anomaly_score": 0.90,
        "sequence_risk_score": 0.85,
        "transaction_risk": 0.95,
        "nodes": ["cust_1"],
        "edges": [],
        "timeline": [
            ("2026-09-15T02:13:00+00:00", "transfer", "transfer 40 KES"),
        ],
    },
}


def _build(case_id: str, fixture: dict) -> CaseDetailResponse:
    explanation = _explainer.build(
        transaction_id=case_id,
        decision=fixture["decision"],
        amount=fixture["transaction_amount"],
        avg_amount=fixture["avg_amount"],
        connected_accounts=fixture["connected_accounts"],
        confirmed_fraud_neighbors=fixture["confirmed_fraud_neighbors"],
        graph_ring_score=fixture["graph_ring_score"],
        graph_confirmed_members=fixture["graph_confirmed_members"],
        sequence_risk_score=fixture["sequence_risk_score"],
        behavioral_anomaly_score=fixture["behavioral_anomaly_score"],
        transaction_risk=fixture["transaction_risk"],
    )
    return CaseDetailResponse(
        case_id=case_id,
        decision=fixture["decision"],
        combined_risk_score=fixture["combined_risk_score"],
        transaction_amount=fixture["transaction_amount"],
        graph=CaseGraphOut(
            root=fixture["nodes"][0],
            nodes=fixture["nodes"],
            edges=[
                GraphEdgeOut(source=s, target=t, label=lbl)
                for (s, t, lbl) in fixture["edges"]
            ],
            ring_score=fixture["graph_ring_score"],
            confirmed_members=fixture["graph_confirmed_members"],
        ),
        timeline=[
            TimelineEntryOut(occurred_at=ts, kind=kind, summary=summary)
            for (ts, kind, summary) in fixture["timeline"]
        ],
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


@router.get("/case/{case_id}", response_model=CaseDetailResponse)
def case_detail(case_id: str) -> CaseDetailResponse:
    fixture = _FIXTURES.get(case_id)
    if fixture is None:
        raise HTTPException(status_code=404, detail="case not found")
    return _build(case_id, fixture)