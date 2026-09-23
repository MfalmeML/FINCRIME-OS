from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class SignalStage(str, Enum):
    TRANSACTION_ONLY = "transaction_only"
    ADD_BEHAVIORAL = "add_behavioral"
    ADD_TEMPORAL = "add_temporal"
    FULL = "full"


@dataclass(frozen=True)
class SegmentRollout:
    segment_key: str
    stage: SignalStage
    percentage: float


@dataclass(frozen=True)
class RolloutTable:
    version: str
    default_stage: SignalStage = SignalStage.FULL
    default_percentage: float = 1.0
    segments: dict[str, SegmentRollout] = field(default_factory=dict)

    def resolve(self, segment_key: str) -> SegmentRollout:
        if segment_key in self.segments:
            return self.segments[segment_key]
        return SegmentRollout(
            segment_key=segment_key,
            stage=self.default_stage,
            percentage=self.default_percentage,
        )


def stage_allows_behavioral(stage: SignalStage) -> bool:
    return stage in (SignalStage.ADD_BEHAVIORAL, SignalStage.ADD_TEMPORAL, SignalStage.FULL)


def stage_allows_temporal(stage: SignalStage) -> bool:
    return stage in (SignalStage.ADD_TEMPORAL, SignalStage.FULL)


def stage_allows_graph(stage: SignalStage) -> bool:
    return stage is SignalStage.FULL


Decision = Literal["APPROVE", "CHALLENGE", "DECLINE"]