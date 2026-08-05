---
title: "fast-inference"
slug: "fast-inference"
lang: "en"
oneLiner: "Self-hosted OpenAI-compatible inference server with INT8 quantization, custom Triton kernels, and async dynamic batching."
category: "Inference & Performance"
year: "2026"
status: "Prototype"
statusTone: "prototype"
featured: true
visible: true
order: 4
metrics:
  - value: "10.25 ms"
    label: "p50 vs 19.58 ms FP32, same CoreML provider, Apple M3 Pro, bge-small"
  - value: "-47.9%"
    label: "INT8 graph vs FP32 source, 127.4 to 66.4 MB"
stack: ["Python", "Triton", "ONNX Runtime", "PyTorch", "FastAPI", "httpx", "Docker"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/fast-inference"
image: "/images/projects/fast-inference.svg"
---

## The problem

A retrieval-augmented generation pipeline makes three kinds of model calls: it embeds documents and queries, reranks the candidates, and generates an answer. The convenient route is sending all three to a cloud API, which means every request pays a network round-trip and every document leaves the machine. For workloads with private data, or with latency budgets measured in tens of milliseconds, that is a poor trade.

Running the models locally sounds like the fix, but a naive local server is slow in its own way. Serving one request at a time leaves the accelerator idle between calls, full-precision weights waste memory bandwidth, and at small batch sizes transformer inference is memory-bound: the chip spends its time moving weights, not doing math. Making local serving genuinely fast means working the whole stack at once: quantized models, batched execution, careful memory use, and a routing layer that survives a worker going down. This project builds that stack end to end, in one codebase.

## What I built

fast-inference is a self-hosted inference server for embedding, reranking, and text-generation models. It exposes one HTTP API that mirrors the OpenAI and Cohere request and response schemas, so any client already written against those services can point at it without changes: embeddings, chat completions with token streaming, reranking, plus health and metrics endpoints.

The same code runs on an NVIDIA GPU, on Apple Silicon, and on plain CPU: a runtime layer resolves the device and the model profile in one place, and the server picks the best available backend at startup. Around the models sit the pieces a serving system needs: an asynchronous batcher that groups incoming requests, an INT8 quantization pipeline, a router that spreads load across workers, a benchmark orchestrator that measures every executable backend and commits the results with the hardware recorded, and an operator dashboard served at the root URL with a live view of the batching queue.

## How it works

Requests land in a dynamic batcher that dispatches one batch at 32 requests or after 10 ms of waiting, whichever comes first; each request gets its own asyncio future, and a failure fans the exception out to every waiting caller. On the torch path, pooled, length-bucketed buffers are recycled across requests, with pooled and unpooled outputs verified bit-identical. Quantization is static INT8 through ONNX Runtime, calibrated on representative data, with precision-sensitive operators (LayerNorm, Softmax, GELU, embedding gathers) deliberately kept in float. The distributed layer scores workers by latency and queue depth (weighted 0.7 and 0.3) behind a three-state circuit breaker with health checks every two seconds.

The non-obvious choice is the router: round-robin is a poor fit because request time scales with sequence length, so two workers with equal request counts can carry very unequal load. Scoring by observed latency and queue depth sends work where it will finish sooner.

## Results

Measured on an Apple M3 Pro with bge-small-en-v1.5 at batch size 1, over 10 timed iterations after warmup: switching from FP32 to INT8 on the same CoreML execution provider cut p50 latency from 19.58 ms to 10.25 ms. The INT8 graph is 47.9% smaller than its FP32 source (127.4 MB to 66.4 MB), with 41 of 549 operators kept in float to protect accuracy. These are laptop numbers on a small embedding model, not datacenter figures: the benchmark orchestrator commits every run as JSON and Markdown with the hardware attached, so each number carries its own context.

## Limits and what I'd redo

The hand-written Triton kernels live in a standalone optimization layer with their own benchmarks; the serving path does not import them, so the latencies above come from ONNX Runtime, not from my kernels. Reranking is queue-managed but not GPU-batched. If I started over, I would build the benchmark harness on day one: early documentation quoted reference targets as if they were results, and I later retracted them in favor of committed measurements with the hardware stated.
