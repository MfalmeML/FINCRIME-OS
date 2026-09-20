from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class SegmentMetrics:
    segment_key: str
    n: int
    positives: int
    negatives: int
    tp: int
    fp: int
    tn: int
    fn: int
    precision: float
    recall: float
    f1: float
    false_positive_rate: float
    auc: float


@dataclass(frozen=True)
class EvalReport:
    version: str
    threshold: float
    total: int
    overall: SegmentMetrics
    segments: dict[str, SegmentMetrics] = field(default_factory=dict)


def _safe_div(n: float, d: float) -> float:
    return float(n) / float(d) if d else 0.0


def _auc(scores: list[tuple[float, int]]) -> float:
    """Rank-based AUC (Mann-Whitney U). scores = [(score, label)] with label in {0,1}."""
    pos = [s for s, y in scores if y == 1]
    neg = [s for s, y in scores if y == 0]
    if not pos or not neg:
        return 0.0
    combined = sorted([(s, 1) for s in pos] + [(s, 0) for s in neg], key=lambda x: x[0])
    rank_sum_pos = 0.0
    i = 0
    ranks = [0.0] * len(combined)
    while i < len(combined):
        j = i
        while j < len(combined) and combined[j][0] == combined[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j
    for idx, (_, label) in enumerate(combined):
        if label == 1:
            rank_sum_pos += ranks[idx]
    n_pos = len(pos)
    n_neg = len(neg)
    u = rank_sum_pos - n_pos * (n_pos + 1) / 2.0
    return u / (n_pos * n_neg)


def _metrics(segment_key: str, rows: list[tuple[float, int]], threshold: float) -> SegmentMetrics:
    tp = fp = tn = fn = 0
    for score, label in rows:
        pred = 1 if score >= threshold else 0
        if pred == 1 and label == 1:
            tp += 1
        elif pred == 1 and label == 0:
            fp += 1
        elif pred == 0 and label == 0:
            tn += 1
        else:
            fn += 1
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall)
    fpr = _safe_div(fp, fp + tn)
    return SegmentMetrics(
        segment_key=segment_key,
        n=len(rows),
        positives=tp + fn,
        negatives=tn + fp,
        tp=tp, fp=fp, tn=tn, fn=fn,
        precision=precision,
        recall=recall,
        f1=f1,
        false_positive_rate=fpr,
        auc=_auc(rows),
    )


def build_report(
    predictions: list[dict],
    labels: list[dict],
    segment_lookup: dict[str, str],
    threshold: float,
    version: str,
) -> EvalReport:
    labels_by_id = {r["transaction_id"]: int(r["is_fraud"]) for r in labels}
    rows: list[tuple[float, int, str]] = []
    for p in predictions:
        tid = p["transaction_id"]
        if tid not in labels_by_id:
            continue
        score = float(p["score"])
        label = labels_by_id[tid]
        seg = segment_lookup.get(tid, "default")
        rows.append((score, label, seg))

    overall_pairs = [(s, y) for s, y, _ in rows]
    overall = _metrics("__overall__", overall_pairs, threshold)

    buckets: dict[str, list[tuple[float, int]]] = {}
    for s, y, seg in rows:
        buckets.setdefault(seg, []).append((s, y))
    segments = {k: _metrics(k, v, threshold) for k, v in buckets.items()}

    return EvalReport(
        version=version,
        threshold=threshold,
        total=len(rows),
        overall=overall,
        segments=segments,
    )


def as_dict(report: EvalReport) -> dict:
    return {
        "version": report.version,
        "threshold": report.threshold,
        "total": report.total,
        "overall": asdict(report.overall),
        "segments": {k: asdict(v) for k, v in report.segments.items()},
    }