from __future__ import annotations
import argparse
import json
import random
from pathlib import Path


def _draw(rng: random.Random, is_ring_member: bool) -> dict:
    if is_ring_member:
        connected = rng.randint(8, 40)
        confirmed = rng.randint(3, max(4, connected // 2))
        members = rng.randint(2, max(3, confirmed))
        ring = min(0.99, rng.uniform(0.85, 0.99))
    else:
        connected = rng.randint(1, 6)
        confirmed = rng.randint(0, 1)
        members = rng.randint(0, 1)
        ring = min(0.85, rng.betavariate(1.2, 8))

    return {
        "connected_accounts": connected,
        "confirmed_fraud_neighbors": confirmed,
        "graph_confirmed_members": members,
        "graph_ring_score": round(ring, 4),
        "is_ring_member": 1 if is_ring_member else 0,
    }


def generate(out: Path, n: int, ring_rate: float, seed: int) -> None:
    rng = random.Random(seed)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for _ in range(n):
            is_ring = rng.random() < ring_rate
            row = _draw(rng, is_ring)
            f.write(json.dumps(row) + "\n")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="data/graph.jsonl")
    p.add_argument("--n", type=int, default=40000)
    p.add_argument("--ring-rate", type=float, default=0.05)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    generate(Path(args.out), args.n, args.ring_rate, args.seed)
    print(f"wrote {args.n} rows to {args.out} ring_rate={args.ring_rate}")


if __name__ == "__main__":
    main()