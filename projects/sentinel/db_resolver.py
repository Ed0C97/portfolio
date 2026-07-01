# Portfolio excerpt, adapted. Generic multi-tenant DB-URL resolution; imports stubbed to read standalone.
"""Resolve a tenant's PostgreSQL connection URL.

We store db_url_secret_id, not the URL itself, so credentials never sit in
the tenants table in plaintext. Resolving combines the ORM lookup with secret
resolution to hand Alembic a runnable URL.

Resolution by deploy_mode:
  * "saas": shared master URL (all SaaS tenants live in one DB).
  * "dedicated"/"on_premise" with db_url_secret_id: resolve and return it.
  * "dedicated"/"on_premise" without a secret: TenantDBNotConfigured
    (operator never wired the secret).
  * unknown tenant: TenantNotFound.
"""

from __future__ import annotations

import logging
from typing import Optional

# stubs; real codebase pulls these from ORM models, secret resolver, settings
from secrets_resolver import SecretNotFound, resolve_secret  # noqa: F401


class SessionLocal:
    ...


class Tenant:
    ...


class _Settings:
    postgres_uri = "postgresql+asyncpg://..."


settings = _Settings()

logger = logging.getLogger(__name__)


class TenantNotFound(LookupError):
    pass


class TenantDBNotConfigured(RuntimeError):
    pass


def _load_tenant(tenant_id: str) -> Tenant:
    session = SessionLocal()
    try:
        row = session.query(Tenant).filter(Tenant.tenant_id == tenant_id).one_or_none()
    finally:
        session.close()
    if row is None:
        raise TenantNotFound(f"unknown tenant_id={tenant_id!r}")
    return row


async def resolve_tenant_db_url(tenant_id: str) -> str:
    """Return the runnable PostgreSQL URL for the given tenant.

    Sync DB I/O is fine here: the lookup is one cheap row and callers
    (orchestrator, dashboard) treat the whole thing as a single await.
    """
    tenant = _load_tenant(tenant_id)
    mode = (tenant.deploy_mode or "saas").lower()

    if mode == "saas":
        return settings.postgres_uri

    secret_id: Optional[str] = tenant.db_url_secret_id
    if not secret_id:
        raise TenantDBNotConfigured(
            f"tenant {tenant_id!r} is in deploy_mode={mode!r} but has no "
            "db_url_secret_id: set the secret and update the tenants row "
            "before running migrations against it."
        )

    try:
        return resolve_secret(secret_id)
    except SecretNotFound as exc:
        raise TenantDBNotConfigured(
            f"tenant {tenant_id!r} secret_id={secret_id!r} could not be "
            f"resolved by any configured backend ({exc})"
        ) from exc


async def iter_dedicated_tenants() -> list[tuple[str, str]]:
    """Return (tenant_id, db_url) for every active dedicated/on-premise tenant.

    Unresolvable secrets are skipped with a warning so a batch run finishes
    the tenants it can instead of aborting on the first bad one.
    """
    session = SessionLocal()
    try:
        rows = (
            session.query(Tenant)
            .filter(Tenant.is_active.is_(True))
            .filter(Tenant.deploy_mode.in_(("dedicated", "on_premise")))
            .all()
        )
        ids = [r.tenant_id for r in rows]
    finally:
        session.close()

    out: list[tuple[str, str]] = []
    for tid in ids:
        try:
            url = await resolve_tenant_db_url(tid)
            out.append((tid, url))
        except TenantDBNotConfigured as exc:
            logger.warning("[migrations] skipping tenant %s: %s", tid, exc)
    return out
