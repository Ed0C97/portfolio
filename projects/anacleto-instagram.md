# Anacleto

> A REST API and engine that analyzes Instagram images, computes an optimal feed order, schedules posts, and publishes them automatically through the official Meta Graph API.

## Overview

Anacleto automates the end-to-end content pipeline for Instagram Business and Creator accounts. It extracts visual signals from images, searches for the post ordering that produces the most coherent feed grid, generates captions, queues the result, and publishes on schedule. The platform is delivered as an authenticated web API with user accounts and API keys, plus a cross-platform desktop client for users who prefer a graphical interface. Per-account social and media credentials are supplied per request and are never persisted server-side.

## Highlights

- **Visual feature extraction** — derives color, texture, object, and aesthetic signals from images using a combination of self-hosted vision models and external vision APIs.
- **Feed-order optimization** — automatically searches the space of grid arrangements to produce a feed that maximizes overall visual coherence, with multiple interchangeable search strategies available depending on the speed/quality trade-off required.
- **Aesthetic grid scoring** — evaluates candidate layouts across multiple visual-quality dimensions (color harmony, composition, flow, balance, theme consistency) to drive ordering decisions toward a consistently strong result.
- **Caption generation** — produces context-aware captions and hashtags grounded in the analysis of each image.
- **Smart scheduling** — publishes posts automatically at configurable per-weekday time slots in any timezone, with a safe dry-run mode for previewing the plan before going live.
- **Queue management** — endpoints to list, add, reorder, and track the status of queued posts.
- **Multi-format publishing** — posts images, videos, carousels, stories, and reels via the Meta Graph API, with resilient retry handling and cloud-backed media hosting.
- **Accounts, auth, and rate control** — registration with password-strength validation, one-time-password email verification, login, and API-key issuance with optional expiry, protected by API-key authentication, per-client rate limiting, and configurable CORS.
- **Stateless credential handling** — user Instagram, media-storage, and vision-API secrets are passed per request and used in-memory only, removing the platform from custody of third-party secrets.
- **Desktop client** — a graphical application covering registration, verification, credential and API-key management, and account stats, with packaged builds for macOS and Windows.

## Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python 3.11 |
| Web framework | FastAPI, Uvicorn, Pydantic |
| Vision / ML | PyTorch, torchvision, Pillow, Ultralytics (YOLO), Hugging Face Transformers |
| External AI APIs | Google Gemini, Vertex AI, Replicate |
| Data stores | PostgreSQL (accounts, API keys, verification); SQLite (local engine data) |
| Media / social | Cloudinary, Instagram Graph API (Meta) |
| Scheduling | APScheduler |
| Auth / email | bcrypt, transactional email delivery |
| Desktop client | Dear PyGui (packaged for macOS and Windows) |
| Infra / DevOps | Docker (multi-stage), Docker Compose, Render |

## Status

Beta. A multi-component system spanning a deployable API, a standalone scheduler service, and a desktop client, with containerized deployment configuration. Architecture is built around swappable extractor / optimizer / evaluator components so model and strategy choices can be changed by configuration.

Source code is private and proprietary — code review available on request.

---


## Code sample

A small, IP-safe excerpt is in [`anacleto-instagram/`](./anacleto-instagram/) — typed ABC contracts plus production Graph API and Cloudinary clients with retry/backoff and SDK-or-HTTP fallback.

_© 2026 Edoardo Caciolo — all rights reserved. Proprietary and not open source; source code is private and available for review on request._
