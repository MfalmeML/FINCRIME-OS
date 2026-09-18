from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

import fincrime_os.models.behavioral.loader as loader_mod
from fincrime_os.features.contracts import TransactionFeatures, BehavioralBaseline
from fincrime_os.models.behavioral.features import feature_names, vectorize
from fincrime_os.models.behavioral.model import BehavioralModel


T0 = datetime(2026, 9, 1, 14, 0, tzinfo=timezone.utc)


def _tx(amount=100.0, hour=14, country="KE", device="D1", currency="KES", channel="app"):
    t = T0.replace(hour=hour)
    return TransactionFeatures(
        transaction_id="tx_1", account_id="cust_1", device_id=device,
        amount=amount, currency=currency, merchant_id="M1",
        mcc="5411", country=country, channel=channel,
        event_time=t, as_of=t,
    )


def _baseline(avg=100.0, hours=(8, 20), countries=("KE",), devices=("D1",)):
    return BehavioralBaseline(
        account_id="cust_1",
        txn_per_day=4.0,
        avg_amount=avg,
        typical_hours=hours,
        typical_countries=frozenset(countries),
        typical_devices=frozenset(devices),
        as_of=T0,
    )


def test_feature_vector_shape_and_finiteness():
    v = vectorize(_tx(), _baseline())
    assert v.shape == (len(feature_names()),)
    assert np.isfinite(v).all()


def test_amount_ratio_increases_with_amount():
    small = vectorize(_tx(amount=50.0), _baseline(avg=100.0))
    large = vectorize(_tx(amount=10000.0), _baseline(avg=100.0))
    assert large[0] > small[0]


def test_out_of_device_flag():
    v = vectorize(_tx(device="D99"), _baseline(devices=("D1",)))
    names = feature_names()
    assert v[names.index("out_of_device")] == 1.0
    assert v[names.index("in_typical_device")] == 0.0


def test_out_of_country_flag():
    v = vectorize(_tx(country="NG"), _baseline(countries=("KE",)))
    names = feature_names()
    assert v[names.index("out_of_country")] == 1.0


def test_out_of_hours_flag():
    v = vectorize(_tx(hour=2), _baseline(hours=(8, 20)))
    names = feature_names()
    assert v[names.index("out_of_hours")] == 1.0


def test_untrained_returns_zero(tmp_path, monkeypatch):
    monkeypatch.setattr(loader_mod, "STATE_ROOT", tmp_path)
    m = BehavioralModel()
    assert m.is_trained is False
    assert m.predict(_tx(), _baseline()) == 0.0


def test_trained_returns_probability(tmp_path, monkeypatch):
    monkeypatch.setattr(loader_mod, "STATE_ROOT", tmp_path)
    rng = np.random.default_rng(0)
    X = rng.normal(size=(200, len(feature_names())))
    y = (X[:, 0] > 0.5).astype(int)
    clf = HistGradientBoostingClassifier(max_iter=20, random_state=0)
    clf.fit(X, y)
    model_dir = tmp_path / "models" / "behavioral"
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"model": clf, "feature_names": feature_names(), "version": "v-test"},
        model_dir / "v-test.joblib",
    )
    m = BehavioralModel()
    assert m.is_trained is True
    p = m.predict(_tx(), _baseline())
    assert 0.0 <= p <= 1.0