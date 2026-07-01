"""Portfolio excerpt, adapted. Feed-grid order optimizer.

Anacleto arranges a set of posts into the Instagram feed grid so that the visual
whole reads as coherent, not just each post in isolation. This is a permutation
search: for n posts there are n! orderings, so we cannot enumerate. This file
ships two interchangeable search strategies behind one interface, matching the
project's "MCTS / Beam / Greedy" design:

  Greedy: nearest-neighbour construction from every seed, O(n^3) pair scoring,
          good enough for the small feeds this path targets.
  Beam:   keeps the best `beam_width` partial arrangements at each step and
          extends them, trading time for arrangement quality.

The aesthetic scorer is INJECTED as a Protocol. Only an obvious illustrative
placeholder ships here. The real scorer (color-harmony, composition, flow,
balance, and theme dimensions, their weights, and the CNN/color feature
extraction behind them) is the product moat and stays private.

The scoring contract is deliberately incremental: score_pair(a, b) rates the
adjacency of two posts, and score_arrangement(order) rates a whole (possibly
partial) ordering. Beam search leans on the pairwise delta so extending a
partial arrangement costs one pair evaluation, not a full rescore.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Post:
    """A candidate post. `features` is an opaque handle the scorer understands.

    The engine fills `features` with extracted color/composition vectors. Nothing
    in this file inspects it; only the injected scorer does, which keeps feature
    extraction out of the portfolio excerpt.
    """

    post_id: str
    features: object = None


class AestheticScorer(Protocol):
    """Scores how coherent a feed arrangement looks. Higher is better.

    score_pair is bounded (the placeholder returns a value in [0, 1]) and is
    treated as the marginal contribution of placing `b` immediately after `a`.
    score_arrangement is the sum of the adjacent pair scores along the ordering,
    so it is not bounded to [0, 1]: it grows with length, up to (len - 1) times
    the per-pair maximum. Beam search relies on that additive decomposition, so
    score_arrangement must stay consistent with score_pair or beam pruning would
    compare running scores that no longer mean the same thing.
    """

    def score_pair(self, a: Post, b: Post) -> float:
        """Rate the visual adjacency of two neighbouring posts, in [0, 1]."""
        ...

    def score_arrangement(self, order: Sequence[Post]) -> float:
        """Sum score_pair over adjacent posts. Orders under length 2 score 0."""
        ...


class PlaceholderScorer:
    """Illustrative scorer only. NOT the real aesthetic model.

    It rewards adjacency between posts whose id digests differ in their low bit,
    a stand-in "contrast" signal that makes the demo produce a visibly
    non-trivial ordering. The production scorer replaces this with the real
    color-harmony, composition, flow, balance, and theme dimensions and their
    tuned weights. Those are omitted from this excerpt.
    """

    @staticmethod
    def _digest_bit(post_id: str) -> int:
        # A stable per-id bit. We use blake2b rather than the builtin hash() so
        # the signal (and therefore the demo output) is reproducible across
        # processes; hash() of a str is salted by PYTHONHASHSEED and varies run
        # to run, which would undercut the deterministic framing of the search.
        digest = hashlib.blake2b(post_id.encode("utf-8"), digest_size=8).digest()
        return digest[0] & 1

    def score_pair(self, a: Post, b: Post) -> float:
        # Reward neighbours whose id digests disagree in the low bit: an
        # alternating pattern reads as "contrast" for this illustrative signal.
        contrast = self._digest_bit(a.post_id) ^ self._digest_bit(b.post_id)
        return 1.0 if contrast else 0.25

    def score_arrangement(self, order: Sequence[Post]) -> float:
        if len(order) < 2:
            return 0.0
        return sum(
            self.score_pair(order[i], order[i + 1]) for i in range(len(order) - 1)
        )


@dataclass(frozen=True, slots=True)
class Arrangement:
    """A scored ordering of posts. `score` is the coherence of `order`."""

    order: tuple[Post, ...]
    score: float


class SearchStrategy(Protocol):
    """A pluggable order-search algorithm. The engine picks one at runtime."""

    def search(self, posts: Sequence[Post], scorer: AestheticScorer) -> Arrangement:
        ...


class GreedySearch:
    """Nearest-neighbour construction. Fast path for small feeds.

    Start from each possible first post, then repeatedly append the unused post
    with the best pairwise score against the current tail. Restarting from every
    seed costs O(n^3) pair evaluations (n seeds, each an O(n^2) construction) but
    removes the first-move bias a single seed would bake in; for the small n this
    feature targets that is cheap.
    """

    def search(self, posts: Sequence[Post], scorer: AestheticScorer) -> Arrangement:
        items = list(posts)
        if len(items) < 2:
            return Arrangement(tuple(items), 0.0)

        best: Arrangement | None = None
        for seed in items:
            order = [seed]
            remaining = [p for p in items if p is not seed]
            while remaining:
                tail = order[-1]
                # deterministic tie-break: pick the highest pair score, and on a
                # tie the lexicographically smaller id, so runs are reproducible.
                # min() over (-score, id) gives "max score, then smallest id".
                nxt = min(
                    remaining,
                    key=lambda p, tail=tail: (-scorer.score_pair(tail, p), p.post_id),
                )
                order.append(nxt)
                remaining.remove(nxt)
            candidate = Arrangement(tuple(order), scorer.score_arrangement(order))
            if best is None or _better(candidate, best):
                best = candidate
        assert best is not None
        return best


class BeamSearch:
    """Beam search over feed orderings.

    State is a partial arrangement plus its running pairwise score. At each step
    every beam entry is extended by each unused post; we keep the top
    `beam_width` by running score. Because score is additive over adjacent pairs,
    extending costs a single score_pair call, and the running score is exact for
    the partial order (no rescore needed).

    Pruning is the whole point: without the width cap this degrades to breadth
    first over n! leaves. Ties are broken deterministically so results are
    reproducible and the beam does not silently reorder equal-scoring states.
    """

    def __init__(self, beam_width: int = 8) -> None:
        if beam_width < 1:
            raise ValueError("beam_width must be at least 1")
        self.beam_width = beam_width

    def search(self, posts: Sequence[Post], scorer: AestheticScorer) -> Arrangement:
        items = list(posts)
        n = len(items)
        if n < 2:
            return Arrangement(tuple(items), 0.0)

        # a beam entry: (running_score, used_index_mask, order_tuple)
        # the bitmask makes "which posts are still placed" an O(1) membership
        # test, cheaper than scanning the order tuple on every expansion.
        beam: list[tuple[float, int, tuple[Post, ...]]] = [
            (0.0, 1 << i, (items[i],)) for i in range(n)
        ]

        for _ in range(n - 1):
            expanded: list[tuple[float, int, tuple[Post, ...]]] = []
            for running, mask, order in beam:
                tail = order[-1]
                for i in range(n):
                    if mask & (1 << i):
                        continue  # post i already placed on this path
                    step = scorer.score_pair(tail, items[i])
                    expanded.append(
                        (running + step, mask | (1 << i), order + (items[i],))
                    )
            beam = self._prune(expanded)

        # every beam entry is now a complete permutation; the running score is
        # the exact additive arrangement score, so no final rescore is needed
        top = beam[0]
        return Arrangement(top[2], top[0])

    def _prune(
        self, entries: list[tuple[float, int, tuple[Post, ...]]]
    ) -> list[tuple[float, int, tuple[Post, ...]]]:
        # sort by score descending, then by a stable order key so equal-scoring
        # arrangements keep a fixed, reproducible ranking across runs
        entries.sort(key=lambda e: (-e[0], _order_key(e[2])))
        return entries[: self.beam_width]


class GridOptimizer:
    """Facade: pick a strategy, inject a scorer, get the best feed order."""

    def __init__(
        self,
        strategy: SearchStrategy | None = None,
        scorer: AestheticScorer | None = None,
    ) -> None:
        self.strategy: SearchStrategy = strategy or BeamSearch()
        self.scorer: AestheticScorer = scorer or PlaceholderScorer()

    def optimize(self, posts: Sequence[Post]) -> Arrangement:
        """Return the highest-scoring ordering the chosen strategy found."""
        return self.strategy.search(posts, self.scorer)


def _better(a: Arrangement, b: Arrangement) -> bool:
    """Total order on arrangements: score first, then a stable id tie-break."""
    if a.score != b.score:
        return a.score > b.score
    return _order_key(a.order) < _order_key(b.order)


def _order_key(order: Sequence[Post]) -> tuple[str, ...]:
    return tuple(p.post_id for p in order)


if __name__ == "__main__":
    # The placeholder scorer is fully deterministic (stable digest, no salted
    # hash()), so this output is identical across processes and runs.
    demo_posts = [Post(post_id=f"p{i}") for i in range(6)]
    optimizer = GridOptimizer(strategy=BeamSearch(beam_width=4))
    result = optimizer.optimize(demo_posts)
    print("order:", [p.post_id for p in result.order], "score:", result.score)

    # the greedy fast path over the same posts and scorer, for comparison
    greedy = GridOptimizer(strategy=GreedySearch())
    fast = greedy.optimize(demo_posts)
    print("greedy:", [p.post_id for p in fast.order], "score:", fast.score)
