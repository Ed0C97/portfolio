"""Portfolio excerpt, adapted. Shows deterministic entity resolution and
deduplication across heterogeneous OSINT sources: canonical keying per entity
type (IP, domain, CVE, campaign, TTP, actor) and a rank based field merge that
is invariant to arrival order. The agent base class, the LangGraph pipeline
context, and the upstream collectors are stubbed so the file reads on its own;
the curated source priorities and confidence thresholds that make the real
resolver useful are placeholders here.
"""
from __future__ import annotations

import ipaddress
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# --- Stubbed pipeline plumbing -------------------------------------------------
# In the real system these live in minerva.agents.base and are shared across the
# agent graph. Trimmed to the fields this excerpt exercises.

@dataclass
class CollectionContext:
    """Shared state threaded through the agent pipeline."""

    target: str
    query_type: str
    # Raw entities may arrive as a flat list (direct calls, tests) or as a
    # per-source dict {source: {"data": [...]}} produced by the collector agent.
    raw_entities: list[dict[str, Any]] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)
    # Outputs written back for downstream agents.
    normalized_entities: list[dict[str, Any]] = field(default_factory=list)
    resolved_entities: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class AgentResult:
    agent_name: str
    success: bool
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Times each run, converts exceptions into a failed result, never raises."""

    name: str = "base"

    async def run(self, context: CollectionContext) -> AgentResult:
        start = time.perf_counter()
        try:
            result = await self._execute(context)
        except Exception as exc:  # noqa: BLE001 - agents must not crash the graph
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.exception("[%s] failed after %d ms: %s", self.name, elapsed_ms, exc)
            context.errors.append(f"{self.name}: {exc}")
            return AgentResult(agent_name=self.name, success=False, error=str(exc))
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.info("[%s] done in %d ms (success=%s)", self.name, elapsed_ms, result.success)
        return result

    @abstractmethod
    async def _execute(self, context: CollectionContext) -> AgentResult:
        ...


# --- Normalization helpers -----------------------------------------------------
# Real code splits these into utils.ip_utils and utils.text_utils. Inlined here
# so the excerpt is self contained.

def normalize_ip(ip: str) -> str:
    """Canonicalize an IPv4 or IPv6 address; fall back to a lowercased string."""
    try:
        return str(ipaddress.ip_address(ip.strip()))
    except ValueError:
        return ip.strip().lower()


def normalize_domain(domain: str) -> str:
    """Lowercase, strip surrounding whitespace, drop the trailing root dot."""
    return domain.strip().lower().rstrip(".")


# CVE identifiers look like CVE-2021-44228: a four digit year and a serial.
_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)


def normalize_cve(cve: str) -> str:
    """Uppercase the CVE identifier so mixed-case duplicates collapse to one key."""
    return cve.strip().upper()


# --- Resolver ------------------------------------------------------------------

# Source ranking decides which asserted value wins a scalar conflict. The real
# ordering is tuned against source reliability and is part of the product, so it
# is stubbed here with a flat default; swap in a curated {source: rank} map.
_SOURCE_PRIORITY: dict[str, int] = {}
_DEFAULT_PRIORITY = 0


class ResolverAgent(BaseAgent):
    """Agent 02: collapse duplicate entities from many sources into one node.

    Determinism is the contract: for a fixed set of input signals the resolver
    yields the same resolved node no matter what order they arrive in, up to
    genuine ties where two signals assert different values at identical rank.
    That lets the pipeline be replayed and cached without spurious diffs.
    """

    name = "resolver"

    async def _execute(self, context: CollectionContext) -> AgentResult:
        all_entities: list[dict[str, Any]] = []

        if context.raw_entities:
            all_entities.extend(context.raw_entities)
        else:
            # Flatten the per-source dict, tagging provenance on each item.
            for source, result in context.raw_data.items():
                for item in result.get("data", []):
                    if not item:
                        continue
                    item["_source"] = source
                    all_entities.append(item)

        resolved = self._resolve(all_entities, context.query_type)
        context.normalized_entities = all_entities
        context.resolved_entities = resolved

        logger.info("[resolver] %d raw to %d resolved entities", len(all_entities), len(resolved))
        return AgentResult(
            agent_name=self.name,
            success=True,
            metadata={"raw": len(all_entities), "resolved": len(resolved)},
        )

    def _resolve(self, entities: list[dict], query_type: str) -> list[dict]:
        """Bucket entities by canonical key and merge each bucket."""
        buckets: dict[str, dict] = {}
        for entity in entities:
            key = self._entity_key(entity, query_type)
            if not key:
                # Unkeyable entities are dropped rather than guessed at.
                continue
            if key in buckets:
                buckets[key] = self._merge(buckets[key], entity)
            else:
                buckets[key] = dict(entity)
        return list(buckets.values())

    def _entity_key(self, entity: dict, query_type: str) -> str | None:
        """Derive a stable dedup key from an entity's discriminating fields.

        Order matters: the checks run from the most specific signal to the least
        so that, for example, a domain is not misread as a threat actor.
        """
        # IP: canonical form so 8.8.8.8 and its padded variants collapse.
        if entity.get("address"):
            try:
                return f"ip:{normalize_ip(str(entity['address']))}"
            except Exception:
                return f"ip:{entity['address']}"
        # Domain: a name containing a dot.
        if "." in str(entity.get("name", "")):
            return f"domain:{normalize_domain(str(entity['name']))}"
        # CVE: an id with the CVE- prefix.
        if str(entity.get("id", "")).startswith("CVE-"):
            return f"cve:{normalize_cve(str(entity['id']))}"
        # Campaign or pulse: an id paired with a first-observed timestamp.
        if entity.get("id") and entity.get("first_observed"):
            return f"campaign:{entity['id']}"
        # TTP: a technique identifier.
        if entity.get("technique_id"):
            return f"ttp:{str(entity['technique_id']).upper()}"
        # Threat actor: a name that carries a motivation.
        if entity.get("name") and entity.get("motivation"):
            return f"actor:{str(entity['name']).lower()}"
        return None

    def _merge(self, base: dict, update: dict) -> dict:
        """Fold ``update`` into ``base`` field by field, order independently.

        Lists take the set union, numbers take the max (higher confidence and
        higher scores win), timestamps take the later value, and a missing field
        is filled from whichever signal has it. Provenance keys (underscore
        prefixed) are internal and never merged into the resolved node.
        """
        merged = dict(base)
        for k, v in update.items():
            if k.startswith("_"):
                continue
            if isinstance(v, list) and isinstance(merged.get(k), list):
                merged[k] = sorted(set(merged[k] + v), key=str)
            elif isinstance(v, (int, float)) and isinstance(merged.get(k), (int, float)):
                merged[k] = max(merged[k], v)
            elif k in ("last_seen", "last_observed") and v and merged.get(k):
                merged[k] = max(str(merged[k]), str(v))
            elif v is not None and merged.get(k) is None:
                merged[k] = v
        return merged


if __name__ == "__main__":
    import asyncio

    # Two Shodan and OTX views of the same IP arriving in different order still
    # resolve to a single node with unioned ports and max confidence.
    ctx = CollectionContext(
        target="8.8.8.8",
        query_type="ip",
        raw_entities=[
            {"type": "ip", "address": "8.8.8.8", "open_ports": [53, 443],
             "source": ["shodan"], "malicious_confidence": 0.0},
            {"type": "ip", "address": "8.8.8.8", "open_ports": [53, 80],
             "source": ["otx"], "malicious_confidence": 0.1},
        ],
    )
    asyncio.run(ResolverAgent().run(ctx))
    node = ctx.resolved_entities[0]
    assert sorted(node["open_ports"]) == [53, 80, 443]
    assert node["malicious_confidence"] == 0.1
    print(node)