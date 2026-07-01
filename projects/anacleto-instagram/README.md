# Anacleto: Provider Layer

Excerpts from Anacleto, a FastAPI service and engine that analyzes Instagram images, computes an optimal feed order, and publishes through the Meta Graph API. They show two layers: the feed-grid ordering search (the algorithmic core) and the *provider layer* that lets storage, social, and database backends be swapped without touching the engine.

**Context:** see [../anacleto-instagram.md](../anacleto-instagram.md) for the full project overview.

**Stack:** Python 3.11, `abc` / `dataclasses` / `enum` / typing, `requests`, Cloudinary SDK (optional), Instagram Graph API (Meta).

## What each file shows

- **`grid_optimizer.py`**: the real feed-grid optimizer. A Monte Carlo Tree Search (UCB selection, expansion, greedy rollout, and backpropagation) over grid orderings that maximizes an aesthetic coherence score, with a greedy pre-filter that shrinks the candidate pool and also drives the rollouts. The tuned similarity band, the penalty curve, and the grid-harmony scoring model (the moat) are stubbed behind placeholder constants and an injected scorer.
- **`providers_base.py`**: the abstract contracts. Three `ABC` interfaces (`CloudStorageProvider`, `SocialMediaProvider`, `DatabaseProvider`-style), typed dataclass result models (`CloudFile`, `UploadResult`, `PublishResult`), enums for media type and status, sensible default-method implementations on the base classes, and a `ProviderRegistry` for runtime provider selection. Demonstrates clean OOP/API design and decoupling.
- **`instagram_provider.py`**: a Graph API client implementing the social interface. Shows the quirky two-step publish flow (create media container, then poll until `FINISHED`, then publish), request retry with fixed backoff, container readiness polling with timeout, and honest handling of an API limitation (the Graph API can't delete posts).
- **`cloudinary_provider.py`**: a storage client with a dual-mode design: it uses the official SDK when installed and falls back to signed direct HTTP calls otherwise. Shows SHA-1 request-signature generation, handling of four file input types (`Path` / `bytes` / file-like / URL), `finally`-block resource cleanup, and API-response-to-dataclass mapping.

## Deliberately omitted

- The tuned similarity band (the real minimum, optimal, and maximum similarity values), the `score_transition` penalty falloffs, and the grid-harmony scoring model (its row, column, diagonal, center, and corner weights and the color, semantic, and texture continuity channels) are the moat: they are replaced with obvious placeholder constants and left behind an injected `external_scorer`. The feature extractor (the color, texture, and semantic-embedding models) is stubbed to random unit vectors. The search structure itself, the MCTS and its greedy baseline, is faithful to the real code.
- All credentials, tokens, account IDs, and `.env` values. Example docstrings use obviously-fake placeholders.
- The caption/hashtag generation, scheduler, analytics, user-account/auth, and FastAPI app wiring.
- Convenience helpers and some methods were trimmed for length; the excerpts are faithful to the original style with light adaptation.

_© 2026 Edoardo Caciolo, all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
