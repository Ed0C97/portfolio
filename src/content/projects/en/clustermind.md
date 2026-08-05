---
title: "ClusterMind"
slug: "clustermind"
lang: "en"
oneLiner: "Deterministic CLI that turns a service description into an auditable capacity plan and cloud TCO, from Erlang-C sizing to GPU roofline."
category: "Capacity Planning & CLI"
status: "Beta"
statusTone: "beta"
featured: false
visible: true
order: 10
metrics:
  - value: "Every number"
    label: "traced to a printed formula: expression, inputs, units"
  - value: "5 stages"
    label: "resumable pipeline over a single Git-versioned config file"
stack: ["Python 3.11-3.13", "Typer", "Rich", "PyYAML", "psutil", "reportlab", "Quarto"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/clustermind"
image: "/images/projects/clustermind.svg"
---

## The problem

"How many servers does this need, and what will it cost per year?" is a question every team answers before launch, and most answers come from a spreadsheet, a gut feeling, or lately a chat with a language model. All three fail the same test: a budget review. A spreadsheet hides its assumptions; intuition does not scale past the systems you have already run; a language model produces a plausible number that nobody can re-derive, and a different one tomorrow. Yet the underlying questions are not vague at all. How many servers a tier needs to hit a latency target is queueing theory; how many tokens per second a GPU can decode is memory-bandwidth arithmetic; how uncertain the annual cost is depends on which inputs you actually know. What is missing is not the math but a tool that applies it, shows its work on every line, and refuses to guess where a model would.

## What I built

ClusterMind is a command-line tool that turns a short description of a web, SaaS, or self-hosted LLM service (traffic, endpoints, latency targets, growth, compliance constraints) into a capacity plan and a total cost of ownership. It proposes per-tier instance counts, concrete AWS, GCP, or Azure instance types, storage and bandwidth figures, autoscaling policies, and unit economics down to cost per request and per million tokens. Everything runs over a single Git-versioned config file, so the work can stop and resume at any stage: an interview captures the inputs in plain language, a static scan of the codebase detects routes and concurrency in FastAPI, Flask, and Django projects, an optional benchmark stage generates and parses load tests for k6, wrk, locust, and vegeta, then the compute stage sizes the tiers and the report stage renders Markdown, HTML, JSON, PDF, or Quarto documents. There is an optional local-LLM layer, but it only rephrases questions and narrates results: it never produces a number.

![clustermind detail placeholder 1](/images/projects/clustermind-2.svg)

## How it works

The math lives in a pure layer with no clocks, randomness, or I/O: the same input file always yields byte-identical output, and every computed value is recorded as a FormulaRecord (name, expression, inputs, result, units) printed in the report, so anyone can re-derive it by hand. Tier sizing uses an M/M/c (Erlang-C) queueing model driven to a latency target; unstable configurations return infinity, so the sizing layer adds servers instead of crashing. Self-hosted LLM inference gets a first-order GPU roofline: weight memory, decode throughput bounded by memory bandwidth, and KV-cache-limited batch size, with a single efficiency factor (default 0.35) as the one knob a benchmark calibrates. A Monte Carlo pass with a fixed seed propagates input uncertainty into P10/P50/P90/P95 bands, ranks cost drivers with a tornado sensitivity analysis, and grades the estimate A to D from the width of the P10-P90 band. The non-obvious choice is making determinism the invariant: the auditability the tool sells would not survive a stochastic dependency anywhere in the pipeline.

## Who it's for

SREs, platform teams, and anyone who has to defend a sizing decision in front of the people who approve the budget. The status is a declared beta: a single-author project under the MIT license, with a pytest suite of around 20 test modules and CI across Python 3.11, 3.12, and 3.13.

![clustermind detail placeholder 2](/images/projects/clustermind-3.svg)

## Limits and what I'd redo

Prices come from a dated list-price snapshot, so a plan's TCO ages with that snapshot, and the GPU roofline stays a first-order estimate until a benchmark calibrates its efficiency factor. If I redid it, I would ship fewer report formats (there are five today: Markdown, HTML, JSON, PDF, Quarto) and spend that effort on keeping the pricing data current, because the freshness of the cost figures is the first thing a reader checks.
