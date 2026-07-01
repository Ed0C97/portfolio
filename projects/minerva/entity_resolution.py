"""Cross-source entity resolution for the threat-intel graph. Portfolio excerpt, adapted.

Different OSINT sources describe the same real-world entity (an IP, a domain, a
CVE, a threat actor) with slightly different spellings and disagreeing fields.
This collapses those signals into one canonical node so attribution and
attack-surface queries see a deduplicated graph rather than one node per source.

Two-stage matching:
  1. Strong-id match. Each entity type has a canonical key derived by normalizing
     its natural identifier (lowercased domain without trailing dot, validated and
     compressed IP, upper-cased CVE with zero-padding stripped). Entities that
     produce the same key are the same node, deterministically.
  2. Fuzzy fallback. Entities without a strong id (mostly named threat actors with
     aliases) are matched by token-set similarity against already-resolved nodes.

Field-level conflicts are resolved deterministically: the value from the
higher-priority source wins, ties broken by higher confidence, then by a stable
source ordering, so the same inputs always yield the same node regardless of
arrival order. Every kept field records which source and confidence produced it
(provenance), which is what makes a finding auditable downstream.

The graph store sits behind a Protocol so this file reads standalone; production
backs it with Neo4j. The curated threat-actor alias set and the per-source
confidence weighting are proprietary and stubbed out.
"""

from __future__ import annotations

import enum
import ipaddress
import re
from dataclasses import dataclass, field
from typing import Protocol


class EntityType(enum.Enum):
    IP = "ip"
    DOMAIN = "domain"
    CVE = "cve"
    ACTOR = "actor"


# Higher wins when two sources set the same field. These are illustrative ranks,
# not the tuned production weighting.
SOURCE_PRIORITY: dict[str, int] = {
    "internal_analyst": 100,
    "commercial_feed": 60,
    "public_feed": 40,
    "passive_dns": 30,
    "opportunistic": 10,
}

# CVE ids are "CVE-YYYY-N" where N has at least one digit and no fixed width.
# The sequence number is intentionally unpadded here (\d+, not \d{4,}) because
# early ids are short (CVE-2014-1) and the same id shows up zero-padded in some
# feeds (CVE-2021-0044); int() below removes the padding so both forms unify.
_CVE_RE = re.compile(r"^CVE-(\d{4})-(\d+)$", re.IGNORECASE)


@dataclass
class SignalField:
    """One field value as asserted by one source, with its provenance."""

    value: object
    source: str
    confidence: float  # source-reported [0.0, 1.0]


@dataclass
class Signal:
    """One source's observation of an entity, before resolution."""

    entity_type: EntityType
    raw_identifier: str
    source: str
    confidence: float = 0.5
    fields: dict[str, object] = field(default_factory=dict)


@dataclass
class CanonicalEntity:
    """A resolved node: canonical key plus best-value fields and their provenance."""

    entity_type: EntityType
    key: str
    fields: dict[str, SignalField] = field(default_factory=dict)
    contributing_sources: set[str] = field(default_factory=set)

    def value_of(self, name: str) -> object | None:
        """Return the winning value for a field, or None if no source set it."""
        chosen = self.fields.get(name)
        return chosen.value if chosen else None


class GraphStore(Protocol):
    """Async upsert surface for canonical nodes. Real impl targets Neo4j."""

    async def upsert_entity(self, entity: CanonicalEntity) -> None: ...


class CanonicalKeyError(ValueError):
    """Raised when a raw identifier cannot be normalized to a canonical key."""


def canonical_key(entity_type: EntityType, raw: str) -> str:
    """Return the type-specific canonical key for a raw identifier.

    The key is the deduplication primitive: two signals are the same entity iff
    they share a key. Normalization must therefore be total and idempotent, so
    equivalent-but-differently-spelled identifiers collapse and genuinely
    different ones never collide.
    """
    text = raw.strip()
    if not text:
        raise CanonicalKeyError("empty identifier")

    if entity_type is EntityType.IP:
        try:
            # ip_address collapses IPv6 zero groups and rejects junk; str() gives
            # the canonical compressed form, so 2001:DB8::0:1 and 2001:db8::1 unify.
            return str(ipaddress.ip_address(text))
        except ValueError as exc:
            raise CanonicalKeyError(f"invalid IP: {raw!r}") from exc

    if entity_type is EntityType.DOMAIN:
        host = text.lower().rstrip(".")  # DNS treats a trailing dot as equivalent
        if "://" in host or "/" in host or " " in host or not host:
            raise CanonicalKeyError(f"invalid domain: {raw!r}")
        # IDN homographs are unified via Punycode; a bare ASCII domain is unchanged.
        try:
            host = host.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise CanonicalKeyError(f"invalid domain: {raw!r}") from exc
        return host

    if entity_type is EntityType.CVE:
        m = _CVE_RE.match(text)
        if not m:
            raise CanonicalKeyError(f"invalid CVE id: {raw!r}")
        # Upper-case the year and drop any zero-padding on the sequence number so
        # CVE-2021-0044 and cve-2021-44 both canonicalize to CVE-2021-44, while a
        # genuinely short id such as CVE-2014-1 survives untouched.
        return f"CVE-{m.group(1)}-{int(m.group(2))}"

    if entity_type is EntityType.ACTOR:
        # Actors have no strong id here; the alias-canonicalization table that maps
        # "APT29" / "Cozy Bear" / "Midnight Blizzard" to one key is proprietary.
        return _resolve_actor_alias(text)

    raise CanonicalKeyError(f"unhandled entity type: {entity_type}")


