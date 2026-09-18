from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from fincrime_os.api.schemas import QueueResponse, RankedAlertOut
from fincrime_os.investigation.engine import Alert, InvestigationEngine
from fincrime_os.investigation.queue import InvestigatorQueue

router = APIRouter(tags=["investigation"])

_engine = InvestigationEngine()
_queue = InvestigatorQueue(engine=_engine)


def _fixture_alerts() -> list[Alert]:
    return [
        Alert("case_1", 0.96, 40.0, 0.0, 0, "default"),
        Alert("case_2", 0.88, 40000.0, 0.0, 0, "default"),
        Alert("case_3", 0.90, 1000.0, 0.95, 4, "default"),
        Alert("case_4", 0.55, 500.0, 0.0, 0, "default"),
        Alert("case_5", 0.72, 2500.0, 0.0, 0, "default"),
    ]


@router.get("/queue", response_model=QueueResponse)
def queue() -> QueueResponse:
    alerts = _fixture_alerts()
    ranked = _queue.build(alerts)
    workable = _queue.workable_slice(alerts)
    return QueueResponse(
        generated_at=datetime.now(tz=UTC).isoformat(),
        capacity=_engine.investigator_daily_capacity,
        alerts_considered=len(alerts),
        alerts_returned=len(workable),
        ranked=[
            RankedAlertOut(
                case_id=r.case_id,
                expected_loss_prevented=round(r.expected_loss_prevented, 2),
                priority=r.priority,
                rank=r.rank,
            )
            for r in ranked
        ],
    )