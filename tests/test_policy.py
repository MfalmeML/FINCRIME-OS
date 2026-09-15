from fincrime_os.decision_engine.policy import decide


def test_graph_override_beats_thresholds():
    d, r = decide(0.10, 0.99, 5)
    assert d == "DECLINE"
    assert r == "graph_override"


def test_approve_below_threshold():
    d, _ = decide(0.10, 0.0, 0)
    assert d == "APPROVE"


def test_challenge_band():
    d, _ = decide(0.55, 0.0, 0)
    assert d == "CHALLENGE"


def test_decline_above_threshold():
    d, _ = decide(0.90, 0.0, 0)
    assert d == "DECLINE"


def test_override_requires_two_members():
    d, _ = decide(0.10, 0.99, 1)
    assert d == "APPROVE"