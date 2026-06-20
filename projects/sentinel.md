# Sentinel

> A multi-tenant document intelligence platform that extracts, scores, and attests risk in legal and financial documents, producing auditable findings instead of free-form summaries.

## Overview

Sentinel analyzes legal and business documents — primarily due-diligence reports, but also contracts, comfort letters, and term sheets in English and Italian — and returns structured findings with calibrated risk scores. It pairs LLM-based extraction and multi-agent verification with deterministic banking rules and hybrid retrieval, so every result is grounded, defensible, and reproducible. Each analysis yields a signed, encrypted attestation and a generated report (PDF, DOCX, PPTX, or XLSX). The platform is built for banking and credit-intelligence teams that need traceable document review rather than opaque AI output.

## Highlights

- **Reproducible, document-driven findings** — extraction produces a stable set of findings that reflects the document itself rather than varying run to run, with each finding grounded against source text.
- **Multi-agent verification** — independent verification, severity calibration, and coverage review run after extraction, so accepted findings are checked for grounding and consistency rather than taken at face value.
- **Surfaces implicit as well as explicit risk** — beyond per-clause findings, the system reasons across sections to flag risks that single-pass extraction misses.
- **Deterministic rule layer over AI scoring** — a hard banking-rule layer is applied alongside AI scoring, calibration, and ensemble aggregation to produce a final risk score and verdict that teams can trust and audit.
- **Hybrid retrieval (RAG)** — analysis and question-answering fuse keyword search, vector semantic search, and knowledge-graph traversal for well-grounded responses.
- **Provider-neutral LLM routing** — task-appropriate model selection across multiple providers, with no single provider hard-coded.
- **Active learning from feedback** — few-shot extraction modules adapt per document type and language, improving from user feedback over time.
- **Document ingestion and OCR** — a vision-language OCR pipeline plus layout extraction handles real-world PDFs and scanned documents.
- **Attestation and auditability** — each run is recorded as a signed, encrypted proof-of-analysis token that can be fetched, verified, and downloaded.
- **PII detection and content guardrails** — entity detection in English and Italian plus content-safety guardrails.
- **Report generation** — native PDF, DOCX, PPTX, and XLSX export.
- **Multi-tenant control plane** — a separate provisioning service for tenant lifecycle, per-tenant configuration, quotas, rate limits, and administration.
- **Enterprise security and auth** — JWT in HttpOnly cookies, SAML 2.0, OIDC, TOTP MFA, WebAuthn passkeys, rate limiting, secrets management, and an archived audit log.
- **Billing and CPQ** — usage metering and configure-price-quote flows.
- **Multiple distribution surfaces** — a web UI, an Electron desktop app, a Python SDK, and a marketing site.
- **Leverages reusable in-house toolkits** — builds on a set of framework-agnostic, independently-versioned libraries (document OCR, retrieval grounding and hallucination detection, prompt-program optimization, recursive LLM execution) designed to be reused across multiple projects, not only here.

## Tech Stack

| Area | Technologies |
| --- | --- |
| Language | Python 3.12+ (JavaScript/CSS for web UI, Astro landing page, Electron desktop app) |
| Web framework | FastAPI, Uvicorn, Pydantic v2, GraphQL |
| AI / orchestration | LangGraph, DSPy, litellm provider-neutral router, Instructor, GPTCache |
| OCR / NLP | Vision-language OCR (Hugging Face Transformers), PyMuPDF, Azure Document Intelligence, spaCy, NLTK |
| RAG / data stores | PostgreSQL (SQLAlchemy async, asyncpg, Alembic), Neo4j, Pinecone |
| Security / compliance | PyJWT, passlib/bcrypt, pyotp (TOTP), WebAuthn, SAML/OIDC, Presidio + NeMo Guardrails, HashiCorp Vault, post-quantum crypto (ML-KEM / ML-DSA) |
| Reporting | PyLaTeX, ReportLab, python-docx, python-pptx |
| Infra / DevOps | Docker, Docker Compose, Terraform (AWS/Azure), Tilt, OpenTelemetry, Stripe; CI via GitHub Actions |
| Notable libraries | APScheduler, SlowAPI, Tenacity, structlog, httpx, Typer, z3-solver/sympy |

## Status

Beta and actively developed, on calendar versioning with an extensive CI suite. Built as a Python monorepo (two FastAPI applications plus supporting surfaces) backed by PostgreSQL, Neo4j, and Pinecone, and part of a coordinated multi-repository ecosystem of versioned toolkit packages. Sole architect and developer.

Source code private and proprietary (Copyright Edoardo Caciolo) — review available on request.

---

_© 2026 Edoardo Caciolo — all rights reserved. Proprietary and not open source; source code is private and available for review on request._
