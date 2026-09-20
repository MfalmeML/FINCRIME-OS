from __future__ import annotations
import argparse
from datetime import datetime, timezone

from fincrime_os.state.loader import publish
from fincrime_os.state.model_discovery import COMPONENTS, discover_all


FALLBACK_VERSIONS = {
    "transaction_model": "txn-dev",
    "behavioral_model": "behav-dev",
    "temporal_model": "seq-dev",
    "graph_model": "graph-dev",
    "fusion_model": "fusion-dev",
}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--version", default=None,
                   help="registry artifact version; defaults to UTC timestamp")
    args = p.parse_args()

    registry_version = args.version or datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")

    discovered = discover_all()
    models: dict[str, str] = {}
    trained_flag: dict[str, bool] = {}

    for component in COMPONENTS:
        d = discovered[component]
        if d.trained and d.version:
            models[component] = d.version
            trained_flag[component] = True
        else:
            models[component] = FALLBACK_VERSIONS[component]
            trained_flag[component] = False

    payload = {
        "models": models,
        "trained": trained_flag,
        "discovered_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    path = publish("model_versions", registry_version, payload)

    print(f"published model_versions version={registry_version} -> {path}")
    for component, version in models.items():
        marker = "trained" if trained_flag[component] else "fallback"
        print(f"  {component}={version} ({marker})")


if __name__ == "__main__":
    main()