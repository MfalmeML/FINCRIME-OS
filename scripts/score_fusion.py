from __future__ import annotations
import argparse
import json
from pathlib import Path

from fincrime_os.models.fusion.model import FusionModel


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="data/fusion.jsonl")
    p.add_argument("--preds-out", default="artifacts/preds_fusion.jsonl")
    p.add_argument("--labels-out", default="artifacts/labels_fusion.jsonl")
    args = p.parse_args()

    model = FusionModel()
    if not model.is_trained:
        raise SystemExit("no trained fusion model found")

    preds_path = Path(args.preds_out)
    labels_path = Path(args.labels_out)
    preds_path.parent.mkdir(parents=True, exist_ok=True)

    n = 0
    with Path(args.data).open("r", encoding="utf-8") as src, \
         preds_path.open("w", encoding="utf-8") as pf, \
         labels_path.open("w", encoding="utf-8") as lf:
        for line in src:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            score = model.predict(
                float(row["transaction_risk"]),
                float(row["behavioral_score"]),
                float(row["sequence_score"]),
                float(row["graph_score"]),
                float(row["customer_baseline_risk"]),
            )
            tid = f"fu_{n}"
            pf.write(json.dumps({"transaction_id": tid, "score": score}) + "\n")
            lf.write(json.dumps({"transaction_id": tid, "is_fraud": int(row["is_fraud"])}) + "\n")
            n += 1
    print(f"wrote {n} predictions to {preds_path}")


if __name__ == "__main__":
    main()