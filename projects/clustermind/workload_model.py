# Portfolio excerpt, adapted. Trimmed from ClusterMind (private) to read standalone.
# The real project imports its Survey/WorkloadModel/EndpointClass dataclasses; those
# are stubbed locally below so this file stands alone.
"""Convert operator inputs to headline traffic numbers.

Takes volume and shape (DAU, requests per user, peaking factor, growth rate,
horizon) and returns average/peak RPS at the horizon, split by traffic class.
Pure and deterministic: no I/O, randomness, or clock. Rates are requests per
second throughout.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field

SECONDS_PER_DAY = 86_400.0


# local stubs; the real project defines these with more fields


@dataclass
class EndpointClass:
    """One class of traffic, e.g. read, write, inference."""

    name: str
    share: float = 0.0  # fraction of peak traffic, normalized later
    triggers_inference: bool = False


@dataclass
class WorkloadModel:
    """Operator-provided volume and shape inputs.

    average_rps/peak_rps default to None so an explicit 0.0 reads as "no traffic"
    instead of falling back to the DAU derivation.
    """

    dau: float = 0.0
    requests_per_user_per_day: float = 0.0
    peak_to_average_ratio: float = 1.0
    growth_rate_monthly: float = 0.0
    horizon_months: int = 0
    average_rps: float | None = None
    peak_rps: float | None = None


def per_day_to_rps(events_per_day: float) -> float:
    """Convert a per-day rate to per-second."""
    return events_per_day / SECONDS_PER_DAY


# the actual workload math


def normalize_shares(classes: list[EndpointClass]) -> list[EndpointClass]:
    """Return copies of classes with shares rescaled to sum to 1.0.

    Inputs are never mutated. Zero or non-positive total splits the weight equally;
    empty input returns an empty list.
    """
    if not classes:
        return []

    total = sum(c.share for c in classes)
    n = len(classes)

    if total > 0.0:
        return [dataclasses.replace(c, share=c.share / total) for c in classes]

    # nothing to scale against, so weight everything the same
    equal = 1.0 / n
    return [dataclasses.replace(c, share=equal) for c in classes]


def derive_average_rps(w: WorkloadModel) -> float:
    """Return average RPS, from average_rps if set else dau * requests/86400.

    An explicit average_rps of 0.0 wins over the DAU derivation.
    """
    if w.average_rps is not None:
        return w.average_rps
    requests_per_day = w.dau * w.requests_per_user_per_day
    return per_day_to_rps(requests_per_day)


def derive_peak_rps(w: WorkloadModel) -> float:
    """Return peak RPS, from peak_rps if set else average scaled by the peaking factor."""
    if w.peak_rps is not None:
        return w.peak_rps
    return derive_average_rps(w) * w.peak_to_average_ratio


def project_growth(value: float, monthly_rate: float, months: int) -> float:
    """Compound value over months at a fractional monthly rate (0.10 means +10%/month)."""
    return value * (1.0 + monthly_rate) ** months
