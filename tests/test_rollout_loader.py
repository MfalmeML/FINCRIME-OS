import fincrime_os.state.loader as loader
from fincrime_os.rollout.contracts import SignalStage
from fincrime_os.rollout.loader import load_rollout


def test_load_returns_default_when_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    t = load_rollout()
    assert t.version == "unversioned-dev"
    assert t.default_stage == SignalStage.FULL


def test_load_parses_published_table(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    loader.publish(
        "rollout_table",
        "v-roll",
        {
            "default_stage": "full",
            "default_percentage": 1.0,
            "segments": {
                "vip": {"stage": "add_temporal", "percentage": 0.20},
                "new_account": {"stage": "transaction_only", "percentage": 0.0},
            },
        },
    )
    t = load_rollout()
    assert t.version == "v-roll"
    assert t.segments["vip"].stage == SignalStage.ADD_TEMPORAL
    assert t.segments["vip"].percentage == 0.20
    assert t.segments["new_account"].stage == SignalStage.TRANSACTION_ONLY


def test_load_handles_unknown_stage(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    loader.publish(
        "rollout_table",
        "v-roll-unknown",
        {
            "default_stage": "full",
            "default_percentage": 1.0,
            "segments": {"weird": {"stage": "not_a_real_stage", "percentage": 0.5}},
        },
    )
    t = load_rollout()
    assert t.segments["weird"].stage == SignalStage.FULL