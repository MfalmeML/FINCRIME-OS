from datetime import datetime, timedelta

import pytest

from fincrime_os.features.contracts import (
    TransactionFeatures,
    BehavioralBaseline,
    EventSequence,
    GraphFeatures,
)
from fincrime_os.features.point_in_time import (
    PointInTimeViolation,
    assert_not_future,
    assert_labels_are_mature,
)
from fincrime_os.pipeline import Pipeline

NOW = datetime(2026, 9, 15, 12, 0, 0)


def _tx():
    return TransactionFeatures(
        transaction_id="tx_1",
        account_id="cust_1",
        device_id="D1",
        amount=100.0,
        currency="KES",
        merchant_id="M1",
        mcc="5411",
        country="KE",
        channel="app",
        event_time=NOW,
        as_of=NOW,
    )


def _baseline(as_of=NOW):
    return BehavioralBaseline(
        account_id="cust_1",
        txn_per_day=4.0,
        avg_amount=120.0,
        typical_hours=(8, 20),
        typical_countries=frozenset({"KE"}),
        typical_devices=frozenset({"D1"}),
        as_of=as_of,
    )


def _sequence(as_of=NOW):
    return EventSequence(account_id="cust_1", events=[], as_of=as_of)


def test_pipeline_runs_with_graph():
    gf = GraphFeatures(
        account_id="cust_1",
        device_id="D1",
        connected_accounts=14,
        confirmed_fraud_neighbors=4,
        graph_ring_score=0.97,
        graph_confirmed_members=4,
        graph_snapshot_version="graph-2026-09-15",
        as_of=NOW,
    )
    bundle = Pipeline().score(_tx(), _baseline(), _sequence(), gf)
    assert bundle.graph_degraded is False
    assert bundle.graph_confirmed_members == 4


def test_pipeline_degrades_without_graph():
    bundle = Pipeline().score(_tx(), _baseline(), _sequence(), None)
    assert bundle.graph_degraded is True
    assert bundle.graph_confirmed_members == 0


def test_point_in_time_violation_raises():
    future = NOW + timedelta(seconds=1)
    with pytest.raises(PointInTimeViolation):
        assert_not_future(future, NOW)


def test_label_maturity_guard():
    with pytest.raises(PointInTimeViolation):
        assert_labels_are_mature(NOW, NOW)
    assert_labels_are_mature(NOW + timedelta(seconds=1), NOW)