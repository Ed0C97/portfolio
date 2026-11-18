# Edoardo Caciolo - Technical Portfolio

Public technical portfolio presenting the purpose, capabilities, engineering approach, architecture, and visual results of my software, AI, and product engineering projects.

**Contact:** [caciolo.edoardo@gmail.com](mailto:caciolo.edoardo@gmail.com) | **GitHub:** [github.com/Ed0C97](https://github.com/Ed0C97) | **LinkedIn:** [linkedin.com/in/edoardo-caciolo](https://www.linkedin.com/in/edoardo-caciolo)

---

## How This Portfolio Is Organized

Most projects presented here are proprietary SaaS platforms, vertical AI systems, or client products whose production repositories remain private to protect intellectual property.

Each folder in this repository acts as a self-contained **project showcase** following the same 8-section structure (`Project Overview`, `Objectives`, `Key Features`, `Development Approach`, `Architecture Overview`, `Screenshots & Demonstrations`, `Code Samples`, `Results`) and visual asset layout (`assets/previews/`, `assets/screenshots/`, `assets/diagrams/`), so any project can be understood in roughly 10 seconds.

For open academic projects, direct links to the full public source repositories are provided alongside their standardized showcase pages.

---

## AI, Data & SaaS Platforms

| Project | Domain | What It Does | Core Stack |
| :--- | :--- | :--- | :--- |
| **[Sentinel](sentinel/README.md)** | Enterprise Due Diligence & Risk | Extracts, verifies, scores, and cryptographically attests risk across credit, legal, and M&A dossiers with multi-stage citation grounding. | Python, FastAPI, PostgreSQL, Neo4j, Vector Search, vLLM |
| **[ARBOR](arbor/README.md)** | Vertical AI & Knowledge Graph | Discovers, curates, and connects 270 verified luxury ateliers, heritage brands, and cultural venues through hybrid retrieval and ontological reasoning. ([Live](https://arbor.porfiriomagazine.it)) | Python, FastAPI, React, Cloudflare Workers, Neo4j, Qdrant |
| **[Alatar](alatar/README.md)** | Career Intelligence & HR Tech | Aligns candidate CVs with job descriptions and returns scored, citation-backed match assessments auditable by both recruiters and candidates. | Python, FastAPI, Next.js, TypeScript, PostgreSQL |
| **[George](george/README.md)** | FinTech & Tax Compliance | 100% deterministic Italian *Regime Forfettario* platform uniting ATECO 2025 orientation, multi-scenario net-pay simulation, and XSD-validated FatturaPA e-invoicing. | Python, FastAPI, Next.js, TypeScript, PostgreSQL, Typst |
| **[13 Medical Record](13-medical-record/README.md)** | Digital Health & Encrypted Vault | Encrypted personal and family health vault with in-memory OCR biomarker extraction, multi-year longitudinal blood matrices, molecular allergy panels, and deductible expense tracking. | Python, FastAPI, Next.js, PostgreSQL (`FORCE RLS`), Vision OCR |
| **[Piero](piero/README.md)** | Local-First Workshop Software | Local-first multi-vehicle garage and maintenance manager featuring spare-parts inventory, suspendable insurance math, confidence-gated OCR import, and an offline AI assistant. | Python, SQLite / PostgreSQL, Local Ollama, Whisper, Vision OCR |

---

## Media, Connected Products, Native AR & Client Web

| Project | Domain | What It Does | Core Stack |
| :--- | :--- | :--- | :--- |
| **[Porfirio Magazine](porfirio-magazine/README.md)** | Digital Publishing & Edge Media | Bilingual (IT/EN) editorial platform and 270-venue interactive directory running at the edge and synchronized 1:1 with ARBOR. ([Live](https://porfiriomagazine.it)) | React, Python, Cloudflare Workers, D1, R2, Capacitor |
| **[Fourth Form](fourth-form/README.md)** | Connected Garments & NFC Provenance | Editorial platform and NFC chain-of-custody archive for numbered Italian wearable-art garments, featuring OTP ownership transfers and a 2D mockup studio. ([Live](https://fourthform.it)) | Next.js, React, TypeScript, Cloudflare Workers, D1, R2 |
| **[Tay](tay/README.md)** | Native Apple AR & Computer Vision | Multi-platform Swift AR application and microservice pipeline for on-device artwork/monument recognition, steganographic canvas verification, and grounded audio narration. | Swift, RealityKit, Core ML, FastAPI, DINOv3, PostgreSQL |
| **[Client Web Platforms](web-projects/README.md)** | Bespoke Client Web Engineering | Two token-driven production web platforms: **Differo** (curated Rome/Milan direct-booking hospitality) and a **Clinical Psychology Practice** platform (WCAG 2.2 AA & CNOP-compliant). | Next.js, React, TypeScript, CSS Tokens, Zod, Cloudflare |

---

## Open Academic Projects (Full Source Public)

| Project | Showcase | Full Source Repository | Summary |
| :--- | :--- | :--- | :--- |
| **Interactive Graphics Projects** | **[Showcase](interactive-graphics/README.md)** | **[Ed0C97/marr-interactive-graphics-projects](https://github.com/Ed0C97/marr-interactive-graphics-projects)** | Six dependency-free browser implementations covering alpha compositing, 2D affine transforms, WebGL textured meshes, Blinn-Phong shading, GLSL GPU ray tracing, and mass-spring physics (Sapienza MSc Robotics & AI). |
| **Machine Learning Projects** | **[Showcase](machine-learning/README.md)** | **[Ed0C97/marr-ml-projects](https://github.com/Ed0C97/marr-ml-projects)** | Six-classifier accuracy-vs-compute benchmark on high-dimensional tabular data and closed-loop CNN autonomous driving policies in Gymnasium `CarRacing-v2` (Sapienza MSc Robotics & AI). |

---

## Repository Structure

```text
portfolio/
├── README.md                     # Master portfolio index
├── 13-medical-record/            # Encrypted personal & family medical vault
├── alatar/                       # Explainable CV-to-job career intelligence
├── arbor/                        # Multi-tenant ontological entity discovery
├── fourth-form/                  # Wearable art & NFC chain-of-custody platform
├── george/                       # Deterministic Italian tax & FatturaPA SaaS
├── interactive-graphics/         # WebGL, GLSL ray tracing & physics (links to public repo)
├── machine-learning/             # Classifier benchmarks & CNN control (links to public repo)
├── piero/                        # Local-first multi-vehicle workshop manager
├── porfirio-magazine/            # Bilingual digital magazine & 270-venue edge directory
├── sentinel/                     # Grounded enterprise due-diligence & risk platform
├── tay/                          # Native Apple AR cultural guide & canvas verification
└── web-projects/                 # Differo hospitality & clinical psychology web platforms
```

---

_Copyright (c) 2026 Edoardo Caciolo. Proprietary project showcases are shared for technical evaluation; original production source code remains private and is available for review upon request._
