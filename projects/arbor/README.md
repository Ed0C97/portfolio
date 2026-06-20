# ARBOR — AI Search & Recommendation Engine

*Portfolio excerpt, adapted.*

ARBOR is the intelligent search and recommendation engine behind a content
platform — a personal magazine that surfaces places, brands, and venues a
reader will love. Under the hood it is a retrieval + ranking system: it has
to turn a fuzzy human query ("cozy rooftop bar in Trastevere") into a tight,
relevant, deduplicated set of results, and it has to do it fast and without
falling over when an external model provider is slow or down.

This folder contains three self-contained excerpts from that engine. They are
the *plumbing* of intelligent search — the parts that are interesting as
engineering, distilled and trimmed so each file reads standalone. Internal
imports are stubbed; nothing here depends on the rest of the codebase.

## What each file shows

### `hybrid_search.py` — Hybrid retrieval with RRF fusion
The retrieval backbone. Runs a **dense vector search** (semantic similarity)
and a **sparse keyword search** in parallel, then fuses the two ranked lists
with **Reciprocal Rank Fusion** (the `1/(k + rank)` formula, `k = 60`, with
configurable per-source weights). Includes an `EntityResolver` that
deduplicates results coming from multiple sources via UUID grouping plus
fuzzy name matching (Jaccard over normalized tokens), merging metadata with a
source-priority policy. This is why ARBOR beats vanilla single-vector RAG on
entity queries: it catches both "feels like what you mean" and "exact name
match" in one pass.

### `reranking_pipeline.py` — Multi-stage ranking funnel
A cost-aware **learning-to-rank funnel** that progressively narrows
candidates through stages of increasing cost: dense cosine → BM25 (fused via
RRF) → cross-encoder rerank → an LLM-as-judge pass. Cheap stages run first
and on many candidates; expensive stages run last and on few. Every external
call is wrapped so the pipeline **degrades gracefully** — if the cross-encoder
API is unavailable it falls back to keyword-overlap scoring; if the LLM pass
fails it passes results through unchanged. Per-stage latency and
input/output counts are tracked for observability, and a `rerank_fast` path
skips all network calls for latency-sensitive requests.

### `ranking.py` — Learning-to-rank with a zero-dependency fallback
The personalization ranker. Extracts a feature vector per candidate
(two-tower score, cosine similarity, popularity, recency, price bucket,
category match, log-scaled interaction counts) and scores it with a LightGBM
LambdaRank model when available — or a **pure-Python linear model** when it
isn't. The fallback means the recommendation surface never hard-fails on a
missing model artifact: it just ranks a little less sharply.

## How they fit together

A request flows roughly: `hybrid_search` retrieves a broad candidate set →
`reranking_pipeline` narrows and reorders it for relevance → `ranking`
applies per-user personalization signals. A thin FastAPI layer (not included
here) composes these behind `/search/hybrid`, `/search/vector`, and the
recommendations endpoints.

## Deliberately omitted

To demonstrate the engineering without handing over the product, the
following are intentionally **not** included or are reduced to stubs:

- **The entity-discovery / enrichment graph-reasoning pipeline.** The
  multi-strategy relationship-discovery engine that enriches the knowledge
  graph is the core moat and is excluded entirely.
- **Core LLM prompt templates and reasoning routing.** The LLM rerank stage
  here carries a *generic, illustrative* relevance-rating prompt — the real
  reasoning prompts, scoring rubric, and model-routing logic are removed.
- **Concrete embedding / gateway / vector-store clients.** Calls to the
  embedding gateway, Qdrant, and Neo4j are stubbed or replaced with minimal
  protocols so each file is readable in isolation.
- **Secrets, API keys, model identifiers, and real catalog/business data.**
  None appear in these excerpts.

---

_© 2026 Edoardo Caciolo — all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
