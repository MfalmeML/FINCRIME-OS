from __future__ import annotations
import hashlib

from fincrime_os.rollout.contracts import SegmentRollout, SignalStage


def _bucket(transaction_id: str) -> float:
    """Deterministic bucket in [0.0, 1.0) for a given transaction id.

    Uses BLAKE2s truncated to 8 bytes so bucketing is stable across processes
    and machines and independent of Python's hash seed.
    """
    digest = hashlib.blake2s(transaction_id.encode("utf-8"), digest_size=8).digest()
    as_int = int.from_bytes(digest, "big", signed=False)
    return (as_int % 10000) / 10000.0


def in_rollout(transaction_id: str, percentage: float) -> bool:
    if percentage >= 1.0:
        return True
    if percentage <= 0.0:
        return False
    return _bucket(transaction_id) < percentage


def effective_stage(
    transaction_id: str,
    rollout: SegmentRollout,
) -> SignalStage:
    """If the transaction is not bucketed into the rollout, downgrade to the
    previous stage. This is the mechanism that lets a segment run at, say, 5%
    full rollout and 95% prior-stage behavior without redeploying."""
    if in_rollout(transaction_id, rollout.percentage):
        return rollout.stage

    order = [
        SignalStage.FULL,
        SignalStage.ADD_TEMPORAL,
        SignalStage.ADD_BEHAVIORAL,
        SignalStage.TRANSACTION_ONLY,
    ]
    idx = order.index(rollout.stage)
    if idx + 1 < len(order):
        return order[idx + 1]
    return SignalStage.TRANSACTION_ONLY