from __future__ import annotations
import argparse
from datetime import datetime, timezone

from fincrime_os.state.loader import publish


DEFAULT_MODELS = {
    "transaction_model": "txn-dev",
    "behavioral_model": "behav-dev",
    "temporal_model": "seq-dev",
    "graph_model": "graph-dev",
    "fusion_model": "fusion-dev",
}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--version", default=None)
    args = p.parse_args()
    version = args.version or datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    path = publish("model_versions", version, {"models": DEFAULT_MODELS})
    print(f"published model_versions version={version} -> {path}")


if __name__ == "__main__":
    main()