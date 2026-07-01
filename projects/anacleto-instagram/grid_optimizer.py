"""Portfolio excerpt, adapted. Feed-grid order optimization: an MCTS search
over Instagram grid arrangements (with a greedy baseline it reuses for
pre-filtering and rollouts) that maximizes an aesthetic coherence score. This
shows the real search structure; the product itself (tuned similarity band,
penalty curve, scoring weights, and the 3x3 grid-harmony model) is stubbed
behind obvious placeholders so the excerpt reads on its own without handing
over the recipe.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np

# PLACEHOLDER weights, not the product's. Real weights split continuity into
# color, semantic, and texture channels and are tuned per account; these merely
# sum to 1.0 so the search runs.
_PLACEHOLDER_WEIGHTS: Dict[str, float] = {"continuity": 0.5, "diversity": 0.25, "aesthetic": 0.25}

def extract_feature_vectors(image_paths: Sequence[str]) -> List[np.ndarray]:
    """Stub for the real extractor. Production runs each image through color,
    texture, and semantic-embedding models and concatenates a normalized vector;
    here we return random unit vectors so the search has inputs."""
    rng = np.random.default_rng(0)
    return [v / (np.linalg.norm(v) or 1.0) for v in (rng.standard_normal(32) for _ in image_paths)]

@dataclass
class OptimizerConfig:
    """The similarity band drives the search: adjacent posts should be related
    but not near-duplicates, so a transition scores highest inside the band. The
    band values below are PLACEHOLDERS, not the tuned production band (part of
    the moat). The MCTS parameters follow the standard formulation."""

    weights: Dict[str, float] = field(default_factory=lambda: dict(_PLACEHOLDER_WEIGHTS))
    sequence_length: int = 9  # a 3x3 grid
    min_similarity: float = 0.25  # placeholder lower bound
    max_similarity: float = 0.9  # placeholder upper bound
    optimal_similarity: float = 0.5  # placeholder target (real value is tuned)
    timeout_seconds: float = 60.0
    num_simulations: int = 500
    exploration_constant: float = 1.414  # sqrt(2), the standard UCB constant
    max_children: int = 10  # cap branching per node
    prefilter_top_k: int = 20

    def validate(self) -> None:
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")

@dataclass
class FeedSequence:
    """One candidate ordering of image indices plus its coherence score."""

    indices: List[int] = field(default_factory=list)
    total_score: float = 0.0

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, idx: int) -> int:
        return self.indices[idx]

@dataclass
class OptimizationResult:
    best_sequence: FeedSequence
    sequences_evaluated: int = 0
    total_time: float = 0.0

class SimilarityMatrix:
    """Precomputed pairwise cosine similarities. The search reads transition
    scores in tight inner loops, so we pay O(n squared) once and read O(1)."""

    def __init__(self, vectors: Sequence[np.ndarray]):
        self.n = len(vectors)
        self.matrix = np.zeros((self.n, self.n))
        for i in range(self.n):
            for j in range(i, self.n):
                self.matrix[i, j] = self.matrix[j, i] = 1.0 if i == j else self._cosine(vectors[i], vectors[j])

    def get(self, i: int, j: int) -> float:
        return float(self.matrix[i, j])

    @staticmethod
    def _cosine(v1: np.ndarray, v2: np.ndarray) -> float:
        norm = np.linalg.norm(v1) * np.linalg.norm(v2)
        return float(np.dot(v1, v2) / norm) if norm else 0.0

class Scorer:
    """Shared scoring, kept off the search so any strategy can reuse it."""

    def __init__(self, config: OptimizerConfig):
        self.config = config
        # Hook for the real grid renderer plus aesthetic model. The production
        # grid scorer (its row, column, diagonal, center, and corner weights and
        # its ideal row and column similarity thresholds) is the actual moat and
        # is intentionally not reproduced here: it lives behind this callable.
        self.external_scorer: Optional[Callable[[FeedSequence], float]] = None

    def transition(self, a: int, b: int, sims: SimilarityMatrix) -> float:
        """Score one adjacency: reward similarities inside the band, penalize
        pairs too different or too alike. The shape (piecewise, peaking in the
        band) is real; the penalty constants are round placeholders, not the
        tuned falloff the product uses."""
        sim = sims.get(a, b)
        lo, hi, opt = self.config.min_similarity, self.config.max_similarity, self.config.optimal_similarity
        if sim < lo:  # too different
            return sim / lo * 0.5
        if sim > hi:  # too alike
            return 1.0 - (sim - hi) / (1.0 - hi) * 0.5
        return 1.0 - abs(sim - opt) / max(opt - lo, hi - opt) * 0.5

    def sequence(self, seq: FeedSequence, sims: SimilarityMatrix) -> FeedSequence:
        """Aggregate the coherence score for a whole ordering. The real system
        derives color, semantic, and texture continuity from feature-vector
        slices plus a grid-harmony term; here those collapse into one continuity
        signal so the blending structure stays intact while the models stay stubbed."""
        if len(seq) < 2:
            return seq
        transitions = [sims.get(seq[i], seq[i + 1]) for i in range(len(seq) - 1)]
        opt = self.config.optimal_similarity
        continuity = 1.0 - abs(float(np.mean(transitions)) - opt) / opt
        diversity = min(1.0, float(np.std(transitions)) * 2)
        aesthetic = 0.7  # stubbed aesthetic model
        w = self.config.weights
        seq.total_score = w["continuity"] * continuity + w["diversity"] * diversity + w["aesthetic"] * aesthetic
        # Blend in grid-harmony when a real scorer is wired in. The split below
        # is an illustrative placeholder, not the tuned production blend ratio.
        if self.external_scorer is not None:
            seq.total_score = seq.total_score * 0.5 + self.external_scorer(seq) * 0.5
        return seq

def greedy_prefilter(scorer: Scorer, vectors: List[np.ndarray], top_k: int) -> List[int]:
    """Shrink the search space before MCTS with a greedy baseline: from a fixed
    start take the best next image until the pool fills. The same greedy step
    drives MCTS rollouts. Real code also backfills for diversity; trimmed here."""
    n = len(vectors)
    if n <= top_k:
        return list(range(n))
    sims = SimilarityMatrix(vectors)
    order, used = [0], {0}
    while len(order) < top_k:
        nxt = max((c for c in range(n) if c not in used), key=lambda c: scorer.transition(order[-1], c, sims), default=None)
        if nxt is None:
            break
        order.append(nxt)
        used.add(nxt)
    return order

@dataclass
class MCTSNode:
    """A partial ordering plus the visit statistics UCB needs."""

    indices: List[int]
    available: Set[int]
    visits: int = 0
    total_value: float = 0.0
    parent: Optional["MCTSNode"] = None
    children: Dict[int, "MCTSNode"] = field(default_factory=dict)

    @property
    def value(self) -> float:
        return self.total_value / self.visits if self.visits else 0.0

    def ucb_score(self, c: float, parent_visits: int) -> float:
        # Unexplored nodes get infinite priority so each action is tried once.
        return math.inf if self.visits == 0 else self.value + c * math.sqrt(math.log(parent_visits) / self.visits)

    def is_terminal(self, target: int) -> bool:
        return len(self.indices) >= target or not self.available

    def expand(self, max_children: int) -> List["MCTSNode"]:
        actions = list(self.available)
        if len(actions) > max_children:
            actions = random.sample(actions, max_children)
        for action in actions:
            self.children.setdefault(action, MCTSNode(self.indices + [action], self.available - {action}, parent=self))
        return list(self.children.values())

class MCTSOptimizer:
    """Global search for cases where a locally weak early choice sets up a
    stronger overall grid. Four-phase loop: select by UCB, expand, roll out,
    backpropagate. Greedy pre-filters the candidate pool first."""

    def __init__(self, config: OptimizerConfig):
        self.config = config
        self.scorer = Scorer(config)

    def optimize(self, feature_vectors: List[np.ndarray]) -> OptimizationResult:
        start = time.time()
        n = len(feature_vectors)
        target = min(self.config.sequence_length, n)
        candidates = (
            greedy_prefilter(self.scorer, feature_vectors, self.config.prefilter_top_k)
            if n > self.config.prefilter_top_k
            else list(range(n))
        )
        sims = SimilarityMatrix([feature_vectors[i] for i in candidates])
        idx_map = dict(enumerate(candidates))
        root = MCTSNode(indices=[], available=set(range(len(candidates))))
        best_rollout: Optional[FeedSequence] = None
        evaluated = 0
        for _ in range(self.config.num_simulations):
            if time.time() - start > self.config.timeout_seconds:
                break
            node = self._select(root)
            if not node.is_terminal(target) and node.visits > 0:
                children = node.expand(self.config.max_children)
                if children:
                    node = random.choice(children)
            indices, value = self._rollout(node, target, sims)
            evaluated += 1
            if best_rollout is None or value > best_rollout.total_score:
                best_rollout = FeedSequence(indices=indices, total_score=value)
            self._backpropagate(node, value)
        # Most-visited path is the robust MCTS pick; fall back to the best
        # rollout if the tree path came out incomplete (e.g. immediate timeout).
        best = FeedSequence(indices=list(self._best_path(root).indices))
        if len(best) < target and best_rollout is not None:
            best = best_rollout
        best.indices = [idx_map[i] for i in best.indices]
        self.scorer.sequence(best, SimilarityMatrix(feature_vectors))
        return OptimizationResult(best, sequences_evaluated=evaluated, total_time=time.time() - start)

    def _select(self, root: MCTSNode) -> MCTSNode:
        node = root
        while node.children and not node.is_terminal(self.config.sequence_length):
            node = max(node.children.values(), key=lambda c: c.ucb_score(self.config.exploration_constant, node.visits))
        return node

    def _rollout(self, node: MCTSNode, target: int, sims: SimilarityMatrix) -> Tuple[List[int], float]:
        """Play the ordering out to full length greedily, then score it."""
        indices, available = list(node.indices), set(node.available)
        while len(indices) < target and available:
            nxt = max(available, key=lambda c: self.scorer.transition(indices[-1], c, sims)) if indices else random.choice(list(available))
            indices.append(nxt)
            available.discard(nxt)
        return indices, self.scorer.sequence(FeedSequence(indices=indices), sims).total_score

    @staticmethod
    def _backpropagate(node: Optional[MCTSNode], value: float) -> None:
        while node is not None:
            node.visits += 1
            node.total_value += value
            node = node.parent

    @staticmethod
    def _best_path(root: MCTSNode) -> MCTSNode:
        node = root
        while node.children:  # most-visited child, less noisy than raw value
            node = max(node.children.values(), key=lambda c: c.visits)
        return node

def optimize_feed(image_paths: Sequence[str], config: Optional[OptimizerConfig] = None) -> OptimizationResult:
    """Extract features for the images, then search for the best grid ordering."""
    cfg = config or OptimizerConfig()
    cfg.validate()
    return MCTSOptimizer(cfg).optimize(extract_feature_vectors(image_paths))

if __name__ == "__main__":
    # Tiny demo on stub features so the search runs end to end. Real usage passes
    # image paths and a tuned config; the order here is arbitrary because the
    # feature extractor is stubbed.
    result = optimize_feed([f"post_{i}.jpg" for i in range(12)])
    print(f"order={result.best_sequence.indices} score={result.best_sequence.total_score:.3f}")