from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable

from fincrime_os.drift.detector import DriftDetector, DriftSignal


@dataclass(frozen=True)
class OutcomeDriftSnapshot:
    version: str
    window_days: int
    recent_fraud_rate: float
    baseline_fraud_rate: float
    fraud_rate_multiplier: float
    recent_fp_rate: float
    baseline_fp_rate: float
    feature_score: float
    prediction_score: float
    graph_score: float
    any_fired: bool


def _rate(rows: list[dict], key: str) -> float:
    if not rows:
        return 0.0
    hits = sum(1 for r in rows if r.get(key) is True)
    return hits / len(rows)


def _split_windows(
    rows: Iterable[dict],
    split_ratio: float,
) -> tuple[list[dict], list[dict]]:
    ordered = sorted(rows, key=lambda r: r.get("observed_at", ""))
    if not ordered:
        return [], []
    cut = int(len(ordered) * (1.0 - split_ratio))
    baseline = ordered[:cut] if cut > 0 else ordered[:1]
    recent = ordered[cut:] if cut < len(ordered) else ordered[-1:]
    return baseline, recent


def compute_outcome_drift(
    rows: Iterable[dict],
    version: str,
    window_days: int,
    recent_ratio: float = 0.25,
) -> OutcomeDriftSnapshot:
    rows = list(rows)
    baseline, recent = _split_windows(rows, recent_ratio)

    baseline_fraud = _rate(baseline, "is_fraud")
    recent_fraud = _rate(recent, "is_fraud")
    if baseline_fraud > 0:
        multiplier = recent_fraud / baseline_fraud
    else:
        multiplier = 1.0 if recent_fraud == 0 else float("inf")

    baseline_fp = _rate(baseline, "is_false_decline")
    recent_fp = _rate(recent, "is_false_decline")

    detector = DriftDetector()
    signals: list[DriftSignal] = detector.check(
        feature_score=abs(recent_fp - baseline_fp),
        prediction_score=abs(recent_fraud - baseline_fraud),
        graph_score=0.0,
        fraud_rate_multiplier=multiplier if multiplier != float("inf") else 1e9,
    )
    any_fired = detector.any_fired(signals)

    return OutcomeDriftSnapshot(
        version=version,
        window_days=window_days,
        recent_fraud_rate=recent_fraud,
        baseline_fraud_rate=baseline_fraud,
        fraud_rate_multiplier=multiplier,
        recent_fp_rate=recent_fp,
        baseline_fp_rate=baseline_fp,
        feature_score=abs(recent_fp - baseline_fp),
        prediction_score=abs(recent_fraud - baseline_fraud),
        graph_score=0.0,
        any_fired=any_fired,
    )


def as_dict(s: OutcomeDriftSnapshot) -> dict:
    return asdict(s)