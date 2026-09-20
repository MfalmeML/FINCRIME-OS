from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from fincrime_os.models.fusion.features import vectorize
from fincrime_os.models.fusion.loader import (
    LoadedFusionModel,
    load_fusion_model,
)


@dataclass
class FusionModel:
    version: str = "fusion-dev"
    weights: tuple[float, float, float, float] = (0.25, 0.25, 0.25, 0.25)
    _loaded: Optional[LoadedFusionModel] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._loaded = load_fusion_model()

    @property
    def is_trained(self) -> bool:
        return self._loaded is not None

    def predict(
        self,
        transaction_risk: float,
        behavioral_score: float,
        sequence_score: float,
        graph_score: float,
        customer_baseline_risk: float = 0.0,
    ) -> float:
        if self._loaded is not None:
            x = vectorize(
                transaction_risk,
                behavioral_score,
                sequence_score,
                graph_score,
                customer_baseline_risk,
            ).reshape(1, -1)
            proba = self._loaded.model.predict_proba(x)[0, 1]
            return float(np.clip(proba, 0.0, 1.0))

        # Fallback: fixed-weight combination, matches pre-fusion behavior.
        w = self.weights
        combined = (
            w[0] * transaction_risk
            + w[1] * behavioral_score
            + w[2] * sequence_score
            + w[3] * graph_score
        )
        return float(np.clip(combined, 0.0, 1.0))