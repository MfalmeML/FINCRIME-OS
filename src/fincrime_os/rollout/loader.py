from __future__ import annotations
from fincrime_os.rollout.contracts import RolloutTable, SegmentRollout, SignalStage
from fincrime_os.state.loader import load_latest


DEFAULT = RolloutTable(
    version="unversioned-dev",
    default_stage=SignalStage.FULL,
    default_percentage=1.0,
    segments={},
)


def load_rollout() -> RolloutTable:
    artifact = load_latest("rollout_table")
    if artifact is None:
        return DEFAULT
    p = artifact.payload
    segments: dict[str, SegmentRollout] = {}
    for key, entry in (p.get("segments") or {}).items():
        try:
            stage = SignalStage(entry.get("stage", "full"))
        except ValueError:
            stage = SignalStage.FULL
        segments[key] = SegmentRollout(
            segment_key=key,
            stage=stage,
            percentage=float(entry.get("percentage", 1.0)),
        )
    try:
        default_stage = SignalStage(p.get("default_stage", "full"))
    except ValueError:
        default_stage = SignalStage.FULL
    return RolloutTable(
        version=artifact.version,
        default_stage=default_stage,
        default_percentage=float(p.get("default_percentage", 1.0)),
        segments=segments,
    )