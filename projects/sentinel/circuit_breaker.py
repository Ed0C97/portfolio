# Portfolio excerpt, adapted. Generic async circuit-breaker pattern; no proprietary logic.
"""Async circuit breaker for external service calls."""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from enum import Enum
from typing import Any

logger = logging.getLogger("circuit_breaker")


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised when a call is rejected because the circuit is open."""

    def __init__(self, service: str, retry_after: float):
        self.service = service
        self.retry_after = retry_after
        super().__init__(f"Circuit open for '{service}'. Retry after {retry_after:.0f}s.")


class CircuitBreaker:
    """Async circuit breaker for external service calls."""

    def __init__(
        self,
        service_name: str,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        half_open_max_calls: int = 1,
        failure_exceptions: tuple[type[BaseException], ...] = (Exception,),
    ):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls
        # which exceptions trip the breaker. transport errors should open it; content
        # or schema errors (e.g. JSON ValueError) should propagate untouched.
        # (Exception,) keeps the old catch-all behavior for callers that don't pass this.
        self.failure_exceptions = failure_exceptions

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0.0
        self._half_open_calls: int = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.reset_timeout:
                return CircuitState.HALF_OPEN
        return self._state

    @property
    def is_available(self) -> bool:
        return self.state != CircuitState.OPEN

    def _record_success(self) -> None:
        self._failure_count = 0
        self._success_count += 1
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            self._half_open_calls = 0
            logger.info("Circuit CLOSED for '%s' (service recovered)", self.service_name)

    def _record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(
                "Circuit OPEN for '%s' (failures=%d, timeout=%ds)",
                self.service_name,
                self._failure_count,
                self.reset_timeout,
            )

    @asynccontextmanager
    async def __call__(self):
        """Guard one call: reject when open, else record success or failure on exit."""
        async with self._lock:
            current_state = self.state

            if current_state == CircuitState.OPEN:
                retry_after = self.reset_timeout - (time.monotonic() - self._last_failure_time)
                raise CircuitOpenError(self.service_name, max(0, retry_after))

            if current_state == CircuitState.HALF_OPEN:
                # the state property derives HALF_OPEN from the clock, but _state is still
                # OPEN. write it back so _record_success sees the transition and can close.
                self._state = CircuitState.HALF_OPEN
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitOpenError(self.service_name, self.reset_timeout / 2)
                self._half_open_calls += 1

        try:
            yield
        except Exception as exc:
            # only failure_exceptions count toward opening; anything else passes through
            # without touching the failure counter
            if isinstance(exc, self.failure_exceptions):
                async with self._lock:
                    self._record_failure()
            raise
        else:
            async with self._lock:
                self._record_success()

    async def __aenter__(self):
        # earlier version dropped the context manager after __aenter__, so __aexit__
        # no-opped: once OPEN the circuit never closed (_half_open_calls never reset)
        # and _record_* never ran. hold the manager and hand off in __aexit__.
        self._active_cm = self()
        return await self._active_cm.__aenter__()

    async def __aexit__(self, exc_type, exc, tb):
        cm = getattr(self, "_active_cm", None)
        self._active_cm = None
        if cm is None:
            return False
        return await cm.__aexit__(exc_type, exc, tb)

    def status(self) -> dict[str, Any]:
        """Return a snapshot of circuit state for health checks."""
        return {
            "service": self.service_name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure": self._last_failure_time,
            "threshold": self.failure_threshold,
            "reset_timeout_s": self.reset_timeout,
        }
