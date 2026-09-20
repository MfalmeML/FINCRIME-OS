from __future__ import annotations

import numpy as np


def vectorize(
    transaction_risk: float,
    behavioral_score: float,
    sequence_score: float,
    graph_score: float,
    customer_baseline_risk: float = 0.0,
) -> np.ndarray:
    """Deterministic fixed-width vector for the fusion model.

    Order MUST stay stable across training and serving. Changes invalidate
    previously trained fusion models.
    """
    t = float(np.clip(transaction_risk, 0.0, 1.0))
    b = float(np.clip(behavioral_score, 0.0, 1.0))
    s = float(np.clip(sequence_score, 0.0, 1.0))
    g = float(np.clip(graph_score, 0.0, 1.0))
    c = float(np.clip(customer_baseline_risk, 0.0, 1.0))

    scores = np.asarray([t, b, s, g, c], dtype=np.float64)
    stats = np.asarray(
        [
            float(scores.max()),
            float(scores.min()),
            float(scores.mean()),
            float(scores.std()),
            float(t * b),
            float(s * g),
            float((t + b + s + g) / 4.0),
        ],
        dtype=np.float64,
    )
    return np.concatenate([scores, stats])


def feature_names() -> list[str]:
    return [
        "transaction_risk",
        "behavioral_score",
        "sequence_score",
        "graph_score",
        "customer_baseline_risk",
        "max_score",
        "min_score",
        "mean_score",
        "std_score",
        "txn_x_behav",
        "seq_x_graph",
        "mean_of_four",
    ]


def vectorize_many(
    rows: list[tuple[float, float, float, float, float]],
) -> np.ndarray:
    if not rows:
        return np.zeros((0, len(feature_names())), dtype=np.float64)
    return np.vstack([vectorize(*r) for r in rows])