from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from fincrime_os.features.contracts import BehavioralBaseline, TransactionFeatures
from fincrime_os.models.behavioral.features import vectorize
from fincrime_os.models.behavioral.loader import (
    LoadedBehavioralModel,
    load_behavioral_model,
)


@dataclass
class BehavioralModel:
    version: str = "behav-dev"
    _loaded: LoadedBehavioralModel | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._loaded = load_behavioral_model()

    @property
    def is_trained(self) -> bool:
        return self._loaded is not None

    def predict(
        self,
        features: TransactionFeatures,
        baseline: BehavioralBaseline,
    ) -> float:
        if self._loaded is None:
            return 0.0
        x = vectorize(features, baseline).reshape(1, -1)
        proba = self._loaded.model.predict_proba(x)[0, 1]
        return float(np.clip(proba, 0.0, 1.0))