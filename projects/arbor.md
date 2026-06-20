# ARBOR

> A multi-tenant AI platform that discovers, enriches, and reasons over real-world entities, combining a knowledge graph, vector search, and an event-sourced data store.

## Overview

ARBOR ingests real-world entities such as brands, venues, and products from external sources, enriches them through an AI pipeline, and exposes them for semantic discovery and conversational querying. It targets teams building contextual discovery and recommendation products over curated entity data. The platform spans a Python backend, a React web frontend, an Expo (React Native) mobile client, and a Kubernetes-based infrastructure layer. Domain behaviour — entity categories, scoring dimensions, prompts, and ontologies — is config-driven rather than hard-coded, so new verticals can be onboarded without code changes.

## Highlights

- **Agentic discovery** — Routes a user query through intent understanding, parallel retrieval, and answer assembly, with resumable conversational sessions that survive interruptions.
- **Hybrid retrieval** — Combines knowledge-graph reasoning, graph-augmented retrieval, and dense-plus-sparse vector search with reranking to return relevant, well-grounded results.
- **Event sourcing and CQRS** — An append-only event store with optimistic concurrency, snapshots, and read-model projections serves as the single source of truth for the entity domain, with reliable event publication to downstream consumers.
- **Durable workflows** — A workflow engine orchestrates multi-step enrichment, ingestion, analytics, and sync pipelines so long-running jobs resume from the last completed step rather than restarting on failure.
- **Configurable ingestion** — Pluggable scrapers and a multi-stage enrichment pipeline collect, analyze, score, validate, and persist entity data, with feedback loops that continuously refine scoring quality.
- **Multi-tenant isolation** — Tenant-level data separation, request-scoped tenant context, and role-based access control enforced consistently across backend and frontend.
- **LLM gateway** — Provider routing across multiple LLM providers with caching, guardrails, and centralized prompt management, isolating application logic from any single model vendor.
- **Compliance and safety** — GDPR erasure, PII redaction, audit and AI-decision logging, data-lineage tracking, EU AI Act mapping, and rule-based safety checks.
- **Observability** — Distributed tracing, metrics, LLM-specific tracing, and defined service-level objectives across the request path.
- **Resilience** — Circuit breaking, bulkhead isolation, retries, and multi-tier caching keep the system responsive under partial failure and load.

## Tech Stack

| Category | Technology |
|----------|------------|
| Languages | Python 3.12, TypeScript, SQL, Cypher, HCL, Shell |
| Backend | FastAPI, Pydantic v2, Uvicorn |
| Data stores | PostgreSQL 16 + PostGIS, Neo4j 5, Qdrant, Redis 7 |
| AI / LLM | LangChain, LangGraph, LiteLLM; multiple LLM providers; in-house reasoning toolkits |
| Workflows / events | Temporal.io, Celery, Kafka |
| Auth / security | JWT, cryptography, PII redaction (Presidio), rate limiting |
| Web frontend | React 18, Vite 6, Zustand, Radix UI, TailwindCSS, D3.js, Recharts |
| Mobile | Expo, React Native, TanStack Query, Zustand |
| Observability | OpenTelemetry, Prometheus, Langfuse, Phoenix |
| Infra / DevOps | Docker, Kubernetes, Terraform, Helm, GitOps, Linkerd, Vault |
| Testing | pytest, Vitest, Playwright, k6 (load), promptfoo (red team) |

## Status

Active private project under heavy development, at backend version 1.1.0, with a large codebase and broad unit, integration, end-to-end, chaos, load, and red-team test suites alongside production-oriented Kubernetes and GitOps manifests. Maturity varies by module. Released under a proprietary license (Copyright Edoardo Caciolo); not open source.

Source code private and proprietary — code review available on request.

---


## Code sample

A small, IP-safe excerpt is in [`arbor/`](./arbor/) — the AI search & recommendation engine behind the platform: hybrid retrieval (dense vector + keyword, RRF fusion), a cost-aware multi-stage reranking funnel with graceful degradation, and learning-to-rank with a zero-dependency fallback.

_© 2026 Edoardo Caciolo — all rights reserved. Proprietary and not open source; source code is private and available for review on request._
