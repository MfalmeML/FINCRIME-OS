
import fincrime_os.state.loader as loader
from fincrime_os.drift.canary import (
    CanaryGate,
    CanaryOutcome,
    VersionRegistry,
    apply_gate,
)


def _promote_if(gate, registry, component, candidate, base, c_loss, b_loss, ceiling):
    return apply_gate(
        gate,
        registry,
        component,
        CanaryOutcome(
            candidate_version=candidate,
            baseline_version=base,
            candidate_fraud_loss=c_loss,
            baseline_fraud_loss=b_loss,
            fraud_loss_ceiling=ceiling,
        ),
    )


def test_hold_does_not_update_registry():
    gate = CanaryGate(fraud_loss_ceiling=0.02)
    registry = VersionRegistry(serving={"fusion_model": "fusion-v1"})
    result = _promote_if(
        gate, registry, "fusion_model",
        candidate="fusion-v2", base="fusion-v1",
        c_loss=0.015, b_loss=0.010, ceiling=0.02,
    )
    assert result == "HOLD"
    assert registry.current("fusion_model") == "fusion-v1"


def test_reject_does_not_update_registry():
    gate = CanaryGate(fraud_loss_ceiling=0.02)
    registry = VersionRegistry(serving={"fusion_model": "fusion-v1"})
    result = _promote_if(
        gate, registry, "fusion_model",
        candidate="fusion-v2", base="fusion-v1",
        c_loss=0.05, b_loss=0.01, ceiling=0.02,
    )
    assert result == "REJECT"
    assert registry.current("fusion_model") == "fusion-v1"


def test_promote_updates_registry():
    gate = CanaryGate(fraud_loss_ceiling=0.02)
    registry = VersionRegistry(serving={"fusion_model": "fusion-v1"})
    result = _promote_if(
        gate, registry, "fusion_model",
        candidate="fusion-v2", base="fusion-v1",
        c_loss=0.005, b_loss=0.01, ceiling=0.02,
    )
    assert result == "PROMOTE"
    assert registry.current("fusion_model") == "fusion-v2"


def test_publish_on_promote_only(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)

    # Baseline published
    loader.publish("model_versions", "baseline-v1", {"models": {"fusion_model": "fusion-v1"}})

    # HOLD: no publish
    gate = CanaryGate(fraud_loss_ceiling=0.02)
    registry = VersionRegistry(serving={"fusion_model": "fusion-v1"})
    _promote_if(
        gate, registry, "fusion_model",
        candidate="fusion-v2", base="fusion-v1",
        c_loss=0.015, b_loss=0.010, ceiling=0.02,
    )
    assert loader.load_version("model_versions", "fusion-v2") is None

    # PROMOTE: publish
    registry2 = VersionRegistry(serving={"fusion_model": "fusion-v1"})
    result = _promote_if(
        gate, registry2, "fusion_model",
        candidate="fusion-v2", base="fusion-v1",
        c_loss=0.005, b_loss=0.010, ceiling=0.02,
    )
    assert result == "PROMOTE"
    loader.publish("model_versions", "fusion-v2", {"models": {"fusion_model": "fusion-v2"}})

    published = loader.load_version("model_versions", "fusion-v2")
    assert published is not None
    assert published.payload["models"]["fusion_model"] == "fusion-v2"