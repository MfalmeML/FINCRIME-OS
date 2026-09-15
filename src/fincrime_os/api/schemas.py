from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field


class Segment(BaseModel):
    customer_tier: str
    channel: str
    merchant_category: str
    geography: str


class DecisionRequest(BaseModel):
    transaction_id: str
    account_id: str
    device_id: str
    event_sequence_ref: str
    transaction_risk: float = Field(ge=0.0, le=1.0)
    behavioral_anomaly_score: float = Field(ge=0.0, le=1.0)
    sequence_risk_score: float = Field(ge=0.0, le=1.0)
    graph_ring_score: float = Field(ge=0.0, le=1.0)
    graph_confirmed_members: int = Field(ge=0)
    combined_risk_score: float = Field(ge=0.0, le=1.0)
    segment: Segment
    transaction_amount: float
    currency: str
    connected_accounts: int = 0
    confirmed_fraud_neighbors: int = 0
    customer_avg_amount: float = 0.0


class ReasonCodeOut(BaseModel):
    code: str
    text: str
    evidence_value: float | str
    source: str


class ExplanationOut(BaseModel):
    transaction_id: str
    decision: str
    reason_codes: list[ReasonCodeOut]
    counterfactual: str
    complete: bool


class DecisionResponse(BaseModel):
    transaction_id: str
    decision: Literal["APPROVE", "CHALLENGE", "DECLINE"]
    decision_reason: str
    graph_degraded: bool
    threshold_table_version: str
    model_versions: dict[str, str]
    explanation_ref: str
    explanation: ExplanationOut


class RankedAlertOut(BaseModel):
    case_id: str
    expected_loss_prevented: float
    priority: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    rank: int


class QueueResponse(BaseModel):
    generated_at: str
    capacity: int
    alerts_considered: int
    alerts_returned: int
    ranked: List[RankedAlertOut]


class DriftRequest(BaseModel):
    feature_score: float = Field(ge=0.0)
    prediction_score: float = Field(ge=0.0)
    graph_score: float = Field(ge=0.0)
    fraud_rate_multiplier: float = Field(ge=0.0)


class DriftSignalOut(BaseModel):
    component: str
    score: float
    threshold: float
    fired: bool


class DriftResponse(BaseModel):
    any_fired: bool
    signals: List[DriftSignalOut]


class CanaryRequest(BaseModel):
    component: str
    candidate_version: str
    baseline_version: str
    candidate_fraud_loss: float = Field(ge=0.0)
    baseline_fraud_loss: float = Field(ge=0.0)


class CanaryResponse(BaseModel):
    component: str
    result: Literal["PROMOTE", "REJECT", "HOLD"]
    serving_version: str


class ReplaySequenceResponse(BaseModel):
    account_id: str
    as_of: str
    window_minutes: int
    events: List[dict]