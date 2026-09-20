from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib

import fincrime_os.state.loader as loader


COMPONENTS = {
    "transaction_model": "transaction",
    "behavioral_model": "behavioral",
    "temporal_model": "temporal",
    "fusion_model": "fusion",
    "graph_model": "graph",
}


@dataclass(frozen=True)
class DiscoveredModel:
    component: str
    version: str | None
    path: Path | None
    trained: bool


def _latest_in(subdir: str) -> Path | None:
    d = loader.STATE_ROOT / "models" / subdir
    if not d.exists():
        return None
    files = sorted(
        [p for p in d.glob("*.joblib") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None


def _version_from(path: Path) -> str:
    try:
        bundle = joblib.load(path)
        v = bundle.get("version")
        if isinstance(v, str) and v:
            return v
    except Exception:
        pass
    return path.stem


def discover(component: str) -> DiscoveredModel:
    subdir = COMPONENTS.get(component)
    if subdir is None:
        return DiscoveredModel(component=component, version=None, path=None, trained=False)
    path = _latest_in(subdir)
    if path is None:
        return DiscoveredModel(component=component, version=None, path=None, trained=False)
    return DiscoveredModel(
        component=component,
        version=_version_from(path),
        path=path,
        trained=True,
    )


def discover_all() -> dict[str, DiscoveredModel]:
    return {c: discover(c) for c in COMPONENTS}
