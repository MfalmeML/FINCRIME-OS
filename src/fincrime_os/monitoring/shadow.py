from __future__ import annotations
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

log = logging.getLogger("fincrime_os.shadow")

SHADOW_ROOT = Path("state") / "shadow"


@dataclass(frozen=True)
class ShadowRecord:
    transaction_id: str
    observed_at: str
    live_decision: str
    shadow_decision: str
    live_reason: str
    shadow_reason: str
    live_combined_risk: float
    shadow_combined_risk: float
    divergence: bool


_lock = Lock()


def _path_for(observed_at: datetime) -> Path:
    day = observed_at.strftime("%Y-%m-%d")
    return SHADOW_ROOT / f"{day}.jsonl"


def record(record: ShadowRecord) -> Path | None:
    SHADOW_ROOT.mkdir(parents=True, exist_ok=True)
    path = _path_for(datetime.now(tz=timezone.utc))
    with _lock:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record), sort_keys=True) + "\n")
    log.info(
        "shadow_record",
        extra={
            "transaction_id": record.transaction_id,
            "live": record.live_decision,
            "shadow": record.shadow_decision,
            "divergence": record.divergence,
        },
    )
    return path


def read_day(day: str) -> list[dict]:
    path = SHADOW_ROOT / f"{day}.jsonl"
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out