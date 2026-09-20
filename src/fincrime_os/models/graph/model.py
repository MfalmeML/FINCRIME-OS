from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from fincrime_os.features.contracts import GraphFeatures
from fincrime_os.models.graph.features import vectorize
from fincrime_os.models.graph.loader import (
    LoadedGraphModel,
    load_graph_model,
)


@dataclass
class GraphModel:
    version: str = "graph-dev"
    _loaded: Optional[LoadedGraphModel] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._loaded = load_graph_model()

    @property
    def is_trained(self) -> bool:
        return self._loaded is not None

    def predict(self, features: GraphFeatures) -> float:
        if self._loaded is None:
            # Fallback: trust the precomputed snapshot ring score.
            return float(np.clip(features.graph_ring_score, 0.0, 1.0))
        x = vectorize(features).reshape(1, -1)
        proba = self._loaded.model.predict_proba(x)[0, 1]
        return float(np.clip(proba, 0.0, 1.0))