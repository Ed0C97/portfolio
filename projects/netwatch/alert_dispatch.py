"""Portfolio excerpt, adapted. Multi-channel alert dispatch for a network
monitoring service: fan-out delivery to syslog (CEF), webhook, file, and
WebSocket channels, with sliding-window deduplication in front. Internal
settings, the real SIEM vendor identity, tuned severity maps, retry
thresholds, and detection-model types are stubbed so this reads on its own.
"""

from __future__ import annotations

import asyncio
import re
import socket
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

# Stubs for internal modules (real project wires httpx, tenacity, structlog,
# a Pydantic Alert model, and a config-driven settings object).


class AlertSeverity(str, Enum):
    """Ordinal severity; real product has a richer taxonomy."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Trimmed stand-in for the real Pydantic alert model."""

    id: str
    signature_id: str
    signature_name: str
    severity: AlertSeverity
    source_host: str
    dest_host: str
    evidence: str
    last_seen: datetime
    count: int = 1
    anomaly_score: float | None = None

    def to_json(self) -> str:
        # Real model serialises via Pydantic; kept trivial here on purpose.
        return f'{{"id": "{self.id}", "sig": "{self.signature_id}", "count": {self.count}}}'


# Tuned in the real product from field data. Stubbed placeholders here: the
# exact CEF severity integers are part of the SIEM integration contract.
_SEVERITY_INT: dict[AlertSeverity, int] = {
    AlertSeverity.LOW: 0,  # stub
    AlertSeverity.MEDIUM: 0,  # stub
    AlertSeverity.HIGH: 0,  # stub
    AlertSeverity.CRITICAL: 0,  # stub
}


class _Settings(Protocol):
    """Shape of the injected config. Real values come from the env-backed store."""

    siem_syslog_host: str | None
    siem_syslog_port: int
    siem_syslog_protocol: str
    siem_webhook_url: str | None
    alert_file_path: str | None
    alert_dedup_window_seconds: int


# ---------------------------------------------------------------------------
#  CEF FORMATTER
# ---------------------------------------------------------------------------

# Real product ships a vendor/product identity registered with the SIEM. The
# exact strings are stubbed: they are part of the commercial integration.
_DEVICE_VENDOR = "ExampleVendor"
_DEVICE_PRODUCT = "ExampleProduct"
_DEVICE_VERSION = "0.0"

# Mandatory CEF header: CEF:Version|Vendor|Product|Version|SigID|Name|Severity|
_CEF_PATTERN = re.compile(
    r"^CEF:\d+\|"   # CEF:0|
    r"[^|]*\|"      # Device Vendor
    r"[^|]*\|"      # Device Product
    r"[^|]*\|"      # Device Version
    r"[^|]*\|"      # Signature ID
    r"[^|]*\|"      # Name
    r"\d{1,2}\|"    # Severity (0 to 10)
    r".*$"          # Extension
)


def _escape_header(value: str) -> str:
    r"""Escape backslash and pipe, which CEF reserves in header fields."""
    return value.replace("\\", "\\\\").replace("|", "\\|")


def _escape_value(value: str) -> str:
    r"""Escape backslash and equals; strip newlines, in CEF extension values."""
    escaped = value.replace("\\", "\\\\").replace("=", "\\=")
    return escaped.replace("\n", " ").replace("\r", "")


class CEFFormatter:
    """Render an Alert as a single ArcSight CEF:0 line for syslog or file.

    Structure follows the real formatter; the extension-field selection and
    device identity are trimmed and stubbed. SIEMs ingest CEF directly, so
    correct escaping is the whole point.
    """

    def __init__(self) -> None:
        self._hostname = socket.gethostname()

    def format(self, alert: Alert) -> str:
        severity_int = _SEVERITY_INT.get(alert.severity, 0)

        header = (
            f"CEF:0"
            f"|{_escape_header(_DEVICE_VENDOR)}"
            f"|{_escape_header(_DEVICE_PRODUCT)}"
            f"|{_escape_header(_DEVICE_VERSION)}"
            f"|{_escape_header(alert.signature_id)}"
            f"|{_escape_header(alert.signature_name)}"
            f"|{severity_int}|"
        )

        # rt is receipt time in epoch milliseconds; assume UTC if naive.
        seen = alert.last_seen
        if seen.tzinfo is None:
            seen = seen.replace(tzinfo=timezone.utc)
        rt_ms = int(seen.timestamp() * 1000)

        extensions = [
            f"rt={rt_ms}",
            f"dvchost={_escape_value(self._hostname)}",
            f"src={_escape_value(alert.source_host)}",
            f"dst={_escape_value(alert.dest_host)}",
            f"reason={_escape_value(alert.evidence)}",
            f"cnt={alert.count}",
        ]
        return header + " ".join(extensions)

    @staticmethod
    def validate(cef_string: str) -> bool:
        """Structural header check only; does not validate every key."""
        return bool(_CEF_PATTERN.match(cef_string))


# ---------------------------------------------------------------------------
#  DEDUPLICATION (sliding window)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _DedupKey:
    """Collapse repeats of the same signature between the same hosts."""

    signature_id: str
    source_host: str
    dest_host: str


