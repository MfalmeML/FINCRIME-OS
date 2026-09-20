from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

import fincrime_os.models.graph.loader as loader_mod
from fincrime_os.features.contracts import GraphFeatures
from fincrime_os.models.graph.features import feature_names, vectorize
from fincrime_os.models.graph.model import GraphModel


T0 = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)


def _gf(connected=14, confirmed=4, members=4, ring=0.97):
    return GraphFeatures(
        account_id="cust_1",
        device_id="D1",
        connected_accounts=connected,
        confirmed_fraud_neighbors=confirmed,
        graph_ring_score=ring,
        graph_confirmed_members=members,
        graph_snapshot_version="v-test",
        as_of=T0,
    )


def test_feature_vector_shape_and_finiteness():
    v = vectorize(_gf())
    assert v.shape == (len(feature_names()),)
    assert np.isfinite(v).all()


def test_connected_bucket_flags():
    names = feature_names()
    v = vectorize(_gf(connected=3))
    assert v[names.index("connected_ge_5")] == 0.0
    assert v[names.index("connected_ge_10")] == 0.0

    v = vectorize(_gf(connected=14))
    assert v[names.index("connected_ge_5")] == 1.0
    assert v[names.index("connected_ge_10")] == 1.0


def test_zero_connected_no_divide_error():
    v = vectorize(_gf(connected=0, confirmed=0, members=0, ring=0.0))
    assert np.isfinite(v).all()


def test_untrained_falls_back_to_snapshot_score(tmp_path, monkeypatch):
    monkeypatch.setattr(loader_mod, "STATE_ROOT", tmp_path)
    m = GraphModel()
    assert m.is_trained is False
    assert m.predict(_gf(ring=0.42)) == 0.42


def test_trained_returns_probability(tmp_path, monkeypatch):
    monkeypatch.setattr(loader_mod, "STATE_ROOT", tmp_path)
    rng = np.random.default_rng(0)
    X = rng.normal(size=(300, len(feature_names())))
    y = (X[:, 0] > 0.5).astype(int)
    clf = HistGradientBoostingClassifier(max_iter=30, random_state=0)
    clf.fit(X, y)
    model_dir = tmp_path / "models" / "graph"
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"model": clf, "feature_names": feature_names(), "version": "v-test"},
        model_dir / "v-test.joblib",
    )
    m = GraphModel()
    assert m.is_trained is True
    p = m.predict(_gf())
    assert 0.0 <= p <= 1.0