def _resolve_actor_alias(name: str) -> str:
    """Map a threat-actor name or alias to its canonical key.

    The curated alias graph (thousands of aliases across naming conventions) is
    proprietary and omitted from this excerpt.
    """
    raise NotImplementedError(
        "curated threat-actor alias resolution omitted from portfolio excerpt"
    )


def _field_rank(f: SignalField) -> tuple[int, float, str]:
    """Return a total ordering key for a candidate field value.

    Deterministic by construction: source priority first, then source-reported
    confidence, then a stable lexicographic source tiebreak. No wall-clock time
    and no dependence on iteration order, so resolution is reproducible.
    """
    return (SOURCE_PRIORITY.get(f.source, 0), f.confidence, f.source)


class EntityResolver:
    """Resolve a batch of raw signals into canonical entities.

    Strong-id grouping is exact and order-independent. The fuzzy pass is a
    deliberate fallback for id-less entities only; it never overrides a
    strong-id match.
    """

    def __init__(self, fuzzy_threshold: float = 0.6) -> None:
        # token-set Jaccard at or above this fuses two id-less entities
        self.fuzzy_threshold = fuzzy_threshold

    def resolve(self, signals: list[Signal]) -> list[CanonicalEntity]:
        """Return canonical entities merged from the given signals."""
        by_key: dict[tuple[EntityType, str], CanonicalEntity] = {}
        needs_fuzzy: list[Signal] = []

        for sig in signals:
            try:
                key = canonical_key(sig.entity_type, sig.raw_identifier)
            except NotImplementedError:
                # actor alias table absent in this excerpt: route to fuzzy fallback
                needs_fuzzy.append(sig)
                continue
            except CanonicalKeyError:
                # unparseable identifiers are dropped rather than guessed at
                continue
            self._absorb(by_key, (sig.entity_type, key), key, sig)

        resolved = list(by_key.values())
        for sig in needs_fuzzy:
            self._absorb_fuzzy(resolved, sig)
        return resolved

    def _absorb(
        self,
        table: dict[tuple[EntityType, str], CanonicalEntity],
        table_key: tuple[EntityType, str],
        canon: str,
        sig: Signal,
    ) -> None:
        """Merge a signal into the canonical entity for its key, creating it if new."""
        entity = table.get(table_key)
        if entity is None:
            entity = CanonicalEntity(entity_type=sig.entity_type, key=canon)
            table[table_key] = entity
        self._merge_fields(entity, sig)

    def _absorb_fuzzy(self, resolved: list[CanonicalEntity], sig: Signal) -> None:
        """Merge an id-less signal into the best fuzzy match, or add it as new."""
        candidate_name = str(sig.fields.get("name", sig.raw_identifier))
        best: CanonicalEntity | None = None
        best_score = self.fuzzy_threshold
        for entity in resolved:
            if entity.entity_type is not sig.entity_type:
                continue
            existing_name = str(entity.value_of("name") or entity.key)
            score = _token_set_ratio(candidate_name, existing_name)
            if score >= best_score:
                best, best_score = entity, score

        if best is None:
            # no confident match: seed a provisional node keyed by the raw name
            best = CanonicalEntity(
                entity_type=sig.entity_type,
                key=_normalize_name(candidate_name),
            )
            resolved.append(best)
        self._merge_fields(best, sig)

    @staticmethod
    def _merge_fields(entity: CanonicalEntity, sig: Signal) -> None:
        """Fold one signal's fields into an entity, keeping the winner per field.

        Applied field by field so a low-priority source can still contribute a
        field that no higher-priority source asserted, while never overwriting a
        field a higher-priority source already won.
        """
        entity.contributing_sources.add(sig.source)
        for name, value in sig.fields.items():
            if value is None:
                continue
            candidate = SignalField(value=value, source=sig.source,
                                    confidence=sig.confidence)
            incumbent = entity.fields.get(name)
            if incumbent is None or _field_rank(candidate) > _field_rank(incumbent):
                entity.fields[name] = candidate


def _normalize_name(name: str) -> str:
    """Lowercase, strip punctuation, and collapse whitespace for name matching."""
    stripped = re.sub(r"[^\w\s]", " ", name.lower())
    return re.sub(r"\s+", " ", stripped).strip()


def _token_set_ratio(a: str, b: str) -> float:
    """Return token-set Jaccard similarity in [0.0, 1.0].

    Token-set over token-sequence because actor aliases reorder and pad words
    ("Cozy Bear Group" vs "the Cozy Bear"); set overlap ignores order and
    duplication, which is the right invariance for alias matching.
    """
    tokens_a = set(_normalize_name(a).split())
    tokens_b = set(_normalize_name(b).split())
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


if __name__ == "__main__":
    # Same IP two ways, one domain with a trailing dot, one zero-padded CVE.
    batch = [
        Signal(EntityType.IP, "2001:DB8::0:1", "public_feed", 0.4,
               {"asn": "AS64500", "country": "NL"}),
        Signal(EntityType.IP, "2001:db8::1", "internal_analyst", 0.9,
               {"country": "DE", "note": "sinkholed"}),
        Signal(EntityType.DOMAIN, "Evil.Example.COM.", "passive_dns", 0.5,
               {"first_seen": "2026-01-02"}),
        Signal(EntityType.CVE, "cve-2021-0044", "commercial_feed", 0.8,
               {"cvss": 9.8}),
    ]
    for e in EntityResolver().resolve(batch):
        winners = {k: (f.value, f.source) for k, f in e.fields.items()}
        print(e.entity_type.value, e.key, winners)
