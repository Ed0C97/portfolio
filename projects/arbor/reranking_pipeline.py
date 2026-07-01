"""Portfolio excerpt, adapted.

Multi-stage reranking funnel for entity search. Cheap stages run on many
candidates, expensive stages on few:

    Stage 1: Dense retrieval   (cosine similarity)   -> top 100   (cheap)
    Stage 2: Sparse retrieval  (BM25)                -> top  50   (cheap, parallel)
             ... Stage 1 + 2 merged via RRF ...
    Stage 3: Cross-encoder     (rerank API)          -> top  20   (network)
    Stage 4: LLM-as-judge      (relevance rating)    -> top  10   (expensive)

Every external call has a local fallback, so a slow or down provider degrades
the result quality instead of failing the request. Per-stage latency and
input/output counts are recorded for tracing.

The rerank and LLM clients are stubbed behind small async methods so the file
reads standalone. The production relevance prompt and model routing are left
out; the placeholder prompt only shows the call shape.
"""

from __future__ import annotations

import asyncio
import logging
import math
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# trimmed for the example; production uses a much larger set
STOPWORDS: set[str] = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "at", "for",
    "with", "by", "from", "is", "it", "as", "this", "that", "near",
}


class RankingStage(Enum):
    DENSE_RETRIEVAL = "dense_retrieval"
    SPARSE_RETRIEVAL = "sparse_retrieval"
    CROSS_ENCODER = "cross_encoder"
    LLM_RERANKER = "llm_reranker"


@dataclass
class RankedResult:
    """Search result carrying per-stage scores and metadata."""

    entity_id: str
    name: str
    category: str
    city: str
    score: float
    stage_scores: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    rank: int = 0


# ---------------------------------------------------------------------------
# Stage 1: Dense retrieval (cosine similarity)
# ---------------------------------------------------------------------------


class Stage1DenseRetrieval:
    """Score candidates by cosine similarity against the query embedding."""

    async def rank(
        self,
        query_embedding: list[float],
        candidates: list[dict[str, Any]],
        top_k: int = 100,
    ) -> list[RankedResult]:
        scored: list[RankedResult] = []
        for c in candidates:
            emb = c.get("embedding")
            # fall back to the candidate's own score when no embedding is present
            sim = (
                self._cosine(query_embedding, emb)
                if emb is not None and query_embedding
                else float(c.get("score", 0.0))
            )
            scored.append(_to_result(c, sim, RankingStage.DENSE_RETRIEVAL))

        scored.sort(key=lambda r: r.score, reverse=True)
        return _assign_ranks(scored[:top_k])

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        # mismatched dims mean different embedding models; treat as no match
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        return dot / (mag_a * mag_b) if mag_a and mag_b else 0.0


# ---------------------------------------------------------------------------
# Stage 2: Sparse retrieval (Okapi BM25)
# ---------------------------------------------------------------------------


