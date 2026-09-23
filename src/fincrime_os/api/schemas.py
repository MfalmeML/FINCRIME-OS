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
    ranked: list[RankedAlertOut]


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
    signals: list[DriftSignalOut]


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
    events: list[dict]


class GraphEdgeOut(BaseModel):
    source: str
    target: str
    label: str


class CaseGraphOut(BaseModel):
    root: str
    nodes: list[str]
    edges: list[GraphEdgeOut]
    ring_score: float
    confirmed_members: int


class TimelineEntryOut(BaseModel):
    occurred_at: str
    kind: str
    summary: str


class CaseDetailResponse(BaseModel):
    case_id: str
    decision: str
    combined_risk_score: float
    transaction_amount: float
    graph: CaseGraphOut
    timeline: list[TimelineEntryOut]
    explanation: ExplanationOut


class OutcomeSubmission(BaseModel):
    transaction_id: str
    account_id: str
    decision: Literal["APPROVE", "CHALLENGE", "DECLINE"]
    decided_at: str
    observed_at: str
    is_fraud: bool | None = None
    is_ring_member: bool | None = None
    is_false_decline: bool | None = None
    churned_after_decline: bool | None = None
    investigation_outcome: Literal[
        "confirmed_fraud", "false_positive", "inconclusive"
    ] | None = None
    transaction_amount: float | None = None
    segment: dict | None = None


class OutcomeAck(BaseModel):
    transaction_id: str
    stored_path: str


class CostInputsOut(BaseModel):
    version: str
    window_days: int
    total_outcomes: int
    declines_observed: int
    false_declines: int
    churned_after_decline: int
    p_false_decline: float
    p_churn_given_decline: float
    avg_transaction_amount: float
    confirmed_fraud_rate: float


class SegmentQualityOut(BaseModel):
    segment_key: str
    total_outcomes: int
    approves: int
    declines_and_challenges: int
    missed_detections: int
    detection_miss_rate: float
    false_declines: int
    false_decline_rate: float
    churn_after_decline: int
    churn_rate: float


class QualityResponse(BaseModel):
    available: bool
    version: str | None = None
    window_days: int = 0
    total_outcomes: int = 0
    overall_miss_rate: float = 0.0
    overall_false_decline_rate: float = 0.0
    segments: list[SegmentQualityOut] = []


class ShadowDivergenceOut(BaseModel):
    window_days: int
    total: int
    divergent: int
    divergence_rate: float
    by_live_decision: dict[str, int]
    by_shadow_decision: dict[str, int]


class SegmentRolloutOut(BaseModel):
    segment_key: str
    stage: str
    percentage: float


class RolloutResponse(BaseModel):
    version: str
    default_stage: str
    default_percentage: float
    segments: List[SegmentRolloutOut]