@dataclass(slots=True)
class _DedupEntry:
    alert: Alert
    window_seconds: int
    expires_at: float = field(init=False)

    def __post_init__(self) -> None:
        self.expires_at = self.alert.last_seen.timestamp() + self.window_seconds

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc).timestamp() > self.expires_at

    def refresh(self, alert: Alert) -> None:
        """Merge a duplicate: bump count, advance the window, keep the peak score."""
        self.alert.count += 1
        self.alert.last_seen = alert.last_seen
        if alert.anomaly_score is not None:
            prev = self.alert.anomaly_score
            self.alert.anomaly_score = (
                alert.anomaly_score if prev is None else max(prev, alert.anomaly_score)
            )
        self.expires_at = alert.last_seen.timestamp() + self.window_seconds


class AlertDeduplicator:
    """Suppress repeated alerts within a sliding time window.

    An OrderedDict gives O(1) insertion-order eviction. now() is monotonic in
    practice, so insertion order tracks expiry order and popitem(last=False)
    always evicts the oldest entry. Async-locked for concurrent dispatch.
    """

    def __init__(self, default_window_seconds: int, max_entries: int = 10_000) -> None:
        self._default_window = default_window_seconds
        self._max_entries = max_entries
        self._entries: OrderedDict[_DedupKey, _DedupEntry] = OrderedDict()
        self._lock = asyncio.Lock()

    async def deduplicate(self, alert: Alert) -> Alert | None:
        """Return the alert if new; return None if it folds into a live entry."""
        key = _DedupKey(alert.signature_id, alert.source_host, alert.dest_host)
        async with self._lock:
            self._expire()
            entry = self._entries.get(key)
            if entry is not None and not entry.is_expired:
                entry.refresh(alert)
                return None

            self._entries[key] = _DedupEntry(alert, self._default_window)
            if len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)
            return alert

    def _expire(self) -> None:
        """Drop entries whose window has closed. Caller holds the lock."""
        dead = [k for k, e in self._entries.items() if e.is_expired]
        for k in dead:
            del self._entries[k]


# ---------------------------------------------------------------------------
#  DISPATCHER (fan-out)
# ---------------------------------------------------------------------------


class WebSocketManager:
    """Track dashboard clients and broadcast alert JSON; drop dead sockets."""

    def __init__(self) -> None:
        self._clients: set[Any] = set()
        self._lock = asyncio.Lock()

    async def register(self, ws: Any) -> None:
        async with self._lock:
            self._clients.add(ws)

    async def unregister(self, ws: Any) -> None:
        async with self._lock:
            self._clients.discard(ws)

    async def broadcast(self, alert_json: str) -> None:
        async with self._lock:
            clients = set(self._clients)
        stale = [ws for ws in clients if not await self._try_send(ws, alert_json)]
        if stale:
            async with self._lock:
                for ws in stale:
                    self._clients.discard(ws)

    @staticmethod
    async def _try_send(ws: Any, payload: str) -> bool:
        try:
            await ws.send_text(payload)
            return True
        except Exception:
            return False


class AlertDispatcher:
    """Fan-out delivery to every configured channel, concurrently.

    Each channel runs as its own task. A failure in one is caught and logged
    without blocking the others, so one dead SIEM never starves the dashboard.
    The real webhook path adds tenacity retries and bearer auth, stubbed here.
    """

    def __init__(self, settings: _Settings) -> None:
        self._settings = settings
        self._cef = CEFFormatter()
        self._ws = WebSocketManager()

    @property
    def ws_manager(self) -> WebSocketManager:
        return self._ws

    async def dispatch(self, alert: Alert) -> None:
        cef_line = self._cef.format(alert)
        alert_json = alert.to_json()

        tasks: list[asyncio.Task[None]] = []
        if self._settings.siem_syslog_host:
            tasks.append(asyncio.create_task(self._send_syslog(cef_line), name="syslog"))
        if self._settings.siem_webhook_url:
            tasks.append(asyncio.create_task(self._send_webhook(alert_json), name="webhook"))
        if self._settings.alert_file_path:
            tasks.append(asyncio.create_task(self._send_file(cef_line), name="file"))
        # WebSocket is always on for the live dashboard.
        tasks.append(asyncio.create_task(self._ws.broadcast(alert_json), name="ws"))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for task, result in zip(tasks, results):
            if isinstance(result, Exception):
                # Real code emits structured logs keyed by channel and alert id.
                print(f"dispatch.channel_error channel={task.get_name()} error={result}")

    async def _send_syslog(self, cef_line: str) -> None:
        host = self._settings.siem_syslog_host
        port = self._settings.siem_syslog_port
        payload = cef_line.encode("utf-8")
        loop = asyncio.get_running_loop()
        if self._settings.siem_syslog_protocol == "UDP":
            await loop.run_in_executor(None, self._udp_send, host, port, payload)
        else:
            await loop.run_in_executor(None, self._tcp_send, host, port, payload)

    @staticmethod
    def _udp_send(host: str, port: int, payload: bytes) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(payload, (host, port))

    @staticmethod
    def _tcp_send(host: str, port: int, payload: bytes) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(10.0)
            sock.connect((host, port))
            sock.sendall(payload + b"\n")

    async def _send_webhook(self, alert_json: str) -> None:
        # Real path: httpx.AsyncClient POST wrapped in tenacity retry with
        # exponential backoff and bearer auth. Retry policy and endpoint stubbed.
        raise NotImplementedError("webhook transport stubbed in portfolio excerpt")

    async def _send_file(self, cef_line: str) -> None:
        path = Path(self._settings.alert_file_path)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._file_append, path, cef_line)

    @staticmethod
    def _file_append(path: Path, line: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")