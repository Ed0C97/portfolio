# ClusterMind: portfolio excerpts

Selected internals from ClusterMind, a deterministic capacity-planning tool that sizes service tiers from a workload survey using queueing theory. These excerpts show the correctness-critical math and abstraction layers; they are trimmed for standalone reading and contain no business logic, prompts, or proprietary data.

**Context:** see [../clustermind.md](../clustermind.md) for the project overview.

**Stack:** Python 3.11+ (standard library only, `math`, `dataclasses`, `enum`, `typing`), pure/deterministic functions, no third-party runtime dependencies.

## What each file shows

- **`queueing.py`**: M/M/c (Erlang-C) queueing primitives for capacity sizing. Computes the Erlang-C wait probability via a numerically stable Erlang-B recurrence (no factorials or large powers, so it holds for very large server counts), derives mean sojourn time, and searches for the smallest instance count meeting a p95 latency target via a conservative exponential-tail approximation. Every function documents its formula and units, validates inputs, and returns `inf` for unstable systems rather than crashing.
- **`workload_model.py`**: Defensive workload-derivation math: normalizing traffic-class shares (with a clear equal-split policy for degenerate all-zero input), honoring explicit-vs-derived values, and compound growth projection. Small functions where correctness on the boundaries is the whole point.
- **`serde.py`**: A 130-line `Serializable` mixin giving any dataclass recursive, order-stable `to_dict`/`from_dict` round-tripping using only the standard library. Handles nested dataclasses, enums, `Optional`/`Union`, and typed containers via `typing` introspection; field-declaration order is preserved so serialized output is reproducible and diff-friendly.

## Deliberately omitted

- The tier-sizing, TCO, Monte Carlo, and orchestration layers that consume these primitives.
- All domain models, survey schemas, signal vocabularies, and report templates.
- Any I/O, configuration, credentials, or business-specific rules.

These files are faithful excerpts, lightly trimmed and with imports stubbed/minimized for standalone readability.

_© 2026 Edoardo Caciolo, all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
