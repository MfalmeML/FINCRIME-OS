from fincrime_os.decision_engine.cost_model import CostModelInputs
from fincrime_os.decision_engine.optimizer import (
    GRID,
    SegmentOutcomeStats,
    optimize_all,
    optimize_segment,
    segment_stats_from_rows,
)


def _cost(p_fd=0.10, p_churn=0.05):
    return CostModelInputs(
        version="t",
        window_days=30,
        total_outcomes=0,
        declines_observed=0,
        false_declines=0,
        churned_after_decline=0,
        p_false_decline=p_fd,
        p_churn_given_decline=p_churn,
        avg_transaction_amount=100.0,
        confirmed_fraud_rate=0.05,
    )


def test_segment_stats_buckets_by_tier():
    rows = [
        {"segment": {"customer_tier": "vip"}, "transaction_amount": 100.0, "is_fraud": False},
        {"segment": {"customer_tier": "vip"}, "transaction_amount": 200.0, "is_fraud": True},
        {"segment": {"customer_tier": "default"}, "transaction_amount": 50.0, "is_fraud": False},
    ]
    stats = segment_stats_from_rows(rows)
    assert stats["vip"].n == 2
    assert stats["vip"].fraud_rate == 0.5
    assert stats["vip"].mean_amount == 150.0
    assert stats["default"].n == 1


def test_optimize_segment_returns_valid_pair():
    s = SegmentOutcomeStats(segment_key="default", n=100, fraud_rate=0.05, mean_amount=200.0)
    pair = optimize_segment(s, _cost())
    assert 0.0 < pair.t_challenge < pair.t_decline < 1.0
    assert pair.t_challenge in GRID
    assert pair.t_decline in GRID


def test_high_fraud_rate_pushes_thresholds_lower():
    cheap = _cost(p_fd=0.01, p_churn=0.01)
    high_fraud = SegmentOutcomeStats("default", 100, fraud_rate=0.50, mean_amount=200.0)
    low_fraud = SegmentOutcomeStats("default", 100, fraud_rate=0.01, mean_amount=200.0)
    high = optimize_segment(high_fraud, cheap)
    low = optimize_segment(low_fraud, cheap)
    # High fraud rate: challenge threshold should be no higher than low-fraud case
    assert high.t_challenge <= low.t_challenge


def test_high_friction_cost_pushes_thresholds_higher():
    cheap = _cost(p_fd=0.01, p_churn=0.01)
    expensive = _cost(p_fd=0.80, p_churn=0.50)
    s = SegmentOutcomeStats("default", 100, fraud_rate=0.05, mean_amount=200.0)
    t_cheap = optimize_segment(s, cheap)
    t_expensive = optimize_segment(s, expensive)
    # Expensive friction: challenge threshold should rise (more approving)
    assert t_expensive.t_challenge >= t_cheap.t_challenge


def test_optimize_all_returns_one_pair_per_segment():
    rows = [
        {"segment": {"customer_tier": "vip"}, "transaction_amount": 100.0, "is_fraud": False},
        {"segment": {"customer_tier": "default"}, "transaction_amount": 100.0, "is_fraud": True},
    ]
    result = optimize_all(rows, _cost())
    assert set(result.keys()) == {"vip", "default"}
    for tc, td in result.values():
        assert tc < td