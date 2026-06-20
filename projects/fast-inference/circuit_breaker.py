"""Health checker + circuit breaker for backend workers. Portfolio excerpt, adapted.

Once a worker starts failing, fail fast instead of queuing requests behind it
and dragging down latency for everyone else.

States:
  CLOSED:    requests flow normally
  OPEN:      reject immediately, no request reaches the worker
  HALF_OPEN: after recovery_timeout, let one probe through to test recovery

Transitions:
  CLOSED -> OPEN      consecutive failures hit failure_threshold
  OPEN -> HALF_OPEN   recovery_timeout elapsed
  HALF_OPEN -> CLOSED probe succeeded
  HALF_OPEN -> OPEN   probe failed
"""

import asyncio
import enum
import logging
import time

import httpx

logger = logging.getLogger(__name__)


class CircuitState(enum.Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class HealthChecker:
    """Poll a worker's health endpoint and drive its circuit state.

    recovery_timeout_s is the cooldown before an open circuit lets a probe
    through; failure_threshold is the consecutive-failure count that opens it.
    """

    def __init__(
        self,
        worker_url: str,
        health_path: str = "/health",
        check_interval_s: float = 2.0,
        failure_threshold: int = 3,
        recovery_timeout_s: float = 10.0,
        request_timeout_s: float = 2.0,
    ):
        self.worker_url = worker_url.rstrip("/")
        self.health_path = health_path
        self.check_interval_s = check_interval_s
        self.failure_threshold = failure_threshold
        self.recovery_timeout_s = recovery_timeout_s
        self.request_timeout_s = request_timeout_s

        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.last_failure_time = 0.0
        self.last_latency_ms = 0.0

        self._running = False
        self._task: asyncio.Task | None = None
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        """Open the HTTP client and kick off the background check loop."""
        self._client = httpx.AsyncClient(timeout=self.request_timeout_s)
        self._running = True
        self._task = asyncio.create_task(self._check_loop())
        logger.info("Health checker started for %s", self.worker_url)

    async def stop(self) -> None:
        """Cancel the check loop and close the HTTP client."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._client:
            await self._client.aclose()

    @property
    def is_healthy(self) -> bool:
        """Return whether the worker should receive requests right now.

        Has a side effect: flips OPEN to HALF_OPEN once recovery_timeout has
        elapsed, so the next caller is the recovery probe.
        """
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.HALF_OPEN:
            return True
        if time.time() - self.last_failure_time >= self.recovery_timeout_s:
            self.state = CircuitState.HALF_OPEN
            return True
        return False

    def record_success(self) -> None:
        """Reset the failure count; a success while HALF_OPEN closes the circuit."""
        if self.state == CircuitState.HALF_OPEN:
            logger.info("Worker %s recovered; closing circuit", self.worker_url)
            self.state = CircuitState.CLOSED
        self.consecutive_failures = 0

    def record_failure(self) -> None:
        """Count a failure and open the circuit once the threshold is hit."""
        self.consecutive_failures += 1
        self.last_failure_time = time.time()
        if self.consecutive_failures >= self.failure_threshold:
            # log the transition once, not on every failure past the threshold
            if self.state != CircuitState.OPEN:
                logger.warning(
                    "Worker %s circuit OPEN after %d failures",
                    self.worker_url, self.consecutive_failures,
                )
            self.state = CircuitState.OPEN

    async def _check_loop(self) -> None:
        while self._running:
            await self._do_check()
            await asyncio.sleep(self.check_interval_s)

    async def _do_check(self) -> None:
        """Hit the health endpoint and record the result. Non-200 counts as a failure."""
        url = f"{self.worker_url}{self.health_path}"
        start = time.perf_counter()
        try:
            response = await self._client.get(url)
            self.last_latency_ms = (time.perf_counter() - start) * 1000
            if response.status_code == 200:
                self.record_success()
            else:
                logger.warning("Health check %s returned %d", url, response.status_code)
                self.record_failure()
        except (httpx.RequestError, httpx.TimeoutException) as e:
            # connect error or timeout: still record the elapsed time for the latency metric
            self.last_latency_ms = (time.perf_counter() - start) * 1000
            logger.warning("Health check %s failed: %s", url, e)
            self.record_failure()

    def get_status(self) -> dict:
        """Return a snapshot of circuit state for metrics/health reporting."""
        return {
            "worker_url": self.worker_url,
            "state": self.state.value,
            "consecutive_failures": self.consecutive_failures,
            "last_latency_ms": round(self.last_latency_ms, 1),
            "is_healthy": self.is_healthy,
        }
