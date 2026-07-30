# Anacleto

> A FastAPI platform that analyzes Instagram images with vision models, optimizes feed order via MCTS, Beam Search, or Greedy strategies, schedules posts, and publishes through the Meta Graph API.

## Overview

Anacleto automates the Instagram content pipeline for Business and Creator
accounts. It extracts visual features from images with vision models, searches
for the post ordering that produces the most coherent feed grid, generates
context-aware captions and hashtags, queues the result against per-weekday time
slots, and publishes through the Instagram Graph API. The platform exposes its
capabilities as a FastAPI service with user accounts, email-verified
registration, and API keys, and ships a desktop client for users who prefer a
graphical interface. Per-account credentials (Instagram, Cloudinary, Gemini) are
supplied per request and used statelessly rather than stored.

## Highlights

- **Visual feature extraction.** Color, texture, detected objects, and aesthetic
  signals are extracted per image with vision models (PyTorch, Ultralytics YOLO,
  Hugging Face Transformers) coordinated with Google Gemini, Vertex AI, and
  Replicate calls.
- **Feed-order optimization.** A grid-assignment optimizer plus interchangeable
  search strategies (Greedy, Beam Search, and a Monte Carlo Tree Search with a
  greedy pre-filter and rollouts) select the arrangement that maximizes visual
  coherence, scored by a tuned aesthetic model.
- **Caption generation.** Context-aware captions and hashtags produced from
  image-analysis results.
- **Smart scheduling.** An APScheduler-based job manager publishes queued posts
  at per-weekday time slots (default three posts per day, Europe/Rome) with a
  dry-run mode.
- **Real publishing.** Multi-format publishing (images, videos, carousels,
  stories, reels) through the Meta Graph API v21.0 with retry logic.
- **Per-request credentials.** User Instagram, Cloudinary, and Gemini secrets are
  supplied per request and used statelessly; they are never persisted server-side.
- **Accounts and API keys.** Registration with OTP email verification, bcrypt
  password hashing, API keys with optional expiry, and per-IP rate limiting.
- **Desktop client.** A Dear PyGui application with macOS and Windows builds.

## Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python 3.11 |
| API | FastAPI, Uvicorn, Pydantic |
| Vision / ML | PyTorch, torchvision, Ultralytics YOLO, Hugging Face Transformers; Google Gemini, Vertex AI, Replicate |
| Optimization | Grid-assignment optimizer, MCTS, Beam Search, Greedy (NumPy) |
| Data stores | PostgreSQL (users, API keys, OTP) via asyncpg; SQLite (local engine data) |
| Media / social | Instagram Graph API (Meta), Cloudinary |
| Scheduling | APScheduler |
| Auth / email | bcrypt, OTP email verification (Resend) |
| Desktop client | Dear PyGui (PyInstaller builds for macOS and Windows) |
| Infra / DevOps | Docker (multi-stage), Docker Compose, Render blueprint |

## Status

Beta. Multi-component application with a deployable API, scheduler, desktop
client, and Docker/Render deployment configuration; some advanced engine features
(for example feedback learning) are present but disabled by default. Architecture
is built around swappable extractor, optimizer, and evaluator components so model
and strategy choices change by configuration.

Source code is private and proprietary; code review available on request.

---


## Code sample

A small, IP-safe excerpt is in [`anacleto-instagram/`](./anacleto-instagram/): the feed-grid ordering search (a real Monte Carlo Tree Search with a greedy pre-filter and rollouts over grid arrangements, with the tuned aesthetic scoring model stubbed), plus the provider layer, typed ABC contracts and Graph API and Cloudinary clients with retry, backoff, and SDK-or-HTTP fallback.

_© 2026 Edoardo Caciolo, all rights reserved. Proprietary and not open source; source code is private and available for review on request._
