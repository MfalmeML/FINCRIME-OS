from __future__ import annotations

from dataclasses import dataclass

from fincrime_os.features.contracts import EventSequence


@dataclass
class TemporalModel:
    version: str = "seq-dev"

    def predict(self, sequence: EventSequence) -> float:
        return 0.0