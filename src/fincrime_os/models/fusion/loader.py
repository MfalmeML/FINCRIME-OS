from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

import joblib

from fincrime_os.state.loader import STATE_ROOT


@dataclass(frozen=True)
class LoadedFusionModel:
    version: str
    model: object
    feature_names: list[str]
    path: Path


def _latest_model_file() -> Path | None:
    d = STATE_ROOT / "models" / "fusion"
    if not d.exists():
        return None
    files = sorted(
        [p for p in d.glob("*.joblib") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None


def load_fusion_model() -> LoadedFusionModel | None:
    path = _latest_model_file()
    if path is None:
        return None
    bundle = joblib.load(path)
    return LoadedFusionModel(
        version=bundle.get("version", path.stem),
        model=bundle["model"],
        feature_names=bundle.get("feature_names", []),
        path=path,
    )