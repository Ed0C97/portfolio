"""Pre-allocated GPU tensor pool. Portfolio excerpt, adapted.

cudaMalloc serializes on the driver, so it tanks throughput under load. Allocate
fixed-shape buffers at startup and recycle them, keeping the hot path allocation-free.

Buffers are grouped into named categories by shape and dtype, each backed by an
asyncio.Queue. When a pool runs dry, acquire() allocates fresh and logs a throttled
warning so the under-sizing shows up without flooding the log.
"""

import asyncio
import logging
from dataclasses import dataclass

import torch

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BufferSpec:
    """Shape, dtype, and count for one buffer category."""
    name: str
    shape: tuple[int, ...]
    dtype: torch.dtype
    count: int


class TensorPool:
    """Pool of pre-allocated GPU tensors.

    Usage:
        pool = TensorPool(device="cuda")
        pool.register("embedding", (32, 512, 1024), torch.float16, count=4)
        pool.allocate()

        buf = await pool.acquire("embedding")
        pool.release("embedding", buf)
    """

    def __init__(self, device: str = "cuda"):
        self.device = torch.device(device)
        self._specs: dict[str, BufferSpec] = {}
        self._pools: dict[str, asyncio.Queue] = {}
        self._allocated = False
        self._stats: dict[str, dict] = {}

    def register(
        self,
        name: str,
        shape: tuple[int, ...],
        dtype: torch.dtype = torch.float16,
        count: int = 4,
    ) -> None:
        """Register a buffer category. Call before allocate()."""
        self._specs[name] = BufferSpec(name=name, shape=shape, dtype=dtype, count=count)

    def allocate(self) -> None:
        """Pre-allocate every registered pool. Call once at startup."""
        total_bytes = 0
        for name, spec in self._specs.items():
            queue: asyncio.Queue = asyncio.Queue(maxsize=spec.count)
            for _ in range(spec.count):
                buf = torch.empty(spec.shape, dtype=spec.dtype, device=self.device)
                queue.put_nowait(buf)
                total_bytes += buf.nelement() * buf.element_size()
            self._pools[name] = queue
            self._stats[name] = {"acquired": 0, "released": 0, "fallbacks": 0}

        self._allocated = True
        total_mb = total_bytes / (1024 * 1024)
        logger.info(
            "Tensor pool allocated: %d categories, %.1f MB total",
            len(self._specs), total_mb,
        )

    async def acquire(self, name: str) -> torch.Tensor:
        """Return a pooled buffer, or a fresh allocation if the pool is empty."""
        if name not in self._pools:
            raise KeyError(f"Unknown buffer category: {name}")

        self._stats[name]["acquired"] += 1
        try:
            buf = self._pools[name].get_nowait()
            buf.zero_()
            return buf
        except asyncio.QueueEmpty:
            self._stats[name]["fallbacks"] += 1
            spec = self._specs[name]
            # log every 100th fallback so a chronically under-sized pool surfaces
            if self._stats[name]["fallbacks"] % 100 == 1:
                logger.warning(
                    "Pool '%s' exhausted (%d fallbacks); consider increasing size.",
                    name, self._stats[name]["fallbacks"],
                )
            return torch.empty(spec.shape, dtype=spec.dtype, device=self.device)

    def release(self, name: str, tensor: torch.Tensor) -> None:
        """Return a buffer to the pool. A full pool means this was a fallback, so drop it."""
        if name not in self._pools:
            return
        self._stats[name]["released"] += 1
        try:
            self._pools[name].put_nowait(tensor)
        except asyncio.QueueFull:
            pass

    def get_stats(self) -> dict:
        """Return per-category pool usage statistics."""
        return {
            name: {
                "pool_size": spec.count,
                "available": self._pools[name].qsize() if name in self._pools else 0,
                **self._stats.get(name, {}),
            }
            for name, spec in self._specs.items()
        }
