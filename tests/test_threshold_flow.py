
import fincrime_os.state.loader as loader
from fincrime_os.decision_engine.cost_model import CostModelInputs
from fincrime_os.decision_engine.optimizer import optimize_all
from fincrime_os.state.loader import publish


def _rows():
    return [
        {"segment": {"customer_tier": "vip"}, "transaction_amount": 500.0, "is_fraud": False, "decision": "APPROVE"},
        {"segment": {"customer_tier": "vip"}, "transaction_amount": 800.0, "is_fraud": True, "decision": "DECLINE"},
        {"segment": {"customer_tier": "default"}, "transaction_amount": 100.0, "is_fraud": False, "decision": "APPROVE"},
    ]


def _cost():
    return CostModelInputs(
        version="t", window_days=30, total_outcomes=0, declines_observed=0,
        false_declines=0, churned_after_decline=0,
        p_false_decline=0.10, p_churn_given_decline=0.05,
        avg_transaction_amount=100.0, confirmed_fraud_rate=0.05,
    )


def test_optimize_then_publish_then_load(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "STATE_ROOT", tmp_path)
    optimized = optimize_all(_rows(), _cost())
    entries = {k: [float(v[0]), float(v[1])] for k, v in optimized.items()}
    publish("threshold_tables", "v-opt", {"entries": entries})

    a = loader.load_latest("threshold_tables")
    assert a is not None
    assert a.version == "v-opt"
    assert "vip" in a.payload["entries"]
    tc, td = a.payload["entries"]["vip"]
    assert tc < td