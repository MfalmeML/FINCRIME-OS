from __future__ import annotations

from fincrime_os.monitoring.quality import QualityReport, SegmentQuality
from fincrime_os.state.loader import load_latest


def load_quality_report() -> QualityReport | None:
    artifact = load_latest("quality_metrics")
    if artifact is None:
        return None
    p = artifact.payload
    segments = {}
    for key, s in (p.get("segments") or {}).items():
        segments[key] = SegmentQuality(
            segment_key=s.get("segment_key", key),
            total_outcomes=int(s.get("total_outcomes", 0)),
            approves=int(s.get("approves", 0)),
            declines_and_challenges=int(s.get("declines_and_challenges", 0)),
            missed_detections=int(s.get("missed_detections", 0)),
            detection_miss_rate=float(s.get("detection_miss_rate", 0.0)),
            false_declines=int(s.get("false_declines", 0)),
            false_decline_rate=float(s.get("false_decline_rate", 0.0)),
            churn_after_decline=int(s.get("churn_after_decline", 0)),
            churn_rate=float(s.get("churn_rate", 0.0)),
        )
    return QualityReport(
        version=artifact.version,
        window_days=int(p.get("window_days", 0)),
        total_outcomes=int(p.get("total_outcomes", 0)),
        overall_miss_rate=float(p.get("overall_miss_rate", 0.0)),
        overall_false_decline_rate=float(p.get("overall_false_decline_rate", 0.0)),
        segments=segments,
    )