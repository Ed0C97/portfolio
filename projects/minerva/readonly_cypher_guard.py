"""Read-only Cypher guard. Portfolio excerpt, adapted.

Shows the security-critical validator that keeps a natural-language query
interface read-only: an LLM turns a question into Cypher, and this guard is
the last gate before the query reaches the database. It enforces four things:
no write clauses, an allowed read-only prefix, a mandatory RETURN, and a
capped LIMIT. It also blocks a couple of denial-of-service shapes (dangerous
procedures, unbounded variable-length paths). The graph schema, the tuned
clause whitelist, and the LLM translation layer are stubbed; only the guard's
structure and naming are preserved.
"""
from __future__ import annotations

import re

# --- Stubbed internals -------------------------------------------------------
# In the real package these live in sibling modules (the schema-aware NL
# engine, the graph driver, tuned config). Stubbed here so the guard reads on
# its own. The real whitelist is longer and tuned to the deployed schema.

ALLOWED_CLAUSES = frozenset([
    "MATCH", "RETURN", "WITH", "WHERE", "ORDER", "BY", "LIMIT",
    "SKIP", "OPTIONAL", "CALL", "YIELD", "UNWIND", "AS", "DISTINCT",
    # ... additional read-only functions and keywords trimmed for the excerpt.
])

WRITE_CLAUSES = frozenset([
    "CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE",
    "DROP", "FOREACH", "LOAD", "CSV", "CALL.*write",
])

# Read-only introspection procedures are fine (dbms.components, db.labels).
# Anything under these prefixes can mutate state or leak config, so it is a
# partial deny: CALL is allowed, these targets are not. The real prefix set is
# tuned to the deployment; two representative entries are shown.
WRITE_PROCEDURE_PREFIXES = ("dbms.security", "apoc.create", "apoc.merge")

DEFAULT_LIMIT = 50
MAX_LIMIT = 1000


# --- Compiled guards ---------------------------------------------------------
# Word-boundary matches on the clauses that mutate the graph. SET is qualified
# with a following word so "toSet" style function names do not false-positive.
_WRITE_PATTERN = re.compile(
    r"\b(CREATE|MERGE|DELETE|DETACH\s+DELETE|SET\s+\w|REMOVE|DROP|FOREACH|LOAD\s+CSV)\b",
    re.IGNORECASE,
)

# CALL into one of the mutating/config procedure namespaces above. The dot is
# escaped because these are literal procedure paths, not regex wildcards.
_WRITE_PROC_PATTERN = re.compile(
    r"\bCALL\s+(" + "|".join(re.escape(p) for p in WRITE_PROCEDURE_PREFIXES) + r")",
    re.IGNORECASE,
)

# Unbounded variable-length path, for example [*] or [*2..]. A missing upper
# bound lets one query traverse the whole graph, so it is a denial-of-service
# risk even though it never writes. Bounded forms like [*1..6] are allowed.
_UNBOUNDED_PATH_PATTERN = re.compile(r"\[\s*\*\s*(\d+\s*\.\.\s*)?\]")

_LIMIT_PATTERN = re.compile(r"\bLIMIT\s+\d+", re.IGNORECASE)
_LIMIT_CAP_PATTERN = re.compile(r"\bLIMIT\s+(\d+)", re.IGNORECASE)

_ALLOWED_PREFIXES = ("MATCH", "WITH", "CALL", "OPTIONAL MATCH", "UNWIND")


def validate_cypher(query: str) -> str:
    """Validate a Cypher query for read-only safety.

    Returns the sanitized query string. Raises ValueError for an empty query
    or any write operation. Security critical: this is the boundary that keeps
    an LLM-generated query from mutating the graph.
    """
    if not query or not query.strip():
        raise ValueError("Query must not be empty")

    # Strip comments first so a "// CREATE ..." note cannot smuggle a keyword
    # past the write check, and so a commented-out clause is not counted.
    cleaned = re.sub(r"//[^\n]*", "", query)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)

    # 1. Block write clauses. SECURITY CRITICAL.
    write_match = _WRITE_PATTERN.search(cleaned)
    if write_match:
        raise ValueError(
            f"Forbidden write operation '{write_match.group()}' detected: "
            "the query interface is read-only"
        )

    # 1b. Block mutating/config procedures. Read-only CALL still passes.
    proc_match = _WRITE_PROC_PATTERN.search(cleaned)
    if proc_match:
        raise ValueError(
            f"Forbidden procedure call '{proc_match.group()}' detected"
        )

    # 1c. Block unbounded variable-length paths (traversal blowup).
    if _UNBOUNDED_PATH_PATTERN.search(cleaned):
        raise ValueError(
            "Unbounded variable-length path detected: add an upper bound, "
            "for example [*1..6]"
        )

    stripped = cleaned.strip().upper()

    # 2. Require a read-only starting clause. Anything else is either a write
    # (already blocked) or a shape this interface does not expose.
    if not any(stripped.startswith(prefix) for prefix in _ALLOWED_PREFIXES):
        raise ValueError(
            "Query must begin with MATCH, WITH, CALL, OPTIONAL MATCH, or UNWIND"
        )

    # 3. Require RETURN, so the query produces a result set rather than a
    # side effect.
    if "RETURN" not in stripped:
        raise ValueError("Query must contain a RETURN clause")

    # 4. Enforce a bounded result set. Inject a default LIMIT when none is
    # present, then cap any LIMIT (injected or user-supplied) at MAX_LIMIT.
    if not _LIMIT_PATTERN.search(cleaned):
        cleaned = cleaned.rstrip(";").rstrip() + f" LIMIT {DEFAULT_LIMIT}"

    def _cap(match: re.Match[str]) -> str:
        return f"LIMIT {min(int(match.group(1)), MAX_LIMIT)}"

    cleaned = _LIMIT_CAP_PATTERN.sub(_cap, cleaned)

    return cleaned.strip()


if __name__ == "__main__":
    # A few cases that show the guard's contract. Reads pass (LIMIT is added or
    # capped), writes and denial-of-service shapes raise. The dbms.components
    # case exercises the read-only-CALL branch of the procedure check.
    read_only_call = "CALL dbms.components() YIELD name RETURN name"
    passing = [
        "MATCH (n) RETURN n",                        # LIMIT injected
        "MATCH (n) RETURN n LIMIT 99999",            # LIMIT capped
        read_only_call,                              # introspection is allowed
    ]
    failing = [
        "CREATE (n:Node) RETURN n",                  # write clause
        "MATCH (n) DETACH DELETE n",                 # write clause
        "CALL apoc.create.node(['X'], {}) YIELD node RETURN node",  # mutating proc
        "MATCH (a)-[*]-(b) RETURN a, b",             # unbounded path
        "MATCH (n) SET n.x = 1 RETURN n",            # write clause
    ]

    for q in passing:
        print("PASS:", validate_cypher(q))
    for q in failing:
        try:
            validate_cypher(q)
            print("MISS (should have failed):", q)
        except ValueError as exc:
            print("BLOCKED:", exc)