# MINERVA

> An API-first OSINT engine that aggregates public cyber-threat data into a knowledge graph and answers natural-language questions about the threat landscape.

## Overview

MINERVA is a cyber threat intelligence (CTI) platform that collects open-source intelligence on IP addresses, domains, vulnerabilities, and threat actors from multiple public sources, resolves those signals into a single correlated knowledge graph, and lets analysts query the result in plain language. It is built as a REST service so other systems can consume it as a threat-intelligence backend rather than a standalone tool. Findings are aligned to the MITRE ATT&CK framework and can be exported as STIX 2.1 bundles or formatted reports. The system is designed to run fully standalone via containers.

## Highlights

- **Multi-source intelligence collection.** Asynchronous, rate-limited collectors aggregate exposed-host data, indicators of compromise, vulnerability and CVSS data, DNS, and WHOIS, degrading gracefully when an individual source or credential is unavailable.
- **Cross-source entity resolution.** Signals describing the same real-world entity across different sources are merged into a single canonical node, producing a clean, deduplicated graph rather than fragmented per-source records.
- **Knowledge-graph correlation.** Builds a typed graph of IPs, domains, organizations, vulnerabilities, techniques, threat actors, and campaigns, with relationships that make attribution and attack-surface analysis queryable.
- **MITRE ATT&CK enrichment.** Maps observed tactics, techniques, and procedures to the ATT&CK framework with confidence scoring.
- **Natural-language querying.** Analysts ask questions in plain language and receive prose answers grounded in the graph, with no need to know the underlying query language.
- **Read-only query safety by construction.** The natural-language interface is structurally prevented from mutating or exhausting the graph, so untrusted questions cannot cause harmful operations.
- **Threat-actor attribution.** Correlates an entity's techniques and infrastructure against a curated set of documented threat actors and returns ranked, evidence-weighted results.
- **Reporting and export.** Generates intelligence reports in multiple formats and exports findings as STIX 2.1 for interoperability with other security tooling.
- **Production API concerns handled.** JWT authentication with role-based access control, security middleware, rate limiting, append-only audit logging, and asynchronous collection jobs with live progress streaming.

## Tech Stack

| Category | Technologies |
| --- | --- |
| Language | Python (3.11+) |
| Web / API | FastAPI, Uvicorn, Pydantic v2 |
| Agent orchestration | LangGraph |
| AI / LLM | LLM provider across reasoning and embedding models |
| Graph store | Neo4j 5 (async) |
| Relational store | PostgreSQL, SQLAlchemy 2.0 (async), Alembic |
| Cache | Redis |
| Vector store | Qdrant |
| Auth & security | JWT, bcrypt, rate limiting |
| Collection & HTTP | httpx, tenacity, async rate limiting |
| Reporting | WeasyPrint, ReportLab, Jinja2, stix2 |
| Logging | structlog (JSON) |
| Infra / DevOps | Docker, Docker Compose |
| Testing & lint | pytest, ruff |

## Status

Beta, version 1.0.0 — feature-complete multi-agent collection pipeline, full REST API, authentication, database migrations, unit and integration tests, and containerized deployment. Role: sole architect and developer.

Source code private and proprietary — code review available on request.

---

_© 2026 Edoardo Caciolo — all rights reserved. Proprietary and not open source; source code is private and available for review on request._
