from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GraphOverrideConfig:
    ring_score_cutoff: float = 0.90
    min_confirmed_members: int = 2


@dataclass(frozen=True)
class DriftConfig:
    feature_threshold: float = 0.20
    prediction_threshold: float = 0.20
    graph_threshold: float = 0.25
    fraud_rate_threshold: float = 3.0


@dataclass(frozen=True)
class ThresholdTable:
    version: str
    entries: dict[str, tuple[float, float]] = field(
        default_factory=lambda: {"default": (0.40, 0.75)}
    )

    def lookup(self, segment_key: str) -> tuple[float, float]:
        return self.entries.get(segment_key, self.entries["default"])


@dataclass(frozen=True)
class PlatformConfig:
    graph_override: GraphOverrideConfig = GraphOverrideConfig()
    drift: DriftConfig = DriftConfig()
    threshold_table: ThresholdTable = ThresholdTable(version="2026-09-15T00:00Z-v0")
    latency_budget_ms: int = 100


def default_config() -> PlatformConfig:
    return PlatformConfig()