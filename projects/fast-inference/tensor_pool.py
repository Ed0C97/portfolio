"""Pre-allocated GPU tensor pool. Portfolio excerpt, adapted.

cudaMalloc serializes on the driver, so it tanks throughput under load. Allocate
fixed-shape buffers at startup and recycle them, keeping the hot path allocation-free.

Buffers are grouped into named categories by shape and dtype, each backed by a
deque guarded by a threading.Lock: the server runs model calls on worker threads
(asyncio.to_thread), so an asyncio.Queue would only be safe from the loop thread.
When a pool runs dry, acquire() allocates fresh and logs a throttled warning so
the under-sizing shows up without flooding the log.

In the server this pool backs the torch embedding path, which pads each request
up to one of a few fixed sequence-length buckets. The allocation saving is the
smaller half of the win: collapsing every request onto a handful of shapes keeps
the framework's per-shape planning caches warm instead of re-planning per request.
"""


import logging
import threading
from collections import deque
from dataclasses import dataclass

import torch

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BufferSpec:
    """Specification for a category of GPU buffers."""
    name: str
    shape: tuple[int, ...]
    dtype: torch.dtype
    count: int  # How many buffers to pre-allocate


class TensorPool:
    """Pool of pre-allocated GPU tensors.

    Usage:
        pool = TensorPool(device="cuda")
        pool.register("embedding", (32, 512, 1024), torch.float16, count=4)
        pool.allocate()

        buf = await pool.acquire("embedding")
        # ... use buf for inference ...
        pool.release("embedding", buf)
    """

    def __init__(self, device: str = "cuda"):
        self.device = torch.device(device)
        self._specs: dict[str, BufferSpec] = {}
        self._pools: dict[str, deque] = {}
        self._lock = threading.Lock()
        self._allocated = False
        self._stats: dict[str, dict] = {}

    def register(
        self,
        name: str,
        shape: tuple[int, ...],
        dtype: torch.dtype = torch.float16,
        count: int = 4,
    ) -> None:
        """Register a buffer category.

        Args:
            name: Category name (e.g., "embedding", "attention").
            shape: Max tensor shape for this category.
            dtype: Tensor data type.
            count: Number of buffers to pre-allocate.
        """
        self._specs[name] = BufferSpec(name=name, shape=shape, dtype=dtype, count=count)

    def allocate(self) -> None:
        """Pre-allocate all registered buffer pools.

        Call this once at server startup, after all categories are registered.
        """
        total_bytes = 0

        for name, spec in self._specs.items():
            pool: deque = deque(maxlen=spec.count)
            for _ in range(spec.count):
                buf = torch.empty(spec.shape, dtype=spec.dtype, device=self.device)
                pool.append(buf)
                total_bytes += buf.nelement() * buf.element_size()

            self._pools[name] = pool
            self._stats[name] = {"acquired": 0, "released": 0, "fallbacks": 0}

        self._allocated = True
        total_mb = total_bytes / (1024 * 1024)
        logger.info(
            "Memory pool allocated: %d categories, %.1f MB total",
            len(self._specs), total_mb,
        )

    def acquire(self, name: str) -> torch.Tensor:
        """Acquire a buffer from the pool. Safe to call from any thread.

        A pool miss is not an error: the caller gets a freshly allocated
        buffer of the same spec and the miss is counted, so exhaustion shows
        up in the metrics instead of failing a request.

        Args:
            name: Buffer category name.

        Returns:
            Zeroed tensor of the registered shape (slice it as required).

        Raises:
            KeyError: If the category was never registered.
        """
        if name not in self._pools:
            raise KeyError(f"Unknown buffer category: {name}")

        with self._lock:
            self._stats[name]["acquired"] += 1
            if self._pools[name]:
                buf = self._pools[name].popleft()
                buf.zero_()
                return buf

            self._stats[name]["fallbacks"] += 1
            fallbacks = self._stats[name]["fallbacks"]
            spec = self._specs[name]

        if fallbacks % 100 == 1:
            logger.warning(
                "Pool '%s' exhausted (%d fallbacks). Consider increasing pool size.",
                name, fallbacks,
            )
        return torch.zeros(spec.shape, dtype=spec.dtype, device=self.device)

    def release(self, name: str, tensor: torch.Tensor) -> None:
        """Return a buffer to the pool. Safe to call from any thread.

        Args:
            name: Buffer category name.
            tensor: The tensor to return (must be from this pool).
        """
        if name not in self._pools:
            return

        with self._lock:
            self._stats[name]["released"] += 1
            pool = self._pools[name]
            if len(pool) < (pool.maxlen or 0):
                pool.append(tensor)
            # Otherwise drop it: a fallback-allocated buffer beyond capacity.

    def get_stats(self) -> dict:
        """Return pool usage statistics."""
        return {
            name: {
                "pool_size": spec.count,
                "available": len(self._pools[name]) if name in self._pools else 0,
                **self._stats.get(name, {}),
            }
            for name, spec in self._specs.items()
        }

    def get_memory_usage_mb(self) -> float:
        """Return total pre-allocated memory in MB."""
        total = 0
        for spec in self._specs.values():
            buf_size = 1
            for dim in spec.shape:
                buf_size *= dim
            element_size = torch.tensor([], dtype=spec.dtype).element_size()
            total += buf_size * element_size * spec.count
        return total / (1024 * 1024)