class Stage2SparseRetrieval:
    """BM25 over an in-memory inverted index (k1=1.2, b=0.75)."""

    K1: float = 1.2
    B: float = 0.75

    def __init__(self) -> None:
        self._doc_tokens: dict[str, list[str]] = {}
        self._inverted_index: dict[str, set[str]] = defaultdict(set)
        self._doc_lengths: dict[str, int] = {}
        self._doc_count: int = 0
        self._avg_doc_len: float = 0.0

    def add_documents(self, docs: list[dict[str, Any]]) -> None:
        """Index docs, concatenating name, description, category, and tags into one field."""
        for doc in docs:
            doc_id = str(doc.get("id", doc.get("entity_id", "")))
            if not doc_id:
                continue
            parts = [str(doc[f]) for f in ("name", "description", "category")
                     if doc.get(f)]
            parts += [str(t) for t in doc.get("tags", []) if isinstance(doc.get("tags"), list)]
            tokens = self._tokenize(" ".join(parts))
            self._doc_tokens[doc_id] = tokens
            self._doc_lengths[doc_id] = len(tokens)
            for token in set(tokens):
                self._inverted_index[token].add(doc_id)

        self._doc_count = len(self._doc_tokens)
        total = sum(self._doc_lengths.values())
        self._avg_doc_len = total / self._doc_count if self._doc_count else 0.0

    def rank(
        self, query_text: str, candidates: list[dict[str, Any]], top_k: int = 50
    ) -> list[RankedResult]:
        # lazily index the candidates themselves if nothing was indexed up front
        if self._doc_count == 0 and candidates:
            self.add_documents(candidates)

        query_tokens = self._tokenize(query_text)
        scored = [
            _to_result(
                c,
                self._bm25(str(c.get("entity_id", c.get("id", ""))), query_tokens),
                RankingStage.SPARSE_RETRIEVAL,
            )
            for c in candidates
        ]
        scored.sort(key=lambda r: r.score, reverse=True)
        return _assign_ranks(scored[:top_k])

    def _bm25(self, doc_id: str, query_tokens: list[str]) -> float:
        """Okapi BM25: sum_t IDF(t) * (tf * (k1+1)) / (tf + k1*(1 - b + b*dl/avgdl)).

        IDF(t) = log((N - n_t + 0.5) / (n_t + 0.5) + 1); the +1 keeps IDF
        non-negative even for terms in more than half the corpus.
        """
        doc_tokens = self._doc_tokens.get(doc_id)
        if not doc_tokens:
            return 0.0
        dl = self._doc_lengths.get(doc_id, 0)
        tf_map: dict[str, int] = defaultdict(int)
        for t in doc_tokens:
            tf_map[t] += 1

        score = 0.0
        for term in query_tokens:
            n_t = len(self._inverted_index.get(term, set()))
            tf = tf_map.get(term, 0)
            if not n_t or not tf:
                continue
            idf = math.log((self._doc_count - n_t + 0.5) / (n_t + 0.5) + 1.0)
            # skip length normalization before any doc is indexed (avgdl == 0)
            denom = (
                tf + self.K1 * (1.0 - self.B + self.B * dl / self._avg_doc_len)
                if self._avg_doc_len else tf + self.K1
            )
            score += idf * (tf * (self.K1 + 1.0)) / denom
        return score

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


# ---------------------------------------------------------------------------
# Stage 3: Cross-encoder rerank (network) with a keyword-overlap fallback
# ---------------------------------------------------------------------------


class Stage3CrossEncoder:
    """Cross-encoder rerank via an external API, with a keyword fallback.

    Primary path is the rerank API (behind a circuit breaker in production).
    When the breaker is open or the call fails, drop to keyword-overlap scoring.
    """

    async def rank(
        self, query: str, candidates: list[RankedResult], top_k: int = 20
    ) -> list[RankedResult]:
        if not candidates:
            return []
        try:
            return await self._rank_remote(query, candidates, top_k)
        except Exception as exc:
            logger.warning("Cross-encoder failed, using fallback: %s", exc)
            return self._rank_keyword_overlap(query, candidates, top_k)

    async def _rank_remote(
        self, query: str, candidates: list[RankedResult], top_k: int
    ) -> list[RankedResult]:
        """Call the external rerank model. Stubbed here.

        Production builds one document string per candidate, calls the rerank
        API under a circuit breaker, and maps relevance scores back.
        """
        raise NotImplementedError("rerank client omitted from portfolio excerpt")

    def _rank_keyword_overlap(
        self, query: str, candidates: list[RankedResult], top_k: int
    ) -> list[RankedResult]:
        """Score by Jaccard token overlap; no external call."""
        q = set(self._tokenize(query))
        if not q:
            return candidates[:top_k]
        scored: list[tuple[float, RankedResult]] = []
        for r in candidates:
            doc = self._tokenize(f"{r.name} {r.category} {r.city} "
                                 f"{r.metadata.get('description', '')}")
            d = set(doc)
            overlap = len(q & d) / len(q | d) if d else 0.0
            r.score = overlap
            r.stage_scores[RankingStage.CROSS_ENCODER.value] = overlap
            scored.append((overlap, r))
        scored.sort(key=lambda t: t[0], reverse=True)
        return _assign_ranks([r for _, r in scored[:top_k]])

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


# ---------------------------------------------------------------------------
# Stage 4: LLM-as-judge rerank (most expensive; <= 20 candidates)
# ---------------------------------------------------------------------------


