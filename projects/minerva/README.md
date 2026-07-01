# MINERVA: Correlation and Query-Safety Layer

Two excerpts from MINERVA, an API-first OSINT and cyber-threat-intelligence engine that correlates public threat data into a single knowledge graph and answers natural-language questions grounded in it.

**Context:** see [../minerva.md](../minerva.md) for the full project overview.

**Stack:** Python, standard library (`ipaddress`, `re`). The real system runs a LangGraph agent pipeline over Neo4j, stubbed here.

## What each file shows

- **`entity_resolution.py`**: deterministic entity resolution and deduplication across heterogeneous OSINT sources. Derives a canonical key per entity type (IP, domain, CVE, campaign, TTP, threat actor) so signals about the same real-world thing collapse to one node, then merges their fields with a rank-based policy that is invariant to arrival order (the higher-priority source wins a scalar conflict). The agent base class and the collector pipeline are trimmed to what the file exercises.
- **`readonly_cypher_guard.py`**: the security-critical validator that keeps the natural-language query interface read-only. An LLM turns a question into Cypher, and this is the last gate before the database: it enforces four things (no write clauses, an allowed read-only clause set, a mandatory RETURN, and a capped LIMIT) and blocks two denial-of-service shapes (dangerous procedures and unbounded variable-length paths).

## Deliberately omitted

- The curated per-source reliability ranking (`_SOURCE_PRIORITY`) that decides scalar conflicts is the tuned part and is stubbed to a flat default; confidence thresholds and scoring weights are not present.
- The upstream collector agents, the full LangGraph pipeline wiring, and the fuzzy matcher are reduced to the fields this excerpt exercises.
- For the guard: the full read-only clause whitelist is trimmed to a comment, and the real graph schema, the few-shot NL-to-Cypher examples, and the LLM translation layer (provider, model, system prompt, temperature) are not reproduced. The non-bypassable control remains a read-only database account; the guard is defense in depth in front of it.

_© 2026 Edoardo Caciolo, all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
