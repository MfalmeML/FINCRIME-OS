from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fincrime_os.decision_engine.cost_model import build_inputs
from fincrime_os.decision_engine.cost_model import as_dict as cost_dict
from fincrime_os.decision_engine.optimizer import optimize_all
from fincrime_os.drift.outcome_drift import compute_outcome_drift
from fincrime_os.drift.outcome_drift import as_dict as drift_dict
from fincrime_os.monitoring.quality import build_report
from fincrime_os.monitoring.quality import as_dict as quality_dict
from fincrime_os.state.loader import publish
from fincrime_os.state.outcomes import read_outcomes


@dataclass(frozen=True)
class RebuildResult:
    version: str
    window_days: int
    rows: int
    published: list[str]


def _read_window(days: int) -> list[dict]:
    today = datetime.now(tz=timezone.utc).date()
    rows: list[dict] = []
    for offset in range(days):
        day = (today - timedelta(days=offset)).strftime("%Y-%m-%d")
        rows.extend(read_outcomes(day))
    return rows


def rebuild_all(window_days: int, version: str | None = None) -> RebuildResult:
    version = version or datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    rows = _read_window(window_days)

    cost = build_inputs(rows, version=version, window_days=window_days)
    publish("cost_model_inputs", version, cost_dict(cost))

    drift = compute_outcome_drift(rows, version=version, window_days=window_days)
    publish("drift_signals", version, drift_dict(drift))

    quality = build_report(rows, version=version, window_days=window_days)
    publish("quality_metrics", version, quality_dict(quality))

    if rows:
        optimized = optimize_all(rows, cost)
        entries = {k: [float(v[0]), float(v[1])] for k, v in optimized.items()}
        if "default" not in entries:
            entries["default"] = [0.40, 0.75]
    else:
        entries = {"default": [0.40, 0.75]}
    publish("threshold_tables", version, {"entries": entries})

    return RebuildResult(
        version=version,
        window_days=window_days,
        rows=len(rows),
        published=[
            "cost_model_inputs",
            "drift_signals",
            "quality_metrics",
            "threshold_tables",
        ],
    )