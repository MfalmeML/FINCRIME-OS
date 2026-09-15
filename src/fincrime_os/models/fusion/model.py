from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FusionModel:
    version: str = "fusion-dev"
    weights: tuple[float, float, float, float] = (0.25, 0.25, 0.25, 0.25)

    def predict(
        self,
        transaction_risk: float,
        behavioral_score: float,
        sequence_score: float,
        graph_score: float,
    ) -> float:
        w = self.weights
        combined = (
            w[0] * transaction_risk
            + w[1] * behavioral_score
            + w[2] * sequence_score
            + w[3] * graph_score
        )
        return max(0.0, min(1.0, combined))