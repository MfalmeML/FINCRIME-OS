from fincrime_os.monitoring.runtime_metrics import RuntimeMetrics


def test_empty_snapshot_is_zero():
    m = RuntimeMetrics()
    s = m.snapshot()
    assert s["decisions"] == 0
    assert s["graph_degraded"] == 0
    assert s["graph_degraded_rate"] == 0.0


def test_rate_computed_correctly():
    m = RuntimeMetrics()
    for _ in range(7):
        m.record_decision(graph_degraded=False)
    for _ in range(3):
        m.record_decision(graph_degraded=True)
    s = m.snapshot()
    assert s["decisions"] == 10
    assert s["graph_degraded"] == 3
    assert abs(s["graph_degraded_rate"] - 0.3) < 1e-9


def test_reset_clears_counters():
    m = RuntimeMetrics()
    m.record_decision(graph_degraded=True)
    m.reset()
    assert m.snapshot()["decisions"] == 0


def test_window_prunes_old_entries():
    m = RuntimeMetrics(window_seconds=0)
    m.record_decision(graph_degraded=True)
    # window_seconds=0 means everything is older than cutoff on next snapshot
    import time
    time.sleep(0.01)
    s = m.snapshot()
    assert s["decisions"] == 0
    assert s["graph_degraded"] == 0