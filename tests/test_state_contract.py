import json

import pytest

import fincrime_os.state.loader as loader
from fincrime_os.state.graph_snapshot import load_snapshot
from fincrime_os.state.model_registry import load_registry


KINDS = ["threshold_tables", "graph_snapshots", "model_versions"]


@pytest.fixture
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    return tmp_path


def _publish_all(version: str):
    loader.publish(
        "threshold_tables",
        version,
        {"entries": {"default": [0.4, 0.75]}},
    )
    loader.publish(
        "graph_snapshots",
        version,
        {
            "ring_scores": {"cust_1": 0.97},
            "confirmed_members": {"cust_1": 4},
            "connected_accounts": {"cust_1": 14},
            "confirmed_fraud_neighbors": {"cust_1": 4},
        },
    )
    loader.publish(
        "model_versions",
        version,
        {"models": {"transaction_model": "txn-v9"}},
    )


def test_every_kind_round_trips(isolated_state):
    _publish_all("v-rt")
    for kind in KINDS:
        a = loader.load_latest(kind)
        assert a is not None
        assert a.kind == kind
        assert a.version == "v-rt"
        assert a.payload["version"] == "v-rt"


def test_version_specific_load(isolated_state):
    _publish_all("v1")
    _publish_all("v2")
    a = loader.load_version("graph_snapshots", "v1")
    assert a is not None
    assert a.version == "v1"


def test_loaders_read_published_artifacts(isolated_state):
    _publish_all("v-loaders")
    snap = load_snapshot()
    assert snap.version == "v-loaders"
    assert snap.for_account("cust_1")["graph_ring_score"] == 0.97

    reg = load_registry()
    assert reg.version == "v-loaders"
    assert reg.get("transaction_model") == "txn-v9"


def test_published_file_is_valid_json(isolated_state):
    _publish_all("v-json")
    for kind in KINDS:
        for path in (isolated_state / kind).glob("*.json"):
            json.loads(path.read_text(encoding="utf-8"))


def test_publish_overwrites_same_version(isolated_state):
    loader.publish("model_versions", "v-dup", {"models": {"fusion_model": "a"}})
    loader.publish("model_versions", "v-dup", {"models": {"fusion_model": "b"}})
    a = loader.load_version("model_versions", "v-dup")
    assert a is not None
    assert a.payload["models"]["fusion_model"] == "b"