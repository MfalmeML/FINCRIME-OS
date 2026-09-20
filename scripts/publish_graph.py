from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import argparse
from datetime import datetime, timezone

from fincrime_os.state.loader import publish


DEFAULT_SNAPSHOT = {
    "ring_scores": {
        "cust_1": 0.97,
        "cust_2": 0.42,
        "cust_3": 0.10,
    },
    "confirmed_members": {
        "cust_1": 4,
        "cust_2": 1,
        "cust_3": 0,
    },
    "connected_accounts": {
        "cust_1": 14,
        "cust_2": 3,
        "cust_3": 1,
    },
    "confirmed_fraud_neighbors": {
        "cust_1": 4,
        "cust_2": 0,
        "cust_3": 0,
    },
}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--version", default=None)
    args = p.parse_args()
    version = args.version or datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    path = publish("graph_snapshots", version, DEFAULT_SNAPSHOT)
    print(f"published graph_snapshots version={version} -> {path}")


if __name__ == "__main__":
    main()
