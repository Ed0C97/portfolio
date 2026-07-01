# fast-inference

> A self-hosted, OpenAI-compatible inference server for embedding, reranking, and generation models, built to keep retrieval-augmented generation (RAG) workloads fast and fully on-premise.

## Overview

fast-inference serves embedding, reranking, and text-generation models behind a single HTTP API that mirrors the widely used OpenAI and Cohere request/response schemas, so existing RAG clients can point at it with no code changes. It targets teams that want to run RAG locally instead of depending on a cloud provider: by keeping models on the machine, it removes network round-trips and keeps processed data in-house. The project pairs the serving layer with low-level GPU optimization and a benchmark suite, demonstrating the full inference-serving stack end to end.

## Highlights

- **Drop-in OpenAI/Cohere-compatible API**: embeddings, chat completions with streaming, and reranking endpoints, plus health and metrics, validated against the public schemas so existing clients integrate without changes.
- **GPU-level performance engineering**: custom fused GPU kernels and memory-aware execution reduce HBM traffic for the small-batch, memory-bound regime typical of RAG, cutting latency without sacrificing accuracy on precision-sensitive operations.
- **Low-precision quantization**: an INT8 quantization path shrinks model footprint and speeds inference while protecting numerically sensitive layers, delivering smaller, faster models with controlled quality impact.
- **High-throughput request handling**: asynchronous dynamic batching coalesces concurrent requests into efficient GPU batches and recycles pre-allocated GPU memory off the hot path, sustaining throughput under concurrent load.
- **Distributed, fault-tolerant serving**: a health-aware load balancer routes traffic to the best-performing healthy worker and fails fast when capacity is unavailable, keeping the service responsive under partial outages.
- **Multiple model classes**: wraps embedding, cross-encoder reranking, and instruction-tuned generation models behind one consistent interface, with streaming and standard sampling controls for generation.
- **Built-in benchmarking**: a profiling suite measures throughput, latency across batch and sequence dimensions and backends, memory- vs compute-bound behavior, and end-to-end RAG cost comparison between cloud-API and local inference, making each optimization measurable.

## Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python (3.10 or newer) |
| GPU kernels | Triton |
| Quantization / inference runtime | ONNX Runtime GPU, ONNX |
| Generation backend | PyTorch, Transformers, Tokenizers |
| API | FastAPI, Uvicorn, Pydantic v2 |
| Distributed / networking | asyncio, httpx |
| Logging | structlog |
| Numerics | NumPy |
| Testing & quality | pytest, pytest-asyncio, pytest-benchmark, ruff, mypy (strict) |
| Optional (pipeline tooling) | LangGraph, OpenAI SDK, Matplotlib |
| Infrastructure | Docker, Docker Compose (NVIDIA CUDA base image) |

## Status

Single-author engineering project, structured and documented like a production server. Targets NVIDIA CUDA GPUs and runs containerized or natively. Source code private/proprietary, review available on request.

---


## Code sample

A small, IP-safe excerpt is in [`fast-inference/`](./fast-inference/): INT8 static quantization for ONNX transformers (a calibration reader, an op skip-list that keeps precision-sensitive layers in float, per-channel weight quantization, and FP32-versus-INT8 cosine validation), plus the serving-layer utilities: a dynamic request batcher, a pre-allocated GPU tensor pool, and a circuit-breaker health checker.

_© 2026 Edoardo Caciolo, all rights reserved. Proprietary and not open source; source code is private and available for review on request._
