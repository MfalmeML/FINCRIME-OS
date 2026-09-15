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
    def __init__(self) -> None:
        self.transaction = TransactionModel()
        self.behavioral = BehavioralModel()
        self.temporal = TemporalModel()
        self.graph = GraphModel()
        self.fusion = FusionModel()

    def model_versions(self) -> dict:
        return {
            "transaction_model": self.transaction.version,
            "behavioral_model": self.behavioral.version,
            "temporal_model": self.temporal.version,
            "graph_model": self.graph.version,
            "fusion_model": self.fusion.version,
        }

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
            model_versions={
                "transaction_model": self.transaction.version,
                "behavioral_model": self.behavioral.version,
                "temporal_model": self.temporal.version,
                "graph_model": self.graph.version,
                "fusion_model": self.fusion.version,
            },
        )