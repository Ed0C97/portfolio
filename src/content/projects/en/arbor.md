---
title: "ARBOR"
slug: "arbor"
lang: "en"
oneLiner: "Multi-tenant AI platform that discovers, enriches and reasons over real-world entities via knowledge graph and vector search."
category: "Distributed Systems & AI Search"
status: "Active development"
statusTone: "beta"
featured: true
visible: true
order: 3
metrics:
  - value: "4 stores"
    label: "PostgreSQL, Neo4j, Qdrant and Redis behind one API"
  - value: "5 stages"
    label: "Temporal enrichment pipeline with per-activity retry"
stack: ["Python 3.12", "FastAPI", "PostgreSQL", "Neo4j", "Qdrant", "Temporal.io", "Kubernetes"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/arbor"
image: "/images/projects/arbor.svg"
---

## The problem

Information about real-world entities (a venue, a brand, a product) is scattered across maps listings, social profiles and websites, and it goes stale quickly. A product that wants to recommend "a quiet wine bar with natural wines near the station" needs more than a row in a table: it needs the entity's attributes, its relationships to other entities, a semantic representation of what the place is like, and some record of where each claim came from. The usual shortcuts all break somewhere. Keyword search over a relational database cannot answer semantic queries. A vector index alone loses relationships and structure. Ad-hoc enrichment scripts overwrite yesterday's data with today's, so when an AI pipeline writes something wrong there is no history to roll back to and no audit trail to inspect. And if the system serves several customers, each with their own catalogue, their data has to stay strictly apart.

## What I built

ARBOR (Advanced Reasoning By Ontological Rules) is a multi-tenant platform that ingests entities from external sources, enriches them through a multi-stage AI pipeline, and exposes them for semantic discovery and conversational querying. Scrapers collect raw material from Google Maps, Instagram and generic web pages; an enrichment pipeline analyzes, scores and validates it; the result lands in a knowledge graph, a vector index and an event-sourced record. On top sits an agentic search flow: a query is classified, routed to parallel vector and metadata searches, and assembled into an answer by a curator step. The platform is a monorepo with a FastAPI backend, a React web client, an Expo mobile client and a Kubernetes-based infrastructure layer. Domain behaviour (entity categories, scoring dimensions, prompts, ontologies) lives in YAML configuration rather than code, so a new vertical can be added by editing config files. Each tenant's data lives in its own database schema.

## How it works

The one non-obvious choice is the storage model: the source of truth is an append-only PostgreSQL event store with optimistic concurrency, snapshots and read-model projections, and a transactional outbox publishes domain events to Kafka. I chose event sourcing because enrichment rewrites entities constantly: with a full event history, a bad AI-generated write can be traced and replayed instead of silently replacing good data. Discovery runs on a LangGraph state machine (intent router, parallel vector and metadata agents, historian, curator) compiled once at startup, with a PostgreSQL checkpointer so a session can resume where it stopped. Enrichment is a five-stage Temporal workflow (collect, analyze, score, validate, persist) with per-activity retry and timeouts. Retrieval combines hybrid dense plus sparse vector search with BGE reranking over Qdrant, and GraphRAG and HippoRAG over the Neo4j graph. Four data stores share the work: PostgreSQL with PostGIS, Neo4j, Qdrant and Redis. Design decisions are recorded as ADRs.

## Who it's for

Teams building contextual discovery and recommendation products over curated entity data: local-discovery apps, brand and venue directories, vertical search. It is an active private project, not in production; the backend reports version 1.1.0, and the codebase, over 4 MB of Python, carries unit, integration, end-to-end, chaos, load (k6) and red-team (promptfoo) test suites.

## Limits and what I'd redo

The breadth is the honest limit: coverage and maturity vary by module, and the backend depends on private sibling toolkits, so nobody can run it standalone without access to those repositories. If I started again I would prove one vertical end to end before building a web client, a mobile client and a full GitOps infrastructure layer around it. The architectural core (event store, agent graph, enrichment workflow) is the part I would keep as is.
