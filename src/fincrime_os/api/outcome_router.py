from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException

from fincrime_os.api.schemas import OutcomeAck, OutcomeSubmission
from fincrime_os.config import default_config
from fincrime_os.features.point_in_time import (
    PointInTimeViolation,
    assert_labels_are_mature,
)
from fincrime_os.pipeline.auto_rebuild import auto_rebuild_enabled, get_throttle
from fincrime_os.pipeline.rebuild import rebuild_all
from fincrime_os.state.outcomes import (
    InvestigationOutcome,
    OutcomeRecord,
    append_outcome,
)

log = logging.getLogger("fincrime_os.outcomes")

router = APIRouter(tags=["outcomes"])


def _run_rebuild(window_days: int) -> None:
    try:
        result = rebuild_all(window_days=window_days)
        log.info(
            "auto_rebuild",
            extra={
                "version": result.version,
                "rows": result.rows,
                "published": ",".join(result.published),
            },
        )
    except Exception:
        log.exception("auto_rebuild_failed")


@router.post("/outcome", response_model=OutcomeAck)
def submit_outcome(
    req: OutcomeSubmission,
    background: BackgroundTasks,
) -> OutcomeAck:
    decided_at = datetime.fromisoformat(req.decided_at)
    observed_at = datetime.fromisoformat(req.observed_at)

    try:
        assert_labels_are_mature(observed_at, decided_at)
    except PointInTimeViolation as e:
        raise HTTPException(status_code=422, detail=str(e))

    inv = None
    if req.investigation_outcome is not None:
        inv = InvestigationOutcome(req.investigation_outcome)

    record = OutcomeRecord(
        transaction_id=req.transaction_id,
        account_id=req.account_id,
        decision=req.decision,
        decided_at=decided_at,
        observed_at=observed_at,
        is_fraud=req.is_fraud,
        is_ring_member=req.is_ring_member,
        is_false_decline=req.is_false_decline,
        churned_after_decline=req.churned_after_decline,
        investigation_outcome=inv,
        transaction_amount=req.transaction_amount,
        segment=req.segment,
    )
    path = append_outcome(record)

    cfg = default_config()
    if (
        auto_rebuild_enabled()
        and cfg.auto_rebuild.enabled
        and get_throttle().should_run()
    ):
        background.add_task(_run_rebuild, cfg.auto_rebuild.window_days)

    return OutcomeAck(transaction_id=req.transaction_id, stored_path=str(path))