from __future__ import annotations

import numpy as np

from fincrime_os.features.contracts import BehavioralBaseline, TransactionFeatures


def _safe_ratio(a: float, b: float) -> float:
    return float(a) / float(b) if b > 0 else 0.0


def _hour_in_range(hour: float, lo: int, hi: int) -> float:
    return 1.0 if lo <= hour <= hi else 0.0


def vectorize(
    tx: TransactionFeatures,
    baseline: BehavioralBaseline,
) -> np.ndarray:
    """Deterministic fixed-width feature vector for the behavioral model.

    Feature order MUST stay stable across training and serving. Changing this
    function invalidates previously trained behavioral models and requires a
    version bump.
    """
    hour = tx.event_time.hour + tx.event_time.minute / 60.0

    amount_ratio = _safe_ratio(tx.amount, baseline.avg_amount)
    txn_ratio = _safe_ratio(1.0, baseline.txn_per_day) if baseline.txn_per_day else 0.0

    in_hours = _hour_in_range(hour, baseline.typical_hours[0], baseline.typical_hours[1])
    in_country = 1.0 if tx.country in baseline.typical_countries else 0.0
    in_device = 1.0 if tx.device_id in baseline.typical_devices else 0.0

    has_history = 1.0 if baseline.txn_per_day > 0 and baseline.avg_amount > 0 else 0.0
    country_unknown = 1.0 if not baseline.typical_countries else 0.0
    device_unknown = 1.0 if not baseline.typical_devices else 0.0

    return np.asarray(
        [
            np.log1p(max(0.0, amount_ratio)),
            np.log1p(max(0.0, txn_ratio)),
            hour,
            in_hours,
            in_country,
            in_device,
            1.0 - in_hours,
            1.0 - in_country,
            1.0 - in_device,
            has_history,
            country_unknown,
            device_unknown,
            float(tx.channel in ("app", "web")),
            float(tx.currency != "KES"),
        ],
        dtype=np.float64,
    )


def feature_names() -> list[str]:
    return [
        "log_amount_ratio",
        "log_txn_ratio",
        "hour_of_day",
        "in_typical_hours",
        "in_typical_country",
        "in_typical_device",
        "out_of_hours",
        "out_of_country",
        "out_of_device",
        "has_history",
        "no_country_history",
        "no_device_history",
        "remote_channel",
        "foreign_currency",
    ]


def vectorize_many(
    rows: list[tuple[TransactionFeatures, BehavioralBaseline]],
) -> np.ndarray:
    if not rows:
        return np.zeros((0, len(feature_names())), dtype=np.float64)
    return np.vstack([vectorize(tx, b) for tx, b in rows])