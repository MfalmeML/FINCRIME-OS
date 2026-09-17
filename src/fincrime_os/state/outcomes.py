from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Literal, Optional
import json

OUTCOMES_ROOT = Path(__file__).resolve().parents[3] / "state" / "outcomes"


class InvestigationOutcome(str, Enum):
    CONFIRMED_FRAUD = "confirmed_fraud"
    FALSE_POSITIVE = "false_positive"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class OutcomeRecord:
    transaction_id: str
    account_id: str
    decision: str
    decided_at: datetime
    observed_at: datetime
    is_fraud: Optional[bool] = None
    is_ring_member: Optional[bool] = None
    is_false_decline: Optional[bool] = None
    churned_after_decline: Optional[bool] = None
    investigation_outcome: Optional[InvestigationOutcome] = None
    transaction_amount: float | None = None
    segment: dict | None = None

    def to_json(self) -> str:
        d = asdict(self)
        d["decided_at"] = self.decided_at.isoformat()
        d["observed_at"] = self.observed_at.isoformat()
        if self.investigation_outcome is not None:
            d["investigation_outcome"] = self.investigation_outcome.value
        return json.dumps(d, sort_keys=True)


def append_outcome(record: OutcomeRecord) -> Path:
    OUTCOMES_ROOT.mkdir(parents=True, exist_ok=True)
    day = record.observed_at.strftime("%Y-%m-%d")
    path = OUTCOMES_ROOT / f"{day}.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(record.to_json() + "\n")
    return path


def read_outcomes(day: str) -> list[dict]:
    path = OUTCOMES_ROOT / f"{day}.jsonl"
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out