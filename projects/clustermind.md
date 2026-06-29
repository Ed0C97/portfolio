# ClusterMind

> A command-line tool that turns a short description of a web, SaaS, or self-hosted LLM service into a deterministic, auditable infrastructure capacity and cloud-cost plan.

## Overview

ClusterMind sizes infrastructure and estimates its cost from a small set of inputs: traffic, endpoints, latency targets, growth, and compliance constraints. It produces per-tier instance counts, cloud instance-type suggestions, storage and bandwidth figures, autoscaling policies, and a total cost of ownership (TCO) breakdown. It is aimed at site reliability engineers, platform teams, and anyone who needs a defensible sizing decision that survives a budget review. Crucially, every numeric result is derived from explicit math rather than a language model, so each figure can be traced back to a formula and re-derived by hand.

## Highlights

- **Deterministic, reproducible sizing.** The same input always produces byte-identical output, with no dependence on clocks, randomness, or network state, so plans are stable enough to put in front of a budget review.
- **Fully auditable figures.** Every computed value carries the formula, inputs, and units behind it, so a reviewer can re-derive any number by hand rather than trusting a black box.
- **Queueing-theory tier sizing.** Capacity for each tier is sized using established queueing models that account for utilization and latency targets, and the system stays stable instead of failing on infeasible configurations.
- **LLM serving capacity model.** A first-principles model sizes self-hosted LLM inference from hardware and token-level constraints (memory, throughput, batching), with a single calibration knob tied to a benchmark.
- **Static code and infrastructure analysis.** Scans common Python web frameworks for routes, dependencies, and concurrency, and infers infrastructure intent from container and orchestration files.
- **Load-test integration.** Generates, runs, and parses load tests across multiple industry-standard tools, samples host resource usage, and feeds structured results back into the plan.
- **Plain-language interview.** An adaptive questionnaire translates everyday answers into numeric drivers with uncertainty ranges, asking follow-up questions conditionally based on prior responses.
- **Investment-grade economics.** Computes monthly and annual TCO plus unit economics (cost per user, per request, per inference batch, per token) from a dated price snapshot, accounting for on-demand, reserved, and spot pricing.
- **Uncertainty and sensitivity analysis.** Propagates per-driver uncertainty through the full pipeline to report confidence bands on headline metrics, ranks which drivers most affect cost, and grades overall confidence, pointing to the specific measurements that would tighten the estimate.
- **Multi-format reporting.** Renders Markdown, HTML, executive summaries with JSON export, optional PDF, and brand-aware documents that adapt to a project's fonts, colors, and logo.
- **Cloud-agnostic instance mapping.** Reasons in abstract resource classes and maps each to a concrete AWS, GCP, or Azure instance type.
- **Optional, non-load-bearing AI.** An optional local-LLM layer rephrases survey questions and narrates plans; it never produces a number and degrades gracefully to a no-op when no model is reachable.

## Architecture

ClusterMind runs as a resumable pipeline over a single Git-versioned config file. Each stage reads the file, fills in its own section, and writes it back, so work can stop and resume at any point. A strict separation is enforced between the pure math layer, which never performs I/O and never depends on the AI layer, and the presentation and orchestration layers, keeping facts cleanly separated from formatting. Stages cover interview/survey capture, static code and infrastructure analysis, benchmarking, deterministic sizing, and reporting plus economics.

## Tech Stack

| Category | Details |
| --- | --- |
| Language | Python 3.11 to 3.13 |
| CLI / UX | Typer, Rich |
| Config / serialization | PyYAML, custom dataclass serialization layer |
| Math / analysis | Standard library; queueing theory, LLM roofline modeling, Monte Carlo |
| System metrics | psutil |
| Reporting | Markdown, HTML; reportlab + matplotlib (PDF, optional); Quarto/Typst (optional) |
| Optional AI | httpx (local-LLM UX layer, optional) |
| Tooling | pytest, pytest-cov, mypy, ruff |
| CI/CD | GitHub Actions (test matrix across Python 3.11/3.12/3.13) |
| External load tools | k6, wrk, locust, vegeta (invoked as subprocesses) |

## Status

Beta. Actively developed single-author project with a comprehensive pytest suite, multi-version CI, and frozen internal contracts. Source code private/proprietary, review available on request.

---


## Code sample

A small, IP-safe excerpt is in [`clustermind/`](./clustermind/): numerically-stable Erlang-C queueing math, defensive workload derivation, and a zero-dependency typed dataclass serializer.

_© 2026 Edoardo Caciolo, all rights reserved. Proprietary and not open source; source code is private and available for review on request._
