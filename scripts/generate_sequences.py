from __future__ import annotations
import argparse
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path


KINDS_NORMAL = ["login", "transfer", "login", "transfer", "login", "transfer"]
KINDS_SUSPICIOUS = [
    "login",
    "password_change",
    "device_registration",
    "beneficiary_addition",
    "transfer",
    "transfer",
    "transfer",
]


def _make_sequence(rng: random.Random, base: datetime, is_suspicious: bool) -> list[dict]:
    if is_suspicious:
        kinds = KINDS_SUSPICIOUS
        start = base.replace(hour=rng.choice([1, 2, 3, 4, 23]))
        gap = rng.randint(60, 240)
    else:
        kinds = rng.sample(KINDS_NORMAL, k=len(KINDS_NORMAL))
        start = base.replace(hour=rng.randint(8, 20))
        gap = rng.randint(600, 3600)

    events = []
    t = start
    for k in kinds:
        t = t + timedelta(seconds=gap)
        events.append(
            {
                "event_id": f"evt_{uuid.uuid4().hex[:10]}",
                "kind": k,
                "occurred_at": t.isoformat(),
                "payload": {
                    "amount": rng.choice([200, 2000, 5000, 8700]) if k == "transfer" else 0,
                    "device_id": f"D{rng.randint(1, 400)}",
                },
            }
        )
    return events


def generate(out: Path, n: int, suspicious_rate: float, seed: int) -> None:
    rng = random.Random(seed)
    base = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for _ in range(n):
            is_suspicious = rng.random() < suspicious_rate
            offset = timedelta(minutes=rng.randint(0, 60 * 24 * 30))
            events = _make_sequence(rng, base + offset, is_suspicious)
            f.write(
                json.dumps(
                    {
                        "account_id": f"cust_{rng.randint(1, 2000):04d}",
                        "events": events,
                        "is_suspicious": 1 if is_suspicious else 0,
                    }
                )
                + "\n"
            )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="data/sequences.jsonl")
    p.add_argument("--n", type=int, default=20000)
    p.add_argument("--suspicious-rate", type=float, default=0.10)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    generate(Path(args.out), args.n, args.suspicious_rate, args.seed)
    print(f"wrote {args.n} rows to {args.out} suspicious_rate={args.suspicious_rate}")


if __name__ == "__main__":
    main()