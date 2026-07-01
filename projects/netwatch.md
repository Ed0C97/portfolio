# NETWATCH

> A Linux endpoint security monitor that observes process, network, and file activity at the kernel level with eBPF, scores it against rules and machine-learning models, and dispatches alerts to a dashboard and SIEM systems.

## Overview

NETWATCH watches what every process on a Linux host does at the kernel level and raises alerts when behavior matches a known attack pattern or deviates from a learned baseline. It captures activity in-kernel with eBPF (using CO-RE and BTF for portability across recent kernels), runs the event stream through a hybrid detection engine, and turns raw events into severity-ranked findings mapped to the Cyber Kill Chain and MITRE ATT&CK.

## Decisions worth defending

- **Hybrid detection with graceful fallback.** A deterministic rule layer mapped to ATT&CK techniques runs alongside machine-learning anomaly scoring (per-process behavior and periodic command-and-control beaconing). Known attacks produce high-confidence rule hits, novel deviations still surface through the models, and when a model is unavailable the engine degrades to rules-only mode rather than failing.
- **Channel-isolated alerting.** Findings are emitted in SIEM formats (CEF, LEEF, Syslog) and delivered concurrently across Syslog, HTTP webhooks, file, and a live WebSocket, with each sink isolated so one failing channel does not block the others, plus duplicate suppression to cut alert fatigue.

## Tech stack

Python user space with C eBPF programs (tracepoints, ring buffers, BPF maps); FastAPI backend; PyTorch and scikit-learn for the models; PostgreSQL with TimescaleDB for time-series persistence; a React dashboard; Docker for deployment.

## Status

Personal project, not a published production release. Source code private and proprietary; a full code review can be provided on request.

---

## Code sample

A small, IP-safe excerpt is in [`netwatch/`](./netwatch/): the interpretable C2 beaconing rule (regularity from the coefficient of variation of connection inter-arrival gaps, plus period bounds and a DNS high-frequency check), and channel-isolated alert dispatch that formats findings as ArcSight CEF and fans them out to multiple SIEM channels without letting one dead sink block the others. The trained anomaly model, the tuned detection thresholds, and the real SIEM identity are stubbed.

_© 2026 Edoardo Caciolo, all rights reserved. Proprietary and not open source; source code is private and available for review on request._
