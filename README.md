# Edoardo Caciolo: Project Portfolio

> Overview documentation for my projects. **All source code is private and proprietary (not open source).** These pages describe what each system does and how it is built, without the implementation. Code review available on request.

**Contact:** caciolo.edoardo@gmail.com, [github.com/Ed0C97](https://github.com/Ed0C97), [linkedin.com/in/edoardo-caciolo](https://www.linkedin.com/in/edoardo-caciolo)

## How to read this portfolio

Projects come in two kinds, kept separate on purpose:

- **Projects with code samples** carry a folder with a short README and a few IP-safe excerpts, adapted and trimmed so each file reads standalone. The excerpts show the engineering (patterns, algorithms, resilience), never the proprietary core.
- **Additional projects** are described at the design and capability level, with no code sample published. A sample or review can be arranged on request.

## What the code samples demonstrate

The published excerpts are chosen to show concrete engineering, each tied to the project that evidences it:

- **Information retrieval and ranking**: hybrid dense-plus-sparse retrieval, Reciprocal Rank Fusion, and a cost-aware reranking funnel that degrades gracefully when a model provider is slow or down ([ARBOR](projects/arbor.md)).
- **Control and estimation math**: Unscented Kalman Filter state estimation and LPV discretization for a vehicle control stack ([thesis](projects/tesi-triennale.md)); numerically stable Erlang-B and Erlang-C queueing for capacity planning ([ClusterMind](projects/clustermind.md)).
- **Native Apple platforms**: real-time camera-quality signal processing and augmented-reality lifecycle handling in Swift ([Tay](projects/tay.md)); hand-laid PDF and CSV export ([Tappo](projects/tappo.md)).- **Resilience and operability**: circuit breakers on a monotonic clock, multi-backend secret resolution, and graceful-degradation fallbacks ([Sentinel](projects/sentinel.md), [fast-inference](projects/fast-inference.md)).
- **Security-conscious design**: SSRF and DNS-rebinding defense on a local gateway, injection-safe SQL over a recursive CTE, and fail-closed field encryption ([BOT Garage](projects/bot-garage.md), [Aptus](projects/aptus.md)).
- **Threat detection and intelligence**: coefficient-of-variation C2 beaconing detection and channel-isolated SIEM alerting ([NETWATCH](projects/netwatch.md)); cross-source entity resolution into a knowledge graph and read-only-by-construction query safety ([MINERVA](projects/minerva.md)).
- **AI evaluation and fairness**: an offline decision-quality gate with per-class metrics, Cohen's kappa run-to-run consistency, and a demographic-parity fairness gap that treats bias as a measured, regressable quantity ([people-os](projects/people-os.md)).
- **Trustworthy data capture**: confidence-gated OCR field extraction that persists a field only above a confidence threshold and routes weaker matches to human review ([BOT Garage](projects/bot-garage.md)).

## Featured

- **[ARBOR](projects/arbor.md)**: A multi-tenant AI platform that discovers, enriches, and reasons over real-world entities, combining a knowledge graph, vector search, and an event-sourced data store. The published excerpt is its search and ranking engine: hybrid retrieval with RRF fusion and a cost-aware reranking funnel that degrades gracefully when a model provider is slow or down.
- **[Sentinel](projects/sentinel.md)**: A multi-tenant document intelligence platform that extracts, scores, and attests risk in legal and financial documents, producing auditable findings instead of free-form summaries.
- **[Aptus](projects/aptus.md)**: A career-intelligence platform that aligns a candidate's CV with a job description and returns a scored, evidence-backed match that both recruiters and candidates can audit.
- **[Tay](projects/tay.md)**: A native Apple-platform app that recognizes physical artworks and monuments through the camera and anchors real-time augmented-reality experiences on top of them.- **[ClusterMind](projects/clustermind.md)**: A command-line tool that turns a short description of a web, SaaS, or self-hosted LLM service into a deterministic, auditable infrastructure capacity and cloud-cost plan.
- **[Hybrid Multi-Layer Control for Robust Autonomous Driving](projects/tesi-triennale.md)**: A bachelor's thesis and simulation framework for a layered learning-plus-model-based control stack that keeps a Formula Student driverless race car safe and accurate when tire grip and vehicle parameters are uncertain.

## Projects with code samples

| Project | What it is |
| --- | --- |
| [Anacleto](projects/anacleto-instagram.md) | A REST API and engine that analyzes Instagram images, computes an optimal feed order, schedules posts, and publishes them automatically through the official Meta Graph API. |
| [Aptus](projects/aptus.md) | A career-intelligence platform that aligns a candidate's CV with a job description and returns a scored, evidence-backed match that both recruiters and candidates can audit. |
| [ARBOR](projects/arbor.md) | A multi-tenant AI platform that discovers, enriches, and reasons over real-world entities, combining a knowledge graph, vector search, and an event-sourced data store. |
| [BOT Garage](projects/bot-garage.md) | A local-first workshop management application that tracks vehicle maintenance, costs, and documents, with OCR import of data straight from registration and invoice PDFs. |
| [ClusterMind](projects/clustermind.md) | A command-line tool that turns a short description of a web, SaaS, or self-hosted LLM service into a deterministic, auditable infrastructure capacity and cloud-cost plan. |
| [fast-inference](projects/fast-inference.md) | A self-hosted, OpenAI-compatible inference server for embedding, reranking, and generation models, built to keep retrieval-augmented generation (RAG) workloads fast and fully on-premise. || [MINERVA](projects/minerva.md) | An API-first OSINT engine that aggregates public cyber-threat data into a knowledge graph and answers natural-language questions about the threat landscape. |
| [NETWATCH](projects/netwatch.md) | A Linux endpoint security monitor that observes process, network, and file activity at the kernel level with eBPF, scores it against rules and machine-learning models, and dispatches alerts to a dashboard and SIEM systems. |
| [people-os](projects/people-os.md) | An AI-assisted hiring platform that exposes resume screening, interview scoring, and onboarding as Model Context Protocol (MCP) tools, paired with an evaluation framework that measures decision quality before changes ship. |
| [Porfirio Magazine](projects/porfirio-magazine.md) | A full-stack digital magazine platform that unifies bilingual publishing, payments, engagement analytics, and automated social-media content generation in a single product. |
| [Sentinel](projects/sentinel.md) | A multi-tenant document intelligence platform that extracts, scores, and attests risk in legal and financial documents, producing auditable findings instead of free-form summaries. |
| [Tappo](projects/tappo.md) | A native iOS app for tracking counts, habits, and goal progress across multiple projects, with Home Screen widgets and Lock Screen Live Activities that stay in sync with the app. |
| [Tay](projects/tay.md) | A native Apple-platform app that recognizes physical artworks and monuments through the camera and anchors real-time augmented-reality experiences on top of them. |
| [Hybrid Multi-Layer Control for Robust Autonomous Driving](projects/tesi-triennale.md) | A bachelor's thesis and simulation framework for a layered learning-plus-model-based control stack that keeps a Formula Student driverless race car safe and accurate when tire grip and vehicle parameters are uncertain. |

## Academic coursework

- [Academic coursework](projects/academic-coursework.md): graduate interactive-graphics and machine-learning assignments from the MSc in Robotics and Artificial Intelligence at Sapienza University of Rome, implemented from scratch.

---

_© 2026 Edoardo Caciolo, all rights reserved. Proprietary and not open source; source code is private and available for review on request._
