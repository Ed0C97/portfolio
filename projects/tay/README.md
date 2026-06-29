# Tay: code samples

A small set of excerpts from Tay, an AR app that brings artworks to life. They are chosen to show engineering craft, real-time signal processing, clean abstraction over a tricky framework lifecycle, and production API governance, without exposing any of the product's core value.

**Context:** see the project page at [../tay.md](../tay.md).

**Stack:** Swift 6 (Swift Concurrency, `@Observable`, `@MainActor`), AVFoundation / CoreVideo / QuartzCore, RealityKit; Python 3.12, FastAPI, asyncio.

## What each file shows

- **`CameraQualityMonitor.swift`**: A real-time viewfinder quality engine. A single-pass BGRA frame analyzer computes mean luminance, luminance variance, a Laplacian-variance sharpness proxy, and saturation spread in one loop; the monitor fuses those with motion (RMS rotation) and KVO on `AVCaptureDevice` focus/exposure to emit an `@Observable` quality report at ~2 Hz. Notable: multi-signal fusion, persistence-based debouncing to stop badge flicker, and an explicit per-iPhone-13 CPU budget.
- **`CharacterAnimator.swift`**: A thin, `@MainActor` RealityKit animation driver. Loads a USDZ, caches its clips by name, and cross-fades between them on FSM state transitions with a configurable blend duration and optional look-at target. Notable: animation names come from the asset (not hardcoded enums) and a three-step fallback chain (requested clip, then neutral idle, then first available) keeps the rig animating even when an asset is missing a slot.
- **`rate_limiter.py`**: Per-user, route-aware token-bucket rate limiting for LLM-backed endpoints. One limiter instance per user (so one noisy client can't starve others), a bounded in-memory registry that's safe to overflow, a Redis-swappable surface for multi-instance deployments, and a deliberate fail-open philosophy so the limiter never becomes the thing that breaks the service.

## Deliberately omitted

The proprietary core of Tay is not included here, at any level of detail:

- **Art recognition**: the on-device CoreML recognition pipeline and its models, embeddings, and matching logic.
- **Anti-counterfeit verification**: how a canvas is authenticated as genuine.
- **Steganographic canvas signing**: the watermark scheme and its error-correcting codec that encodes canvas identity into the artwork.
- **Prompt templates, domain rules, and tenant/business configuration**: narration/QA prompt content, catalog business logic, and any credentials, tokens, or environment values.

These excerpts are infrastructure and "supporting craft" only; they reference the moat behind protocols and abstractions but contain none of its logic.

_© 2026 Edoardo Caciolo, all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
