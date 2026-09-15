from __future__ import annotations

from dataclasses import dataclass

from fincrime_os.features.contracts import BehavioralBaseline, TransactionFeatures


@dataclass
class BehavioralModel:
    version: str = "behav-dev"

    def predict(
        self, features: TransactionFeatures, baseline: BehavioralBaseline
    ) -> float:
        return 0.0