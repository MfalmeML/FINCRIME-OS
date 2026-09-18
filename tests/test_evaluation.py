from fincrime_os.evaluation.metrics import build_report


def _preds(pairs):
    return [{"transaction_id": tid, "score": s} for tid, s in pairs]


def _labels(pairs):
    return [{"transaction_id": tid, "is_fraud": y} for tid, y in pairs]


def test_perfect_classifier():
    preds = _preds([("t1", 0.9), ("t2", 0.1), ("t3", 0.8), ("t4", 0.2)])
    labels = _labels([("t1", 1), ("t2", 0), ("t3", 1), ("t4", 0)])
    r = build_report(preds, labels, {}, threshold=0.5, version="v")
    assert r.overall.precision == 1.0
    assert r.overall.recall == 1.0
    assert r.overall.f1 == 1.0
    assert r.overall.false_positive_rate == 0.0
    assert r.overall.auc == 1.0


def test_worst_classifier_inverts_auc():
    preds = _preds([("t1", 0.1), ("t2", 0.9), ("t3", 0.2), ("t4", 0.8)])
    labels = _labels([("t1", 1), ("t2", 0), ("t3", 1), ("t4", 0)])
    r = build_report(preds, labels, {}, threshold=0.5, version="v")
    assert r.overall.auc == 0.0


def test_false_positive_rate_computed():
    preds = _preds([("t1", 0.9), ("t2", 0.9), ("t3", 0.1), ("t4", 0.1)])
    labels = _labels([("t1", 1), ("t2", 0), ("t3", 1), ("t4", 0)])
    r = build_report(preds, labels, {}, threshold=0.5, version="v")
    assert r.overall.tp == 1
    assert r.overall.fp == 1
    assert r.overall.fn == 1
    assert r.overall.false_positive_rate == 0.5
    assert r.overall.recall == 0.5


def test_per_segment_metrics_isolated():
    preds = _preds([
        ("t1", 0.9), ("t2", 0.1), ("t3", 0.9), ("t4", 0.1),
    ])
    labels = _labels([("t1", 1), ("t2", 0), ("t3", 0), ("t4", 1)])
    segs = {"t1": "vip", "t2": "vip", "t3": "default", "t4": "default"}
    r = build_report(preds, labels, segs, threshold=0.5, version="v")
    assert r.segments["vip"].recall == 1.0
    assert r.segments["default"].recall == 0.0


def test_missing_labels_are_skipped():
    preds = _preds([("t1", 0.9), ("t2", 0.1), ("t_unlabeled", 0.5)])
    labels = _labels([("t1", 1), ("t2", 0)])
    r = build_report(preds, labels, {}, threshold=0.5, version="v")
    assert r.total == 2


def test_auc_ties_handled():
    preds = _preds([("t1", 0.5), ("t2", 0.5), ("t3", 0.5), ("t4", 0.5)])
    labels = _labels([("t1", 1), ("t2", 0), ("t3", 1), ("t4", 0)])
    r = build_report(preds, labels, {}, threshold=0.5, version="v")
    assert abs(r.overall.auc - 0.5) < 1e-9
