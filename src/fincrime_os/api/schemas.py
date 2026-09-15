from __future__ import annotations
from typing import Literal, Dict
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


class DecisionResponse(BaseModel):
    transaction_id: str
    decision: Literal["APPROVE", "CHALLENGE", "DECLINE"]
    decision_reason: str
    threshold_table_version: str
    model_versions: Dict[str, str]
    explanation_ref: str