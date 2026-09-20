import joblib
import pytest

import fincrime_os.state.loader as loader
from fincrime_os.state.model_discovery import discover, discover_all


def _fake_bundle(version: str):
    return {"version": version, "feature_names": [], "model": object()}


def test_discover_returns_untrained_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    d = discover("transaction_model")
    assert d.trained is False
    assert d.version is None


def test_discover_returns_trained_when_file_present(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    model_dir = tmp_path / "models" / "transaction"
    model_dir.mkdir(parents=True)
    joblib.dump(_fake_bundle("txn-v9"), model_dir / "txn-v9.joblib")

    d = discover("transaction_model")
    assert d.trained is True
    assert d.version == "txn-v9"


def test_discover_all_covers_every_component(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    result = discover_all()
    assert set(result.keys()) == {
        "transaction_model",
        "behavioral_model",
        "temporal_model",
        "fusion_model",
        "graph_model",
    }