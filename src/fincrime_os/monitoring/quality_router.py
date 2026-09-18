from __future__ import annotations

from fastapi import APIRouter

from fincrime_os.monitoring.quality_loader import load_quality_report

router = APIRouter(tags=["monitoring"])


@router.get("/metrics/quality")
def metrics_quality() -> dict:
    report = load_quality_report()
    if report is None:
        return {"available": False}

    return {
        "available": True,
        "version": report.version,
        "window_days": report.window_days,
        "total_outcomes": report.total_outcomes,
        "overall_miss_rate": report.overall_miss_rate,
        "overall_false_decline_rate": report.overall_false_decline_rate,
        "segments": [
            {
                "segment_key": s.segment_key,
                "total_outcomes": s.total_outcomes,
                "approves": s.approves,
                "declines_and_challenges": s.declines_and_challenges,
                "missed_detections": s.missed_detections,
                "detection_miss_rate": s.detection_miss_rate,
                "false_declines": s.false_declines,
                "false_decline_rate": s.false_decline_rate,
                "churn_after_decline": s.churn_after_decline,
                "churn_rate": s.churn_rate,
            }
            for s in report.segments.values()
        ],
    }
