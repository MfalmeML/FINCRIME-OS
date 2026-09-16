from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

STATE_ROOT = Path(__file__).resolve().parents[3] / "state"


@dataclass(frozen=True)
class Artifact:
    kind: str
    version: str
    payload: dict
    path: Path


def _latest_file(kind_dir: Path) -> Path | None:
    if not kind_dir.exists():
        return None
    candidates = sorted(
        [p for p in kind_dir.glob("*.json") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def load_latest(kind: str) -> Artifact | None:
    kind_dir = STATE_ROOT / kind
    path = _latest_file(kind_dir)
    if path is None:
        return None
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    version = payload.get("version", path.stem)
    return Artifact(kind=kind, version=version, payload=payload, path=path)


def load_version(kind: str, version: str) -> Artifact | None:
    kind_dir = STATE_ROOT / kind
    path = kind_dir / f"{version}.json"
    if not path.exists():
        return None
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return Artifact(kind=kind, version=version, payload=payload, path=path)


def publish(kind: str, version: str, payload: dict) -> Path:
    kind_dir = STATE_ROOT / kind
    kind_dir.mkdir(parents=True, exist_ok=True)
    path = kind_dir / f"{version}.json"
    body = {"version": version, **payload}
    path.write_text(json.dumps(body, indent=2, sort_keys=True), encoding="utf-8")
    return path
