from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from fincrime_os.features.contracts import EventSequence
from fincrime_os.models.temporal.features import vectorize
from fincrime_os.models.temporal.loader import (
    LoadedTemporalModel,
    load_temporal_model,
)


@dataclass
class TemporalModel:
    version: str = "seq-dev"
    _loaded: LoadedTemporalModel | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._loaded = load_temporal_model()

    @property
    def is_trained(self) -> bool:
        return self._loaded is not None

    def predict(self, sequence: EventSequence) -> float:
        if self._loaded is None:
            return 0.0
        x = vectorize(sequence).reshape(1, -1)
        proba = self._loaded.model.predict_proba(x)[0, 1]
        return float(np.clip(proba, 0.0, 1.0))