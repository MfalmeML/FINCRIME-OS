from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from time import monotonic


@dataclass
class RuntimeMetrics:
    window_seconds: int = 3600
    _decisions: deque = field(default_factory=lambda: deque(maxlen=100000))
    _graph_degraded: deque = field(default_factory=lambda: deque(maxlen=100000))
    _lock: Lock = field(default_factory=Lock)

    def _prune(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._decisions and self._decisions[0] < cutoff:
            self._decisions.popleft()
        while self._graph_degraded and self._graph_degraded[0] < cutoff:
            self._graph_degraded.popleft()

    def record_decision(self, graph_degraded: bool) -> None:
        now = monotonic()
        with self._lock:
            self._decisions.append(now)
            if graph_degraded:
                self._graph_degraded.append(now)
            self._prune(now)

    def snapshot(self) -> dict:
        now = monotonic()
        with self._lock:
            self._prune(now)
            decisions = len(self._decisions)
            degraded = len(self._graph_degraded)
        rate = (degraded / decisions) if decisions else 0.0
        return {
            "window_seconds": self.window_seconds,
            "decisions": decisions,
            "graph_degraded": degraded,
            "graph_degraded_rate": rate,
        }

    def reset(self) -> None:
        with self._lock:
            self._decisions.clear()
            self._graph_degraded.clear()


_metrics = RuntimeMetrics()


def get_metrics() -> RuntimeMetrics:
    return _metrics