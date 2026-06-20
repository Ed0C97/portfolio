# Anacleto — Provider Layer

Excerpts from Anacleto, a FastAPI service and engine that analyzes Instagram images, computes an optimal feed order, and publishes through the Meta Graph API. These three files are the platform's *provider layer*: the abstraction that lets storage, social, and database backends be swapped without touching the engine.

**Context:** see [../anacleto-instagram.md](../anacleto-instagram.md) for the full project overview.

**Stack:** Python 3.11 · `abc` / `dataclasses` / `enum` / typing · `requests` · Cloudinary SDK (optional) · Instagram Graph API (Meta).

## What each file shows

- **`providers_base.py`** — the abstract contracts. Three `ABC` interfaces (`CloudStorageProvider`, `SocialMediaProvider`, `DatabaseProvider`-style), typed dataclass result models (`CloudFile`, `UploadResult`, `PublishResult`), enums for media type and status, sensible default-method implementations on the base classes, and a `ProviderRegistry` for runtime provider selection. Demonstrates clean OOP/API design and decoupling.
- **`instagram_provider.py`** — a Graph API client implementing the social interface. Shows the quirky two-step publish flow (create media container → poll until `FINISHED` → publish), request retry with fixed backoff, container readiness polling with timeout, and honest handling of an API limitation (the Graph API can't delete posts).
- **`cloudinary_provider.py`** — a storage client with a dual-mode design: it uses the official SDK when installed and falls back to signed direct HTTP calls otherwise. Shows SHA-1 request-signature generation, handling of four file input types (`Path` / `bytes` / file-like / URL), `finally`-block resource cleanup, and API-response-to-dataclass mapping.

## Deliberately omitted

- The feed-optimization search (MCTS / Beam / Greedy heuristics), the grid aesthetic-scoring weights and criteria, and all feature-extraction logic — these are the product's moat and live in the engine's `godmode/` package, untouched here.
- All credentials, tokens, account IDs, and `.env` values. Example docstrings use obviously-fake placeholders.
- The caption/hashtag generation, scheduler, analytics, user-account/auth, and FastAPI app wiring.
- Convenience helpers and some methods were trimmed for length; the excerpts are faithful to the original style with light adaptation.

_© 2026 Edoardo Caciolo — all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
