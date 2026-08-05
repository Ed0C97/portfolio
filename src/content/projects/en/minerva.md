---
title: "MINERVA"
slug: "minerva"
lang: "en"
oneLiner: "Multi-source OSINT engine that correlates public threat data in a Neo4j knowledge graph and answers natural-language questions."
category: "OSINT & Knowledge Graph"
status: "Beta"
statusTone: "beta"
featured: false
visible: true
order: 9
metrics:
  - value: "5 sources"
    label: "Async collectors: Shodan, OTX, CVE/NVD, DNS, WHOIS"
  - value: "20 profiles"
    label: "Curated APT profiles used for evidence-ranked attribution"
stack: ["Python", "FastAPI", "LangGraph", "Cohere", "Neo4j", "PostgreSQL", "Docker"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/minerva"
image: "/images/projects/minerva.svg"
---

## The problem

Public information about cyber threats is abundant and almost unusable in its raw form. Shodan knows which hosts expose which ports, AlienVault OTX publishes indicators of compromise, the NVD catalogues vulnerabilities, DNS and WHOIS records describe infrastructure. Each source has its own API, its own rate limits, its own identifiers, and no notion of the others. The same IP address shows up in three feeds as three unrelated records. An analyst investigating an incident pivots between browser tabs, deduplicates by hand, and keeps the actual intelligence, the connections between an actor, its techniques and its infrastructure, in their head or in a spreadsheet. Graph databases can hold those connections, but querying them means learning a query language most analysts have no time for. And any pipeline built on public feeds has to survive the feeds themselves: keys expire, APIs go down, and a collector that fails hard turns one missing source into zero output.

## What I built

MINERVA automates that collection and correlation cycle end to end. It pulls data from five public sources (Shodan, OTX, CVE/NVD, DNS, WHOIS), recognises when different sources are describing the same real-world artifact, and merges everything into a single knowledge graph of IP addresses, domains, organisations, vulnerabilities, techniques, threat actors and campaigns. On top of that graph sits a plain-language interface: an analyst asks a question in English and gets an answer in prose, backed by the graph rather than by a model's imagination. Findings can leave the system as STIX 2.1 bundles, the standard exchange format for threat intelligence, or as PDF, Markdown and JSON reports. The whole thing is API-first: it runs standalone with Docker and exposes a REST API with authentication and role-based access control, so another platform can use it as a threat-intelligence service rather than a tool someone has to sit in front of.

## How it works

Five asynchronous collectors fetch from the source APIs, each rate-limited and built to fail soft: when a key is missing or a source is down, the run still yields a graph from what remains. A LangGraph pipeline orchestrates collection, correlation and enrichment, then writes typed nodes and relationships (ATTRIBUTED_TO, USES_TTP, EXPLOITS_CVE) into Neo4j. Techniques are validated against MITRE ATT&CK and scored for confidence, and an attribution engine ranks an entity's overlap with 20 documented APT profiles, returning the evidence behind each candidate rather than a bare name. Natural-language questions are translated into graph queries by a Cohere reasoning model grounded in the graph schema. The non-obvious choice sits here: the query engine is read-only by construction, with a validation step before execution, because letting a language model write arbitrary queries against an intelligence store is how you corrupt it. Collection runs as async jobs (202 Accepted, progress over SSE), with JWT, RBAC and append-only audit logging.

## Who it's for

MINERVA targets cyber threat intelligence analysts and, through its REST API, the platforms they work in: it is designed to be embedded as a service, not adopted as yet another dashboard. The project is in beta at version 1.0.0, feature-complete, with a Docker Compose deployment, but it remains a personal project.

## Limits and what I'd redo

Attribution is only as wide as its profile set: with 20 curated APT profiles, an actor outside that set cannot be named, and no confidence score fixes a coverage gap. If I rebuilt it, I would start with the analyst-facing side: the value of the system is the graph, and it deserves an interface that lets you walk it instead of only querying it through the API.
