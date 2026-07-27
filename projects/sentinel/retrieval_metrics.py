"""Information-retrieval metrics for the evaluation harness: pure Python.

Canonical definitions that the offline eval harness and the Prometheus
exporters both key off, so a number quoted in a report and a number on a
dashboard are computed by the same code:

    precision_at_k   |retrieved_k intersect relevant| / |retrieved_k|
    recall_at_k      |retrieved_k intersect relevant| / |relevant|
    reciprocal_rank  1 / rank_of_first_relevant   (0 if none in top-k)
    dcg_at_k         sum rel_i / log2(i + 1)      (binary relevance)
    ndcg_at_k        dcg_at_k / ideal_dcg_at_k
    mean_*           unweighted mean across a list of queries

Two decisions worth stating, because both are places where IR metric
implementations quietly disagree with each other:

1.  **Duplicates are collapsed before truncation.** A retriever that fuses
    several channels (keyword, dense, graph) can legitimately return the
    same chunk id from more than one channel. Counting it twice inflates
    precision and hides a fusion bug. `_unique_prefix` takes the first *k*
    *distinct* ids in rank order, so the metric measures distinct evidence
    rather than retriever chattiness.

2.  **precision_at_k divides by the number of results actually returned,
    not by k.** When a query returns fewer than *k* results, dividing by
    *k* charges the system for documents it never claimed to have found,
    which makes precision drift with corpus size rather than with ranking
    quality. Recall still divides by the size of the relevant set, which
    is where a short result list should be penalised.

The helpers take `retrieved` as an ordered iterable of ids and `relevant`
as an iterable of gold ids. They assume nothing about the retrieval system:
the caller produces the id lists, the metrics stay scheme-agnostic.

Portfolio excerpt: standalone, no project imports, no external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log2
from typing import Iterable, List, Sequence


def _unique_prefix(retrieved: Sequence[str], k: int) -> List[str]:
    """Return the first *k* distinct ids from *retrieved*, preserving rank order."""
    seen = set()
    out: List[str] = []
    for item in retrieved:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
        if len(out) == k:
            break
    return out


def precision_at_k(retrieved: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """Fraction of the distinct top-*k* results that are relevant.

    Denominator is the number of distinct results actually returned, capped
    at *k*: see decision 2 in the module docstring.
    """
    if k <= 0:
        raise ValueError("k must be positive")
    rel = set(relevant)
    if not rel:
        return 0.0
    top = _unique_prefix(retrieved, k)
    if not top:
        return 0.0
    hits = sum(1 for item in top if item in rel)
    return hits / float(len(top))


def recall_at_k(retrieved: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """Fraction of the relevant set recovered within the distinct top-*k*."""
    if k <= 0:
        raise ValueError("k must be positive")
    rel = set(relevant)
    if not rel:
        return 0.0
    hits = sum(1 for item in _unique_prefix(retrieved, k) if item in rel)
    return hits / float(len(rel))


def reciprocal_rank(retrieved: Sequence[str], relevant: Iterable[str], k: int = 0) -> float:
    """Reciprocal rank of the first relevant item.

    With *k* > 0 the search is restricted to the distinct top-*k*; with the
    default *k* = 0 the whole list is considered. Returns 0.0 when nothing
    relevant appears, which is the conventional "no credit" encoding and
    keeps the mean well defined over queries that miss entirely.
    """
    rel = set(relevant)
    if not rel:
        return 0.0
    pool = _unique_prefix(retrieved, k) if k > 0 else list(retrieved)
    for rank, item in enumerate(pool, start=1):
        if item in rel:
            return 1.0 / rank
    return 0.0


def dcg_at_k(retrieved: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """Discounted cumulative gain over the distinct top-*k*, binary relevance."""
    if k <= 0:
        raise ValueError("k must be positive")
    rel = set(relevant)
    if not rel:
        return 0.0
    score = 0.0
    for position, item in enumerate(_unique_prefix(retrieved, k), start=1):
        if item in rel:
            score += 1.0 / log2(position + 1)
    return score


def ndcg_at_k(retrieved: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """DCG normalised by the best achievable DCG for this relevant set.

    The ideal DCG is computed over ``min(len(relevant), k)`` positions, so a
    query with fewer relevant documents than *k* can still reach 1.0 instead
    of being permanently capped below it.
    """
    if k <= 0:
        raise ValueError("k must be positive")
    rel = set(relevant)
    if not rel:
        return 0.0
    dcg = dcg_at_k(retrieved, rel, k)
    ideal_positions = min(len(rel), k)
    idcg = sum(1.0 / log2(position + 1) for position in range(1, ideal_positions + 1))
    return dcg / idcg if idcg > 0 else 0.0


# ---------------------------------------------------------------------------
# Aggregation across a query set
# ---------------------------------------------------------------------------


@dataclass
class QueryResult:
    """One evaluated query: what the retriever returned, and what was gold."""

    retrieved: Sequence[str]
    relevant: Sequence[str]


def mean_precision_at_k(queries: Sequence[QueryResult], k: int) -> float:
    if not queries:
        return 0.0
    return sum(precision_at_k(q.retrieved, q.relevant, k) for q in queries) / len(queries)


def mean_recall_at_k(queries: Sequence[QueryResult], k: int) -> float:
    if not queries:
        return 0.0
    return sum(recall_at_k(q.retrieved, q.relevant, k) for q in queries) / len(queries)


def mean_reciprocal_rank(queries: Sequence[QueryResult], k: int = 0) -> float:
    if not queries:
        return 0.0
    return sum(reciprocal_rank(q.retrieved, q.relevant, k) for q in queries) / len(queries)


def mean_ndcg_at_k(queries: Sequence[QueryResult], k: int) -> float:
    if not queries:
        return 0.0
    return sum(ndcg_at_k(q.retrieved, q.relevant, k) for q in queries) / len(queries)


__all__ = [
    "QueryResult",
    "dcg_at_k",
    "mean_ndcg_at_k",
    "mean_precision_at_k",
    "mean_recall_at_k",
    "mean_reciprocal_rank",
    "ndcg_at_k",
    "precision_at_k",
    "recall_at_k",
    "reciprocal_rank",
]
