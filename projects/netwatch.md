# NETWATCH

> A Linux endpoint security monitor that observes process, network, and file activity at the kernel level with eBPF, scores it against rules and machine-learning models, and dispatches alerts to a dashboard and SIEM systems.

## Overview

NETWATCH watches what every process on a Linux host does at the kernel level and raises alerts when behavior matches a known attack pattern or deviates from a learned baseline. It captures activity in-kernel with eBPF, runs the event stream through a hybrid detection engine, and turns raw events into severity-ranked findings mapped to the Cyber Kill Chain and MITRE ATT&CK. It targets security analysts who need host-based detection that runs where user-space malware cannot easily hide from it.

## Highlights

- **Kernel-level event capture via eBPF.** In-kernel programs observe process execution, privilege changes, process tampering, network connections, and filesystem operations, streaming a typed event feed to user space with minimal overhead. Built on modern eBPF (CO-RE / BTF) for portability across recent kernels.
- **Hybrid detection engine.** A deterministic rule layer mapped to MITRE ATT&CK techniques runs alongside machine-learning anomaly detection (per-process behavioral anomaly scoring and detection of periodic command-and-control beaconing). The combination yields high-confidence findings on known attacks while still surfacing novel deviations, and degrades gracefully to a rules-only mode when models are unavailable.
- **Kill-chain coverage.** Detections span reconnaissance, execution, persistence, privilege escalation, defense evasion, lateral movement, process injection, C2 beaconing, and data exfiltration, each carrying severity, confidence, and a recommended response.
- **Incident correlation.** Individual findings are clustered into incidents by temporal proximity, process lineage, and kill-chain progression, cutting per-event noise into a smaller set of actionable records.
- **Multi-channel alerting.** Findings are emitted in SIEM-compatible formats (CEF, LEEF, Syslog) and delivered concurrently across Syslog, HTTP webhooks, file, and a live WebSocket feed, with channel isolation so one failing sink does not block the others and duplicate suppression to reduce alert fatigue.
- **REST API and web dashboard.** A FastAPI service exposes monitoring control, alerts, incidents, process, and baseline/training endpoints; a React single-page dashboard provides live event, alert, incident, and process-tree views.
- **Security hardening.** JWT authentication with role-based access, password hashing, request-ID and security-header middleware, and rate limiting.
- **Time-series persistence.** Events, alerts, and incidents are stored in a time-series-optimized datastore for efficient historical queries.
- **Threat intelligence.** Indicator-of-compromise matching against bundled malicious domain and IP feeds.

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| Languages | Python, C (eBPF programs), JavaScript |
| Kernel / eBPF | eBPF (CO-RE / BTF), kernel tracepoints, ring buffers, BPF maps |
| Backend | FastAPI, Uvicorn, Pydantic |
| Machine learning | PyTorch, scikit-learn, NumPy, pandas |
| Data stores | PostgreSQL with TimescaleDB |
| Persistence / migrations | SQLAlchemy (async), asyncpg, Alembic |
| Auth & security | JWT, bcrypt, rate limiting |
| Alerting / integration | CEF / LEEF / Syslog, HTTP webhooks, WebSockets |
| Observability | structlog, tenacity, PyYAML |
| Frontend | React, Vite, Tailwind CSS, Recharts |
| Infra / DevOps | Docker (multi-stage), Docker Compose, pytest, ruff |

## Status

Beta. Feature-complete across capture, detection, ML, alerting, API, dashboard, and a Docker/Compose deployment, with unit, integration, and validation test suites. Personal project, not a published production release.

Source code private and proprietary, code review available on request.

---

_© 2026 Edoardo Caciolo, all rights reserved. Proprietary and not open source; source code is private and available for review on request._
