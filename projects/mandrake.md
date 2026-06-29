# Mandrake

> A multi-agent AI trading platform that keeps a human operator in the loop and enforces hard, non-bypassable risk constraints on every trade.

## Overview

Mandrake is a self-hosted, single-operator system in which specialized AI agents propose trades while a deterministic risk engine and a human operator gate every order before it can reach a broker. It is deliberately scoped to long-only, loss-capped strategies (no short selling, no leverage, no naked options, no perpetual futures), so a position can never lose more than the capital allocated to it. It is built for one operator who wants automated trade research and execution under explicit, auditable controls.

## Highlights

- **Non-bypassable risk gate.** A set of independent hard constraints (long-only, per-trade loss cap, balance floor, instrument whitelist, kill switch, operator approval) runs on every proposal. Any single failure rejects the order, and the design provides no path around the gate.
- **Cryptographically signed approvals.** The risk engine issues a signed approval that the execution layer requires before it will act; an order without a valid approval is refused, decoupling who may propose from what may execute.
- **Operator-in-the-loop lifecycle.** Agents may only submit proposals; approval and rejection are reserved to the human operator through the API, giving a clear separation between AI suggestion and human authorization.
- **Tamper-evident audit trail.** An append-only audit log is chained so that any modification to a past event is detectable through integrity verification, providing a defensible record of every decision and transition.
- **Stateless, replaceable agent runtime.** Each agent runs behind a common base that handles audit logging, timing, LLM-call accounting, and cost tracking. Agents are independently enable/disable-able, so any one can be swapped or turned off without affecting the rest.
- **Provider-agnostic LLM routing.** Model access sits behind an abstraction supporting capability-based routing, cost policy, circuit breaking, and prompt caching across multiple providers, plus a mock path for offline boot and tests.
- **Safe configuration and secrets handling.** Runtime configuration is exposed as editable toggles, and secret values can be set but never read back through the CLI or API, reducing accidental exposure.
- **API, real-time dashboard, and CLI.** A versioned HTTP API and WebSocket stream drive a live dashboard covering system control, configuration, portfolio, orders, agents, proposals, kill switch, and audit, with a companion command-line tool for operations.
- **Decimal-safe money handling.** Monetary values use exact decimal arithmetic with explicit currency codes; money is never represented as a floating-point number.

## Architecture

Mandrake is single-tenant and self-hosted, organized around three principles: hard constraints sit in front of the broker as a perimeter, each agent is independently replaceable and disableable, and audit durability takes priority over performance. The end-to-end flow is outcome-oriented: an agent turns a market signal into a structured proposal, the operator approves or rejects it, the risk engine evaluates all hard constraints and issues a signed approval only when every one passes, and only a validly signed order is routed to a broker. Every transition is appended to the tamper-evident audit log.

Protocol-based seams across audit, LLM routing, brokers, and storage allow in-memory implementations to be swapped for database-backed or live integrations, and the system boots fully on in-memory storage so the API and dashboard run without external infrastructure.

## Tech Stack

| Category | Technologies |
| --- | --- |
| Language | Python 3.11+ |
| Web / API | FastAPI, Uvicorn, WebSockets, vanilla JavaScript / CSS / HTML |
| CLI | Typer, Rich |
| Core libraries | Pydantic, pydantic-settings, structlog, httpx, PyYAML |
| Data | Polars, pandas, NumPy |
| Data stores | PostgreSQL (async SQLAlchemy, asyncpg, Alembic); Redis; ClickHouse and ArcticDB (optional) |
| Agents / LLM | LangGraph, Anthropic SDK, OpenAI SDK, MCP |
| Quant / ML (optional) | scikit-learn, XGBoost, LightGBM, PyTorch, QuantLib, statsmodels, PyPortfolioOpt, Riskfolio-Lib; time-series and RL toolkits |
| Trading integrations (optional) | NautilusTrader, ib_async (IBKR), ccxt, web3, py-clob-client (Polymarket), kalshi-python (Kalshi) |
| Observability | Prometheus, OpenTelemetry, structlog |
| Tooling | pytest, Hypothesis, Ruff, mypy, uv, Make, Quarto |

## Status

Pre-alpha foundation: the system runs end to end against mock broker and LLM adapters with in-memory storage, paired with an extensive design and research documentation set; production integrations are the next phase. Single-author project.

Source code private/proprietary, review available on request.

---

_© 2026 Edoardo Caciolo, all rights reserved. Proprietary and not open source; source code is private and available for review on request._
