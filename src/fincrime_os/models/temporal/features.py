from __future__ import annotations
import numpy as np

from fincrime_os.features.contracts import EventSequence


KINDS = [
    "login",
    "password_change",
    "device_registration",
    "beneficiary_addition",
    "transfer",
]


def _counts(events: list[dict]) -> np.ndarray:
    counts = {k: 0 for k in KINDS}
    for e in events:
        k = e.get("kind")
        if k in counts:
            counts[k] += 1
    return np.asarray([counts[k] for k in KINDS], dtype=np.float64)


def _transition_matrix(events: list[dict]) -> np.ndarray:
    idx = {k: i for i, k in enumerate(KINDS)}
    m = np.zeros((len(KINDS), len(KINDS)), dtype=np.float64)
    for a, b in zip(events[:-1], events[1:]):
        ka, kb = a.get("kind"), b.get("kind")
        if ka in idx and kb in idx:
            m[idx[ka], idx[kb]] += 1.0
    return m.flatten()


def _durations(events: list[dict]) -> np.ndarray:
    if len(events) < 2:
        return np.zeros(4, dtype=np.float64)
    times = [e.get("occurred_at") for e in events if e.get("occurred_at")]
    if len(times) < 2:
        return np.zeros(4, dtype=np.float64)
    from datetime import datetime
    parsed = [datetime.fromisoformat(t) for t in times]
    deltas = [(b - a).total_seconds() for a, b in zip(parsed[:-1], parsed[1:])]
    if not deltas:
        return np.zeros(4, dtype=np.float64)
    return np.asarray(
        [
            float(min(deltas)),
            float(max(deltas)),
            float(sum(deltas) / len(deltas)),
            float(parsed[-1].timestamp() - parsed[0].timestamp()),
        ],
        dtype=np.float64,
    )


def _has_chain(events: list[dict]) -> np.ndarray:
    seq = [e.get("kind") for e in events]
    chain = ["login", "password_change", "device_registration", "beneficiary_addition"]
    flags = []
    for i in range(len(chain) - 1):
        flags.append(1.0 if chain[i] in seq and chain[i + 1] in seq else 0.0)
    full_chain = 1.0 if all(k in seq for k in chain) else 0.0
    transfer_after_chain = 0.0
    if full_chain:
        last_chain_pos = max(seq.index(k) for k in chain if k in seq)
        transfer_after_chain = 1.0 if any(
            seq[i] == "transfer" for i in range(last_chain_pos + 1, len(seq))
        ) else 0.0
    return np.asarray(flags + [full_chain, transfer_after_chain], dtype=np.float64)


def vectorize(sequence: EventSequence) -> np.ndarray:
    """Deterministic fixed-width vector for the temporal model.

    Feature order MUST stay stable across training and serving. Changes invalidate
    previously trained models.
    """
    events = sequence.events or []
    counts = _counts(events)
    transitions = _transition_matrix(events)
    durations = _durations(events)
    chain = _has_chain(events)

    total = float(len(events))
    comps = np.asarray(
        [
            total,
            float(counts.sum()) if counts.size else 0.0,
            float(1.0 if total > 0 else 0.0),
        ],
        dtype=np.float64,
    )
    return np.concatenate([counts, transitions, durations, chain, comps])


def feature_names() -> list[str]:
    names = [f"count_{k}" for k in KINDS]
    for a in KINDS:
        for b in KINDS:
            names.append(f"transition_{a}_to_{b}")
    names += [
        "dur_min",
        "dur_max",
        "dur_mean",
        "dur_total",
        "chain_login_pwd",
        "chain_pwd_device",
        "chain_device_benef",
        "chain_full",
        "transfer_after_chain",
        "event_count",
        "event_count_sum",
        "has_events",
    ]
    return names


def vectorize_many(rows: list[EventSequence]) -> np.ndarray:
    if not rows:
        return np.zeros((0, len(feature_names())), dtype=np.float64)
    return np.vstack([vectorize(s) for s in rows])