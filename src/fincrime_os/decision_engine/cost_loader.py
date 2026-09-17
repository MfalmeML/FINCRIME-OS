from __future__ import annotations

from fincrime_os.decision_engine.cost_model import CostModelInputs
from fincrime_os.state.loader import load_latest

DEFAULT_VERSION = "unversioned-dev"


def load_cost_inputs() -> CostModelInputs:
    """Load the latest published cost model inputs, or a zeroed default if none exist."""
    artifact = load_latest("cost_model_inputs")
    if artifact is None:
        return CostModelInputs(
            version=DEFAULT_VERSION,
            window_days=0,
            total_outcomes=0,
            declines_observed=0,
            false_declines=0,
            churned_after_decline=0,
            p_false_decline=0.0,
            p_churn_given_decline=0.0,
            avg_transaction_amount=0.0,
            confirmed_fraud_rate=0.0,
        )

    p = artifact.payload
    return CostModelInputs(
        version=artifact.version,
        window_days=p.get("window_days", 0),
        total_outcomes=p.get("total_outcomes", 0),
        declines_observed=p.get("declines_observed", 0),
        false_declines=p.get("false_declines", 0),
        churned_after_decline=p.get("churned_after_decline", 0),
        p_false_decline=p.get("p_false_decline", 0.0),
        p_churn_given_decline=p.get("p_churn_given_decline", 0.0),
        avg_transaction_amount=p.get("avg_transaction_amount", 0.0),
        confirmed_fraud_rate=p.get("confirmed_fraud_rate", 0.0),
    )
