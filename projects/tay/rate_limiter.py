"""Per-user rate limiter for LLM-backed routes. Portfolio excerpt, adapted.

Wraps a provider-side token-bucket primitive with route-aware defaults.
In-memory and async-safe by default; multi-instance deployments swap the
registry for a Redis-backed one without touching the surface here.

Routes call:

    from app.services.rate_limiter import enforce_user_limit
    await enforce_user_limit(user_id="...", route="narration")
"""

from __future__ import annotations

import logging
from typing import Final

from fastapi import HTTPException

logger = logging.getLogger(__name__)


# narration runs the longest LLM inference per call, so it gets the tightest
# rpm. lighter routes trade higher rpm for lower tpm.
_DEFAULT_POLICY: Final[dict[str, dict[str, int]]] = {
    "narration": {"rpm": 30, "tpm": 50_000},
    "qa": {"rpm": 60, "tpm": 30_000},
    "tts": {"rpm": 30, "tpm": 10_000},
}


# one ProviderRateLimiter per user_id. the primitive keys buckets by
# (provider, capability) only, so a single shared limiter would lump every
# device together and let one abusive client drain everyone's quota.
# bounded at _MAX_TRACKED_USERS to cap memory under high cardinality.
_MAX_TRACKED_USERS: Final[int] = 50_000
_limiters: dict[str, object] = {}


def _build_limiter():
    """Return a fresh ProviderRateLimiter, or None if the import fails."""
    try:
        from app.integrations.core_rate_limiter import (
            ProviderRateLimiter,
            RateLimitConfig,
        )
    except Exception as exc:
        logger.debug("rate_limiter import skipped (%s)", exc)
        return None

    config = {
        "tay": {
            route: RateLimitConfig(rpm=policy["rpm"], tpm=policy["tpm"])
            for route, policy in _DEFAULT_POLICY.items()
        }
    }
    return ProviderRateLimiter(config)


def _get_limiter(user_id: str):
    """Return this user's limiter, building and bounding the registry lazily."""
    limiter = _limiters.get(user_id)
    if limiter is not None:
        return limiter
    if len(_limiters) >= _MAX_TRACKED_USERS:
        # drop the whole registry instead of growing unbounded. harmless: every
        # user gets a fresh full bucket. a Redis-backed registry lifts this cap.
        _limiters.clear()
    limiter = _build_limiter()
    if limiter is None:
        return None
    _limiters[user_id] = limiter
    return limiter


async def enforce_user_limit(
    *,
    user_id: str,
    route: str,
    tokens: int = 1,
) -> None:
    """Acquire tokens from the per-route bucket for user_id.

    Raises HTTPException(429) on rate limit timeout.
    Routes without a configured policy pass through unchecked.
    """
    if route not in _DEFAULT_POLICY:
        return

    limiter = _get_limiter(user_id)
    if limiter is None:
        return

    try:
        from app.integrations.core_rate_limiter import RateLimitWaitTimeout
    except Exception:
        RateLimitWaitTimeout = RuntimeError  # type: ignore[assignment]

    try:
        # buckets within this user's limiter key on (provider="tay", route),
        # so throttling is per-user per-route
        await limiter.acquire(
            provider="tay",
            capability=route,
            tokens=tokens,
        )
    except AttributeError:
        # limiter has no acquire(): wiring bug, not a throttle. log so the
        # fail-open is visible
        logger.debug("rate limiter missing acquire(); failing open")
        return
    except RateLimitWaitTimeout as exc:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limited",
                "route": route,
                "user_id": user_id,
            },
            headers={"Retry-After": "1"},
        ) from exc
    except Exception as exc:
        # fail open: a broken limiter must never take the service down
        logger.warning("rate_limiter_unexpected_error", exc_info=exc)


__all__ = ["enforce_user_limit"]
