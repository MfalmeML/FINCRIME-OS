from datetime import datetime, timedelta, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

import fincrime_os.models.temporal.loader as loader_mod
from fincrime_os.features.contracts import EventSequence
from fincrime_os.models.temporal.features import feature_names, vectorize
from fincrime_os.models.temporal.model import TemporalModel


T0 = datetime(2026, 9, 1, 2, 0, tzinfo=timezone.utc)


def _events(kinds, gap_seconds=60):
    out = []
    t = T0
    for k in kinds:
        t = t + timedelta(seconds=gap_seconds)
        out.append({"event_id": f"e_{k}", "kind": k, "occurred_at": t.isoformat(), "payload": {}})
    return out


def _seq(kinds, gap_seconds=60):
    return EventSequence(account_id="cust_1", events=_events(kinds, gap_seconds), as_of=T0)


def test_feature_vector_shape():
    v = vectorize(_seq(["login", "transfer"]))
    assert v.shape == (len(feature_names()),)
    assert np.isfinite(v).all()


def test_mule_chain_detected():
    seq = _seq(["login", "password_change", "device_registration", "beneficiary_addition", "transfer"])
    v = vectorize(seq)
    names = feature_names()
    assert v[names.index("chain_full")] == 1.0
    assert v[names.index("transfer_after_chain")] == 1.0


def test_normal_sequence_has_no_chain():
    seq = _seq(["login", "transfer", "login", "transfer"])
    v = vectorize(seq)
    names = feature_names()
    assert v[names.index("chain_full")] == 0.0


def test_empty_sequence_is_finite():
    seq = EventSequence(account_id="cust_1", events=[], as_of=T0)
    v = vectorize(seq)
    assert np.isfinite(v).all()
    assert v[feature_names().index("event_count")] == 0.0


def test_untrained_returns_zero(tmp_path, monkeypatch):
    monkeypatch.setattr(loader_mod, "STATE_ROOT", tmp_path)
    m = TemporalModel()
    assert m.is_trained is False
    assert m.predict(_seq(["login"])) == 0.0


def test_trained_returns_probability(tmp_path, monkeypatch):
    monkeypatch.setattr(loader_mod, "STATE_ROOT", tmp_path)
    rng = np.random.default_rng(0)
    X = rng.normal(size=(200, len(feature_names())))
    y = (X[:, 0] > 0.5).astype(int)
    clf = HistGradientBoostingClassifier(max_iter=20, random_state=0)
    clf.fit(X, y)
    model_dir = tmp_path / "models" / "temporal"
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"model": clf, "feature_names": feature_names(), "version": "v-test"},
        model_dir / "v-test.joblib",
    )
    m = TemporalModel()
    assert m.is_trained is True
    p = m.predict(_seq(["login"]))
    assert 0.0 <= p <= 1.0