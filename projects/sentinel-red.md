# Sentinel Red

> An AI security platform that classifies sensitive documents against NATO and government standards and runs adversarial red-team campaigns against LLM endpoints, mapping findings to the MITRE ATLAS threat taxonomy.

## Overview

Sentinel Red is a security service for teams operating LLM systems in regulated or defense-adjacent environments who need auditable classification decisions and repeatable adversarial testing. It performs two functions: it ingests documents across common formats (PDF, DOCX, TXT, HTML, images) and assigns a government-grade security classification, and it stress-tests live or logged LLM conversations for vulnerabilities, producing a quantified security posture. Findings are labeled against MITRE ATLAS (Adversarial Threat Landscape for Artificial-Intelligence Systems), the industry threat taxonomy for AI systems, so results are auditable and comparable over time.

## Highlights

- **Auditable document classification** across a five-level NATO/government scale (UNCLASSIFIED through TOP SECRET), pairing an AI advisory opinion with a deterministic rule layer so classification decisions are explainable and traceable.
- **Safety-by-design guarantee**: the system is architected so that no AI output or configuration change can ever under-classify a document — the deterministic layer is the authority, and this invariant is enforced and test-proven.
- **Adversarial red-team campaigns** that probe LLM endpoints across major classes of AI attack — prompt injection, jailbreaks, adversarial inputs, information extraction, indirect injection, and model inversion — and can also evaluate offline conversation logs after the fact.
- **MITRE ATLAS-aligned findings** so vulnerabilities are reported in a recognized, standardized threat vocabulary rather than ad-hoc labels.
- **Quantified security posture** delivered as a 0–100 score with a clear posture rating, supporting trend tracking and exportable PDF/JSON reports for audit and stakeholder review.
- **Provider-flexible AI layer** routing across multiple commercial LLM providers, so the platform is not locked to a single vendor.
- **Cryptographically signed audit trail** capturing every state change with tamper-evident signing, suitable for compliance and forensic review.
- **Enterprise-grade access control** with JWT authentication, secure password hashing, refresh tokens, and role-based admin protection.
- **Real-time progress streaming** to the dashboard for both classification jobs and red-team campaigns.
- **Usable as a service or a library**: the core engine runs standalone, embeds as a sub-application, or is consumed programmatically without the web or database layers, plus a CLI for common operations.
- **Hardened web surface** with security headers, rate limiting, and request tracing built in.

## Tech Stack

| Category | Technologies |
|---|---|
| Language | Python 3.11+ |
| Web framework | FastAPI, Uvicorn, Jinja2, Server-Sent Events |
| Data validation | Pydantic v2 |
| Data store | PostgreSQL (async SQLAlchemy 2.0, Alembic) |
| LLM orchestration | Multi-provider LLM routing, structured prompting, httpx |
| Document parsing | PyMuPDF, python-docx, BeautifulSoup4, OCR (Tesseract), Pillow |
| Auth & security | JWT, bcrypt, Ed25519 signing, rate limiting |
| Reporting | PDF and JSON export |
| Observability & resilience | Structured logging, retry/backoff |
| Frontend | HTMX, vanilla JavaScript, CSS |
| Infra/DevOps | Docker, docker-compose |
| Tooling | pytest, ruff, mypy (strict) |

## Status

Production-oriented, version 1.0.0. Packaged with Docker, database migrations, strict typing and linting configuration, and unit plus integration test suites including a proof of the core classification safety invariant.

Source code private and proprietary — code review available on request.

---

_© 2026 Edoardo Caciolo — all rights reserved. Proprietary and not open source; source code is private and available for review on request._
