from __future__ import annotations
from dataclasses import dataclass

from fincrime_os.features.contracts import GraphFeatures


@dataclass
class GraphModel:
    version: str = "graph-dev"

    def predict(self, features: GraphFeatures) -> float:
        return features.graph_ring_score