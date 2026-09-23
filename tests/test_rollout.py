from fincrime_os.rollout.contracts import (
    RolloutTable,
    SegmentRollout,
    SignalStage,
    stage_allows_behavioral,
    stage_allows_graph,
    stage_allows_temporal,
)
from fincrime_os.rollout.resolver import _bucket, effective_stage, in_rollout


def test_bucket_is_deterministic():
    assert _bucket("tx_1") == _bucket("tx_1")
    assert 0.0 <= _bucket("tx_1") < 1.0


def test_bucket_varies_across_ids():
    buckets = {_bucket(f"tx_{i}") for i in range(500)}
    # Very unlikely to be fewer than 400 distinct buckets out of 500.
    assert len(buckets) > 400


def test_in_rollout_boundaries():
    assert in_rollout("tx_1", 1.0) is True
    assert in_rollout("tx_1", 0.0) is False


def test_effective_stage_downgrades_when_out_of_rollout():
    row = SegmentRollout(segment_key="vip", stage=SignalStage.FULL, percentage=0.0)
    stage = effective_stage("tx_never", row)
    assert stage == SignalStage.ADD_TEMPORAL


def test_effective_stage_keeps_when_in_rollout():
    row = SegmentRollout(segment_key="vip", stage=SignalStage.FULL, percentage=1.0)
    stage = effective_stage("tx_always", row)
    assert stage == SignalStage.FULL


def test_effective_stage_lowest_stays_lowest():
    row = SegmentRollout(
        segment_key="new_account", stage=SignalStage.TRANSACTION_ONLY, percentage=0.0
    )
    assert effective_stage("tx_1", row) == SignalStage.TRANSACTION_ONLY


def test_stage_allows_helpers():
    assert stage_allows_behavioral(SignalStage.TRANSACTION_ONLY) is False
    assert stage_allows_behavioral(SignalStage.ADD_BEHAVIORAL) is True
    assert stage_allows_temporal(SignalStage.ADD_BEHAVIORAL) is False
    assert stage_allows_temporal(SignalStage.ADD_TEMPORAL) is True
    assert stage_allows_graph(SignalStage.ADD_TEMPORAL) is False
    assert stage_allows_graph(SignalStage.FULL) is True


def test_table_default_resolution():
    table = RolloutTable(version="v1")
    row = table.resolve("unknown_segment")
    assert row.stage == SignalStage.FULL
    assert row.percentage == 1.0