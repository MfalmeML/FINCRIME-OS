from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass(frozen=True)
class CostModelInputs:
    version: str
    window_days: int
    total_outcomes: int
    declines_observed: int
    false_declines: int
    churned_after_decline: int
    p_false_decline: float
    p_churn_given_decline: float
    avg_transaction_amount: float
    confirmed_fraud_rate: float


def _safe_div(n: float, d: float) -> float:
    return float(n) / float(d) if d else 0.0


def build_inputs(
    rows: Iterable[dict],
    version: str,
    window_days: int,
) -> CostModelInputs:
    rows = list(rows)
    declines = [r for r in rows if r.get("decision") in ("DECLINE", "CHALLENGE")]
    false_declines = [r for r in declines if r.get("is_false_decline") is True]
    churned = [r for r in declines if r.get("churned_after_decline") is True]
    fraud_confirmed = [r for r in rows if r.get("is_fraud") is True]

    total_amount = 0.0
    counted = 0
    for r in rows:
        amt = r.get("transaction_amount")
        if isinstance(amt, (int, float)):
            total_amount += float(amt)
            counted += 1

    return CostModelInputs(
        version=version,
        window_days=window_days,
        total_outcomes=len(rows),
        declines_observed=len(declines),
        false_declines=len(false_declines),
        churned_after_decline=len(churned),
        p_false_decline=_safe_div(len(false_declines), len(declines)),
        p_churn_given_decline=_safe_div(len(churned), len(declines)),
        avg_transaction_amount=_safe_div(total_amount, counted),
        confirmed_fraud_rate=_safe_div(len(fraud_confirmed), len(rows)),
    )


def as_dict(inputs: CostModelInputs) -> dict:
    return asdict(inputs)