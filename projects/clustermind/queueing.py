# Portfolio excerpt, adapted from ClusterMind (private). Trimmed for standalone reading.
# Deterministic queueing-theory primitives used by the capacity tier-sizing layer.
"""Deterministic M/M/c queueing primitives for capacity planning.

Pure, side-effect-free, fully deterministic.

Units:
    arrival_rate_rps / service_rate_rps  requests per second
    service_time_s                       mean service demand per request, seconds
    servers / parallelism                integer count of parallel channels
    utilizations / probabilities         dimensionless fractions in [0, 1]

For c servers each completing mu = 1/S requests per second: offered load
a = lambda * S erlangs, per-server utilization rho = a / c. Stable iff a < c.
When a >= c the queue grows unbounded; every waiting/response metric returns
math.inf so the sizing layer adds servers instead of crashing.
"""

from __future__ import annotations

import math


def littles_law_in_system(arrival_rate_rps: float, response_time_s: float) -> float:
    """Return mean requests in system, L = lambda * W."""
    if math.isinf(response_time_s):
        return math.inf
    return arrival_rate_rps * response_time_s


def erlang_c(servers: int, offered_load_erlangs: float) -> float:
    """Return P(wait), the Erlang-C queueing probability for M/M/c.

    Direct Erlang-C needs a**c / c!, which overflows for large c. Compute
    Erlang-B B(c, a) with the recurrence below (no factorials, no large
    powers), then convert:

        B(0, a) = 1
        B(k, a) = a*B(k-1, a) / (k + a*B(k-1, a))
        C(c, a) = c*B(c, a) / (c - a*(1 - B(c, a)))

    Every B intermediate stays in [0, 1], so the recurrence holds up at very
    large c.

    Returns 1.0 when a >= c (saturated, every arrival queues).
    Raises ValueError on servers < 1 or offered_load_erlangs < 0.
    """
    if servers < 1:
        raise ValueError(f"servers must be >= 1, got {servers!r}")
    if offered_load_erlangs < 0:
        raise ValueError(f"offered_load_erlangs must be >= 0, got {offered_load_erlangs!r}")
    a = offered_load_erlangs
    if a == 0:
        return 0.0
    if a >= servers:
        # saturated: queue with certainty
        return 1.0

    b = 1.0
    for k in range(1, servers + 1):
        b = (a * b) / (k + a * b)

    # a < c here, so this stays positive
    denom = servers - a * (1.0 - b)
    if denom <= 0:
        # unreachable for a < c; guard against returning a value outside [0, 1]
        return 1.0
    c_prob = (servers * b) / denom
    # absorb float drift; the [0, 1] contract must hold exactly
    return min(1.0, max(0.0, c_prob))


def mmc_response_time(arrival_rate_rps: float, service_time_s: float, servers: int) -> float:
    """Return mean sojourn time W of an M/M/c queue, in seconds.

        a  = lambda * S
        Wq = C(c, a) * S / (c - a)
        W  = S + Wq

    Returns math.inf when unstable (a >= c).
    Raises ValueError on service_time_s <= 0 or servers < 1.
    """
    if service_time_s <= 0:
        raise ValueError(f"service_time_s must be > 0, got {service_time_s!r}")
    if servers < 1:
        raise ValueError(f"servers must be >= 1, got {servers!r}")
    if arrival_rate_rps <= 0:
        # no load: sojourn is service time alone
        return service_time_s
    a = arrival_rate_rps * service_time_s
    if a >= servers:
        return math.inf
    pw = erlang_c(servers, a)
    wq = pw * service_time_s / (servers - a)
    return service_time_s + wq


def servers_for_utilization(
    arrival_rate_rps: float,
    service_time_s: float,
    utilization_ceiling: float,
    parallelism: int = 1,
) -> int:
    """Return the fewest servers holding per-instance utilization at or below the ceiling.

        c = ceil( (lambda * S) / (utilization_ceiling * parallelism) )

    Non-queueing lower bound on instances: ignores queueing delay, only meets
    the utilization target. For latency-aware sizing use min_servers_for_latency.
    """
    if service_time_s <= 0:
        raise ValueError(f"service_time_s must be > 0, got {service_time_s!r}")
    if utilization_ceiling <= 0:
        raise ValueError(f"utilization_ceiling must be > 0, got {utilization_ceiling!r}")
    if parallelism < 1:
        raise ValueError(f"parallelism must be >= 1, got {parallelism!r}")
    if arrival_rate_rps < 0:
        raise ValueError(f"arrival_rate_rps must be >= 0, got {arrival_rate_rps!r}")
    if arrival_rate_rps == 0:
        return 1
    per_instance = parallelism * utilization_ceiling / service_time_s
    return max(1, int(math.ceil(arrival_rate_rps / per_instance - 1e-9)))


def min_servers_for_latency(
    arrival_rate_rps: float,
    service_time_s: float,
    p95_target_s: float,
    parallelism: int = 1,
    max_servers: int = 100000,
) -> int:
    """Return the fewest instances whose estimated p95 sojourn meets the target.

    Walk up from the stability floor until the p95 estimate drops to or below
    p95_target_s.

    p95 estimate models the sojourn tail as exponential:

        p95 ~= W_mean * ln(1 / 0.05) = W_mean * ln(20)   (ln 20 ~= 2.9957)

    Exact for M/M/1 (sojourn is Exponential(mu - lambda)); for M/M/c the tail
    is lighter, so this over-estimates p95 and over-provisions, the safe side
    for capacity planning.

    Each instance gives `parallelism` channels, so the queue is M/M/c with
    c = instances * parallelism.

    Returns the instance count, capped at max_servers.
    """
    if service_time_s <= 0:
        raise ValueError(f"service_time_s must be > 0, got {service_time_s!r}")
    if p95_target_s <= 0:
        raise ValueError(f"p95_target_s must be > 0, got {p95_target_s!r}")
    if parallelism < 1:
        raise ValueError(f"parallelism must be >= 1, got {parallelism!r}")
    if max_servers < 1:
        raise ValueError(f"max_servers must be >= 1, got {max_servers!r}")

    p95_factor = math.log(20.0)  # ln(1/0.05) ~= 2.9957

    # stability floor (rho < 1 at this parallelism); counts below it give an
    # inf W_mean and get skipped by the loop
    start = max(1, servers_for_utilization(
        arrival_rate_rps, service_time_s, utilization_ceiling=1.0, parallelism=parallelism
    ))

    for instances in range(start, max_servers + 1):
        channels = instances * parallelism
        w_mean = mmc_response_time(arrival_rate_rps, service_time_s, channels)
        if math.isinf(w_mean):
            continue  # still unstable, add more instances
        if w_mean * p95_factor <= p95_target_s:
            return instances
    return max_servers
