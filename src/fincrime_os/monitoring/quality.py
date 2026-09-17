from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Iterable


@dataclass(frozen=True)
class SegmentQuality:
    segment_key: str
    total_outcomes: int
    approves: int
    declines_and_challenges: int
    missed_detections: int
    detection_miss_rate: float
    false_declines: int
    false_decline_rate: float
    churn_after_decline: int
    churn_rate: float


@dataclass(frozen=True)
class QualityReport:
    version: str
    window_days: int
    total_outcomes: int
    overall_miss_rate: float
    overall_false_decline_rate: float
    segments: dict[str, SegmentQuality] = field(default_factory=dict)


def _segment_key(row: dict) -> str:
    seg = row.get("segment") or {}
    return seg.get("customer_tier") or "default"


def _safe_div(n: float, d: float) -> float:
    return float(n) / float(d) if d else 0.0


def _segment_quality(segment_key: str, rows: list[dict]) -> SegmentQuality:
    approves = [r for r in rows if r.get("decision") == "APPROVE"]
    frictions = [r for r in rows if r.get("decision") in ("DECLINE", "CHALLENGE")]

    # Missed detection: approved, but outcome says fraud.
    missed = [r for r in approves if r.get("is_fraud") is True]

    # False decline: declined/challenged, but customer was legitimate.
    false_declines = [r for r in frictions if r.get("is_false_decline") is True]
    churned = [r for r in frictions if r.get("churned_after_decline") is True]

    return SegmentQuality(
        segment_key=segment_key,
        total_outcomes=len(rows),
        approves=len(approves),
        declines_and_challenges=len(frictions),
        missed_detections=len(missed),
        detection_miss_rate=_safe_div(len(missed), len(approves)),
        false_declines=len(false_declines),
        false_decline_rate=_safe_div(len(false_declines), len(frictions)),
        churn_after_decline=len(churned),
        churn_rate=_safe_div(len(churned), len(frictions)),
    )


def build_report(
    rows: Iterable[dict],
    version: str,
    window_days: int,
) -> QualityReport:
    rows = list(rows)
    buckets: dict[str, list[dict]] = {}
    for r in rows:
        buckets.setdefault(_segment_key(r), []).append(r)

    segments = {k: _segment_quality(k, v) for k, v in buckets.items()}

    approves = [r for r in rows if r.get("decision") == "APPROVE"]
    frictions = [r for r in rows if r.get("decision") in ("DECLINE", "CHALLENGE")]
    missed = [r for r in approves if r.get("is_fraud") is True]
    false_declines = [r for r in frictions if r.get("is_false_decline") is True]

    return QualityReport(
        version=version,
        window_days=window_days,
        total_outcomes=len(rows),
        overall_miss_rate=_safe_div(len(missed), len(approves)),
        overall_false_decline_rate=_safe_div(len(false_declines), len(frictions)),
        segments=segments,
    )


def as_dict(report: QualityReport) -> dict:
    d = asdict(report)
    d["segments"] = {k: asdict(v) for k, v in report.segments.items()}
    return d