# MINERVA: Correlation and Query-Safety Layer

Two excerpts from MINERVA, an API-first OSINT and cyber-threat-intelligence engine that correlates public threat data into a single knowledge graph and answers natural-language questions grounded in it.

**Context:** see [../minerva.md](../minerva.md) for the full project overview.

**Stack:** Python, standard library (`ipaddress`, the IDNA codec, `re`), Neo4j behind a Protocol.

## What each file shows

- **`entity_resolution.py`**: cross-source entity resolution into a deduplicated graph. Derives a total, idempotent canonical key per entity type (compressed IP via `ipaddress`, trailing-dot and IDN-normalized domain, zero-padding-stripped CVE), groups strong-id matches exactly and order-independently, and falls back to token-set (Jaccard) similarity for id-less named actors. Field conflicts resolve deterministically by (source priority, confidence, stable source tiebreak), and every kept value records its provenance.
- **`readonly_cypher_guard.py`**: a static read-only safety guard for LLM-generated Cypher. Tokenizes with quoted-string and comment awareness so keywords inside literals are never matched, rejects write clauses (including LOAD CSV and USING PERIODIC COMMIT) and write or admin procedures, refuses unbounded variable-length paths while allowing bounded `*N` and `*..M` forms, and clamps or injects a trailing `LIMIT`. Documented as defense in depth in front of a read-only Neo4j account, not a replacement for it.

## Deliberately omitted

- The curated threat-actor alias graph (thousands of aliases across naming conventions) that maps names like APT29, Cozy Bear, and Midnight Blizzard to one canonical key; `_resolve_actor_alias` raises `NotImplementedError` and actors fall back to token-set matching in this excerpt.
- The tuned per-source confidence weighting; `SOURCE_PRIORITY` here is an illustrative rank order, not production values.
- The real Neo4j-backed graph store; only the `GraphStore` Protocol surface is shown, and the read-only database credentials (the actual non-bypassable control the guard sits in front of) live in the deployment, not here.

_© 2026 Edoardo Caciolo, all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
