"""Portfolio excerpt, adapted.

Learning-to-rank for the recommendation surface.

  Input:  list of (item_id, feature_vector) for the top-K candidates
  Output: per-candidate score -> sorted list

  Primary:  LightGBM LambdaRank (listwise / pairwise).
  Fallback: weighted linear model + sigmoid, pure Python. Used whenever
            LightGBM or its model artifact is missing.

When the trained model can't load, the endpoint keeps serving with slightly
worse ordering instead of erroring out. Interaction counts are log-scaled so
a handful of power users can't dominate the score.

Feature vector:
  [two_tower_score, cosine_sim, popularity, recency, price_bucket,
   category_match, log1p(user_history_count), log1p(item_views_count)]
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RankingFeatures:
    """Dense per-candidate features for ranking."""

    two_tower_score: float = 0.0
    cosine_sim: float = 0.0
    popularity: float = 0.0
    recency_days: float = 30.0
    price_bucket: int = 0
    category_match: float = 0.0
    user_history_count: int = 0
    item_views_count: int = 0

    def to_vector(self) -> list[float]:
        return [
            self.two_tower_score,
            self.cosine_sim,
            self.popularity,
            1.0 / (1.0 + self.recency_days),
            float(self.price_bucket),
            self.category_match,
            math.log1p(self.user_history_count),
            math.log1p(self.item_views_count),
        ]


@dataclass
class RankedCandidate:
    item_id: str
    score: float
    features: RankingFeatures | None = None
    metadata: dict = field(default_factory=dict)


_DEFAULT_WEIGHTS = [
    0.30,
    0.20,
    0.15,
    0.10,
    0.05,
    0.10,
    0.05,
    0.05,
]
_DEFAULT_BIAS = 0.0


class LinearRanker:
    """Linear ranker, pure Python. Default weights are hand-set, not trained."""

    def __init__(self, weights: list[float] | None = None, bias: float = _DEFAULT_BIAS) -> None:
        self.weights = weights or list(_DEFAULT_WEIGHTS)
        self.bias = bias

    def score(self, features: RankingFeatures) -> float:
        vec = features.to_vector()
        if len(vec) != len(self.weights):
            # weights and feature layout drifted apart; bail rather than scoring garbage
            logger.warning("Feature/weight dim mismatch: %d vs %d",
                           len(vec), len(self.weights))
            return 0.0
        dot = sum(v * w for v, w in zip(vec, self.weights))
        return _sigmoid(dot + self.bias)


def _sigmoid(x: float) -> float:
    """Return the logistic sigmoid of x without overflowing exp on large |x|."""
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


class LightGBMRanker:
    """Wrap a LightGBM LambdaRank booster loaded from disk."""

    def __init__(self, model_path: str | None = None) -> None:
        self._booster: Any = None
        if model_path and Path(model_path).exists():
            self._load(model_path)

    def _load(self, path: str) -> None:
        try:
            import lightgbm as lgb

            self._booster = lgb.Booster(model_file=path)
            logger.info("LightGBM ranker loaded from %s", path)
        except Exception as exc:
            # missing lib or corrupt artifact; caller falls back to LinearRanker
            logger.warning("LightGBM load failed (%s) - using LinearRanker fallback", exc)

    def is_loaded(self) -> bool:
        return self._booster is not None

    def score(self, features: RankingFeatures) -> float:
        if not self._booster:
            return 0.0
        try:
            return float(self._booster.predict([features.to_vector()])[0])
        except Exception as exc:
            logger.warning("LightGBM predict failed: %s", exc)
            return 0.0


class Ranker:
    """Ranker with LightGBM primary and LinearRanker fallback."""

    def __init__(self, lgb_model_path: str | None = None) -> None:
        self._lgb = LightGBMRanker(model_path=lgb_model_path)
        self._linear = LinearRanker()

    def rank(
        self, candidates: list[tuple[str, RankingFeatures]]
    ) -> list[RankedCandidate]:
        """Score candidates and return them sorted by score, descending."""
        scorer = self._lgb.score if self._lgb.is_loaded() else self._linear.score
        ranked = [
            RankedCandidate(item_id=item_id, score=scorer(feats), features=feats)
            for item_id, feats in candidates
        ]
        ranked.sort(key=lambda c: c.score, reverse=True)
        return ranked
