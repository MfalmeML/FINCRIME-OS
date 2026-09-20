from __future__ import annotations

from dataclasses import dataclass

from fincrime_os.features.contracts import TransactionFeatures


@dataclass
class TransactionModel:
    version: str = "txn-dev"

    @property
    def is_trained(self) -> bool:
        return False

    def predict(self, features: TransactionFeatures) -> float:
        return 0.0
