from fincrime_os.api.schemas import (
    DecisionRequest,
    DecisionResponse,
    ExplanationOut,
    ReasonCodeOut,
    Segment,
)

DECISION_REQUEST_FIELDS = {
    "transaction_id",
    "account_id",
    "device_id",
    "event_sequence_ref",
    "transaction_risk",
    "behavioral_anomaly_score",
    "sequence_risk_score",
    "graph_ring_score",
    "graph_confirmed_members",
    "combined_risk_score",
    "segment",
    "transaction_amount",
    "currency",
    "connected_accounts",
    "confirmed_fraud_neighbors",
    "customer_avg_amount",
}

DECISION_RESPONSE_FIELDS = {
    "transaction_id",
    "decision",
    "decision_reason",
    "graph_degraded",
    "threshold_table_version",
    "model_versions",
    "explanation_ref",
    "explanation",
}

REASON_CODE_FIELDS = {"code", "text", "evidence_value", "source"}

EXPLANATION_FIELDS = {
    "transaction_id",
    "decision",
    "reason_codes",
    "counterfactual",
    "complete",
}

SEGMENT_FIELDS = {"customer_tier", "channel", "merchant_category", "geography"}


def test_decision_request_contract():
    assert set(DecisionRequest.model_fields.keys()) == DECISION_REQUEST_FIELDS


def test_decision_response_contract():
    assert set(DecisionResponse.model_fields.keys()) == DECISION_RESPONSE_FIELDS


def test_explanation_contract():
    assert set(ExplanationOut.model_fields.keys()) == EXPLANATION_FIELDS


def test_reason_code_contract():
    assert set(ReasonCodeOut.model_fields.keys()) == REASON_CODE_FIELDS


def test_segment_contract():
    assert set(Segment.model_fields.keys()) == SEGMENT_FIELDS


def test_decision_enum_values_frozen():
    from typing import get_args
    args = get_args(DecisionResponse.model_fields["decision"].annotation)
    assert set(args) == {"APPROVE", "CHALLENGE", "DECLINE"}