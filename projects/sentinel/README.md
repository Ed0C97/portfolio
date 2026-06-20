# Sentinel — code samples

Three self-contained excerpts from Sentinel's infrastructure layer. They show how the platform stays resilient and operable under real production conditions — failing fast when an external dependency is unhealthy, resolving secrets across heterogeneous backends without code changes, and surfacing misconfiguration with actionable error messages — all without exposing any of the product's analysis logic.

**Context:** see the [project page](../sentinel.md) for what Sentinel is and how these pieces fit together.

**Stack:** Python 3.12+, `asyncio`, SQLAlchemy, optional HashiCorp Vault (`httpx`) / AWS Secrets Manager (`boto3`) backends.

## What each file shows

- **`circuit_breaker.py`** — an async circuit breaker (CLOSED / OPEN / HALF_OPEN) for external-service calls. Notable: a *selective* failure filter so transport errors trip the breaker while schema/content errors propagate untouched, and a documented `__aenter__`/`__aexit__` fix that materializes the context manager so the HALF_OPEN → CLOSED recovery transition actually fires (the previous form silently dropped the CM and never recorded outcomes).
- **`secrets_resolver.py`** — a fail-soft resolver that tries Vault → AWS Secrets Manager → environment-variable fallback in priority order. Try-import keeps it working when optional SDKs aren't installed, secret IDs are normalized through a whitelist regex before becoming env keys, and a dedicated `SecretNotFound` exception names every backend that was checked.
- **`db_resolver.py`** — maps a `tenant_id` to a runnable PostgreSQL URL with deployment-mode branching (shared SaaS DB vs. per-tenant secret lookup). Each custom exception tells the operator exactly what to fix, and the batch iterator skips a single broken tenant with a warning instead of aborting the whole migration run.

## Deliberately omitted

These samples are infrastructure only. Nothing here is part of the product's moat, and the following are intentionally not included:

- The verification rule-set and grounding/coverage gates.
- The risk-scoring prompts, calibration, and deterministic banking rules.
- The multi-agent orchestration graph and agent state container that make findings auditable.
- All concrete secret values, tenant data, connection strings, and provider integrations (delegated to external/optional libraries and stubbed here).

_© 2026 Edoardo Caciolo — all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
