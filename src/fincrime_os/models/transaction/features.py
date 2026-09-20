from __future__ import annotations

import numpy as np

from fincrime_os.features.contracts import TransactionFeatures

CHANNELS = ["app", "web", "pos", "atm", "branch", "unknown"]
COUNTRIES = ["KE", "NG", "ZA", "UG", "TZ", "GB", "US", "OTHER"]


def _bucket_amount(amount: float) -> float:
    return float(np.log1p(max(0.0, amount)))


def _bucket_hour(dt) -> float:
    return float(dt.hour + dt.minute / 60.0)


def _one_hot(value: str, choices: list[str]) -> list[float]:
    v = value if value in choices else "OTHER"
    if v == "OTHER" and "OTHER" not in choices:
        v = choices[-1]
    return [1.0 if c == v else 0.0 for c in choices]


def vectorize(tx: TransactionFeatures) -> np.ndarray:
    """Deterministic fixed-width feature vector for the transaction model.

    Feature order MUST stay stable across training and serving. Any change to this
    function invalidates previously trained models and requires a version bump on
    the transaction_model artifact.
    """
    parts: list[float] = []
    parts.append(_bucket_amount(tx.amount))
    parts.append(_bucket_hour(tx.event_time))
    parts.append(float(tx.event_time.weekday()))
    parts.extend(_one_hot(tx.channel, CHANNELS))
    parts.extend(_one_hot(tx.country, COUNTRIES))
    parts.append(1.0 if tx.mcc and tx.mcc.startswith("6") else 0.0)
    parts.append(1.0 if tx.currency != "KES" else 0.0)
    return np.asarray(parts, dtype=np.float64)


def feature_names() -> list[str]:
    names = ["amount_log1p", "hour_of_day", "weekday"]
    names += [f"channel_{c}" for c in CHANNELS]
    names += [f"country_{c}" for c in COUNTRIES]
    names += ["mcc_high_risk_prefix", "foreign_currency"]
    return names


def vectorize_many(rows: list[TransactionFeatures]) -> np.ndarray:
    if not rows:
        return np.zeros((0, len(feature_names())), dtype=np.float64)
    return np.vstack([vectorize(r) for r in rows])