class Stage4LLMReranker:
    """Rerank by asking an LLM to rate each candidate's relevance.

    Production prompt and model routing are part of the product and omitted.
    On any failure the stage passes results through unchanged.
    """

    # placeholder, not the production prompt
    PROMPT_TEMPLATE: str = (
        "Rate how well the entity matches the query from 0 to 100.\n"
        "Query: {query}\nEntity: {name} ({category}, {city})\n"
        "Respond with a single integer."
    )

    async def rank(
        self, query: str, candidates: list[RankedResult], top_k: int = 10
    ) -> list[RankedResult]:
        if not candidates:
            return []
        try:
            return await self._rank_with_llm(query, candidates, top_k)
        except Exception as exc:
            logger.warning("LLM rerank failed, passing through: %s", exc)
            return self._passthrough(candidates, top_k)

    async def _rank_with_llm(
        self, query: str, candidates: list[RankedResult], top_k: int
    ) -> list[RankedResult]:
        """Score candidates concurrently, bounded to avoid rate-limit storms.

        Gateway call is stubbed; _parse_score shows how the free-text reply is
        coerced into a 0-1 score.
        """
        raise NotImplementedError("LLM gateway omitted from portfolio excerpt")

    @staticmethod
    def _parse_score(response: str) -> float:
        """Pull the first integer from the reply, clamped to [0, 100]; default 50 on no match."""
        if not response:
            return 50.0
        match = re.search(r"\d+", response.strip())
        return max(0.0, min(100.0, float(match.group()))) if match else 50.0

    @staticmethod
    def _passthrough(candidates: list[RankedResult], top_k: int) -> list[RankedResult]:
        top = _assign_ranks(candidates[:top_k])
        for r in top:
            r.stage_scores[RankingStage.LLM_RERANKER.value] = r.score
        return top


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion merger
# ---------------------------------------------------------------------------


class RRFMerger:
    """Fuse N ranked lists: fused = sum_L weight_L * 1/(k + rank_L).

    RRF works on ranks, not raw scores, so cosine and BM25 never have to share
    a scale.
    """

    def merge(
        self,
        ranked_lists: list[list[RankedResult]],
        weights: list[float] | None = None,
        k: int = 60,
    ) -> list[RankedResult]:
        if not ranked_lists:
            return []
        weights = weights or [1.0] * len(ranked_lists)
        if len(weights) != len(ranked_lists):
            raise ValueError("weights length must match ranked_lists length")

        fused_scores: dict[str, float] = defaultdict(float)
        best: dict[str, RankedResult] = {}
        merged_stage: dict[str, dict[str, float]] = defaultdict(dict)

        for ranked_list, weight in zip(ranked_lists, weights):
            for r in ranked_list:
                fused_scores[r.entity_id] += weight * (1.0 / (k + r.rank))
                # keep the copy that has seen the most stages, so its scores survive the merge
                if (r.entity_id not in best
                        or len(r.stage_scores) > len(best[r.entity_id].stage_scores)):
                    best[r.entity_id] = r
                merged_stage[r.entity_id].update(r.stage_scores)

        out = [
            RankedResult(
                entity_id=eid,
                name=best[eid].name,
                category=best[eid].category,
                city=best[eid].city,
                score=score,
                stage_scores=merged_stage[eid],
                metadata=best[eid].metadata,
            )
            for eid, score in fused_scores.items()
        ]
        out.sort(key=lambda r: r.score, reverse=True)
        return _assign_ranks(out)


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------


@dataclass
class _StageStats:
    stage: str
    latency_ms: float
    input_count: int
    output_count: int


