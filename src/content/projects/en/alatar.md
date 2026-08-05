---
title: "Alatar"
slug: "alatar"
lang: "en"
oneLiner: "Career-intelligence platform that aligns a CV with a job description and returns a scored, evidence-backed, auditable match."
category: "Career Intelligence & LLM"
status: "Prototype"
statusTone: "prototype"
featured: true
visible: true
order: 6
metrics:
  - value: "3 layers"
    label: "Match engine: deterministic, one batched LLM pass, scoring"
  - value: "~25 engines"
    label: "Domain engines, from CV rewriting to recruiter simulation"
stack: ["Python 3.12", "FastAPI", "LangGraph", "LiteLLM", "PostgreSQL + pgvector", "Next.js 16", "TypeScript"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/alatar"
image: "/images/projects/alatar.svg"
---

## The problem

When software screens a job application, the output is usually a number with no explanation attached. The candidate gets rejected without knowing which requirement they failed; the recruiter gets a ranking they could not defend if anyone asked how it was produced. Neither side can audit the decision. The obvious fix, asking a large language model to compare the CV to the job description, brings problems of its own: every comparison costs an API call, the same input can produce different scores on different days, and the reasoning stays locked inside the model. On top of that, the EU AI Act places AI used in employment decisions in its high-risk category (Annex III), which turns traceability from a nice-to-have into a legal obligation. A screening tool that cannot show its evidence is not just frustrating for the people on both ends of it; in Europe it is on its way to being non-compliant.

## What I built

Alatar takes a CV and a job description and returns a match that both sides can inspect. It parses the two documents, extracts the candidate's profile and the role's requirements, and produces an overall fit score, a per-category breakdown, a list of gaps, and an analysis of how the CV overlaps with the keywords an applicant tracking system would search for. Every requirement in the result carries a verdict (pass, review, or redflag) and an evidence item with citations pointing to the exact passages in both documents that justify it, so the score can be checked rather than trusted. The platform serves two audiences in one system: candidates tuning a CV against a specific role, and recruiters who need a screen they can explain. Compliance sits inside the pipeline rather than bolted on: the evidence trail maps to the EU AI Act's employment obligations, and GDPR erasure, export, and rectification endpoints exist alongside a data-protection impact assessment module.

## How it works

The match engine has three layers, ordered by cost. A deterministic layer normalizes skills, resolves aliases, and fuzzy-matches everything it can at zero LLM cost. Whatever remains ambiguous goes to a single batched LLM pass that classifies each requirement into one of six tiers, from exact match to missing. A scoring layer then computes a category-weighted aggregate with tier multipliers and ATS keyword overlap. The non-obvious choice is that ordering: deterministic first, LLM second, one batched call, which bounds the cost per match instead of letting it grow with the number of requirements. Around the engine sits a monorepo: a FastAPI backend with roughly 25 domain engines (CV rewriting, recruiter simulation across HR, technical, and hiring-manager personas, ATS adapters, skill ontologies), a Next.js 16 client fed by server-sent events, multi-tenant isolation through PostgreSQL Row-Level Security, seven sibling toolkits pinned in lockstep CalVer, and a CI eval-gate with adversarial red-team tests.

## Who it's for

Nothing has been measured on real users yet, so there are no performance claims to make. Alatar is aimed at candidates who want to know, requirement by requirement, where their CV stands against a role, and at recruiters who need to defend every verdict with citations into both documents.

## Limits and what I'd redo

It is a prototype: several CLI commands and some engine entry points are declared but deferred to later phases, so not every path visible in the code actually runs today. If I restarted, I would narrow the first version. Twenty-five domain engines is a lot of surface for one person, and I would rather have the match pipeline, the evidence chain, and the compliance modules fully operational before widening the catalogue.
