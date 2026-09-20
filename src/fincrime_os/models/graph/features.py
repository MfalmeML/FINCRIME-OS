from __future__ import annotations
import numpy as np

from fincrime_os.features.contracts import GraphFeatures


def vectorize(g: GraphFeatures) -> np.ndarray:
    """Deterministic fixed-width vector for the graph model.

    Feature order MUST stay stable across training and serving. Changes
    invalidate previously trained graph models.
    """
    connected = float(max(0, g.connected_accounts))
    confirmed = float(max(0, g.confirmed_fraud_neighbors))
    members = float(max(0, g.graph_confirmed_members))
    ring = float(np.clip(g.graph_ring_score, 0.0, 1.0))

    confirmed_ratio = confirmed / connected if connected > 0 else 0.0
    members_ratio = members / connected if connected > 0 else 0.0
    log_connected = float(np.log1p(connected))

    return np.asarray(
        [
            ring,
            log_connected,
            confirmed,
            members,
            confirmed_ratio,
            members_ratio,
            float(1.0 if connected >= 5 else 0.0),
            float(1.0 if connected >= 10 else 0.0),
            float(1.0 if confirmed >= 1 else 0.0),
            float(1.0 if confirmed >= 3 else 0.0),
            float(1.0 if members >= 2 else 0.0),
            float(1.0 if members >= 4 else 0.0),
            ring * confirmed_ratio,
            ring * members_ratio,
        ],
        dtype=np.float64,
    )


def feature_names() -> list[str]:
    return [
        "graph_ring_score",
        "log_connected_accounts",
        "confirmed_fraud_neighbors",
        "graph_confirmed_members",
        "confirmed_ratio",
        "members_ratio",
        "connected_ge_5",
        "connected_ge_10",
        "confirmed_ge_1",
        "confirmed_ge_3",
        "members_ge_2",
        "members_ge_4",
        "ring_x_confirmed_ratio",
        "ring_x_members_ratio",
    ]


def vectorize_many(rows: list[GraphFeatures]) -> np.ndarray:
    if not rows:
        return np.zeros((0, len(feature_names())), dtype=np.float64)
    return np.vstack([vectorize(r) for r in rows])