class RerankingPipeline:
    """Run the 4-stage funnel; stages can be selectively skipped."""

    def __init__(self, stages: list[RankingStage] | None = None) -> None:
        self.stages = stages or list(RankingStage)
        self._stage1 = Stage1DenseRetrieval()
        self._stage2 = Stage2SparseRetrieval()
        self._stage3 = Stage3CrossEncoder()
        self._stage4 = Stage4LLMReranker()
        self._merger = RRFMerger()
        self._last_stats: list[_StageStats] = []

    async def rerank(
        self,
        query: str,
        query_embedding: list[float],
        candidates: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> list[RankedResult]:
        """Run the full pipeline. Config overrides per-stage top_k, skip_stages, and rrf_weights."""
        if not candidates:
            return []
        cfg = config or {}
        skip = set(cfg.get("skip_stages", []))
        rrf_weights = cfg.get("rrf_weights", [0.6, 0.4])
        self._last_stats = []

        run_dense = self._enabled(RankingStage.DENSE_RETRIEVAL, skip)
        run_sparse = self._enabled(RankingStage.SPARSE_RETRIEVAL, skip)

        # stages 1 and 2 run together; BM25 is sync so it goes to a thread
        merged: list[RankedResult] = []
        if run_dense and run_sparse:
            t0 = time.perf_counter()
            loop = asyncio.get_running_loop()
            dense, sparse = await asyncio.gather(
                self._stage1.rank(query_embedding, candidates,
                                  cfg.get("stage1_top_k", 100)),
                loop.run_in_executor(
                    None, self._stage2.rank, query, candidates,
                    cfg.get("stage2_top_k", 50)),
                return_exceptions=True,
            )
            # one failed retriever shouldn't sink the request; fall back to the other
            dense = [] if isinstance(dense, Exception) else dense
            sparse = [] if isinstance(sparse, Exception) else sparse
            ms = (time.perf_counter() - t0) * 1000
            self._record(RankingStage.DENSE_RETRIEVAL, ms, len(candidates), len(dense))
            self._record(RankingStage.SPARSE_RETRIEVAL, ms, len(candidates), len(sparse))
            if dense and sparse:
                merged = self._merger.merge([dense, sparse], rrf_weights)
            else:
                merged = dense or sparse
        elif run_dense:
            merged = await self._timed(
                RankingStage.DENSE_RETRIEVAL, len(candidates),
                self._stage1.rank(query_embedding, candidates,
                                  cfg.get("stage1_top_k", 100)))
        elif run_sparse:
            merged = self._stage2.rank(query, candidates, cfg.get("stage2_top_k", 50))

        if not merged:
            return []

        # stage 3 then 4, each skipped at one item since there's nothing to reorder
        if self._enabled(RankingStage.CROSS_ENCODER, skip) and len(merged) > 1:
            merged = await self._timed(
                RankingStage.CROSS_ENCODER, len(merged),
                self._stage3.rank(query, merged, cfg.get("stage3_top_k", 20)))
        if self._enabled(RankingStage.LLM_RERANKER, skip) and len(merged) > 1:
            merged = await self._timed(
                RankingStage.LLM_RERANKER, len(merged),
                self._stage4.rank(query, merged, cfg.get("stage4_top_k", 10)))
        return merged

    async def rerank_fast(
        self, query: str, query_embedding: list[float],
        candidates: list[dict[str, Any]],
    ) -> list[RankedResult]:
        """Run stages 1+2 only, skipping the network calls for latency-sensitive paths."""
        return await self.rerank(
            query, query_embedding, candidates,
            config={"skip_stages": [RankingStage.CROSS_ENCODER.value,
                                    RankingStage.LLM_RERANKER.value],
                    "stage1_top_k": 50, "stage2_top_k": 50},
        )

    def get_pipeline_stats(self) -> dict[str, Any]:
        """Return per-stage latency and candidate counts from the last rerank call."""
        return {
            "stages": [
                {"stage": s.stage, "latency_ms": round(s.latency_ms, 2),
                 "input_count": s.input_count, "output_count": s.output_count}
                for s in self._last_stats
            ],
            "total_latency_ms": round(sum(s.latency_ms for s in self._last_stats), 2),
        }

    # -- helpers ----------------------------------------------------------

    def _enabled(self, stage: RankingStage, skip: set[str]) -> bool:
        return stage in self.stages and stage.value not in skip

    async def _timed(self, stage, input_count, coro):
        t0 = time.perf_counter()
        out = await coro
        self._record(stage, (time.perf_counter() - t0) * 1000, input_count, len(out))
        return out

    def _record(self, stage, ms, input_count, output_count):
        self._last_stats.append(_StageStats(stage.value, ms, input_count, output_count))


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


_RESERVED = {"embedding", "entity_id", "id", "name", "category", "city", "score"}


def _to_result(c: dict[str, Any], score: float, stage: RankingStage) -> RankedResult:
    """Build a RankedResult from a raw candidate dict; non-reserved keys go to metadata."""
    return RankedResult(
        entity_id=str(c.get("entity_id", c.get("id", ""))),
        name=c.get("name", ""),
        category=c.get("category", ""),
        city=c.get("city", ""),
        score=score,
        stage_scores={stage.value: score},
        metadata={k: v for k, v in c.items() if k not in _RESERVED},
    )


def _assign_ranks(results: list[RankedResult]) -> list[RankedResult]:
    """Assign 1-based ranks in place and return the list."""
    for i, r in enumerate(results):
        r.rank = i + 1
    return results
