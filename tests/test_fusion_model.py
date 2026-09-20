from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

import fincrime_os.models.fusion.loader as loader_mod
from fincrime_os.models.fusion.features import feature_names, vectorize
from fincrime_os.models.fusion.model import FusionModel


def test_feature_vector_shape_and_finiteness():
    v = vectorize(0.5, 0.5, 0.5, 0.5, 0.1)
    assert v.shape == (len(feature_names()),)
    assert np.isfinite(v).all()


def test_max_min_derived_correctly():
    v = vectorize(0.1, 0.9, 0.3, 0.4, 0.2)
    names = feature_names()
    assert v[names.index("max_score")] == 0.9
    assert v[names.index("min_score")] == 0.1


def test_mean_of_four_only_uses_four_signals():
    v = vectorize(1.0, 0.0, 1.0, 0.0, 0.5)
    names = feature_names()
    assert v[names.index("mean_of_four")] == 0.5


def test_untrained_uses_fixed_weights(tmp_path, monkeypatch):
    monkeypatch.setattr(loader_mod, "STATE_ROOT", tmp_path)
    m = FusionModel()
    assert m.is_trained is False
    p = m.predict(0.8, 0.8, 0.8, 0.8)
    assert abs(p - 0.8) < 1e-9


def test_untrained_zero_scores(tmp_path, monkeypatch):
    monkeypatch.setattr(loader_mod, "STATE_ROOT", tmp_path)
    m = FusionModel()
    assert m.predict(0.0, 0.0, 0.0, 0.0) == 0.0


def test_trained_returns_probability(tmp_path, monkeypatch):
    monkeypatch.setattr(loader_mod, "STATE_ROOT", tmp_path)
    rng = np.random.default_rng(0)
    X = rng.normal(size=(300, len(feature_names())))
    y = (X[:, 0] + X[:, 1] > 0.5).astype(int)
    clf = HistGradientBoostingClassifier(max_iter=30, random_state=0)
    clf.fit(X, y)
    model_dir = tmp_path / "models" / "fusion"
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"model": clf, "feature_names": feature_names(), "version": "v-test"},
        model_dir / "v-test.joblib",
    )
    m = FusionModel()
    assert m.is_trained is True
    p = m.predict(0.9, 0.9, 0.5, 0.4)
    assert 0.0 <= p <= 1.0