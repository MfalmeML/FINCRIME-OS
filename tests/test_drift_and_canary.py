from fincrime_os.drift.detector import DriftDetector
from fincrime_os.drift.canary import (
    CanaryGate,
    CanaryOutcome,
    VersionRegistry,
    apply_gate,
)
from fincrime_os.decision_engine.fallbacks import (
    graph_fallback,
    threshold_fallback,
    drift_freeze,
    adaptation_delay,
)


def test_drift_fires_on_fraud_rate_spike():
    d = DriftDetector()
    signals = d.check(0.05, 0.05, 0.05, fraud_rate_multiplier=6.8)
    assert d.any_fired(signals)
    fired = [s for s in signals if s.fired]
    assert fired[0].component == "fraud_rate"


def test_drift_silent_when_stable():
    d = DriftDetector()
    signals = d.check(0.01, 0.01, 0.01, fraud_rate_multiplier=1.0)
    assert not d.any_fired(signals)


def test_canary_rejects_over_ceiling():
    gate = CanaryGate(fraud_loss_ceiling=0.02)
    outcome = CanaryOutcome(
        candidate_version="v2",
        baseline_version="v1",
        candidate_fraud_loss=0.05,
        baseline_fraud_loss=0.01,
        fraud_loss_ceiling=0.02,
    )
    assert gate.evaluate(outcome) == "REJECT"


def test_canary_promotes_better_model():
    gate = CanaryGate(fraud_loss_ceiling=0.02)
    registry = VersionRegistry(serving={"fusion": "v1"})
    outcome = CanaryOutcome(
        candidate_version="v2",
        baseline_version="v1",
        candidate_fraud_loss=0.005,
        baseline_fraud_loss=0.01,
        fraud_loss_ceiling=0.02,
    )
    result = apply_gate(gate, registry, "fusion", outcome)
    assert result == "PROMOTE"
    assert registry.current("fusion") == "v2"


def test_canary_holds_worse_but_under_ceiling():
    gate = CanaryGate(fraud_loss_ceiling=0.02)
    registry = VersionRegistry(serving={"fusion": "v1"})
    outcome = CanaryOutcome(
        candidate_version="v2",
        baseline_version="v1",
        candidate_fraud_loss=0.015,
        baseline_fraud_loss=0.01,
        fraud_loss_ceiling=0.02,
    )
    result = apply_gate(gate, registry, "fusion", outcome)
    assert result == "HOLD"
    assert registry.current("fusion") == "v1"


def test_fallback_flags():
    assert graph_fallback().flags()["graph_degraded"] is True
    assert threshold_fallback().flags()["threshold_degraded"] is True
    assert drift_freeze().flags()["drift_frozen"] is True
    assert adaptation_delay().flags()["adaptation_delayed"] is True