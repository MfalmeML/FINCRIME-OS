from __future__ import annotations
from dataclasses import dataclass, field

from fincrime_os.explainability.reason_codes import (
    ReasonCode,
    amount_vs_baseline,
    device_connectivity,
    ring_score_reason,
    sequence_pattern_reason,
    behavioral_deviation_reason,
)
from fincrime_os.explainability.counterfactual import counterfactual_for


@dataclass(frozen=True)
class Explanation:
    transaction_id: str
    decision: str
    reason_codes: list[ReasonCode]
    counterfactual: str
    complete: bool


@dataclass
class Explainer:
    def build(
        self,
        transaction_id: str,
        decision: str,
        amount: float,
        avg_amount: float,
        connected_accounts: int,
        confirmed_fraud_neighbors: int,
        graph_ring_score: float,
        graph_confirmed_members: int,
        sequence_risk_score: float,
        behavioral_anomaly_score: float,
        transaction_risk: float,
    ) -> Explanation:
        codes: list[ReasonCode] = []
        for candidate in (
            amount_vs_baseline(amount, avg_amount),
            device_connectivity(connected_accounts, confirmed_fraud_neighbors),
            ring_score_reason(graph_ring_score, graph_confirmed_members),
            sequence_pattern_reason(sequence_risk_score),
            behavioral_deviation_reason(behavioral_anomaly_score),
        ):
            if candidate is not None:
                codes.append(candidate)

        cf = counterfactual_for(
            graph_ring_score=graph_ring_score,
            behavioral_anomaly_score=behavioral_anomaly_score,
            sequence_risk_score=sequence_risk_score,
            transaction_risk=transaction_risk,
        )

        is_approve = decision == "APPROVE"
        complete = is_approve or (len(codes) > 0 and len(cf.text) > 0)

        return Explanation(
            transaction_id=transaction_id,
            decision=decision,
            reason_codes=codes,
            counterfactual=cf.text,
            complete=complete,
        )