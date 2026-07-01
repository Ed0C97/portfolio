# NETWATCH: Detection and Alerting Layer

Two excerpts from NETWATCH, a Linux eBPF endpoint security monitor that scores kernel-level activity against rules and models and dispatches SIEM alerts.

**Context:** see [../netwatch.md](../netwatch.md) for the full project overview.

**Stack:** Python, asyncio, standard library. The eBPF and C capture layer and the trained models are omitted.

## What each file shows

- **`beaconing_detector.py`**: the cheap, interpretable C2 beaconing signal that runs ahead of the trained anomaly model. Scores how periodic a connection series is from the coefficient of variation of inter-arrival gaps (CV = std / mean), maps CV onto a bounded regularity score with `1 / (1 + CV)`, sorts defensively for out-of-order eBPF ring-buffer events, and offers an optional jitter-tolerance pre-filter that snaps gaps within a band of the mean back to the mean so intentional implant jitter does not mask the beacon.
- **`alert_dispatch.py`**: channel-isolated async fan-out of a finding to multiple SIEM sinks. Formats each finding once as an ArcSight CEF line (with the two distinct header versus extension escaping rules), fans out concurrently with `asyncio.gather(..., return_exceptions=True)` so one dead sink cannot cancel or stall the others, logs per-sink failures, and suppresses duplicate findings inside a TTL window with a bounded, time-ordered seen-set.

## Deliberately omitted

- The trained anomaly model (per-process behavior and the learned beaconing classifier) and the per-environment tuning it feeds; the CV detector shown here is the rules-layer fallback, not the model.
- The real sink endpoints (Syslog, HTTP webhook, file, WebSocket transports) behind the `AlertSink` Protocol, and the full CEF and LEEF signature catalog that maps detections to ATT&CK techniques.
- All thresholds and windows shown here (minimum event count, regularity threshold, jitter tolerance, dedup TTL, seen-set cap) are illustrative defaults, not tuned production values.

_© 2026 Edoardo Caciolo, all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
