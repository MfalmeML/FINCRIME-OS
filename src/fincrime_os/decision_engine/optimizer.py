from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from itertools import product

from fincrime_os.decision_engine.cost_model import CostModelInputs


@dataclass(frozen=True)
class SegmentOutcomeStats:
    segment_key: str
    n: int
    fraud_rate: float
    mean_amount: float


@dataclass(frozen=True)
class ThresholdPair:
    segment_key: str
    t_challenge: float
    t_decline: float
    expected_cost: float


GRID = [i / 100 for i in range(5, 100, 5)]


def _expected_cost(
    fraud_rate: float,
    mean_amount: float,
    p_false_decline: float,
    p_churn_given_decline: float,
    t_challenge: float,
    t_decline: float,
) -> float:
    # Simplified cost model: probability mass above each threshold is approximated
    # by the fraction of the [0,1] risk range covered. This is a v1 grid-search
    # placeholder; the real optimizer replaces the mass estimate with a calibrated
    # risk distribution per segment once enough outcomes exist.
    approve_mass = t_challenge
    challenge_mass = t_decline - t_challenge
    decline_mass = 1.0 - t_decline

    fraud_loss = fraud_rate * mean_amount * approve_mass
    friction_cost = (
        (p_false_decline * mean_amount) * challenge_mass
        + (p_false_decline * mean_amount + p_churn_given_decline * mean_amount) * decline_mass
    )
    return fraud_loss + friction_cost


def optimize_segment(
    stats: SegmentOutcomeStats,
    cost_inputs: CostModelInputs,
) -> ThresholdPair:
    best: tuple[float, float, float] | None = None
    for tc, td in product(GRID, GRID):
        if tc >= td:
            continue
        cost = _expected_cost(
            fraud_rate=stats.fraud_rate,
            mean_amount=stats.mean_amount,
            p_false_decline=cost_inputs.p_false_decline,
            p_churn_given_decline=cost_inputs.p_churn_given_decline,
            t_challenge=tc,
            t_decline=td,
        )
        if best is None or cost < best[2]:
            best = (tc, td, cost)
    assert best is not None
    return ThresholdPair(
        segment_key=stats.segment_key,
        t_challenge=best[0],
        t_decline=best[1],
        expected_cost=best[2],
    )


def segment_stats_from_rows(rows: Iterable[dict]) -> dict[str, SegmentOutcomeStats]:
    buckets: dict[str, list[dict]] = {}
    for r in rows:
        key = (r.get("segment") or {}).get("customer_tier") or "default"
        buckets.setdefault(key, []).append(r)

    out: dict[str, SegmentOutcomeStats] = {}
    for key, items in buckets.items():
        amounts = [
            float(r["transaction_amount"])
            for r in items
            if isinstance(r.get("transaction_amount"), (int, float))
        ]
        frauds = [r for r in items if r.get("is_fraud") is True]
        n = len(items)
        out[key] = SegmentOutcomeStats(
            segment_key=key,
            n=n,
            fraud_rate=(len(frauds) / n) if n else 0.0,
            mean_amount=(sum(amounts) / len(amounts)) if amounts else 0.0,
        )
    return out


def optimize_all(
    rows: Iterable[dict],
    cost_inputs: CostModelInputs,
) -> dict[str, tuple[float, float]]:
    stats = segment_stats_from_rows(rows)
    result: dict[str, tuple[float, float]] = {}
    for key, s in stats.items():
        pair = optimize_segment(s, cost_inputs)
        result[key] = (pair.t_challenge, pair.t_decline)
    return result