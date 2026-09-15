from fincrime_os.investigation.engine import Alert, InvestigationEngine
from fincrime_os.investigation.queue import InvestigatorQueue


def _alert(case_id, risk, amount, ring=0.0, members=0):
    return Alert(
        case_id=case_id,
        combined_risk_score=risk,
        transaction_amount=amount,
        graph_ring_score=ring,
        graph_confirmed_members=members,
        segment_tier="default",
    )


def test_high_value_high_risk_outranks_low_value_high_risk():
    engine = InvestigationEngine()
    alerts = [
        _alert("small", 0.96, 40.0),
        _alert("large", 0.88, 40000.0),
    ]
    ranked = engine.rank(alerts)
    assert ranked[0].case_id == "large"


def test_network_membership_boosts_priority():
    engine = InvestigationEngine()
    alerts = [
        _alert("isolated", 0.90, 1000.0),
        _alert("networked", 0.90, 1000.0, ring=0.95, members=4),
    ]
    ranked = engine.rank(alerts)
    assert ranked[0].case_id == "networked"


def test_rank_is_monotonic_decreasing():
    engine = InvestigationEngine()
    alerts = [
        _alert("a", 0.5, 100.0),
        _alert("b", 0.9, 5000.0),
        _alert("c", 0.7, 500.0),
    ]
    ranked = engine.rank(alerts)
    values = [r.expected_loss_prevented for r in ranked]
    assert values == sorted(values, reverse=True)
    assert [r.rank for r in ranked] == [1, 2, 3]


def test_queue_respects_capacity():
    engine = InvestigationEngine(investigator_daily_capacity=2)
    queue = InvestigatorQueue(engine=engine)
    alerts = [_alert(f"c{i}", 0.5 + i * 0.01, 100.0 + i) for i in range(10)]
    workable = queue.workable_slice(alerts)
    assert len(workable) == 2


def test_empty_alert_list_returns_empty():
    engine = InvestigationEngine()
    assert engine.rank([]) == []