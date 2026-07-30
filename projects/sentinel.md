# Sentinel

> A multi-tenant document intelligence platform for credit and risk teams: it extracts, verifies, scores, and attests risk in due-diligence documentation, producing grounded, reproducible findings instead of free-form summaries.

## Overview

Sentinel is built for banking and credit-intelligence teams that need traceable, defensible document review. It analyzes due-diligence reports, contracts, comfort letters, and term sheets in English and Italian, and returns structured findings with calibrated risk scores.

The engineering problem it solves is not retrieval, it is trust. An LLM will produce a plausible finding that no source supports, and a risk score that moves between runs, and neither failure announces itself. Sentinel answers both structurally: a verification layer gates every finding on grounding and coverage before acceptance, financial constraints are checked symbolically rather than by asking a model whether the numbers add up, and reproducibility is enforced down to the inference kernels instead of being hoped for at temperature zero. Each analysis yields a signed, encrypted attestation and a generated report, so a result can be re-derived and defended months later.

## Highlights

### Grounding, verification, and determinism

- **Deterministic serving under concurrency**: greedy decoding does not make a multi-tenant LLM service reproducible, because kernel reduction order shifts with how requests happen to be batched together. Serializing requests one at a time fixes it and destroys throughput; that mode was built, benchmarked, and rejected. The shipped path runs batch-invariant kernels on self-hosted inference, certified by a solo-versus-concurrent probe that collapses to a single output hash across trials. Cost: roughly 1.6-2x latency per request, bought for identical output at any batch composition and *higher* aggregate throughput than the serialized mode.
- **Symbolic verification of financial constraints**: figures and relationships extracted from a document are compiled to a formula AST, evaluated with SymPy, and checked for satisfiability by an ensemble of SMT solvers (Z3 and CVC5), so an inconsistency is proven rather than guessed at by a second model pass. Unsatisfiable constraint sets come back as located boundary violations. Separate property and proof backends cover checks that do not reduce to SMT.
- **Reproducible findings**: extraction produces a stable finding set that is a property of the document rather than of the sampling seed, enforced through deduplication and deterministic gates. Run-to-run consistency is measured by a dedicated harness (extraction variance by Jaccard similarity, zero-variance checks on scoring), not assumed.
- **Multi-agent verification layer**: independent verification, severity recalibration, and coverage review run *after* extraction. Findings are checked against source text and rejected when ungrounded, rather than taken at face value.
- **Cross-section reconciliation**: beyond per-clause extraction, the system reasons across sections to surface implicit risk and to resolve documents that contradict each other, which is where single-pass extraction quietly fails.
- **Evaluation harness**: an offline harness runs the pipeline against labelled corpora with retrieval metrics, RAG quality scoring, and a judge benchmark that answers whether the verification layer is worth its cost, by running the same documents with judges off and on and comparing accuracy gain, false-positive reduction, and latency overhead against explicit targets. A layer that buys accuracy by doubling latency fails the gate. Ground truth is built per tenant and held in object storage, never committed; a small set of expert-annotated clauses ships with the code to anchor classification and verdict behaviour in CI.
- **Prompt-program optimization**: analysis modules are compiled offline with DSPy and loaded at runtime, separating optimization from serving, with a dedicated evaluation loop measuring whether a recompilation actually improved anything.
- **Domain NLP in Italian and English**: entity detection, PII recognition, and extraction tuned for Italian legal and financial documents, not English-only pipelines retrofitted to Italian.

### Analysis and retrieval

- **Multi-agent orchestration**: analysis runs as a directed graph of stages with conditional routing by document mode (LangGraph). Agents are stateless, with all mutable state held in an explicit context object, so runs execute concurrently under a configurable semaphore.
- **Hybrid retrieval (RAG)**: keyword search, dense vector search, and knowledge-graph traversal are fused for grounding and question answering, with per-channel retrieval metrics.
- **Deterministic rule layer over AI scoring**: hard banking rules are applied alongside AI scoring, calibration, and ensemble aggregation to produce a final score and verdict that an auditor can follow.
- **Provider-neutral LLM routing**: per-task model selection across multiple providers through a litellm-based router, with no provider hard-coded and no single-vendor dependency.
- **Active learning**: few-shot extraction modules adapt per document type and language and improve from user feedback.
- **Ingestion and OCR**: a vision-language OCR pipeline plus layout extraction handles real-world scanned PDFs.

