
import fincrime_os.state.loader as loader
from fincrime_os.state.loader import load_latest, load_version, publish


def test_publish_and_load_latest(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    publish("threshold_tables", "v1", {"entries": {"default": [0.4, 0.75]}})
    a = load_latest("threshold_tables")
    assert a is not None
    assert a.version == "v1"
    assert a.payload["entries"]["default"] == [0.4, 0.75]


def test_load_specific_version(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    publish("threshold_tables", "v1", {"entries": {"default": [0.4, 0.75]}})
    publish("threshold_tables", "v2", {"entries": {"default": [0.5, 0.85]}})
    a = load_version("threshold_tables", "v1")
    assert a is not None
    assert a.payload["entries"]["default"] == [0.4, 0.75]


def test_load_latest_none_when_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    assert load_latest("threshold_tables") is None