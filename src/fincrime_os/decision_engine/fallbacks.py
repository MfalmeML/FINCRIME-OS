from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FallbackState:
    graph_degraded: bool = False
    threshold_degraded: bool = False
    drift_frozen: bool = False
    adaptation_delayed: bool = False

    def flags(self) -> dict[str, bool]:
        return {
            "graph_degraded": self.graph_degraded,
            "threshold_degraded": self.threshold_degraded,
            "drift_frozen": self.drift_frozen,
            "adaptation_delayed": self.adaptation_delayed,
        }


def graph_fallback() -> FallbackState:
    return FallbackState(graph_degraded=True)


def threshold_fallback() -> FallbackState:
    return FallbackState(threshold_degraded=True)


def drift_freeze() -> FallbackState:
    return FallbackState(drift_frozen=True)


def adaptation_delay() -> FallbackState:
    return FallbackState(adaptation_delayed=True)