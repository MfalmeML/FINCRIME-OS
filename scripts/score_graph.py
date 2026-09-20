from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from fincrime_os.features.contracts import GraphFeatures
from fincrime_os.models.graph.model import GraphModel


def _parse(row: dict) -> GraphFeatures:
    return GraphFeatures(
        account_id="synthetic",
        device_id="synthetic",
        connected_accounts=int(row["connected_accounts"]),
        confirmed_fraud_neighbors=int(row["confirmed_fraud_neighbors"]),
        graph_ring_score=float(row["graph_ring_score"]),
        graph_confirmed_members=int(row["graph_confirmed_members"]),
        graph_snapshot_version="synthetic",
        as_of=datetime.now(tz=timezone.utc),
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="data/graph.jsonl")
    p.add_argument("--preds-out", default="artifacts/preds_graph.jsonl")
    p.add_argument("--labels-out", default="artifacts/labels_graph.jsonl")
    args = p.parse_args()

    model = GraphModel()
    if not model.is_trained:
        raise SystemExit("no trained graph model found")

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
            g = _parse(row)
            score = model.predict(g)
            tid = f"gr_{n}"
            pf.write(json.dumps({"transaction_id": tid, "score": score}) + "\n")
            lf.write(json.dumps({"transaction_id": tid, "is_fraud": int(row["is_ring_member"])}) + "\n")
            n += 1
    print(f"wrote {n} predictions to {preds_path}")


if __name__ == "__main__":
    main()