"""Periodic C2 beaconing detector. Portfolio excerpt, adapted.

Command-and-control implants often "call home" on a fixed cadence (every 30s,
every 5min), so the connections to one destination land at almost-regular
intervals. This scores that regularity from the coefficient of variation of the
inter-arrival gaps: CV = std / mean. A low CV means the gaps barely vary, which
is beacon-like; jittered or human traffic has a high CV. This is the cheap,
interpretable signal that runs before (and as a fallback for) the trained
anomaly model, which is omitted from this excerpt.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class BeaconVerdict:
    """Outcome of scoring one (source, destination) connection series."""

    is_beacon: bool
    score: float  # regularity in [0, 1]; 1.0 is a perfectly periodic series
    mean_interval_s: float  # average gap between connections, seconds
    jitter_s: float  # standard deviation of the gaps, seconds
    event_count: int
    reason: str  # why we decided as we did (useful in the finding payload)


# Defaults are illustrative, not tuned against a real corpus. The real system
# learns these per environment; a noisy LAN tolerates a higher CV than a quiet
# server segment.
_MIN_EVENTS = 6
_DEFAULT_THRESHOLD = 0.75
_JITTER_TOLERANCE_S = 0.0


def _intervals(timestamps: list[float]) -> list[float]:
    """Inter-arrival gaps between consecutive, time-sorted timestamps.

    We sort defensively: eBPF ring-buffer events can arrive slightly out of
    order across CPUs, and a single negative gap would corrupt the statistics.
    """
    ordered = sorted(timestamps)
    return [b - a for a, b in zip(ordered, ordered[1:])]


def _coefficient_of_variation(values: list[float]) -> tuple[float, float, float]:
    """Return (mean, population std, CV) for a non-empty list.

    Uses the population standard deviation (divide by N, not N-1): we are
    describing the spread of the sample we actually observed, not estimating a
    wider population, so Bessel's correction would only add noise on short
    series. CV is undefined when the mean is zero and is reported as infinity.
    """
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    std = math.sqrt(variance)
    cv = std / mean if mean > 0.0 else math.inf
    return mean, std, cv


def _apply_jitter_tolerance(intervals: list[float], tolerance_s: float) -> list[float]:
    """Snap gaps that sit within tolerance of the mean back to the mean.

    A real beacon adds random jitter (say plus or minus a few hundred ms) so it
    is not trivially periodic. Snapping toward the mean gap absorbs symmetric
    wobble on both sides of the cadence, which is what shrinks the CV: a raw CV
    treats a plus-0.7s gap and a minus-0.7s gap as two separate deviations even
    though they cancel in intent. Gaps outside the band are left untouched, so
    genuinely irregular traffic still scores as irregular.

    Limitation worth naming: this is a one-pass snap around the original mean,
    not iterated re-centering, so it flattens jitter up to tolerance_s but does
    not model the cadence itself. A drifting or multi-modal beacon needs the
    trained model, not this cheap pre-filter.
    """
    if tolerance_s <= 0.0 or len(intervals) < 2:
        return intervals
    mean = sum(intervals) / len(intervals)
    return [
        mean if abs(gap - mean) <= tolerance_s else gap
        for gap in intervals
    ]


def score_beaconing(
    timestamps: list[float],
    *,
    threshold: float = _DEFAULT_THRESHOLD,
    min_events: int = _MIN_EVENTS,
    jitter_tolerance_s: float = _JITTER_TOLERANCE_S,
) -> BeaconVerdict:
    """Score a series of connection timestamps for periodic beaconing.

    timestamps are epoch seconds (float) for connections from one source to one
    destination, in any order. threshold is the minimum regularity score at
    which we flag a beacon.

    The score maps CV onto [0, 1] as 1 / (1 + CV): CV = 0 (perfectly periodic)
    gives 1.0, CV = 1 gives 0.5, and it decays smoothly toward 0 as the gaps get
    more chaotic. This is monotonic and bounded, which keeps the threshold easy
    to reason about, unlike a raw CV cutoff.
    """
    count = len(timestamps)

    # A beacon needs enough repetitions to be a pattern rather than a
    # coincidence. Two connections give exactly one interval and a CV of zero,
    # which would look like a perfect beacon, so we refuse to score short series.
    if count < max(min_events, 2):
        return BeaconVerdict(
            is_beacon=False,
            score=0.0,
            mean_interval_s=0.0,
            jitter_s=0.0,
            event_count=count,
            reason=f"too few events ({count} < {max(min_events, 2)})",
        )

    intervals = _intervals(timestamps)
    intervals = _apply_jitter_tolerance(intervals, jitter_tolerance_s)
    mean, std, cv = _coefficient_of_variation(intervals)

    # Coincident timestamps (a burst with mean gap 0) are not a periodic beacon;
    # they are usually a connection storm and belong to a different rule.
    if mean <= 0.0:
        return BeaconVerdict(
            is_beacon=False,
            score=0.0,
            mean_interval_s=0.0,
            jitter_s=std,
            event_count=count,
            reason="zero mean interval (coincident timestamps)",
        )

    score = 1.0 / (1.0 + cv)
    is_beacon = score >= threshold

    return BeaconVerdict(
        is_beacon=is_beacon,
        score=score,
        mean_interval_s=mean,
        jitter_s=std,
        event_count=count,
        reason=(
            f"regularity {score:.3f} {'>=' if is_beacon else '<'} "
            f"threshold {threshold:.3f} (CV={cv:.3f})"
        ),
    )


if __name__ == "__main__":
    import time

    # A 60-second beacon with plus/minus 0.7s of jitter versus bursty human
    # browsing. The offsets make alternating gaps of 60.7s and 59.3s, each 0.7s
    # off the 60.0s mean, so a tolerance of 1.0s snaps every gap back to the
    # mean and lifts the regularity score above the raw-gap score below it.
    base = time.time()
    beacon = [base + i * 60.0 + (0.4 if i % 2 else -0.3) for i in range(12)]
    human = [base, base + 3, base + 5, base + 40, base + 41, base + 300, base + 700]

    print("beacon, raw gaps: ", score_beaconing(beacon).reason)
    print("beacon, tol=1.0s: ", score_beaconing(beacon, jitter_tolerance_s=1.0).reason)
    print("human browsing:   ", score_beaconing(human).reason)
