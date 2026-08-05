# Edoardo Caciolo: Project Portfolio

> Overview documentation for my projects. **Source code is private (not published); most projects are proprietary.** These pages describe what each system does and how it is built, without the implementation. Code review available on request.

**Contact:** caciolo.edoardo@gmail.com, [github.com/Ed0C97](https://github.com/Ed0C97), [linkedin.com/in/edoardo-caciolo](https://www.linkedin.com/in/edoardo-caciolo)

## How to read this portfolio

Projects come in two kinds, kept separate on purpose:

- **Projects with code samples** carry a folder with a short README and a few IP-safe excerpts, adapted and trimmed so each file reads standalone. The excerpts show the engineering (patterns, algorithms, resilience), never the proprietary core.
- **Additional projects** are described at the design and capability level, with no code sample published. A sample or review can be arranged on request.

Images referenced by any page live in `projects/images/<project-slug>/`, never beside the code samples, so a code folder stays code only.

## What the code samples demonstrate

The published excerpts are chosen to show concrete engineering, each tied to the project that evidences it:

- **Information retrieval and ranking**: hybrid dense-plus-sparse retrieval, Reciprocal Rank Fusion, and a cost-aware reranking funnel that degrades gracefully when a model provider is slow or down ([ARBOR](projects/arbor.md)).
- **Control and estimation math**: Unscented Kalman Filter state estimation and LPV discretization for a vehicle control stack ([thesis](projects/tesi-triennale.md)); numerically stable Erlang-B and Erlang-C queueing for capacity planning ([ClusterMind](projects/clustermind.md)).
- **Native Apple platforms**: real-time camera-quality signal processing and augmented-reality lifecycle handling in Swift ([Tay](projects/tay.md)); hand-laid PDF and CSV export ([Tappo](projects/tappo.md)).
- **Resilience and operability**: circuit breakers on a monotonic clock, multi-backend secret resolution, and graceful-degradation fallbacks ([Sentinel](projects/sentinel.md), [fast-inference](projects/fast-inference.md)).
- **Security-conscious design**: SSRF and DNS-rebinding defense on a local gateway, injection-safe SQL over a recursive CTE, and fail-closed field encryption ([BOT Garage](projects/bot-garage.md), [Alatar](projects/alatar.md)).
- **Threat detection and intelligence**: channel-isolated SIEM alerting in ArcSight CEF that never lets one dead sink block the others ([NETWATCH](projects/netwatch.md)); cross-source entity resolution into a knowledge graph and read-only-by-construction query safety ([MINERVA](projects/minerva.md)).
- **AI evaluation**: dependency-free IR metrics shared by an eval harness and its metrics exporters so reported and dashboarded numbers cannot drift, and a judges-off-versus-judges-on benchmark that gates a verification layer on accuracy gain, false-positive reduction, and latency overhead together ([Sentinel](projects/sentinel.md)).
- **Trustworthy data capture**: confidence-gated OCR field extraction that persists a field only above a confidence threshold and routes weaker matches to human review ([BOT Garage](projects/bot-garage.md)).

## Featured

- **[ARBOR](projects/arbor.md)**: A multi-tenant AI platform that discovers, enriches, and reasons over real-world entities, combining a knowledge graph, vector search, and an event-sourced data store. The published excerpt is its search and ranking engine: hybrid retrieval with RRF fusion and a cost-aware reranking funnel that degrades gracefully when a model provider is slow or down.
- **[Sentinel](projects/sentinel.md)**: A multi-tenant document intelligence platform for credit and risk teams that extracts, verifies, scores, and attests risk in due-diligence documentation. Every finding passes a grounding and coverage gate before acceptance, and reproducibility is enforced end to end: batch-invariant deterministic serving under multi-tenant concurrency, and extraction measured against golden sets in CI.
- **[Alatar](projects/alatar.md)**: A career-intelligence platform that aligns a candidate's CV with a job description and returns a scored, evidence-backed match that both recruiters and candidates can audit.
- **[Tay](projects/tay.md)**: A native Apple-platform app that recognizes physical artworks and monuments through the camera and anchors real-time augmented-reality experiences on top of them.
- **[fast-inference](projects/fast-inference.md)**: A self-hosted, OpenAI-compatible inference server for embedding, reranking, and generation models: INT8 static quantization, hand-written Triton GPU kernels, asynchronous dynamic batching, and a benchmark harness that discovers what the current machine can run and attaches the hardware to every measurement. Ships a self-contained operator dashboard.
- **[ClusterMind](projects/clustermind.md)**: A command-line tool that turns a short description of a web, SaaS, or self-hosted LLM service into a deterministic, auditable infrastructure capacity and cloud-cost plan.
- **[Hybrid Multi-Layer Control for Robust Autonomous Driving](projects/tesi-triennale.md)**: A bachelor's thesis and simulation framework for a layered learning-plus-model-based control stack that keeps a Formula Student driverless race car safe and accurate when tire grip and vehicle parameters are uncertain.

## Projects with code samples

| Project | What it is |
| --- | --- |
| [Anacleto](projects/anacleto-instagram.md) | A FastAPI platform that analyzes Instagram images with vision models, optimizes feed order via MCTS, Beam Search, or Greedy strategies, schedules posts, and publishes through the Meta Graph API. |
| [Alatar](projects/alatar.md) | A career-intelligence platform that aligns a candidate's CV with a job description and returns a scored, evidence-backed match that both recruiters and candidates can audit. |
| [ARBOR](projects/arbor.md) | A multi-tenant AI platform that discovers, enriches, and reasons over real-world entities, combining a knowledge graph, vector search, and an event-sourced data store. |
| [BOT Garage](projects/bot-garage.md) | A local-first workshop management application that tracks vehicle maintenance, costs, and documents, with OCR import of data straight from registration and invoice PDFs. |
| [ClusterMind](projects/clustermind.md) | A command-line tool that turns a short description of a web, SaaS, or self-hosted LLM service into a deterministic, auditable infrastructure capacity and cloud-cost plan. |
| [fast-inference](projects/fast-inference.md) | A self-hosted, OpenAI-compatible inference server for embedding, reranking, and generation models, built to keep retrieval-augmented generation (RAG) workloads fast and fully on-premise. Ships an operator dashboard and a benchmark harness that reports the machine behind every number. |
| [MINERVA](projects/minerva.md) | An API-first OSINT engine that aggregates public cyber-threat data into a knowledge graph and answers natural-language questions about the threat landscape. |
| [NETWATCH](projects/netwatch.md) | A Linux endpoint security monitor that observes process, network, and file activity at the kernel level with eBPF, scores it against rules and machine-learning models, and dispatches alerts to a dashboard and SIEM systems. |
| [Porfirio Magazine](projects/porfirio-magazine.md) | A full-stack digital magazine platform that unifies bilingual publishing, payments, engagement analytics, and automated social-media content generation in a single product. |
| [Sentinel](projects/sentinel.md) | A multi-tenant document intelligence platform for credit and risk teams that extracts, verifies, scores, and attests risk in due-diligence documentation, producing grounded, reproducible findings instead of free-form summaries. |
| [Tappo](projects/tappo.md) | A native iOS app for tracking counts, habits, and goal progress across multiple projects, with Home Screen widgets and Lock Screen Live Activities that stay in sync with the app. |
| [Tay](projects/tay.md) | A native Apple-platform app that recognizes physical artworks and monuments through the camera and anchors real-time augmented-reality experiences on top of them. |
| [Hybrid Multi-Layer Control for Robust Autonomous Driving](projects/tesi-triennale.md) | A bachelor's thesis and simulation framework for a layered learning-plus-model-based control stack that keeps a Formula Student driverless race car safe and accurate when tire grip and vehicle parameters are uncertain. |

## Academic coursework

- [Academic coursework](projects/academic-coursework.md): graduate-level interactive-graphics and machine-learning assignments (Sapienza University of Rome), implemented from scratch.

---

_© 2026 Edoardo Caciolo, all rights reserved. Source code is private and available for review on request._

# Edoardo Caciolo · Portfolio

Personal portfolio site. Bilingual (EN default, IT under `/it/`), dark theme only, static build, zero client-side frameworks. Built with [Astro 5](https://astro.build). The design system (palette, radii, buttons, badges, cards) is ported from the Alatar project's `tokens.css`: 5 greys plus 3 accents, flat surfaces with 1px ink borders, yellow as the only action colour. UI arrows are always the inline SVG `Icon.astro` component (never text arrows), so hover motion stays consistent.

## Commands

```bash
npm install        # once
npm run dev        # http://localhost:4321
npm run build      # static output in dist/
npm run preview    # serve dist/ locally
```

## How content works

Every project is a pair of markdown files in `src/content/projects/`:

```
sentinel.en.md
sentinel.it.md
```

The frontmatter drives everything; the two switches you will actually touch:

| Field      | Effect                                                        |
| ---------- | ------------------------------------------------------------- |
| `visible`  | `false` removes the project from the whole site               |
| `featured` | `true` shows it on the home page grid (keep it to 6-8)        |
| `order`    | Sort position everywhere (1 = first)                          |

To add a project: copy an existing pair, change the frontmatter, write the five body sections (The problem / What I built / How it works / Results / Limits and what I'd redo). Both language files must exist.

Facts policy: every number and status comes from the verified content library in the CV repository (`CV/cv_master/content/`). Never promote a status, never add unmeasured metrics. No em dash anywhere.

## Images

All project images are placeholders in `public/images/projects/<slug>.svg` (1200x675, 16:9). Replace each with a real screenshot or render at the same path, any format (`.png`, `.webp`, `.jpg`), then update the `image:` field in both language files of that project.

The typewriter roles, hero stats, about, experience, skills and education all live in `src/data/profile.ts`. UI strings (nav, section titles, buttons) live in `src/i18n/ui.ts`.

## Language

EN at `/`, IT at `/it/`; the header toggle maps the current page to its twin. The site is dark-only: all colours live in `src/styles/tokens.css`, nothing is hardcoded in components.

## Deploying later (GitHub Pages)

The site is local-only for now. When you decide to publish:

1. Set `site` in `astro.config.mjs` (e.g. `https://ed0c97.github.io`) and, if the repo is not `<user>.github.io`, also `base: '/<repo-name>'`.
2. Push to GitHub and enable Pages with the official Astro GitHub Action (`withastro/action`).
3. Custom domain: set `site` to the domain, add the `CNAME` file in `public/`.
