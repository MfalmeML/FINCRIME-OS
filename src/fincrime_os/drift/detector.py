from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

DriftComponent = Literal["feature", "prediction", "graph_structure", "fraud_rate"]


@dataclass(frozen=True)
class DriftSignal:
    component: DriftComponent
    score: float
    threshold: float
    fired: bool


@dataclass
class DriftDetector:
    feature_threshold: float = 0.20
    prediction_threshold: float = 0.20
    graph_threshold: float = 0.25
    fraud_rate_threshold: float = 3.0

    def check(
        self,
        feature_score: float,
        prediction_score: float,
        graph_score: float,
        fraud_rate_multiplier: float,
    ) -> list[DriftSignal]:
        return [
            DriftSignal("feature", feature_score, self.feature_threshold,
                        feature_score > self.feature_threshold),
            DriftSignal("prediction", prediction_score, self.prediction_threshold,
                        prediction_score > self.prediction_threshold),
            DriftSignal("graph_structure", graph_score, self.graph_threshold,
                        graph_score > self.graph_threshold),
            DriftSignal("fraud_rate", fraud_rate_multiplier, self.fraud_rate_threshold,
                        fraud_rate_multiplier > self.fraud_rate_threshold),
        ]

    def any_fired(self, signals: list[DriftSignal]) -> bool:
        return any(s.fired for s in signals)