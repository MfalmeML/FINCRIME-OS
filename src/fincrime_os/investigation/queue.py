from __future__ import annotations
from dataclasses import dataclass

from fincrime_os.investigation.engine import Alert, InvestigationEngine, RankedAlert


@dataclass
class InvestigatorQueue:
    engine: InvestigationEngine

    def build(self, alerts: list[Alert]) -> list[RankedAlert]:
        return self.engine.rank(alerts)

    def workable_slice(self, alerts: list[Alert]) -> list[RankedAlert]:
        ranked = self.rank_if_capacity(alerts)
        return ranked[: self.engine.investigator_daily_capacity]

    def rank_if_capacity(self, alerts: list[Alert]) -> list[RankedAlert]:
        return self.engine.rank(alerts)