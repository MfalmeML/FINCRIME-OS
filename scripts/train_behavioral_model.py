from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

from fincrime_os.features.contracts import TransactionFeatures, BehavioralBaseline
from fincrime_os.models.behavioral.features import feature_names, vectorize
from fincrime_os.state.loader import STATE_ROOT, publish


def _parse(row: dict) -> tuple[TransactionFeatures, BehavioralBaseline]:
    t = datetime.fromisoformat(row["event_time"])
    b = row["baseline"]
    baseline = BehavioralBaseline(
        account_id=row["account_id"],
        txn_per_day=float(b["txn_per_day"]),
        avg_amount=float(b["avg_amount"]),
        typical_hours=(int(b["typical_hours"][0]), int(b["typical_hours"][1])),
        typical_countries=frozenset(b["typical_countries"]),
        typical_devices=frozenset(b["typical_devices"]),
        as_of=t,
    )
    tx = TransactionFeatures(
        transaction_id=row["transaction_id"],
        account_id=row["account_id"],
        device_id=row["device_id"],
        amount=float(row["amount"]),
        currency=row["currency"],
        merchant_id=row["merchant_id"],
        mcc=row["mcc"],
        country=row["country"],
        channel=row["channel"],
        event_time=t,
        as_of=t,
    )
    return tx, baseline


def _load(path: Path) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    features, labels, meta = [], [], []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            tx, b = _parse(row)
            features.append(vectorize(tx, b))
            labels.append(int(row["is_anomaly"]))
            meta.append(row)
    if not features:
        raise SystemExit(f"no rows in {path}")
    return np.vstack(features), np.asarray(labels, dtype=np.int32), meta


def _auc(scores: np.ndarray, labels: np.ndarray) -> float:
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return 0.0
    combined = np.concatenate([pos, neg])
    order = np.argsort(combined)
    ranks = np.empty_like(order, dtype=np.float64)
    ranks[order] = np.arange(1, len(combined) + 1)
    rank_sum_pos = ranks[: len(pos)].sum()
    n_pos, n_neg = len(pos), len(neg)
    u = rank_sum_pos - n_pos * (n_pos + 1) / 2.0
    return u / (n_pos * n_neg)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="data/behavioral.jsonl")
    p.add_argument("--version", default=None)
    p.add_argument("--valid-fraction", type=float, default=0.2)
    p.add_argument("--max-iter", type=int, default=200)
    p.add_argument("--learning-rate", type=float, default=0.08)
    p.add_argument("--max-depth", type=int, default=6)
    args = p.parse_args()

    version = args.version or datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    X, y, meta = _load(Path(args.data))
    order = sorted(range(len(meta)), key=lambda i: meta[i]["event_time"])
    cut = int(len(order) * (1.0 - args.valid_fraction))
    train_idx = np.asarray(order[:cut])
    valid_idx = np.asarray(order[cut:])

    clf = HistGradientBoostingClassifier(
        max_iter=args.max_iter,
        learning_rate=args.learning_rate,
        max_depth=args.max_depth,
        random_state=42,
    )
    clf.fit(X[train_idx], y[train_idx])

    train_auc = _auc(clf.predict_proba(X[train_idx])[:, 1], y[train_idx])
    valid_auc = _auc(clf.predict_proba(X[valid_idx])[:, 1], y[valid_idx])

    model_dir = STATE_ROOT / "models" / "behavioral"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / f"{version}.joblib"
    joblib.dump(
        {"model": clf, "feature_names": feature_names(), "version": version},
        model_path,
    )

    publish(
        "behavioral_model_meta",
        version,
        {
            "data_path": str(args.data),
            "n_total": int(X.shape[0]),
            "n_train": int(len(train_idx)),
            "n_valid": int(len(valid_idx)),
            "anomaly_rate": float(y.mean()),
            "train_auc": float(train_auc),
            "valid_auc": float(valid_auc),
            "features": feature_names(),
            "hyperparams": {
                "max_iter": args.max_iter,
                "learning_rate": args.learning_rate,
                "max_depth": args.max_depth,
            },
        },
    )

    print(f"trained behavioral_model version={version}")
    print(f"  n_train={len(train_idx)} n_valid={len(valid_idx)} anomaly_rate={y.mean():.4f}")
    print(f"  train_auc={train_auc:.4f} valid_auc={valid_auc:.4f}")
    print(f"  model_path={model_path}")


if __name__ == "__main__":
    main()