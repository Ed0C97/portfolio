# Anacleto: Provider Layer

Excerpts from Anacleto, a FastAPI service and engine that analyzes Instagram images, computes an optimal feed order, and publishes through the Meta Graph API. They show two layers: the feed-grid ordering search (the algorithmic core) and the *provider layer* that lets storage, social, and database backends be swapped without touching the engine.

**Context:** see [../anacleto-instagram.md](../anacleto-instagram.md) for the full project overview.

**Stack:** Python 3.11, `abc` / `dataclasses` / `enum` / typing, `requests`, Cloudinary SDK (optional), Instagram Graph API (Meta).

## What each file shows

- **`grid_optimizer.py`**: the feed-grid ordering search. Two interchangeable strategies (nearest-neighbour `GreedySearch` restarted from every seed to remove first-move bias, and a bitmask-state `BeamSearch` that keeps running additive scores so each extension is one `score_pair` call) behind a `SearchStrategy` Protocol, with the aesthetic model injected through an `AestheticScorer` Protocol. Shows permutation-search technique, additive-score pruning, and deterministic tie-breaking; the real scorer is replaced by a clearly labelled, reproducible placeholder.
- **`providers_base.py`**: the abstract contracts. Three `ABC` interfaces (`CloudStorageProvider`, `SocialMediaProvider`, `DatabaseProvider`-style), typed dataclass result models (`CloudFile`, `UploadResult`, `PublishResult`), enums for media type and status, sensible default-method implementations on the base classes, and a `ProviderRegistry` for runtime provider selection. Demonstrates clean OOP/API design and decoupling.
- **`instagram_provider.py`**: a Graph API client implementing the social interface. Shows the quirky two-step publish flow (create media container, then poll until `FINISHED`, then publish), request retry with fixed backoff, container readiness polling with timeout, and honest handling of an API limitation (the Graph API can't delete posts).
- **`cloudinary_provider.py`**: a storage client with a dual-mode design: it uses the official SDK when installed and falls back to signed direct HTTP calls otherwise. Shows SHA-1 request-signature generation, handling of four file input types (`Path` / `bytes` / file-like / URL), `finally`-block resource cleanup, and API-response-to-dataclass mapping.

## Deliberately omitted

- The real aesthetic scoring model (color-harmony, composition, flow, balance, and theme dimensions and their tuned weights) and the feature extraction behind it: injected through the `AestheticScorer` Protocol and never shipped here; only an obvious `PlaceholderScorer` stand-in is included. The MCTS strategy from the production Beam, Greedy, and MCTS set is also omitted. `grid_optimizer.py` shows the search structure as standard, illustrative technique, not the tuned scoring that is the product's moat.
- All credentials, tokens, account IDs, and `.env` values. Example docstrings use obviously-fake placeholders.
- The caption/hashtag generation, scheduler, analytics, user-account/auth, and FastAPI app wiring.
- Convenience helpers and some methods were trimmed for length; the excerpts are faithful to the original style with light adaptation.

_© 2026 Edoardo Caciolo, all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
