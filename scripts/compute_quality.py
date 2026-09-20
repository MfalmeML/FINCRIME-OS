from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import argparse
from datetime import datetime, timedelta, timezone

from fincrime_os.monitoring.quality import as_dict, build_report
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
    report = build_report(rows, version=version, window_days=args.window_days)

    path = publish("quality_metrics", version, as_dict(report))
    print(
        f"quality_metrics version={version} rows={len(rows)} "
        f"miss_rate={report.overall_miss_rate:.4f} "
        f"false_decline_rate={report.overall_false_decline_rate:.4f} -> {path}"
    )
    for k, s in report.segments.items():
        print(
            f"  segment={k} n={s.total_outcomes} "
            f"miss={s.detection_miss_rate:.3f} fp={s.false_decline_rate:.3f} "
            f"churn={s.churn_rate:.3f}"
        )


if __name__ == "__main__":
    main()
