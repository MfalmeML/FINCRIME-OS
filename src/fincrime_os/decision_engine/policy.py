from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Tuple

Decision = Literal["APPROVE", "CHALLENGE", "DECLINE"]

GRAPH_RING_CUTOFF = 0.90
GRAPH_MIN_CONFIRMED_MEMBERS = 2

THRESHOLD_TABLE: dict[str, Tuple[float, float]] = {
    "default": (0.40, 0.75),
}


def graph_hard_override(graph_ring_score: float, confirmed_members: int) -> bool:
    return (
        graph_ring_score > GRAPH_RING_CUTOFF
        and confirmed_members >= GRAPH_MIN_CONFIRMED_MEMBERS
    )


def lookup_thresholds(segment_key: str) -> Tuple[float, float]:
    return THRESHOLD_TABLE.get(segment_key, THRESHOLD_TABLE["default"])


def decide(
    combined_risk_score: float,
    graph_ring_score: float,
    graph_confirmed_members: int,
    segment_key: str = "default",
) -> tuple[Decision, str]:
    if graph_hard_override(graph_ring_score, graph_confirmed_members):
        return "DECLINE", "graph_override"
    t_challenge, t_decline = lookup_thresholds(segment_key)
    if combined_risk_score < t_challenge:
        return "APPROVE", "below_challenge_threshold"
    if combined_risk_score < t_decline:
        return "CHALLENGE", "challenge_band"
    return "DECLINE", "above_decline_threshold"