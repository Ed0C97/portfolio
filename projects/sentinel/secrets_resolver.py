# Portfolio excerpt, adapted.
"""Resolve a secret from Vault, AWS Secrets Manager, or an env var.

Tried in order; first hit wins:
1. Vault (GET /v1/<mount>/data/<id>) when VAULT_ADDR and VAULT_TOKEN are set
2. AWS Secrets Manager GetSecretValue when boto3 is installed and AWS_REGION is set
3. Env var APP_SECRET__<id>, for dev/staging

A missing or misconfigured backend is skipped, not fatal. Raises SecretNotFound
only when every backend is exhausted.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)


class SecretNotFound(LookupError):
    """Raised when no backend resolves the secret_id."""


_ENV_PREFIX = "APP_SECRET__"
_SAFE_RE = re.compile(r"[^A-Z0-9_]")


def _env_key(secret_id: str) -> str:
    return _ENV_PREFIX + _SAFE_RE.sub("_", secret_id.upper())


def _try_vault(secret_id: str) -> Optional[str]:
    addr = os.getenv("VAULT_ADDR")
    token = os.getenv("VAULT_TOKEN")
    if not addr or not token:
        return None
    try:
        import httpx  # type: ignore
    except ImportError:  # pragma: no cover (httpx is in main deps)
        return None
    mount = os.getenv("VAULT_KV_MOUNT", "secret")
    url = f"{addr.rstrip('/')}/v1/{mount}/data/{secret_id}"
    try:
        resp = httpx.get(url, headers={"X-Vault-Token": token}, timeout=3.0)
        if resp.status_code != 200:
            logger.debug("[secrets] vault miss %s: %s", secret_id, resp.status_code)
            return None
        body = resp.json()
        # KVv2 double-wraps: payload lives at data.data.value
        return (body.get("data") or {}).get("data", {}).get("value")
    except Exception as exc:  # pragma: no cover (network)
        logger.debug("[secrets] vault error for %s: %s", secret_id, exc)
        return None


def _try_aws_secrets_manager(secret_id: str) -> Optional[str]:
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    if not region:
        return None
    try:
        import boto3  # type: ignore
    except ImportError:
        return None
    try:
        client = boto3.client("secretsmanager", region_name=region)
        result = client.get_secret_value(SecretId=secret_id)
        return result.get("SecretString")
    except Exception as exc:  # pragma: no cover (network/IAM)
        logger.debug("[secrets] aws-sm error for %s: %s", secret_id, exc)
        return None


def _try_env_fallback(secret_id: str) -> Optional[str]:
    return os.environ.get(_env_key(secret_id))


def resolve_secret(secret_id: str) -> str:
    """Return the plaintext value for secret_id, or raise SecretNotFound."""
    if not secret_id:
        raise SecretNotFound("empty secret_id")

    for fn in (_try_vault, _try_aws_secrets_manager, _try_env_fallback):
        value = fn(secret_id)
        if value:
            return value

    raise SecretNotFound(
        f"no back-end resolved secret_id={secret_id!r} "
        f"(checked Vault, AWS Secrets Manager, env var {_env_key(secret_id)})"
    )
