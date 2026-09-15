from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

GateResult = Literal["PROMOTE", "REJECT", "HOLD"]


@dataclass(frozen=True)
class CanaryOutcome:
    candidate_version: str
    baseline_version: str
    candidate_fraud_loss: float
    baseline_fraud_loss: float
    fraud_loss_ceiling: float


@dataclass
class CanaryGate:
    fraud_loss_ceiling: float = 0.02

    def evaluate(self, outcome: CanaryOutcome) -> GateResult:
        if outcome.candidate_fraud_loss > outcome.fraud_loss_ceiling:
            return "REJECT"
        if outcome.candidate_fraud_loss > outcome.baseline_fraud_loss:
            return "HOLD"
        return "PROMOTE"


@dataclass
class VersionRegistry:
    serving: dict[str, str]

    def promote(self, component: str, version: str) -> None:
        self.serving[component] = version

    def current(self, component: str) -> str | None:
        return self.serving.get(component)


def apply_gate(
    gate: CanaryGate,
    registry: VersionRegistry,
    component: str,
    outcome: CanaryOutcome,
) -> GateResult:
    result = gate.evaluate(outcome)
    if result == "PROMOTE":
        registry.promote(component, outcome.candidate_version)
    return result