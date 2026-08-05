---
title: "Sentinel"
slug: "sentinel"
lang: "en"
oneLiner: "Multi-tenant platform that extracts, scores, and attests risk in legal and financial documents through a verified multi-agent pipeline."
category: "Document AI & Multi-Agent"
status: "Beta"
statusTone: "beta"
featured: true
visible: true
order: 2
metrics:
  - value: "2 apps"
    label: "Analysis API plus a separate multi-tenant control plane"
  - value: "1.6-2x"
    label: "Latency overhead accepted for deterministic serving"
stack: ["Python", "FastAPI", "LangGraph", "DSPy", "LiteLLM", "PostgreSQL", "Terraform"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/sentinel"
image: "/images/projects/sentinel.svg"
---

## The problem

Due diligence reports, contracts, comfort letters, and term sheets decide real money, and someone has to read them. In banking and credit-intelligence teams that reading is slow, expensive, and hard to defend afterwards: a reviewer flags a risk, but the link between the flag and the sentence that justifies it lives in the reviewer's head. Generic LLM summarization makes this worse, not better. A model produces fluent findings, but nothing binds them to the source text, the same document can yield different findings on different runs, and a regulator or counterparty who asks "where exactly does the document say this?" gets no answer. For automated document review to be usable in that world, three properties have to hold at once: every finding must be traceable to evidence in the document, the analysis must be reproducible, and the result must be attestable, meaning provable after the fact that a specific analysis produced a specific output.

## What I built

Sentinel is a multi-tenant platform that analyzes legal and financial documents in English and Italian and returns structured findings with calibrated risk scores. A document goes through a pipeline of specialized agents: some extract clauses and risks, others verify what the first group produced. The verification agents run after extraction and check that every finding is grounded in the source text, recalibrate its severity, and gate coverage before anything is accepted; ungrounded results are discarded. Each analysis ends with two artifacts: a report exported to PDF, DOCX, PPTX, or XLSX, and a signed, encrypted Analysis Attestation Token that can be fetched, verified, and downloaded later as proof of what was analyzed and what came out. Around the analysis core sits a full product: enterprise authentication (SAML, OIDC, passkeys, MFA), Stripe billing, a web interface, an Electron desktop app, and a Python SDK.

![sentinel detail placeholder 1](/images/projects/sentinel-2.svg)

## How it works

The monorepo contains two FastAPI applications: the analysis API and a separate provisioning control plane that handles tenant lifecycle, quotas, migrations, and administration. Agents are stateless, with all mutable state held in an AgentContext, so runs execute concurrently under a configurable semaphore; analysis modules are compiled offline and loaded at runtime. Retrieval is hybrid, drawing on full-text search, a vector index, and a knowledge graph. Verification agents run after extraction: they check grounding, recalibrate severity, and gate coverage before anything is accepted. The non-obvious choice is deterministic serving on batch-invariant kernels for local inference. Without batch invariance, a result depends on which other tenants happen to share its batch, and the only other way to keep reproducibility would have been serializing requests one at a time. I accepted a measured 1.6-2x per-request latency overhead to batch across tenants and stay deterministic at the same time.

## Who it's for

Banking and credit-intelligence teams that need document review they can defend: findings tied to source evidence, the same finding set on every run over the same document, and a cryptographic attestation for each analysis. Sentinel is in beta, under a proprietary license, and actively developed.

![sentinel detail placeholder 2](/images/projects/sentinel-3.svg)

## Limits and what I'd redo

The reproducibility guarantee has a price paid on every single request: the 1.6-2x latency overhead of batch-invariant serving. And I built four distribution surfaces (web app, desktop app, SDK, landing page) around a core that is still in beta; doing it again, I would ship the API and the SDK first and let the rest wait until the analysis core stopped moving.
