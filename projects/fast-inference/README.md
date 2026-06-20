# fast-inference — code samples

Three self-contained excerpts from the serving and resilience layers of a self-hosted, OpenAI-compatible inference server. They show async/await fluency, GPU hot-path optimization, and failure-handling design without exposing any kernel internals or model logic.

**Context:** see [../fast-inference.md](../fast-inference.md) for the full project overview.

**Stack:** Python (≥ 3.10), asyncio, PyTorch (CUDA), httpx.

## What each file shows

- **`dynamic_batcher.py`** — an async dynamic batching engine. Individual requests arrive on an `asyncio.Queue`; a background coroutine drains them on a time/size trigger (`max_batch_size` OR `max_wait_ms`, whichever fires first), runs a single batched call, and fans results back to each request's `asyncio.Future`. Includes per-request wait-time stats, exception propagation to every waiting caller, and clean start/stop/drain lifecycle.
- **`tensor_pool.py`** — a pre-allocated GPU tensor pool that recycles fixed-shape buffers to keep `cudaMalloc` off the hot path. Registers buffer categories by shape/dtype, pre-allocates at startup, and offers async `acquire`/`release` with graceful fallback to dynamic allocation (and throttled warnings) when exhausted, plus usage accounting.
- **`circuit_breaker.py`** — a three-state circuit breaker (CLOSED / OPEN / HALF_OPEN) with periodic async health checks. Trips after a failure threshold, rejects traffic while OPEN, probes a single request after a cooldown, and closes again on recovery — the standard resilience pattern, implemented cleanly over `httpx`.

## Deliberately omitted

- The hand-written **Triton GPU kernels** (attention, normalization, activations) — the performance-sensitive core, kept private.
- The **INT8 quantization / ONNX export** pipeline and any model wrappers (embedder, reranker, generator).
- The **router** that composes these pieces (worker selection, request forwarding) and the FastAPI request/response surface.
- All tuning constants shown here (batch size, wait window, weights, timeouts) are illustrative defaults, not tuned production values.

_© 2026 Edoardo Caciolo — all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
