from datetime import UTC, datetime, timedelta

from fincrime_os.features.baseline_risk import customer_baseline_risk
from fincrime_os.features.contracts import (
    BehavioralBaseline,
    EventSequence,
    GraphFeatures,
    TransactionFeatures,
)
from fincrime_os.pipeline import Pipeline

T0 = datetime(2026, 9, 15, 2, 13, tzinfo=UTC)


def _tx(amount=8700.0, country="NG", channel="web", currency="USD"):
    return TransactionFeatures(
        transaction_id="tx_int_1",
        account_id="cust_int_1",
        device_id="D912",
        amount=amount,
        currency=currency,
        merchant_id="M1",
        mcc="6051",
        country=country,
        channel=channel,
        event_time=T0,
        as_of=T0,
    )


def _baseline_full():
    return BehavioralBaseline(
        account_id="cust_int_1",
        txn_per_day=4.0,
        avg_amount=120.0,
        typical_hours=(8, 20),
        typical_countries=frozenset({"KE"}),
        typical_devices=frozenset({"D1"}),
        as_of=T0,
    )


def _baseline_empty():
    return BehavioralBaseline(
        account_id="cust_int_1",
        txn_per_day=0.0,
        avg_amount=0.0,
        typical_hours=(0, 23),
        typical_countries=frozenset(),
        typical_devices=frozenset(),
        as_of=T0,
    )


def _sequence():
    kinds = [
        "login",
        "password_change",
        "device_registration",
        "beneficiary_addition",
        "transfer",
        "transfer",
        "transfer",
    ]
    events = []
    t = T0 - timedelta(minutes=30)
    for k in kinds:
        t = t + timedelta(minutes=3)
        events.append({"event_id": f"e_{k}", "kind": k, "occurred_at": t.isoformat(), "payload": {}})
    return EventSequence(account_id="cust_int_1", events=events, as_of=T0)


def _graph():
    return GraphFeatures(
        account_id="cust_int_1",
        device_id="D912",
        connected_accounts=14,
        confirmed_fraud_neighbors=4,
        graph_ring_score=0.97,
        graph_confirmed_members=4,
        graph_snapshot_version="v-test",
        as_of=T0,
    )


def test_baseline_risk_full_history_is_low():
    assert customer_baseline_risk(_baseline_full()) <= 0.07


def test_baseline_risk_no_history_is_high():
    assert customer_baseline_risk(_baseline_empty()) >= 0.50


def test_pipeline_returns_bundle_with_baseline_risk():
    p = Pipeline()
    bundle = p.score(_tx(), _baseline_full(), _sequence(), _graph())
    assert 0.0 <= bundle.customer_baseline_risk <= 1.0
    assert 0.0 <= bundle.combined_risk_score <= 1.0
    assert bundle.graph_degraded is False
    assert bundle.graph_confirmed_members == 4


def test_pipeline_without_graph_degrades():
    p = Pipeline()
    bundle = p.score(_tx(), _baseline_full(), _sequence(), None)
    assert bundle.graph_degraded is True
    assert bundle.graph_ring_score == 0.0
    assert bundle.graph_confirmed_members == 0


def test_pipeline_uses_trained_models_when_present():
    """This test only asserts the wiring: if models are trained (they are in this
    repo after running the training scripts), the pipeline scores are non-zero for
    a clearly fraudulent-shaped input. If models are not trained, the test is a
    no-op assertion on the fallback behavior."""
    p = Pipeline()
    tx = _tx()
    baseline = _baseline_full()
    seq = _sequence()
    graph = _graph()
    bundle = p.score(tx, baseline, seq, graph)

    if p.transaction.is_trained:
        assert bundle.transaction_risk > 0.0
    if p.behavioral.is_trained:
        assert bundle.behavioral_anomaly_score > 0.0
    if p.temporal.is_trained:
        assert bundle.sequence_risk_score > 0.0
    if p.fusion.is_trained:
        assert bundle.combined_risk_score > 0.0