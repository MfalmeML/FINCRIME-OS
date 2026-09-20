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
    trained: dict[str, bool] = field(default_factory=dict)

    def as_dict(self) -> dict[str, str]:
        return dict(self.models)

    def get(self, component: str) -> str:
        return self.models.get(component, "unknown")

    def is_trained(self, component: str) -> bool:
        return bool(self.trained.get(component, False))


def load_registry() -> ModelRegistry:
    artifact = load_latest("model_versions")
    if artifact is None:
        return ModelRegistry(version="unversioned-dev")
    p = artifact.payload
    models = p.get("models") or dict(DEFAULT_MODELS)
    trained = p.get("trained") or {}
    return ModelRegistry(
        version=artifact.version,
        models=dict(models),
        trained={k: bool(v) for k, v in trained.items()},
    )