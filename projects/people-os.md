# people-os

> An AI-assisted hiring platform that exposes resume screening, interview scoring, and onboarding as Model Context Protocol (MCP) tools, paired with an evaluation framework that measures decision quality before changes ship.

## Overview

people-os treats AI hiring decisions as a measurable engineering problem rather than ad-hoc prompting. It packages People Operations tasks — querying an applicant tracking system (ATS), parsing resumes, scoring interviews, and generating onboarding plans — as MCP tools and resources that any MCP-compatible client (for example, Claude Desktop or Claude Code) can call. Every AI behavior is governed by versioned prompts and backed by an offline evaluation suite that reports decision-quality metrics, including an explicit fairness measure, so changes can be assessed before they reach users. The full system runs locally in a self-contained demo mode with no API keys required.

## Highlights

- **MCP-native tooling.** Exposes the hiring workflow — ATS queries, resume parsing, interview scoring, and onboarding plan generation — as a coherent set of MCP tools and resources callable from any compatible client.
- **Structured, validated AI outputs.** Every AI tool returns a typed, schema-validated result rather than free text, making downstream automation reliable and outputs safe to consume programmatically.
- **Multi-step agentic workflows.** Graph-based orchestration composes individual tools into screening and onboarding pipelines over typed state, with resilient error handling so a single failure degrades gracefully instead of aborting the run.
- **Decision-quality evaluation.** An offline eval harness scores AI behavior against a labeled dataset and reports accuracy, precision, recall, and run-to-run consistency, giving a quantitative gate on quality before changes ship.
- **Built-in fairness measurement.** The eval suite surfaces systematic undervaluing of non-traditional candidates as a first-class metric, treating bias as something to measure and regress against, not an afterthought.
- **Prompt versioning and A/B comparison.** Prompts are version-controlled artifacts with a documented changelog, and competing versions can be compared head-to-head on the same dataset to select a winner on evidence.
- **Pluggable ATS integration.** Connects to a real ATS (Greenhouse) when credentials are present and transparently falls back to realistic mock data otherwise, so the entire flow is demonstrable end-to-end with no external dependencies.
- **Operator dashboard.** A web dashboard visualizes the candidate pipeline, screening results, and evaluation reporting for non-technical stakeholders.

## Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python (≥3.10) |
| LLM | Anthropic Claude API |
| MCP | FastMCP |
| Orchestration | LangGraph / LangChain |
| Frontend | Streamlit |
| Validation | Pydantic v2 |
| HTTP | httpx (async) |
| Data | pandas, NumPy |
| Logging | structlog |
| ATS | Greenhouse Harvest API |
| Testing | pytest, pytest-asyncio |
| Tooling | Ruff, mypy |
| Packaging / Infra | setuptools, Docker, Docker Compose |

## Status

Working prototype with an automated test suite and a fully offline demo mode. Source code private and proprietary — review available on request.

---

_© 2026 Edoardo Caciolo — all rights reserved. Proprietary and not open source; source code is private and available for review on request._
