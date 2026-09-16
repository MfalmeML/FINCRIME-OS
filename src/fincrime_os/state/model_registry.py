from __future__ import annotations
from dataclasses import dataclass, field

from fincrime_os.state.loader import load_latest


DEFAULT_MODELS: dict[str, str] = {
    "transaction_model": "txn-dev",
    "behavioral_model": "behav-dev",
    "temporal_model": "seq-dev",
    "graph_model": "graph-dev",
    "fusion_model": "fusion-dev",
}


@dataclass(frozen=True)
class ModelRegistry:
    version: str
    models: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_MODELS))

    def as_dict(self) -> dict[str, str]:
        return dict(self.models)

    def get(self, component: str) -> str:
        return self.models.get(component, "unknown")


def load_registry() -> ModelRegistry:
    artifact = load_latest("model_versions")
    if artifact is None:
        return ModelRegistry(version="unversioned-dev")
    models = artifact.payload.get("models") or dict(DEFAULT_MODELS)
    return ModelRegistry(version=artifact.version, models=dict(models))