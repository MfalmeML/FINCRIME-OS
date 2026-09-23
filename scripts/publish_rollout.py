from __future__ import annotations
import argparse
from datetime import datetime, timezone

from fincrime_os.state.loader import publish


DEFAULT_TABLE = {
    "default_stage": "full",
    "default_percentage": 1.0,
    "segments": {
        "default": {"stage": "full", "percentage": 1.0},
        "vip": {"stage": "add_temporal", "percentage": 0.20},
        "new_account": {"stage": "transaction_only", "percentage": 0.0},
    },
}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--version", default=None)
    p.add_argument("--default-stage", default=None,
                   choices=["transaction_only", "add_behavioral", "add_temporal", "full"])
    p.add_argument("--default-percentage", type=float, default=None)
    args = p.parse_args()

    version = args.version or datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")

    table = dict(DEFAULT_TABLE)
    if args.default_stage is not None:
        table["default_stage"] = args.default_stage
    if args.default_percentage is not None:
        table["default_percentage"] = args.default_percentage

    path = publish("rollout_table", version, table)
    print(f"published rollout_table version={version} -> {path}")
    print(f"  default_stage={table['default_stage']} default_percentage={table['default_percentage']}")
    for k, v in table["segments"].items():
        print(f"  segment={k} stage={v['stage']} percentage={v['percentage']}")


if __name__ == "__main__":
    main()