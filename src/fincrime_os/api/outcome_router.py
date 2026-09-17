from __future__ import annotations
from datetime import datetime

from fastapi import APIRouter, HTTPException

from fincrime_os.api.schemas import OutcomeAck, OutcomeSubmission
from fincrime_os.features.point_in_time import (
    PointInTimeViolation,
    assert_labels_are_mature,
)
from fincrime_os.state.outcomes import (
    InvestigationOutcome,
    OutcomeRecord,
    append_outcome,
)

router = APIRouter(tags=["outcomes"])


@router.post("/outcome", response_model=OutcomeAck)
def submit_outcome(req: OutcomeSubmission) -> OutcomeAck:
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
    )
    path = append_outcome(record)
    return OutcomeAck(transaction_id=req.transaction_id, stored_path=str(path))
