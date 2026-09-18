from __future__ import annotations
import os
from dataclasses import dataclass, field
from threading import Lock
from time import monotonic


AUTO_REBUILD_ENV = "FINCRIME_AUTO_REBUILD"


def auto_rebuild_enabled() -> bool:
    return os.environ.get(AUTO_REBUILD_ENV, "1") != "0"


@dataclass
class AutoRebuildThrottle:
    min_interval_seconds: float = 30.0
    _last_run: float = 0.0
    _lock: Lock = field(default_factory=Lock)

    def should_run(self) -> bool:
        now = monotonic()
        with self._lock:
            if now - self._last_run < self.min_interval_seconds:
                return False
            self._last_run = now
            return True

    def reset(self) -> None:
        with self._lock:
            self._last_run = 0.0


_throttle = AutoRebuildThrottle()


def get_throttle() -> AutoRebuildThrottle:
    return _throttle