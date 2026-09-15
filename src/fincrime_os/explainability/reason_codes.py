from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReasonCode:
    code: str
    text: str
    evidence_value: float | str
    source: str


def amount_vs_baseline(amount: float, avg_amount: float) -> ReasonCode | None:
    if avg_amount <= 0:
        return None
    ratio = amount / avg_amount
    if ratio >= 5.0:
        return ReasonCode(
            code="AMOUNT_DEVIATION",
            text=f"transaction amount {ratio:.0f}x customer baseline",
            evidence_value=round(ratio, 2),
            source="behavioral",
        )
    return None


def device_connectivity(connected_accounts: int, confirmed_fraud_neighbors: int) -> ReasonCode | None:
    if connected_accounts >= 5:
        return ReasonCode(
            code="DEVICE_CONNECTIVITY",
            text=(
                f"device linked to {connected_accounts} accounts, "
                f"{confirmed_fraud_neighbors} with prior confirmed fraud"
            ),
            evidence_value=connected_accounts,
            source="graph",
        )
    return None


def ring_score_reason(graph_ring_score: float, confirmed_members: int) -> ReasonCode | None:
    if graph_ring_score > 0.90 and confirmed_members >= 2:
        return ReasonCode(
            code="RING_OVERRIDE",
            text=(
                f"graph ring score {graph_ring_score:.2f} with "
                f"{confirmed_members} confirmed members"
            ),
            evidence_value=graph_ring_score,
            source="graph",
        )
    return None


def sequence_pattern_reason(sequence_risk_score: float) -> ReasonCode | None:
    if sequence_risk_score >= 0.80:
        return ReasonCode(
            code="SEQUENCE_PATTERN",
            text="event sequence matches known mule pattern",
            evidence_value=sequence_risk_score,
            source="temporal",
        )
    return None


def behavioral_deviation_reason(behavioral_anomaly_score: float) -> ReasonCode | None:
    if behavioral_anomaly_score >= 0.85:
        return ReasonCode(
            code="BEHAVIORAL_DEVIATION",
            text="extreme behavioral deviation from customer baseline",
            evidence_value=behavioral_anomaly_score,
            source="behavioral",
        )
    return None