# MINERVA

> An API-first OSINT engine that aggregates public cyber-threat data into a knowledge graph and answers natural-language questions about the threat landscape.

Described at the design and capability level; no code sample is published for this project. A code review can be arranged on request.

## Overview

MINERVA is a cyber threat intelligence (CTI) service. It collects open-source intelligence on IP addresses, domains, vulnerabilities, and threat actors from multiple public sources, resolves those signals into a single correlated knowledge graph, and lets analysts query the result in plain language. It is built as a REST backend so other systems can consume it rather than use it as a standalone tool. Findings are aligned to MITRE ATT&CK and can be exported as STIX 2.1.

## Decisions worth defending

- **Cross-source entity resolution.** Signals describing the same real-world entity across different sources are merged into one canonical node, so the graph is deduplicated rather than fragmented per source. This is the part that makes attribution and attack-surface queries meaningful.
- **Read-only query safety by construction.** The natural-language interface is structurally prevented from mutating or exhausting the graph, so an untrusted question cannot trigger a harmful operation. Safety is enforced by the query layer, not by prompt instructions.

## Tech stack

Python and FastAPI backend; Neo4j for the knowledge graph; PostgreSQL and Redis for relational state and caching; an LLM for natural-language querying over the graph; Docker for deployment.

## Status

Private project, sole architect and developer. Described here without a code sample; a sample or code review can be provided on request.

---

_© 2026 Edoardo Caciolo, all rights reserved. Proprietary and not open source; source code is private and available for review on request._