### Platform and operations

- **Attestation and auditability**: each run is recorded as a signed, encrypted proof-of-analysis token that can be fetched, verified, and downloaded.
- **Multi-tenant control plane**: a separate provisioning service for tenant lifecycle, per-tenant configuration, quotas, rate limits, and administration.
- **Content guardrails**: PII detection in English and Italian plus content-safety guardrails on model output.
- **Enterprise security and auth**: JWT in HttpOnly cookies, SAML 2.0, OIDC, TOTP MFA, WebAuthn passkeys, rate limiting, secrets management, archived audit log.
- **Reporting and distribution**: native PDF, DOCX, PPTX, and XLSX export; a web UI, an Electron desktop app, and a Python SDK. Usage metering and CPQ flows.
- **Reusable in-house toolkits**: builds on framework-agnostic, independently-versioned libraries (document OCR, retrieval grounding and hallucination detection, prompt-program optimization, recursive LLM execution, GPU fleet capacity planning) designed for reuse beyond this project.

## Tech Stack

| Area | Technologies |
| --- | --- |
| Language | Python 3.12+ (JavaScript/CSS for web UI, Astro landing page, Electron desktop app) |
| Web framework | FastAPI, Uvicorn, Pydantic v2, GraphQL |
| AI / orchestration | LangGraph, DSPy, litellm provider-neutral router, Instructor, GPTCache |
| Inference | Self-hosted vLLM in a batch-invariant deterministic serving mode, FlashAttention, GPU capacity planning and autoscaling |
| Symbolic verification | SymPy, Z3, and additional SMT and proof backends behind an ensemble solver |
| Evaluation | Offline eval harness, golden-set builders, LLM-judge benchmark, retrieval metrics, consistency and determinism suites in CI |
| OCR / NLP | Vision-language OCR (Hugging Face Transformers), PyMuPDF, Azure Document Intelligence, spaCy (IT/EN), NLTK |
| RAG / data stores | PostgreSQL (SQLAlchemy async, asyncpg, Alembic), Neo4j, Pinecone |
| Security / compliance | PyJWT, passlib/bcrypt, pyotp (TOTP), WebAuthn, SAML/OIDC, Presidio + NeMo Guardrails, HashiCorp Vault, post-quantum crypto (ML-KEM / ML-DSA) |
| Reporting | PyLaTeX, ReportLab, python-docx, python-pptx |
| Infra / DevOps | Docker, Docker Compose, Terraform (AWS/Azure), Tilt, OpenTelemetry, Stripe; CI via GitHub Actions |
| Notable libraries | APScheduler, SlowAPI, Tenacity, structlog, httpx, Typer |

## Status

Beta and actively developed, on calendar versioning. Built as a Python monorepo (two FastAPI applications plus a web UI, an Electron desktop app, and a Python SDK) backed by PostgreSQL, Neo4j, and Pinecone, and part of a coordinated multi-repository ecosystem of independently-versioned toolkit packages. The test suite spans unit, integration, property, consistency, and determinism tests, behind CI that gates evaluation and grounding on every change. Sole architect and developer.

Source code private and proprietary (Copyright Edoardo Caciolo), review available on request.

---

## Code sample

A small, IP-safe excerpt is in [`sentinel/`](./sentinel/), in two groups. **Evaluation**: the dependency-free IR metric definitions shared by the eval harness and the metrics exporters, and the judge benchmark that measures whether the verification layer earns its latency, with the audit timeline that reconstructs how a finding reached its score. **Infrastructure**: an async circuit breaker, a fail-soft multi-backend secret resolver, and a tenant DB-URL resolver with progressive error design.

_© 2026 Edoardo Caciolo, all rights reserved. Proprietary and not open source; source code is private and available for review on request._
