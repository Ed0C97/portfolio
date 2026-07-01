# NETWATCH: Detection and Alerting Layer

Two excerpts from NETWATCH, a Linux eBPF endpoint security monitor that scores kernel-level activity against rules and models and dispatches SIEM alerts.

**Context:** see [../netwatch.md](../netwatch.md) for the full project overview.

**Stack:** Python, asyncio, standard library. The eBPF and C capture layer and the trained models are omitted.

## What each file shows

- **`beaconing_detector.py`**: the interpretable command-and-control beaconing rule that runs alongside the ML detector. It scores how regular a connection series is from the coefficient of variation of its inter-arrival gaps, bounds the plausible beacon period, and adds a DNS high-frequency check, mapping a hit to a Cyber Kill Chain phase and a severity. The kill-chain module is stubbed to a minimal `Finding`.
- **`alert_dispatch.py`**: multi-channel alert fan-out. It formats a finding once and delivers it concurrently to isolated channels (syslog in CEF, webhook, file, WebSocket) so one dead sink cannot stall the others, with sliding-window deduplication in front to cut alert fatigue.

## Deliberately omitted

- The production-tuned detection constants (minimum samples, regularity threshold, period bounds, window sizes, DNS thresholds, and the confidence-curve coefficients) are the calibration moat and are replaced with labelled placeholders.
- The real SIEM identity (vendor, product, version) and the tuned CEF severity integers, which are part of the SIEM integration contract, are stubbed to example values.
- The webhook transport and retry policy (the async HTTP client, the exponential-backoff parameters, and bearer-token auth) are collapsed to a stub with no endpoint or credentials; the trained anomaly model behind the rules layer is not included.

_© 2026 Edoardo Caciolo, all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
