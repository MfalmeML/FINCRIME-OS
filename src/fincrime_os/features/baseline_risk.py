from __future__ import annotations
from fincrime_os.features.contracts import BehavioralBaseline


def customer_baseline_risk(baseline: BehavioralBaseline) -> float:
    """Prior probability that a customer with this baseline profile is risky.

    Not a trained quantity in v1. It is a deterministic function of how much
    history we have on the customer:

    - No history at all (no txn rate, no amount, no known devices/countries):
      the model has nothing to compare against, so the prior is high. Thin-file
      customers are the population most exposed to over-restriction and also
      the population most used by fraud rings. The fusion layer is expected to
      learn how much to trust this prior.
    - Partial history (some baseline signals present): moderate prior.
    - Full history: low prior.

    This value MUST stay in [0.0, 1.0]. It is consumed by the fusion model as a
    feature, not as a decision.
    """
    has_rate = baseline.txn_per_day > 0
    has_amount = baseline.avg_amount > 0
    has_devices = len(baseline.typical_devices) > 0
    has_countries = len(baseline.typical_countries) > 0
    signals = sum([has_rate, has_amount, has_devices, has_countries])

    if signals == 0:
        return 0.50
    if signals == 1:
        return 0.30
    if signals == 2:
        return 0.15
    if signals == 3:
        return 0.07
    return 0.03