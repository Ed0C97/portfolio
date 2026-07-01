"""Async dynamic batching engine. Portfolio excerpt, adapted.

Batch requests that arrive close together into one GPU call: throughput wins
because per-batch overhead is fixed, latency stays bounded by max_wait_ms.
A background coroutine drains the queue once it hits max_batch_size or the
wait window expires, then resolves each caller's future.
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class BatchRequest:
    """One queued request and the future its caller is awaiting.

    The future is created in submit() on the running loop, not here: a future must
    belong to the loop that awaits it, and asyncio.get_event_loop() with no running
    loop is deprecated and would bind to the wrong loop.
    """
    data: dict  # payload shape varies by endpoint
    future: asyncio.Future = field(init=False)
    enqueue_time: float = field(default_factory=time.perf_counter)


@dataclass
class BatchStats:
    total_requests: int = 0
    total_batches: int = 0
    total_wait_ms: float = 0.0
    max_wait_ms_observed: float = 0.0
    batch_sizes: list[int] = field(default_factory=list)

    @property
    def avg_batch_size(self) -> float:
        return sum(self.batch_sizes) / max(len(self.batch_sizes), 1)

    @property
    def avg_wait_ms(self) -> float:
        return self.total_wait_ms / max(self.total_requests, 1)


class DynamicBatcher:
    """Collect requests and dispatch them as a single batch."""

    def __init__(
        self,
        process_fn: Callable,
        max_batch_size: int = 32,
        max_wait_ms: float = 10.0,
        name: str = "default",
    ):
        """Wire up the batcher.

        process_fn must return one result per input dict, in the same order;
        the loop relies on positional alignment to resolve futures.
        """
        self.process_fn = process_fn
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self.name = name

        self._queue: asyncio.Queue[BatchRequest] = asyncio.Queue()
        self._running = False
        self._task: asyncio.Task | None = None
        self.stats = BatchStats()

    async def start(self) -> None:
        """Start the background dispatcher; no-op if already running."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._dispatch_loop())
        logger.info(
            "Batcher '%s' started: max_batch=%d, max_wait=%.1fms",
            self.name, self.max_batch_size, self.max_wait_ms,
        )

    async def stop(self) -> None:
        """Cancel the loop and flush anything still queued."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._drain_queue()

    async def submit(self, data: dict) -> object:
        """Queue a request and await its batched result."""
        request = BatchRequest(data=data)
        # Bind the future to the loop actually awaiting it (the one running submit),
        # so _process_batch can resolve it from the dispatcher task on the same loop.
        request.future = asyncio.get_running_loop().create_future()
        await self._queue.put(request)
        return await request.future

    async def _dispatch_loop(self) -> None:
        """Form and dispatch batches until stop() is called."""
        while self._running:
            batch: list[BatchRequest] = []

            try:
                # short timeout so the loop can notice _running flipping
                first = await asyncio.wait_for(self._queue.get(), timeout=0.1)
                batch.append(first)
            except (asyncio.TimeoutError, TimeoutError):
                continue

            # keep pulling until the batch fills or the wait window closes
            deadline = time.perf_counter() + self.max_wait_ms / 1000.0
            while len(batch) < self.max_batch_size:
                remaining = deadline - time.perf_counter()
                if remaining <= 0:
                    break
                try:
                    req = await asyncio.wait_for(self._queue.get(), timeout=remaining)
                    batch.append(req)
                except (asyncio.TimeoutError, TimeoutError):
                    break

            await self._process_batch(batch)

    async def _process_batch(self, batch: list[BatchRequest]) -> None:
        """Run process_fn over the batch and settle every future."""
        if not batch:
            return

        now = time.perf_counter()
        batch_data = [req.data for req in batch]

        self.stats.total_batches += 1
        self.stats.total_requests += len(batch)
        self.stats.batch_sizes.append(len(batch))
        for req in batch:
            wait_ms = (now - req.enqueue_time) * 1000
            self.stats.total_wait_ms += wait_ms
            self.stats.max_wait_ms_observed = max(
                self.stats.max_wait_ms_observed, wait_ms,
            )

        try:
            results = await self.process_fn(batch_data)
            if len(results) != len(batch):
                raise ValueError(
                    f"process_fn returned {len(results)} results for "
                    f"{len(batch)} requests"
                )
            for req, result in zip(batch, results):
                if not req.future.done():
                    req.future.set_result(result)
        except Exception as e:
            # one bad batch must not hang every caller waiting on it
            logger.error("Batch processing failed: %s", e)
            for req in batch:
                if not req.future.done():
                    req.future.set_exception(e)

    async def _drain_queue(self) -> None:
        """Process whatever is left in the queue on shutdown."""
        batch: list[BatchRequest] = []
        while not self._queue.empty():
            try:
                batch.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        if batch:
            await self._process_batch(batch)

    def get_stats(self) -> dict:
        """Return a snapshot of the running counters."""
        return {
            "name": self.name,
            "total_requests": self.stats.total_requests,
            "total_batches": self.stats.total_batches,
            "avg_batch_size": round(self.stats.avg_batch_size, 1),
            "avg_wait_ms": round(self.stats.avg_wait_ms, 2),
            "max_wait_ms_observed": round(self.stats.max_wait_ms_observed, 2),
            "queue_depth": self._queue.qsize(),
        }
