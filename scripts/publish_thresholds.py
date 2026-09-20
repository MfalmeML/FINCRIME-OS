from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import argparse
from datetime import datetime, timezone

from fincrime_os.state.loader import publish


DEFAULT_TABLE = {
    "default": [0.40, 0.75],
    "vip": [0.55, 0.85],
    "new_account": [0.30, 0.60],
    "thin_file": [0.30, 0.65],
}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--version", default=None)
    args = p.parse_args()
    version = args.version or datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    path = publish("threshold_tables", version, {"entries": DEFAULT_TABLE})
    print(f"published threshold_tables version={version} -> {path}")


if __name__ == "__main__":
    main()
