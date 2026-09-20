from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fincrime_os.decision_engine.cost_model import build_inputs, as_dict
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
    inputs = build_inputs(rows, version=version, window_days=args.window_days)

    path = publish("cost_model_inputs", version, as_dict(inputs))
    print(f"cost_model_inputs version={version} rows={len(rows)} -> {path}")
    print(f"  p_false_decline={inputs.p_false_decline:.4f}")
    print(f"  p_churn_given_decline={inputs.p_churn_given_decline:.4f}")
    print(f"  confirmed_fraud_rate={inputs.confirmed_fraud_rate:.4f}")


if __name__ == "__main__":
    main()
