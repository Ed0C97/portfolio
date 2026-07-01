"""Read-only safety guard for LLM-generated Cypher. Portfolio excerpt, adapted.

The natural-language query path turns an analyst question into a Cypher query and
runs it against the threat-intel graph. That query is attacker-influenced (the
question is untrusted input), so it must be structurally incapable of mutating or
exhausting the graph before it ever reaches Neo4j. Safety lives here, in the query
layer, not in a prompt instruction the model can be talked out of.

The guard enforces four things:
  1. No write clauses. CREATE, MERGE, DELETE, SET, REMOVE, DROP, DETACH, and
     FOREACH are rejected, as is LOAD CSV / USING PERIODIC COMMIT ingestion and
     write-side or admin procedures invoked through CALL.
  2. No unbounded variable-length paths. A pattern like -[:REL*]-> or -[:REL*2..]->
     can walk the whole graph; only a bounded form (exact *N, or a range with an
     explicit upper bound *..M / *N..M) is allowed.
  3. A hard row cap. Every query must end under a maximum LIMIT; if it has none,
     one is injected.

Honesty about the model: this is a static, token-level check, not a parser and not
a substitute for database permissions. It tokenizes to avoid the classic false
positives (a "CREATE" inside a string literal, a property literally named "delete",
count(*) or arithmetic like a * b), but a determined generator could still find
phrasings a token scanner misreads. The real, non-bypassable control is a Neo4j
account with read-only privileges; this guard is defense in depth and fast
rejection, layered in front of that account, not instead of it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Clause keywords that can change the graph. Matched as whole tokens only.
WRITE_KEYWORDS: frozenset[str] = frozenset(
    {"CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE", "DROP", "FOREACH"}
)

# Procedures that write or administer. CALL to anything outside an allowlist of
# read-only procedures is refused; this names the obviously dangerous namespaces.
# The dbms namespace is only partially denied on purpose: dbms.security.*,
# dbms.setConfigValue, and the kill procedures mutate or administer, but read-only
# introspection (dbms.components, dbms.cluster.overview) is left callable.
WRITE_PROCEDURE_PREFIXES: tuple[str, ...] = (
    "db.create",
    "db.index",
    "db.constraint",
    "apoc.create",
    "apoc.merge",
    "apoc.refactor",
    "apoc.periodic",
    "dbms.security",
    "dbms.setconfigvalue",
    "dbms.killquer",       # dbms.killQuery / dbms.killQueries
    "dbms.killtransaction",
)

MAX_LIMIT = 1000

# One token: a quoted string, a backtick-quoted identifier, a line comment, a
# block comment, a word, or a single other character. Ordering matters so that
# quoted and commented spans are consumed whole and their contents never leak
# out as bare keywords.
_TOKEN_RE = re.compile(
    r"""
      '(?:\\.|[^'\\])*'          # single-quoted string
    | "(?:\\.|[^"\\])*"          # double-quoted string
    | `(?:``|[^`])*`             # backtick-quoted identifier
    | //[^\n]*                   # line comment
    | /\*.*?\*/                  # block comment
    | \w+                        # bare word (keyword, label, number)
    | \S                         # any other single non-space character
    """,
    re.VERBOSE | re.DOTALL,
)

# Variable-length relationship inside a bracket. Anchored to '[' so a bare '*'
# elsewhere (count(*), arithmetic like a * b or 2*n) is never mistaken for a
# hop range. [^\]]*? consumes the optional variable name and :TYPE up to the
# star; the three named groups capture the quantifier so unboundedness is decided
# by inspecting the whole quantifier rather than a fragile lookahead. Runs after
# string and comment spans are blanked, so it cannot fire inside a literal.
_VARLEN_RE = re.compile(
    r"""
    \[                 # relationship bracket
    [^\]]*?            # var name, :TYPE, |-separated types, up to the star
    \*                 # variable-length marker
    \s*
    (?P<lo>\d+)?       # optional lower bound
    \s*
    (?P<dots>\.\.)?    # optional range separator
    \s*
    (?P<hi>\d+)?       # optional upper bound
    """,
    re.VERBOSE,
)

# Trailing LIMIT literal, captured so we can clamp it. Cypher LIMIT takes an
# integer here; a parameterized LIMIT $n is treated as unknown and reclamped.
_LIMIT_TAIL_RE = re.compile(r"(?is)\blimit\s+(\d+)\s*;?\s*$")


class UnsafeQueryError(ValueError):
    """Raised when a query cannot be made read-only-safe."""


@dataclass(frozen=True)
class GuardResult:
    """Outcome of guarding a query: the safe text plus what was changed."""

    query: str
    limit_injected: bool
    limit_clamped: bool


def _significant_tokens(query: str) -> list[str]:
    """Return upper-cased bare-word tokens, skipping strings and comments.

    Only bare words matter for keyword detection: anything inside quotes or
    comments is intentionally discarded so a label named `Create` or the string
    'DELETE this row' cannot be mistaken for a write clause.
    """
    words: list[str] = []
    for tok in _TOKEN_RE.findall(query):
        head = tok[:1]
        if head in "'\"`" or tok.startswith("//") or tok.startswith("/*"):
            continue
        if tok.isalnum() or "_" in tok or "." in tok:
            words.append(tok.upper())
    return words


def _strip_literals_and_comments(query: str) -> str:
    """Return the query with string literals and comments blanked to spaces.

    Blanking in place (each masked span replaced by spaces of the same length)
    keeps every other character at its original offset and preserves the
    whitespace between tokens, so downstream regexes see faithful structure and
    never see literal or comment contents.
    """

    def blank(m: re.Match[str]) -> str:
        tok = m.group(0)
        head = tok[:1]
        if head in "'\"`" or tok.startswith("//") or tok.startswith("/*"):
            # keep newlines so line-based logic and error offsets stay aligned
            return "".join("\n" if c == "\n" else " " for c in tok)
        return tok

    return _TOKEN_RE.sub(blank, query)


