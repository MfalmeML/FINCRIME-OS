from __future__ import annotations
from datetime import datetime


class PointInTimeViolation(Exception):
    pass


def assert_not_future(feature_as_of: datetime, decision_time: datetime) -> None:
    if feature_as_of > decision_time:
        raise PointInTimeViolation(
            f"feature as_of={feature_as_of} is after decision_time={decision_time}"
        )


def assert_labels_are_mature(label_observed_at: datetime, decision_time: datetime) -> None:
    if label_observed_at <= decision_time:
        raise PointInTimeViolation(
            f"label observed at {label_observed_at} is not after decision_time {decision_time}"
        )