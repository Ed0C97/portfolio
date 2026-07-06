# Anacleto

> A multitenant SaaS that automates the Instagram content pipeline with self-hosted vision AI: it analyzes images, optimizes the feed grid, generates on-brand captions, publishes through the Meta Graph API, and closes the loop by learning from real post performance.

## Overview

Anacleto runs the end-to-end content pipeline for Instagram Business and Creator
accounts. It extracts visual signals from images with self-hosted models, searches
for the post ordering that reads best as a grid, generates captions that stay
close to the brand voice, queues and publishes on schedule, and then feeds real
engagement back into the next set of decisions. It is a watertight multitenant
service: every tenant is isolated at the database level, and a single shared AI
engine is tuned per tenant through a per-tenant knowledge base rather than through
private model weights. The product is a FastAPI backend with a Next.js web client;
per-account social and media credentials can be supplied per request and used
statelessly rather than stored.

## Highlights

- **Self-hosted vision and language AI.** Image analysis and captioning run on
  local models reached through a shared inference layer, so analysis is unlimited
  and data does not leave the server. There is no per-call cloud AI bill.
- **Watertight multitenancy.** Tenant isolation is enforced by Postgres Row Level
  Security bound to a request context, so a query for the wrong tenant returns
  nothing even if application code is wrong. Every tenant-scoped table is protected
  the same way.
- **Per-tenant tuning without per-tenant models.** One shared model is steered per
  tenant by a per-tenant vector knowledge base, following a retrieval-augmented
  pattern, so tenants get isolation of their data and behavior without the cost of
  private weights.
- **Feed-order optimization.** A grid-assignment optimizer plus interchangeable
  search strategies (Greedy, Beam Search, and a Monte Carlo Tree Search with a
  greedy pre-filter and rollouts) select the arrangement that maximizes visual
  coherence, scored by a tuned aesthetic model.
- **Closed-loop intelligence.** A maturity-aware insight poller records real
  engagement after posts mature; an engagement prior and an append-only decision
  store drive the next optimization, and captions are regularized toward the brand
  voice. The system keeps a randomized holdout as the primary clean signal rather
  than claiming causal truth from observational data.
- **Real publishing and billing.** Multi-format publishing (images, carousels,
  stories, reels) through the Meta Graph API with token lifecycle and preflight
  checks; Stripe billing with metered quotas, a paywall, and guided onboarding.
- **Secure by construction.** Email-verified registration, bcrypt password hashing,
  API keys stored only as hashes, and a web client that keeps the API key in an
  httpOnly cookie so it never reaches the browser.

## Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python 3.11+ (backend), TypeScript (frontend) |
| API | FastAPI, Uvicorn, Pydantic |
| Web | Next.js (App Router), React, Tailwind CSS |
| Database | Postgres 16 with pgvector, SQLAlchemy (async), Alembic, Row Level Security |
| Vision / ML | Self-hosted models on a local inference server, PyTorch, Transformers, SAM, YOLO |
| Optimization | Grid-assignment optimizer, MCTS, Beam Search, Greedy (NumPy) |
| Media / social | Instagram Graph API (Meta), Cloudinary |
| Billing | Stripe |
| Auth / email | bcrypt, one-time-password email over SMTP |
| Infra / DevOps | Docker (multi-stage), Docker Compose |

## Status

Version 1.0. The multitenant platform is in place: shared local AI, per-tenant
knowledge base, decision store, insight poller, versioned per-tenant model state,
Stripe billing and onboarding, real Instagram publishing with token lifecycle, and
the closed-loop optimizer. The web client implements the shell, authentication,
and section screens over the API. Architecture is built around swappable
extractor, optimizer, and evaluator components so model and strategy choices change
by configuration.

Source code is private and proprietary; code review available on request.

---


## Code sample

A small, IP-safe excerpt is in [`anacleto-instagram/`](./anacleto-instagram/): the feed-grid ordering search (a real Monte Carlo Tree Search with a greedy pre-filter and rollouts over grid arrangements, with the tuned aesthetic scoring model stubbed), plus the provider layer, typed ABC contracts and Graph API and Cloudinary clients with retry, backoff, and SDK-or-HTTP fallback.

_© 2026 Edoardo Caciolo, all rights reserved. Proprietary and not open source; source code is private and available for review on request._
