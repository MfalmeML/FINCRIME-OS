from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone

from fincrime_os.drift.outcome_drift import as_dict, compute_outcome_drift
from fincrime_os.state.loader import publish
from fincrime_os.state.outcomes import read_outcomes


def _read_window(days: int) -> list[dict]:
    today = datetime.now(tz=timezone.utc).date()
    rows: list[dict] = []
    for offset in range(days):
        day = (today - timedelta(days=offset)).strftime("%Y-%m-%d")
        rows.extend(read_outcomes(day))
    return rows


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--window-days", type=int, default=30)
    p.add_argument("--version", default=None)
    args = p.parse_args()

    version = args.version or datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    rows = _read_window(args.window_days)
    snapshot = compute_outcome_drift(rows, version=version, window_days=args.window_days)

    path = publish("drift_signals", version, as_dict(snapshot))
    print(
        f"drift_signals version={version} rows={len(rows)} "
        f"multiplier={snapshot.fraud_rate_multiplier:.2f} fired={snapshot.any_fired} -> {path}"
    )


if __name__ == "__main__":
    main()