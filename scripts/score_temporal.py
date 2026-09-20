from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from fincrime_os.features.contracts import EventSequence
from fincrime_os.models.temporal.model import TemporalModel


def _parse(row: dict) -> EventSequence:
    ts = row["events"][0]["occurred_at"] if row["events"] else datetime.now(tz=timezone.utc).isoformat()
    as_of = datetime.fromisoformat(ts)
    return EventSequence(account_id=row["account_id"], events=row["events"], as_of=as_of)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="data/sequences.jsonl")
    p.add_argument("--preds-out", default="artifacts/preds_temporal.jsonl")
    p.add_argument("--labels-out", default="artifacts/labels_temporal.jsonl")
    args = p.parse_args()

    model = TemporalModel()
    if not model.is_trained:
        raise SystemExit("no trained temporal model found")

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
            seq = _parse(row)
            score = model.predict(seq)
            tid = f"seq_{n}"
            pf.write(json.dumps({"transaction_id": tid, "score": score}) + "\n")
            lf.write(json.dumps({"transaction_id": tid, "is_fraud": int(row["is_suspicious"])}) + "\n")
            n += 1
    print(f"wrote {n} predictions to {preds_path}")


if __name__ == "__main__":
    main()