"""Channel-isolated SIEM alert dispatch. Portfolio excerpt, adapted.

A finding has to reach several places at once (syslog, an HTTP webhook, a file,
a live WebSocket) and one dead endpoint must not stall or drop the others. So
each sink is an injected async Protocol and the fan-out uses
asyncio.gather(..., return_exceptions=True): every sink is awaited
concurrently, a failure comes back as a value rather than cancelling its
siblings, and we log per-sink. A short-TTL seen-set drops duplicate findings so
one flapping condition does not flood the SIEM. Real sink endpoints and the CEF
signature catalog are stubbed here.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Finding:
    """One detection result, ready to be formatted and shipped."""

    signature_id: str  # stable id, e.g. an ATT&CK technique like T1071
    name: str  # human-readable title
    severity: int  # ArcSight scale, 0 (info) to 10 (critical)
    source_host: str
    dest_host: str
    attributes: dict[str, str] = field(default_factory=dict)  # CEF extensions

    def identity(self) -> tuple[str, str, str]:
        """Key used for duplicate suppression.

        Same signature on the same source/destination pair is "the same alert"
        for suppression purposes, even if a volatile field (a timestamp, a byte
        count) differs. Volatile attributes are deliberately excluded.
        """
        return (self.signature_id, self.source_host, self.dest_host)


@runtime_checkable
class AlertSink(Protocol):
    """A destination for a formatted alert. Real impls live outside this excerpt."""

    name: str

    async def send(self, cef_message: str, finding: Finding) -> None:
        """Deliver one alert. Raise on failure; the dispatcher isolates it."""
        ...


# --- CEF formatting -------------------------------------------------------

_CEF_VERSION = "CEF:0"
_VENDOR = "NetWatch"
_PRODUCT = "EndpointMonitor"
_PRODUCT_VERSION = "1.0"

# ArcSight CEF has two escaping rules. In the pipe-delimited header, backslash
# and pipe are escaped. In the key=value extension, backslash, equals, and both
# line breaks are escaped (pipe is a literal there). Getting these wrong
# silently corrupts events in the SIEM, so the two are kept separate on purpose.
_HEADER_ESCAPE = str.maketrans({"\\": "\\\\", "|": "\\|"})


def _escape_header(value: str) -> str:
    return value.translate(_HEADER_ESCAPE)


def _escape_extension(value: str) -> str:
    # Order matters: escape backslashes first, or we double-escape the escapes.
    # CR and LF get distinct tokens (\r and \n); the CEF spec allows both and a
    # value can legitimately carry either, so we preserve rather than normalize.
    return (
        value.replace("\\", "\\\\")
        .replace("=", "\\=")
        .replace("\r", "\\r")
        .replace("\n", "\\n")
    )


def format_cef(finding: Finding) -> str:
    """Render a Finding as one ArcSight CEF line.

    Layout is the public standard:
    CEF:0|Vendor|Product|Version|SignatureID|Name|Severity|ext key=val ...
    """
    header = "|".join(
        (
            _CEF_VERSION,
            _escape_header(_VENDOR),
            _escape_header(_PRODUCT),
            _escape_header(_PRODUCT_VERSION),
            _escape_header(finding.signature_id),
            _escape_header(finding.name),
            str(finding.severity),
        )
    )

    extensions = {
        "src": finding.source_host,
        "dst": finding.dest_host,
        **finding.attributes,
    }
    ext_str = " ".join(
        f"{_escape_extension(k)}={_escape_extension(str(v))}"
        for k, v in extensions.items()
    )
    return f"{header}|{ext_str}"


# --- Dispatch -------------------------------------------------------------


class _DuplicateSuppressor:
    """Bounded, time-ordered seen-set. Drops repeats within a TTL window.

    OrderedDict keeps insertion order so expiry is a cheap walk from the oldest
    entry; we stop at the first live one. A hard cap bounds memory even if a
    burst of unique findings arrives faster than they expire.
    """

    def __init__(self, ttl_s: float, max_entries: int = 10_000):
        self._ttl_s = ttl_s
        self._max_entries = max_entries
        self._seen: OrderedDict[tuple[str, str, str], float] = OrderedDict()

    def should_send(self, finding: Finding, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        self._expire(now)
        key = finding.identity()
        if key in self._seen:
            return False
        self._seen[key] = now
        if len(self._seen) > self._max_entries:
            self._seen.popitem(last=False)  # evict oldest
        return True

    def _expire(self, now: float) -> None:
        cutoff = now - self._ttl_s
        while self._seen:
            key, seen_at = next(iter(self._seen.items()))
            if seen_at > cutoff:
                break  # everything after this is newer; OrderedDict is ordered
            self._seen.popitem(last=False)


class AlertDispatcher:
    """Format a finding once, fan it out to every sink, isolate failures."""

    def __init__(self, sinks: list[AlertSink], dedup_ttl_s: float = 30.0):
        self._sinks = sinks
        self._suppressor = _DuplicateSuppressor(ttl_s=dedup_ttl_s)

    async def dispatch(self, finding: Finding) -> None:
        """Send one finding to all sinks concurrently; never raise for a sink.

        Returns after every sink has settled. Duplicate findings inside the TTL
        window are dropped before any sink is touched.
        """
        if not self._suppressor.should_send(finding):
            logger.debug(
                "[dispatch] suppressed duplicate %s", finding.identity()
            )
            return

        if not self._sinks:
            return

        cef = format_cef(finding)

        # return_exceptions=True is the crux: one sink raising must not cancel
        # the gather and starve the others. Failures come back as values we
        # inspect and log, keeping the channels isolated by construction.
        results = await asyncio.gather(
            *(sink.send(cef, finding) for sink in self._sinks),
            return_exceptions=True,
        )

        for sink, result in zip(self._sinks, results):
            if isinstance(result, Exception):
                logger.error(
                    "[dispatch] sink '%s' failed for %s: %s",
                    sink.name, finding.signature_id, result,
                )
