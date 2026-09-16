import fincrime_os.state.loader as loader
from fincrime_os.state.graph_snapshot import GraphSnapshot, load_snapshot


def test_default_when_no_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    s = load_snapshot()
    assert s.version == "unversioned-dev"
    assert s.for_account("cust_1")["graph_ring_score"] == 0.0


def test_loads_published_snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    loader.publish(
        "graph_snapshots",
        "v-test",
        {
            "ring_scores": {"cust_1": 0.97},
            "confirmed_members": {"cust_1": 4},
            "connected_accounts": {"cust_1": 14},
            "confirmed_fraud_neighbors": {"cust_1": 4},
        },
    )
    s = load_snapshot()
    assert s.version == "v-test"
    row = s.for_account("cust_1")
    assert row["graph_ring_score"] == 0.97
    assert row["graph_confirmed_members"] == 4
    assert row["connected_accounts"] == 14
    assert row["confirmed_fraud_neighbors"] == 4
    assert row["graph_snapshot_version"] == "v-test"


def test_missing_account_defaults():
    s = GraphSnapshot(version="v1")
    row = s.for_account("unknown")
    assert row["graph_ring_score"] == 0.0
    assert row["graph_confirmed_members"] == 0