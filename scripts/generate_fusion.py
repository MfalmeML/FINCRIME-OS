from __future__ import annotations
import argparse
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _draw(rng: random.Random, is_fraud: bool) -> tuple[float, float, float, float, float]:
    if is_fraud:
        # Fraudulent: at least one signal should be high. Mixed shapes.
        t = rng.uniform(0.5, 0.99)
        b = rng.uniform(0.4, 0.99)
        s = rng.uniform(0.3, 0.99)
        g = rng.betavariate(2, 3) if rng.random() < 0.5 else rng.uniform(0.7, 0.99)
        c = rng.uniform(0.0, 0.4)
    else:
        # Legitimate: mostly low, occasional noisy signal.
        t = rng.betavariate(1.5, 6)
        b = rng.betavariate(1.5, 6)
        s = rng.betavariate(1.5, 6)
        g = rng.betavariate(1.2, 8)
        c = rng.uniform(0.0, 0.3)
    return t, b, s, g, c


def generate(out: Path, n: int, fraud_rate: float, seed: int) -> None:
    rng = random.Random(seed)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for _ in range(n):
            is_fraud = rng.random() < fraud_rate
            t, b, s, g, c = _draw(rng, is_fraud)
            f.write(
                json.dumps(
                    {
                        "transaction_risk": round(t, 4),
                        "behavioral_score": round(b, 4),
                        "sequence_score": round(s, 4),
                        "graph_score": round(g, 4),
                        "customer_baseline_risk": round(c, 4),
                        "is_fraud": 1 if is_fraud else 0,
                    }
                )
                + "\n"
            )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="data/fusion.jsonl")
    p.add_argument("--n", type=int, default=40000)
    p.add_argument("--fraud-rate", type=float, default=0.03)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    generate(Path(args.out), args.n, args.fraud_rate, args.seed)
    print(f"wrote {args.n} rows to {args.out} fraud_rate={args.fraud_rate}")


if __name__ == "__main__":
    main()