from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from fincrime_os.evaluation.metrics import as_dict, build_report
from fincrime_os.state.loader import publish


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--predictions", required=True,
                   help="JSONL with {transaction_id, score}")
    p.add_argument("--labels", required=True,
                   help="JSONL with {transaction_id, is_fraud}")
    p.add_argument("--segments", default=None,
                   help="optional JSONL with {transaction_id, segment}")
    p.add_argument("--threshold", type=float, default=0.5)
    p.add_argument("--version", default=None)
    args = p.parse_args()

    version = args.version or datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    preds = _read_jsonl(Path(args.predictions))
    labels = _read_jsonl(Path(args.labels))
    seg_rows = _read_jsonl(Path(args.segments)) if args.segments else []
    segment_lookup = {
        r["transaction_id"]: (r.get("segment") or {}).get("customer_tier", "default")
        for r in seg_rows
    }

    report = build_report(preds, labels, segment_lookup, args.threshold, version)
    path = publish("eval_reports", version, as_dict(report))

    print(f"eval_reports version={version} total={report.total} -> {path}")
    print(f"  overall precision={report.overall.precision:.4f} "
          f"recall={report.overall.recall:.4f} auc={report.overall.auc:.4f} "
          f"fpr={report.overall.false_positive_rate:.4f}")
    for k, m in report.segments.items():
        print(f"  segment={k} n={m.n} recall={m.recall:.3f} "
              f"fpr={m.false_positive_rate:.3f} auc={m.auc:.3f}")


if __name__ == "__main__":
    main()