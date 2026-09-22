from __future__ import annotations

from dataclasses import dataclass, field

from fincrime_os.state.loader import load_latest


@dataclass(frozen=True)
class GraphOverrideConfig:
    ring_score_cutoff: float = 0.90
    min_confirmed_members: int = 2


@dataclass(frozen=True)
class GraphFreshnessConfig:
    max_snapshot_age_seconds: int = 3600


@dataclass(frozen=True)
class AutoRebuildConfig:
    enabled: bool = True
    window_days: int = 30
    min_interval_seconds: float = 30.0


@dataclass(frozen=True)
class ShadowConfig:
    enabled: bool = False
    log_decisions: bool = True


@dataclass(frozen=True)
class DriftConfig:
    feature_threshold: float = 0.20
    prediction_threshold: float = 0.20
    graph_threshold: float = 0.25
    fraud_rate_threshold: float = 3.0


@dataclass(frozen=True)
class ThresholdTable:
    version: str
    entries: dict[str, tuple[float, float]] = field(
        default_factory=lambda: {"default": (0.40, 0.75)}
    )

    def lookup(self, segment_key: str) -> tuple[float, float]:
        return self.entries.get(segment_key, self.entries["default"])


@dataclass(frozen=True)
class PlatformConfig:
    graph_override: GraphOverrideConfig = GraphOverrideConfig()
    graph_freshness: GraphFreshnessConfig = GraphFreshnessConfig()
    auto_rebuild: AutoRebuildConfig = AutoRebuildConfig()
    shadow: ShadowConfig = ShadowConfig()
    drift: DriftConfig = DriftConfig()
    threshold_table: ThresholdTable = ThresholdTable(version="unversioned-dev")
    latency_budget_ms: int = 100


def _threshold_table_from_artifact() -> ThresholdTable:
    artifact = load_latest("threshold_tables")
    if artifact is None:
        return ThresholdTable(version="unversioned-dev")
    entries = {
        k: (float(v[0]), float(v[1]))
        for k, v in artifact.payload.get("entries", {}).items()
    }
    if "default" not in entries:
        entries["default"] = (0.40, 0.75)
    return ThresholdTable(version=artifact.version, entries=entries)


def default_config() -> PlatformConfig:
    return PlatformConfig(threshold_table=_threshold_table_from_artifact())