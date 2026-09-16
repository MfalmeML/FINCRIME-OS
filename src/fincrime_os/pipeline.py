from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from fincrime_os.features.contracts import (
    TransactionFeatures,
    BehavioralBaseline,
    EventSequence,
    GraphFeatures,
)
from fincrime_os.features.point_in_time import assert_not_future
from fincrime_os.models.transaction.model import TransactionModel
from fincrime_os.models.behavioral.model import BehavioralModel
from fincrime_os.models.temporal.model import TemporalModel
from fincrime_os.models.graph.model import GraphModel
from fincrime_os.models.fusion.model import FusionModel
from fincrime_os.state.model_registry import ModelRegistry, load_registry


@dataclass
class SignalBundle:
    transaction_risk: float
    behavioral_anomaly_score: float
    sequence_risk_score: float
    graph_ring_score: float
    graph_confirmed_members: int
    combined_risk_score: float
    graph_degraded: bool
    model_versions: dict


class Pipeline:
    def __init__(self, registry: ModelRegistry | None = None) -> None:
        self.registry = registry or load_registry()
        self.transaction = TransactionModel(version=self.registry.get("transaction_model"))
        self.behavioral = BehavioralModel(version=self.registry.get("behavioral_model"))
        self.temporal = TemporalModel(version=self.registry.get("temporal_model"))
        self.graph = GraphModel(version=self.registry.get("graph_model"))
        self.fusion = FusionModel(version=self.registry.get("fusion_model"))

    def model_versions(self) -> dict:
        return self.registry.as_dict()

    def score(
        self,
        tx: TransactionFeatures,
        baseline: BehavioralBaseline,
        sequence: EventSequence,
        graph_features: Optional[GraphFeatures],
    ) -> SignalBundle:
        assert_not_future(baseline.as_of, tx.event_time)
        assert_not_future(sequence.as_of, tx.event_time)

        t = self.transaction.predict(tx)
        b = self.behavioral.predict(tx, baseline)
        s = self.temporal.predict(sequence)

        graph_degraded = graph_features is None
        if graph_features is not None:
            assert_not_future(graph_features.as_of, tx.event_time)
            g = self.graph.predict(graph_features)
            members = graph_features.graph_confirmed_members
        else:
            g = 0.0
            members = 0

        combined = self.fusion.predict(t, b, s, g)

        return SignalBundle(
            transaction_risk=t,
            behavioral_anomaly_score=b,
            sequence_risk_score=s,
            graph_ring_score=g,
            graph_confirmed_members=members,
            combined_risk_score=combined,
            graph_degraded=graph_degraded,
            model_versions=self.registry.as_dict(),
        )