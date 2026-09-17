from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone

from fincrime_os.decision_engine.cost_loader import load_cost_inputs
from fincrime_os.decision_engine.optimizer import optimize_all
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
    cost = load_cost_inputs()
    rows = _read_window(args.window_days)

    if not rows:
        print("no outcome rows in window; publishing default-only threshold table")
        entries = {"default": [0.40, 0.75]}
    else:
        optimized = optimize_all(rows, cost)
        entries = {k: [float(v[0]), float(v[1])] for k, v in optimized.items()}
        if "default" not in entries:
            entries["default"] = [0.40, 0.75]

    path = publish("threshold_tables", version, {"entries": entries})
    print(f"threshold_tables version={version} segments={list(entries.keys())} -> {path}")


if __name__ == "__main__":
    main()