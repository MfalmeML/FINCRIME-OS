from __future__ import annotations
from typing import Literal, Tuple

from fincrime_os.config import GraphOverrideConfig, ThresholdTable, default_config

Decision = Literal["APPROVE", "CHALLENGE", "DECLINE"]


def graph_hard_override(
    graph_ring_score: float,
    confirmed_members: int,
    cfg: GraphOverrideConfig | None = None,
) -> bool:
    cfg = cfg or default_config().graph_override
    return (
        graph_ring_score > cfg.ring_score_cutoff
        and confirmed_members >= cfg.min_confirmed_members
    )


def lookup_thresholds(
    segment_key: str,
    table: ThresholdTable | None = None,
) -> Tuple[float, float]:
    table = table or default_config().threshold_table
    return table.lookup(segment_key)


def decide(
    combined_risk_score: float,
    graph_ring_score: float,
    graph_confirmed_members: int,
    segment_key: str = "default",
    graph_cfg: GraphOverrideConfig | None = None,
    threshold_table: ThresholdTable | None = None,
) -> tuple[Decision, str]:
    if graph_hard_override(graph_ring_score, graph_confirmed_members, graph_cfg):
        return "DECLINE", "graph_override"
    t_challenge, t_decline = lookup_thresholds(segment_key, threshold_table)
    if combined_risk_score < t_challenge:
        return "APPROVE", "below_challenge_threshold"
    if combined_risk_score < t_decline:
        return "CHALLENGE", "challenge_band"
    return "DECLINE", "above_decline_threshold"