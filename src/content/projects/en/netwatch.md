---
title: "NETWATCH"
slug: "netwatch"
lang: "en"
oneLiner: "Kernel-level Linux endpoint monitor: eBPF event capture, rule-first plus ML detection, incident correlation, SIEM-ready alerting."
category: "Security & eBPF"
status: "Beta"
statusTone: "beta"
featured: true
visible: true
order: 8
metrics:
  - value: "4 programs"
    label: "eBPF capture: syscalls, network, filesystem, processes"
  - value: "25 rules"
    label: "deterministic detections mapped to MITRE ATT&CK"
stack: ["Python", "C (eBPF)", "FastAPI", "PyTorch", "scikit-learn", "TimescaleDB", "React 18"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/netwatch"
image: "/images/projects/netwatch.svg"
---

## The problem

When an attacker lands on a Linux host, everything that follows leaves traces at the kernel boundary: processes are spawned, system calls fire, network connections open, files are read and written. Most monitoring tools observe this activity from user space, one step removed, by polling /proc or tailing logs. That gap matters twice. First, malware running in user space can interfere with a user-space observer far more easily than with the kernel itself, so the telemetry an analyst trusts most is exactly the telemetry those tools cannot produce. Second, raw kernel activity is a firehose: a single busy host emits more events than any person can read, and an isolated event means nothing without the surrounding story. Host-based detection therefore needs three things at once: capture inside the kernel, a way to turn events into findings, and a way to condense findings into a handful of incidents a human can act on, delivered where security teams already work, their SIEM.

## What I built

NETWATCH is an endpoint security monitor for Linux that watches activity from inside the kernel. Small programs written in C, loaded through eBPF, attach to kernel tracepoints and record what every process does: the system calls it makes, the connections it opens, the files it touches, the children it spawns. That event stream feeds a detection engine that checks deterministic rules first, each mapped to a MITRE ATT&CK technique with a severity, a confidence and a recommended response, and consults machine-learning models only afterwards. Related findings are grouped into incidents rather than raised one by one. Alerts go out in parallel over Syslog, webhook, file and WebSocket, formatted as CEF and LEEF so that SIEM platforms such as Splunk, ArcSight and IBM QRadar ingest them directly. A React dashboard shows live events, incidents and process trees, and the whole system ships as a Docker Compose deployment.

## How it works

Four eBPF programs cover syscalls, network, filesystem and processes; they push events to user space through ring buffers, and 24 features are extracted per process every 60 seconds for the detection layer. The rule set holds 25 detections spanning the Cyber Kill Chain phases. The ML side complements it with an Isolation Forest that learns a behavioral baseline and an LSTM that looks for command-and-control beaconing patterns. The one non-obvious choice is the order: deterministic rules always run first and the ML path is a fallback, because a rule match is explainable and reproducible while an anomaly score is neither; with no models loaded the system still runs in rules-only mode. Downstream, a correlator clusters findings by temporal proximity, process lineage and kill-chain progression, alert channels are isolated with retry, backoff and duplicate suppression, and events persist to PostgreSQL with TimescaleDB hypertables through async SQLAlchemy and Alembic migrations, alongside bundled indicator-of-compromise feeds.

## Who it's for

There is no measured detection benchmark yet, so this section stays honest: NETWATCH is a beta-stage personal project, feature-complete across capture, detection, ML, alerting, API, dashboard, migrations and Docker/Compose deployment, not a published production release. It is aimed at security engineers and analysts who want host-based detection on Linux machines they control, and at teams that already run a SIEM and want kernel-level telemetry delivered in formats their tooling parses natively.

## Limits and what I'd redo

It requires a recent kernel (5.15 or later) and elevated BPF privileges, so it is not something you drop onto an arbitrary host. More importantly, detection quality is still a claim rather than a number: no false-positive rate has been measured on real, long-running workloads. If I started over, I would build the evaluation harness before extending the rule set, because 25 unmeasured rules are worth less than 10 measured ones.
