# Aptus

> A career-intelligence platform that aligns a candidate's CV with a job description and returns a scored, evidence-backed match that both recruiters and candidates can audit.

## Overview

Aptus reads a CV and a job description, extracts structured candidate and role data with large language models, and produces an overall fit score, a per-category breakdown, a gap list, and an Applicant Tracking System (ATS) keyword analysis. Every claim in the result is tied back to the exact passage it came from in the source documents, so the final verdict is traceable rather than opaque. It serves two audiences in one system: candidates optimizing their CV against a specific role, and recruiters who need a defensible, explainable screen. Compliance with EU AI Act employment-context requirements is treated as a first-class design constraint, with consent gating, data-governance records, and an auditable evidence trail built into the platform from the ground up.

## Highlights

- **Evidence-grounded results** — every requirement-to-claim match is backed by citations from both the CV and the job description and carries a confidence signal, so a recruiter or candidate can audit exactly why a verdict was reached instead of trusting a black box.
- **Hybrid match engine** — combines a deterministic rule layer with selective LLM reasoning so that clear-cut cases are resolved cheaply and reproducibly while genuinely ambiguous requirements get model-level judgment, keeping results consistent and cost-bounded at scale.
- **Explainable scoring** — surfaces an overall fit score, a category-level breakdown, an explicit gap list, and ATS keyword coverage, turning a single number into an actionable, defensible assessment.
- **Live, incremental results** — the analysis streams to the web client so parsing, extraction, matching, and narrative framing render progressively rather than after a long blocking wait.
- **Broad candidate-intelligence suite** — beyond matching, the platform offers CV rewriting and optimization, narrative framing, multi-persona recruiter simulation, skill-transferability and role-clustering inference, market indexing, interview-question generation, and connectors to common ATS systems and identity sources.
- **Multi-format document ingestion** — robustly parses real-world PDF and DOCX resumes, including scanned documents, with language and section detection.
- **Compliance and privacy by design** — built-in EU AI Act risk-management, transparency, human-oversight, and record-keeping surfaces; Data Protection Impact Assessment tooling; and GDPR erasure, export, and rectification capabilities, with strict multi-tenant data isolation enforced at the database layer.
- **Pluggable provider model** — authentication, billing, database, embeddings, graph store, LLM routing, OCR, and reranking each sit behind a clean interface with interchangeable adapters, so the same code runs fully self-hosted or on managed cloud services.
- **Operational hardening** — multi-factor authentication, CSRF protection, security headers, rate limiting, usage metering, and end-to-end observability and evaluation gating.

## Tech Stack

| Layer | Technologies |
| --- | --- |
| Backend | Python 3.12, FastAPI, Uvicorn, Server-Sent Events |
| LLM and orchestration | LangGraph, Instructor, LiteLLM; an LLM router spanning multiple providers (Anthropic Claude and OpenAI models) |
| Document processing | PyMuPDF, python-docx, mammoth, langdetect, OCR |
| Data stores | PostgreSQL with pgvector and a property-graph store, Redis, SQLAlchemy (async), Alembic, job queue |
| Auth and security | PyJWT, passlib/argon2, TOTP, WebAuthn, rate limiting, defusedxml |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4; Playwright and Vitest |
| Infra and DevOps | Docker Compose, per-service Dockerfiles, Terraform (multi-cloud: AWS/Azure/GCP), GitHub Actions, uv, Ruff, mypy, pytest, pre-commit, bandit |
| Observability | structlog, Langfuse, OpenTelemetry, Sentry, PostHog |
| Compliance | EU AI Act and GDPR modules, DPIA tooling, PostgreSQL Row-Level Security |

## Status

Active, in-development monorepo: substantial backend engines, a Next.js client, CI workflows, and an evolving database schema, with some operational paths deferred to later phases. Source code is private and proprietary (all rights reserved) — code review available on request.

---

_© 2026 Edoardo Caciolo — all rights reserved. Proprietary and not open source; source code is private and available for review on request._
