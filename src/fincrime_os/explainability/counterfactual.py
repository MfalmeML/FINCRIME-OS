from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Counterfactual:
    text: str
    estimated_risk_drop: float


def counterfactual_for(
    graph_ring_score: float,
    behavioral_anomaly_score: float,
    sequence_risk_score: float,
    transaction_risk: float,
) -> Counterfactual:
    drivers = {
        "network_connection_to_known_fraud": graph_ring_score,
        "behavioral_deviation": behavioral_anomaly_score,
        "suspicious_sequence": sequence_risk_score,
        "transaction_level_risk": transaction_risk,
    }
    top = max(drivers, key=drivers.get)
    drop = drivers[top]
    text_map = {
        "network_connection_to_known_fraud": (
            "if the account were not connected to a confirmed fraud network, "
            "estimated risk would decrease substantially"
        ),
        "behavioral_deviation": (
            "if the transaction had originated from the customer's historical "
            "device and normal beneficiary, estimated risk would decrease substantially"
        ),
        "suspicious_sequence": (
            "if the preceding events (login, device change, beneficiary addition) "
            "had not occurred within this window, estimated risk would decrease substantially"
        ),
        "transaction_level_risk": (
            "if transaction-level features matched the customer's historical pattern, "
            "estimated risk would decrease substantially"
        ),
    }
    return Counterfactual(text=text_map[top], estimated_risk_drop=drop)