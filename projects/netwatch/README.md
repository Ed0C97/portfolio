# NETWATCH: Alerting Layer

An excerpt from NETWATCH, a Linux eBPF endpoint security monitor that scores kernel-level activity against rules and models and dispatches SIEM alerts.

**Context:** see [../netwatch.md](../netwatch.md) for the full project overview.

**Stack:** Python, asyncio, standard library. The eBPF and C capture layer, the detection engine, and the trained models are omitted.

## What each file shows

- **`alert_dispatch.py`**: multi-channel alert fan-out. It formats a finding once and delivers it concurrently to isolated channels (syslog in CEF, webhook, file, WebSocket) so one dead sink cannot stall the others, with sliding-window deduplication in front to cut alert fatigue.

## Deliberately omitted

- The detection engine, its rules, and its production-tuned constants are the calibration moat and are not included.
- The real SIEM identity (vendor, product, version) and the tuned CEF severity integers, which are part of the SIEM integration contract, are stubbed to example values.
- The webhook transport and retry policy (the async HTTP client, the exponential-backoff parameters, and bearer-token auth) are collapsed to a stub with no endpoint or credentials; the trained anomaly model behind the rules layer is not included.

_© 2026 Edoardo Caciolo, all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