def _reject_write_clauses(tokens: list[str]) -> None:
    """Raise if a write keyword, LOAD CSV, or PERIODIC COMMIT appears as a clause."""
    for tok in tokens:
        if tok in WRITE_KEYWORDS:
            raise UnsafeQueryError(f"write clause not allowed: {tok}")
    # LOAD CSV is an ingestion/IO vector and USING PERIODIC COMMIT frames write
    # batching; presence of both keywords is a strong signal a read query lacks.
    if "LOAD" in tokens and "CSV" in tokens:
        raise UnsafeQueryError("LOAD CSV not allowed")
    if "USING" in tokens and "PERIODIC" in tokens:
        raise UnsafeQueryError("USING PERIODIC COMMIT not allowed")


def _reject_write_procedures(code: str) -> None:
    """Raise if a CALL targets a known write or admin procedure.

    Scans the literal-stripped text so a procedure name inside a string cannot
    trip it, and matches on a dotted namespace prefix at a word boundary.
    """
    for m in re.finditer(r"(?i)\bcall\s+([\w.]+)", code):
        proc = m.group(1).lower()
        if any(proc.startswith(p) for p in WRITE_PROCEDURE_PREFIXES):
            raise UnsafeQueryError(f"write/admin procedure not allowed: {proc}")


def _reject_unbounded_varlen(code: str) -> None:
    """Raise if a variable-length relationship has no finite upper hop bound.

    A quantifier is bounded iff it names a ceiling: an exact count *N (no dots),
    or a range with an explicit upper number (*..M or *N..M). A bare *, or an
    open-ended *N.., can traverse the entire graph and is refused.
    """
    for m in _VARLEN_RE.finditer(code):
        lo, dots, hi = m.group("lo"), m.group("dots"), m.group("hi")
        unbounded = (hi is None) if dots else (lo is None)
        if unbounded:
            raise UnsafeQueryError(
                "unbounded variable-length relationship not allowed; "
                "add an upper bound such as *1..3"
            )


def _apply_limit(query: str, code: str) -> tuple[str, bool, bool]:
    """Ensure the query ends under MAX_LIMIT, clamping or injecting as needed.

    Detection runs on `code` (the literal-and-comment-stripped query, whose
    offsets match `query` character for character), so a LIMIT inside a string is
    ignored and a real trailing LIMIT is still found. Rewrites are applied to the
    raw `query` at the matched offsets. Returns the rewritten query and flags for
    whether a LIMIT was injected and whether an existing one was clamped down.

    A multi-part query (UNION, or a query whose final RETURN carries no LIMIT)
    gets the cap appended to the final part; per-part LIMITs inside earlier
    branches are left as the author wrote them.
    """
    body = query.rstrip().rstrip(";").rstrip()
    m = _LIMIT_TAIL_RE.search(code)
    if m:
        existing = int(m.group(1))
        if existing <= MAX_LIMIT:
            return query, False, False
        # splice over the exact span of the raw query the stripped match covers
        clamped = query[: m.start()] + f"LIMIT {MAX_LIMIT}" + query[m.end():]
        return clamped, False, True
    # No trailing LIMIT (or a parameterized one we cannot read): append a hard cap
    # on its own line so a trailing line comment cannot swallow it.
    return f"{body}\nLIMIT {MAX_LIMIT}", True, False


def guard_query(query: str) -> GuardResult:
    """Validate a generated Cypher query and return a read-only-safe version.

    Raises UnsafeQueryError for anything that could mutate or exhaust the graph.
    On success the returned query is guaranteed to carry a trailing LIMIT no
    greater than MAX_LIMIT. This does not replace read-only database credentials;
    it is the fast, layered check in front of them.
    """
    if not query or not query.strip():
        raise UnsafeQueryError("empty query")

    # Reject multi-statement submissions: a trailing write hidden after a
    # semicolon is a classic bypass, so only a single terminating ';' is tolerated.
    code = _strip_literals_and_comments(query)
    if code.rstrip().rstrip(";").count(";") > 0:
        raise UnsafeQueryError("multiple statements not allowed")

    tokens = _significant_tokens(query)
    _reject_write_clauses(tokens)
    _reject_write_procedures(code)
    _reject_unbounded_varlen(code)

    safe_query, injected, clamped = _apply_limit(query, code)
    return GuardResult(query=safe_query, limit_injected=injected,
                       limit_clamped=clamped)


if __name__ == "__main__":
    ok = ("MATCH (a:Actor)-[:USES*1..3]->(m:Malware) "
          "WHERE a.name = 'has DELETE in it' RETURN count(*)")
    print(guard_query(ok))  # limit injected, count(*) and bounded varlen accepted

    for bad in [
        "MATCH (n) DETACH DELETE n",
        "MATCH (a)-[:USES*]->(b) RETURN b",             # unbounded varlen
        "MATCH (a)-[:USES*2..]->(b) RETURN b",          # open-ended upper bound
        "CALL apoc.periodic.iterate('MATCH (n) RETURN n', 'DELETE n', {})",
        "MATCH (n) RETURN n; DROP INDEX foo",           # second statement
        "LOAD CSV FROM 'file:///x.csv' AS row CREATE (:N {v: row[0]})",
    ]:
        try:
            guard_query(bad)
        except UnsafeQueryError as e:
            print("rejected:", e)
