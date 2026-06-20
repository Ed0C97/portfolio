"""Portfolio excerpt, adapted.

Hybrid entity search: dense vibe vectors plus sparse keyword scroll, fused with
Reciprocal Rank Fusion.

This searches entities (venues with a vibe vector, tags, city/category filters),
not RAG chunks. Each result keeps the full entity payload so it can feed ranking
and recommendation UIs without a second lookup.

RRF avoids putting a cosine score and a keyword score on the same scale: it ranks
each source independently and combines by rank position.

    score = w_v * 1/(k + rank_vector) + w_k * 1/(k + rank_keyword)

k=60 is the constant from the original RRF paper.

The vector store sits behind a Protocol so this file reads standalone; production
backs it with Qdrant.
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections import defaultdict
from typing import Any, Protocol

logger = logging.getLogger(__name__)

# RRF constant from the original paper; smaller k weights the top ranks harder
RRF_K = 60


class VectorStore(Protocol):
    """Async vector-store surface for dense and sparse search."""

    async def vector_query(
        self, vector: list[float], flt: dict | None, limit: int
    ) -> list[dict]: ...

    async def keyword_scroll(
        self, text: str, flt: dict | None, limit: int
    ) -> list[dict]: ...


class HybridSearch:
    """Fuse semantic and exact-match results via RRF."""

    def __init__(self, store: VectorStore, collection: str = "entities_vectors"):
        self._store = store
        self.collection = collection

    async def search_rrf(
        self,
        query_vector: list[float],
        query_text: str,
        limit: int = 10,
        category: str | None = None,
        city: str | None = None,
        vector_weight: float = 0.5,
        keyword_weight: float = 0.5,
        prefetch_multiplier: int = 5,
    ) -> list[dict]:
        """Return the top results fused from vector and keyword search.

        prefetch_multiplier over-fetches from each source so the two ranked
        lists overlap enough for fusion to matter.
        """
        flt: dict[str, Any] | None = None
        conditions = []
        if category:
            conditions.append({"key": "category", "value": category})
        if city:
            conditions.append({"key": "city", "value": city})
        if conditions:
            flt = {"must": conditions}

        prefetch_limit = limit * prefetch_multiplier

        # run both legs concurrently; one failing must not sink the other
        vector_results, keyword_results = await asyncio.gather(
            self._vector_search(query_vector, flt, prefetch_limit),
            self._keyword_search(query_text, flt, prefetch_limit),
            return_exceptions=True,
        )
        if isinstance(vector_results, Exception):
            logger.warning("Vector search failed: %s", vector_results)
            vector_results = []
        if isinstance(keyword_results, Exception):
            logger.warning("Keyword search failed: %s", keyword_results)
            keyword_results = []

        fused = self._rrf_fusion(
            vector_results, keyword_results, vector_weight, keyword_weight
        )
        final = fused[:limit]
        logger.info(
            "RRF hybrid: %d vector + %d keyword -> %d fused for: %s",
            len(vector_results),
            len(keyword_results),
            len(final),
            query_text[:50],
        )
        return final

    async def _vector_search(
        self, query_vector: list[float], flt: dict | None, limit: int
    ) -> list[dict]:
        """Return formatted dense vector search results."""
        try:
            points = await self._store.vector_query(query_vector, flt, limit)
            return [self._format_result(p) for p in points]
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Vector search error: %s", exc)
            return []

    async def _keyword_search(
        self, query_text: str, flt: dict | None, limit: int
    ) -> list[dict]:
        """Return formatted keyword search results."""
        try:
            points = await self._store.keyword_scroll(query_text, flt, limit)
            # keyword hits are exact; flatten to a uniform score so only RRF rank carries the signal
            return [self._format_result(p, score=1.0) for p in points]
        except Exception as exc:
            logger.debug("Keyword search unavailable or failed: %s", exc)
            return []

    def _rrf_fusion(
        self,
        vector_results: list[dict],
        keyword_results: list[dict],
        vector_weight: float,
        keyword_weight: float,
    ) -> list[dict]:
        """Return entities ranked by fused RRF score.

        An entity in both lists accumulates both contributions, so a strong
        showing in either source is enough to rank it.
        """
        fused: dict[str, dict[str, Any]] = {}

        for rank, result in enumerate(vector_results, start=1):
            eid = result["id"]
            rrf = vector_weight * (1.0 / (RRF_K + rank))
            if eid not in fused:
                fused[eid] = {**result, "rrf_score": rrf,
                              "vector_rank": rank, "keyword_rank": None}
            else:
                fused[eid]["rrf_score"] += rrf
                fused[eid]["vector_rank"] = rank

        for rank, result in enumerate(keyword_results, start=1):
            eid = result["id"]
            rrf = keyword_weight * (1.0 / (RRF_K + rank))
            if eid not in fused:
                fused[eid] = {**result, "rrf_score": rrf,
                              "vector_rank": None, "keyword_rank": rank}
            else:
                fused[eid]["rrf_score"] += rrf
                fused[eid]["keyword_rank"] = rank

        return sorted(fused.values(), key=lambda x: x["rrf_score"], reverse=True)

    @staticmethod
    def _format_result(point: dict, score: float | None = None) -> dict:
        """Normalize a raw vector-store point into a result dict."""
        payload = point.get("payload", {})
        return {
            "id": str(point.get("id", "")),
            "score": score if score is not None else point.get("score", 0.0),
            "name": payload.get("name", ""),
            "category": payload.get("category", ""),
            "city": payload.get("city", ""),
            "price_tier": payload.get("price_tier"),
            "dimensions": payload.get("dimensions", {}),
            "tags": payload.get("tags", []),
            "payload": payload,
        }


class EntityResolver:
    """Deduplicate entities across sources and merge their metadata.

    One place can surface from the vector store, the relational DB, and the
    graph. Collapse by entity_uuid first, then fuzzy-match normalized names,
    merging metadata by source priority.
    """

    # higher wins when two sources disagree on a field
    SOURCE_PRIORITY = {"neo4j": 3, "postgres": 2, "vector": 1}

    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold

    def resolve(self, results: list[dict], source: str = "vector") -> list[dict]:
        """Return deduplicated entities with merged metadata."""
        if not results:
            return []

        uuid_groups: dict[str, list[dict]] = defaultdict(list)
        no_uuid: list[dict] = []
        for r in results:
            uuid = r.get("entity_uuid") or r.get("payload", {}).get("entity_uuid")
            (uuid_groups[uuid].append(r) if uuid else no_uuid.append(r))

        resolved: list[dict] = []
        for uuid, group in uuid_groups.items():
            merged = self._merge_group(group, source)
            merged["entity_uuid"] = uuid
            resolved.append(merged)

        # entities with no uuid fall back to name matching against what's resolved
        for entity in no_uuid:
            normalized = self._normalize_name(entity.get("name", ""))
            for existing in resolved:
                if self._is_similar(normalized,
                                     self._normalize_name(existing.get("name", ""))):
                    self._merge_into(existing, entity, source)
                    break
            else:
                resolved.append(entity)

        return resolved

    def _merge_group(self, group: list[dict], source: str) -> dict:
        """Merge known duplicates, preferring higher-priority sources."""
        if len(group) == 1:
            return group[0].copy()
        ordered = sorted(
            group,
            key=lambda x: self.SOURCE_PRIORITY.get(x.get("source", source), 0),
            reverse=True,
        )
        merged = ordered[0].copy()
        for entity in ordered[1:]:
            self._merge_into(merged, entity, source)
        return merged

    @staticmethod
    def _merge_into(target: dict, src: dict, source: str) -> None:
        """Fill missing fields in target from src; union tags and dimensions."""
        for key, value in src.items():
            if key not in target or target[key] is None:
                target[key] = value
            elif key == "tags" and isinstance(value, list):
                target["tags"] = list(set(target.get("tags", [])) | set(value))
            elif key == "dimensions" and isinstance(value, dict):
                target.setdefault("dimensions", {}).update(value)

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Lowercase, strip punctuation, collapse whitespace."""
        name = re.sub(r"[^\w\s]", "", name.lower())
        return re.sub(r"\s+", " ", name).strip()

    def _is_similar(self, name1: str, name2: str) -> bool:
        """Return True if word-level Jaccard similarity meets the threshold."""
        words1, words2 = set(name1.split()), set(name2.split())
        if not words1 or not words2:
            return False
        jaccard = len(words1 & words2) / len(words1 | words2)
        return jaccard >= self.similarity_threshold
