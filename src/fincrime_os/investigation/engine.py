from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

Priority = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]


@dataclass(frozen=True)
class Alert:
    case_id: str
    combined_risk_score: float
    transaction_amount: float
    graph_ring_score: float
    graph_confirmed_members: int
    segment_tier: str


@dataclass(frozen=True)
class RankedAlert:
    case_id: str
    expected_loss_prevented: float
    priority: Priority
    rank: int


@dataclass
class InvestigationEngine:
    p_recoverable_if_confirmed: float = 0.65
    investigator_daily_capacity: int = 50

    def expected_loss_prevented(self, alert: Alert) -> float:
        network_multiplier = 1.0
        if alert.graph_ring_score > 0.90 and alert.graph_confirmed_members >= 2:
            network_multiplier = 1.5 + 0.1 * alert.graph_confirmed_members
        base = alert.combined_risk_score * alert.transaction_amount
        return base * self.p_recoverable_if_confirmed * network_multiplier

    def _priority(self, score: float, ceiling: float) -> Priority:
        if ceiling <= 0:
            return "LOW"
        ratio = score / ceiling
        if ratio >= 0.75:
            return "CRITICAL"
        if ratio >= 0.50:
            return "HIGH"
        if ratio >= 0.25:
            return "MEDIUM"
        return "LOW"

    def rank(self, alerts: list[Alert]) -> list[RankedAlert]:
        scored = [(a, self.expected_loss_prevented(a)) for a in alerts]
        scored.sort(key=lambda x: x[1], reverse=True)
        ceiling = scored[0][1] if scored else 0.0
        return [
            RankedAlert(
                case_id=a.case_id,
                expected_loss_prevented=value,
                priority=self._priority(value, ceiling),
                rank=i + 1,
            )
            for i, (a, value) in enumerate(scored)
        ]