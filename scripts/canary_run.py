from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from fincrime_os.drift.canary import (
    CanaryGate,
    CanaryOutcome,
    VersionRegistry,
    apply_gate,
)
from fincrime_os.state.loader import load_latest, publish


def _load_json_arg(raw: str | None, path: Path | None) -> dict | None:
    if raw:
        return json.loads(raw)
    if path and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def _next_version(prefix: str) -> str:
    stamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    return f"{prefix}-{stamp}"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--component", required=True,
                   help="e.g. fusion_model, transaction_model, threshold_tables")
    p.add_argument("--kind", required=True,
                   help="artifact kind to publish on PROMOTE: model_versions or threshold_tables")
    p.add_argument("--candidate-fraud-loss", type=float, required=True)
    p.add_argument("--baseline-fraud-loss", type=float, required=True)
    p.add_argument("--fraud-loss-ceiling", type=float, default=0.02)
    p.add_argument("--candidate-version", default=None)
    p.add_argument("--candidate-payload-json", default=None)
    p.add_argument("--candidate-payload-path", default=None)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    baseline_artifact = load_latest(args.kind)
    baseline_version = baseline_artifact.version if baseline_artifact else "unversioned-dev"

    candidate_version = args.candidate_version or _next_version(args.component)
    payload = _load_json_arg(
        args.candidate_payload_json,
        Path(args.candidate_payload_path) if args.candidate_payload_path else None,
    )

    gate = CanaryGate(fraud_loss_ceiling=args.fraud_loss_ceiling)
    registry = VersionRegistry(serving={args.component: baseline_version})

    outcome = CanaryOutcome(
        candidate_version=candidate_version,
        baseline_version=baseline_version,
        candidate_fraud_loss=args.candidate_fraud_loss,
        baseline_fraud_loss=args.baseline_fraud_loss,
        fraud_loss_ceiling=args.fraud_loss_ceiling,
    )
    result = apply_gate(gate, registry, args.component, outcome)

    print(f"component={args.component}")
    print(f"baseline_version={baseline_version}")
    print(f"candidate_version={candidate_version}")
    print(f"candidate_fraud_loss={args.candidate_fraud_loss}")
    print(f"baseline_fraud_loss={args.baseline_fraud_loss}")
    print(f"fraud_loss_ceiling={args.fraud_loss_ceiling}")
    print(f"gate_result={result}")

    if result != "PROMOTE":
        print("no artifact published; previous version remains serving")
        return

    if args.dry_run:
        print("dry-run: skipping publish")
        return

    if payload is None:
        print("PROMOTE requires --candidate-payload-json or --candidate-payload-path")
        raise SystemExit(2)

    if args.kind == "model_versions":
        existing = (baseline_artifact.payload.get("models") if baseline_artifact else {}) or {}
        merged = dict(existing)
        merged[args.component] = candidate_version
        publish("model_versions", candidate_version, {"models": merged})
        print(f"published model_versions={candidate_version} with {args.component}->{candidate_version}")
    elif args.kind == "threshold_tables":
        publish("threshold_tables", candidate_version, {"entries": payload["entries"]})
        print(f"published threshold_tables={candidate_version}")
    else:
        publish(args.kind, candidate_version, payload)
        print(f"published {args.kind}={candidate_version}")


if __name__ == "__main__":
    main()