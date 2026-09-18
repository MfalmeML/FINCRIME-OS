from __future__ import annotations
import argparse
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path


CHANNELS = ["app", "web", "pos", "atm", "branch"]
COUNTRIES = ["KE", "NG", "ZA", "UG", "TZ", "GB", "US"]


def _baseline(rng: random.Random) -> dict:
    avg = rng.uniform(80, 400)
    txn = rng.uniform(1, 8)
    lo = rng.randint(6, 10)
    hi = rng.randint(18, 22)
    countries = ["KE"]
    devices = [f"D{rng.randint(1, 200)}"]
    return {
        "txn_per_day": txn,
        "avg_amount": avg,
        "typical_hours": [lo, hi],
        "typical_countries": countries,
        "typical_devices": devices,
    }


def _make_row(
    rng: random.Random,
    base: datetime,
    account_id: str,
    device_id: str,
    baseline: dict,
    is_anomaly: bool,
) -> dict:
    if is_anomaly:
        amount = baseline["avg_amount"] * rng.uniform(15, 60)
        hour = rng.choice([1, 2, 3, 4, 23])
        country = rng.choice([c for c in COUNTRIES if c not in baseline["typical_countries"]])
        device = f"D{rng.randint(201, 400)}"
        channel = rng.choice(["web", "app"])
        currency = rng.choice(["USD", "GBP"])
    else:
        amount = baseline["avg_amount"] * rng.uniform(0.3, 2.5)
        hour = rng.randint(baseline["typical_hours"][0], baseline["typical_hours"][1])
        country = baseline["typical_countries"][0]
        device = baseline["typical_devices"][0]
        channel = rng.choice(CHANNELS)
        currency = "KES"

    event_time = base.replace(hour=hour, minute=rng.randint(0, 59), second=0)
    return {
        "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
        "account_id": account_id,
        "device_id": device,
        "amount": round(amount, 2),
        "currency": currency,
        "merchant_id": f"M{rng.randint(1, 300)}",
        "mcc": rng.choice(["5411", "5999", "6051"]),
        "country": country,
        "channel": channel,
        "event_time": event_time.isoformat(),
        "baseline": baseline,
        "is_anomaly": 1 if is_anomaly else 0,
    }


def generate(out: Path, n: int, anomaly_rate: float, seed: int) -> None:
    rng = random.Random(seed)
    base = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    out.parent.mkdir(parents=True, exist_ok=True)
    accounts = [f"cust_{i:04d}" for i in range(max(1, n // 20))]
    baselines = {a: _baseline(rng) for a in accounts}
    primary_device = {a: baselines[a]["typical_devices"][0] for a in accounts}

    with out.open("w", encoding="utf-8") as f:
        for _ in range(n):
            account = rng.choice(accounts)
            device = primary_device[account]
            is_anomaly = rng.random() < anomaly_rate
            offset = timedelta(minutes=rng.randint(0, 60 * 24 * 30))
            row = _make_row(rng, base + offset, account, device, baselines[account], is_anomaly)
            f.write(json.dumps(row) + "\n")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="data/behavioral.jsonl")
    p.add_argument("--n", type=int, default=20000)
    p.add_argument("--anomaly-rate", type=float, default=0.05)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    generate(Path(args.out), args.n, args.anomaly_rate, args.seed)
    print(f"wrote {args.n} rows to {args.out} anomaly_rate={args.anomaly_rate}")


if __name__ == "__main__":
    main()