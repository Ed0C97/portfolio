"""
ssrf_guarded_client.py
======================

Portfolio excerpt, adapted.
"""

from __future__ import annotations

import ipaddress
import json
import urllib.error
import urllib.request
from urllib.parse import urlsplit


class GatewayError(Exception):
    """Gateway call failed; message is safe to surface to the user."""


# -- config validation -------------------------------------------------------

def validate_gateway_url(url: str) -> str:
    """Accept only http(s) URLs that resolve to a loopback literal.

    The gateway API is unauthenticated, so any base URL we accept becomes a
    request the attacker controls. Rejecting file://, non-loopback IPs, and
    bare hostnames closes off SSRF to the metadata service and DNS rebinding.
    """
    parts = urlsplit((url or "").strip())
    if parts.scheme not in ("http", "https"):
        raise GatewayError("Invalid gateway URL: use http:// or https://.")
    host = (parts.hostname or "").strip("[]")
    if host == "localhost":
        return url.strip()
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        # not a literal IP. a hostname like localhost.evil.com could resolve to
        # 127.0.0.1 on the first lookup and an internal IP on the second, so we
        # only trust literal loopback names and addresses
        raise GatewayError("Invalid gateway URL: must point at localhost.")
    if not ip.is_loopback:
        raise GatewayError("Gateway URL not allowed: must be on localhost.")
    return url.strip()


# -- HTTP client (stdlib) ----------------------------------------------------

def request(cfg: dict, method: str, path: str,
            payload: dict | None = None, timeout: int = 8) -> object:
    """Call the gateway and return the unwrapped data field.

    Re-validates cfg['gateway_url'] even though config-save already did; the
    config file is editable out of band. Responses come back as
    {"success", "data", "error"}; failures become GatewayError.
    """
    base = validate_gateway_url(cfg["gateway_url"])
    url = base.rstrip("/") + "/api" + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "X-API-Key": cfg.get("api_key", ""),
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        try:
            err = json.loads(exc.read().decode())
            msg = (err.get("error") or {}).get("message") or str(exc)
        except Exception:  # noqa: BLE001 -- body is not JSON
            msg = str(exc)
        raise GatewayError(f"Gateway {exc.code}: {msg}")
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        raise GatewayError(f"Gateway unreachable at {base} ({exc}) -- is it running?")
    if isinstance(body, dict) and body.get("success") is False:
        msg = (body.get("error") or {}).get("message", "unknown error")
        raise GatewayError(f"Gateway: {msg}")
    return body.get("data", body) if isinstance(body, dict) else body


def health(cfg: dict) -> bool:
    request(cfg, "GET", "/health")
    return True
