from __future__ import annotations
import argparse
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

KINDS = [
    "login",
    "password_change",
    "device_registration",
    "beneficiary_addition",
    "transfer",
]


def generate(path: Path, accounts: int, events_per_account: int, seed: int) -> None:
    rng = random.Random(seed)
    base = datetime(2026, 9, 15, 1, 51, tzinfo=timezone.utc)
    with path.open("w", encoding="utf-8") as f:
        for a in range(accounts):
            account_id = f"cust_{a:04d}"
            t = base
            for _ in range(events_per_account):
                t = t + timedelta(seconds=rng.randint(30, 240))
                event = {
                    "event_id": f"evt_{uuid.uuid4().hex[:12]}",
                    "account_id": account_id,
                    "kind": rng.choice(KINDS),
                    "occurred_at": t.isoformat(),
                    "payload": {
                        "device_id": f"D{rng.randint(1, 20)}",
                        "amount": rng.choice([50, 200, 2000, 5000, 8700]),
                        "currency": "KES",
                        "country": rng.choice(["KE", "NG", "ZA"]),
                    },
                }
                f.write(json.dumps(event) + "\n")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="data/events.jsonl")
    p.add_argument("--accounts", type=int, default=5)
    p.add_argument("--events-per-account", type=int, default=8)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    generate(out, args.accounts, args.events_per_account, args.seed)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()