from fincrime_os.explainability.explainer import Explainer


def _explainer():
    return Explainer()


def test_non_approve_decision_has_complete_explanation():
    e = _explainer().build(
        transaction_id="tx_1",
        decision="DECLINE",
        amount=8700.0,
        avg_amount=120.0,
        connected_accounts=14,
        confirmed_fraud_neighbors=4,
        graph_ring_score=0.97,
        graph_confirmed_members=4,
        sequence_risk_score=0.91,
        behavioral_anomaly_score=0.94,
        transaction_risk=0.73,
    )
    assert e.complete is True
    assert len(e.reason_codes) >= 3
    assert e.counterfactual != ""
    codes = {c.code for c in e.reason_codes}
    assert "AMOUNT_DEVIATION" in codes
    assert "DEVICE_CONNECTIVITY" in codes
    assert "RING_OVERRIDE" in codes


def test_approve_decision_is_considered_complete():
    e = _explainer().build(
        transaction_id="tx_2",
        decision="APPROVE",
        amount=50.0,
        avg_amount=120.0,
        connected_accounts=1,
        confirmed_fraud_neighbors=0,
        graph_ring_score=0.0,
        graph_confirmed_members=0,
        sequence_risk_score=0.1,
        behavioral_anomaly_score=0.1,
        transaction_risk=0.1,
    )
    assert e.complete is True
    assert e.reason_codes == []


def test_ring_override_only_fires_above_cutoff():
    e = _explainer().build(
        transaction_id="tx_3",
        decision="CHALLENGE",
        amount=100.0,
        avg_amount=100.0,
        connected_accounts=2,
        confirmed_fraud_neighbors=0,
        graph_ring_score=0.85,
        graph_confirmed_members=4,
        sequence_risk_score=0.3,
        behavioral_anomaly_score=0.3,
        transaction_risk=0.3,
    )
    codes = {c.code for c in e.reason_codes}
    assert "RING_OVERRIDE" not in codes


def test_counterfactual_points_at_top_driver():
    e = _explainer().build(
        transaction_id="tx_4",
        decision="DECLINE",
        amount=100.0,
        avg_amount=100.0,
        connected_accounts=2,
        confirmed_fraud_neighbors=0,
        graph_ring_score=0.99,
        graph_confirmed_members=4,
        sequence_risk_score=0.3,
        behavioral_anomaly_score=0.3,
        transaction_risk=0.3,
    )
    assert "confirmed fraud network" in e.counterfactual