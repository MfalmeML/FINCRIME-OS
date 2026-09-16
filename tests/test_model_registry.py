import fincrime_os.state.loader as loader
from fincrime_os.state.model_registry import (
    DEFAULT_MODELS,
    ModelRegistry,
    load_registry,
)


def test_registry_defaults_when_no_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    r = load_registry()
    assert r.version == "unversioned-dev"
    assert r.get("transaction_model") == DEFAULT_MODELS["transaction_model"]


def test_registry_loads_published_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    loader.publish(
        "model_versions",
        "v-test",
        {"models": {"transaction_model": "txn-v9", "fusion_model": "fusion-v5"}},
    )
    r = load_registry()
    assert r.version == "v-test"
    assert r.get("transaction_model") == "txn-v9"
    assert r.get("fusion_model") == "fusion-v5"
    assert r.get("behavioral_model") == "unknown"


def test_registry_as_dict_is_copy():
    r = ModelRegistry(version="v1")
    d = r.as_dict()
    d["transaction_model"] = "mutated"
    assert r.get("transaction_model") != "mutated"