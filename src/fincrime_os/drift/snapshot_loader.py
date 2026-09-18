from __future__ import annotations

from fincrime_os.drift.outcome_drift import OutcomeDriftSnapshot
from fincrime_os.state.loader import load_latest


def load_drift_snapshot() -> OutcomeDriftSnapshot | None:
    artifact = load_latest("drift_signals")
    if artifact is None:
        return None
    p = artifact.payload
    return OutcomeDriftSnapshot(
        version=artifact.version,
        window_days=int(p.get("window_days", 0)),
        recent_fraud_rate=float(p.get("recent_fraud_rate", 0.0)),
        baseline_fraud_rate=float(p.get("baseline_fraud_rate", 0.0)),
        fraud_rate_multiplier=float(p.get("fraud_rate_multiplier", 1.0)),
        recent_fp_rate=float(p.get("recent_fp_rate", 0.0)),
        baseline_fp_rate=float(p.get("baseline_fp_rate", 0.0)),
        feature_score=float(p.get("feature_score", 0.0)),
        prediction_score=float(p.get("prediction_score", 0.0)),
        graph_score=float(p.get("graph_score", 0.0)),
        any_fired=bool(p.get("any_fired", False)),
    )