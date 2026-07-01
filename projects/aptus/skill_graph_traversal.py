"""Portfolio excerpt, adapted. Recursive-CTE traversal over a skill graph.

Walk runs in SQL, not a Python graph lib, so it scales with Postgres instead of
the app process. Depth and relation filters arrive as bound params; the only
thing chosen in Python is which of two fixed query bodies to run.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True, slots=True)
class TraversalHit:
    skill_id: uuid.UUID
    canonical_name: str
    depth: int
    cumulative_weight: float
    relation_path: list[str]


# two fixed bodies instead of string-building the WHERE clause: keeps relation
# names and depth out of the SQL text entirely
_NEIGHBOURS_SQL_ANY = """
WITH RECURSIVE walk AS (
    SELECT
        e.dst_id      AS skill_id,
        1             AS depth,
        e.weight      AS cumulative_weight,
        ARRAY[e.relation]::varchar[] AS relation_path
    FROM skill_edges e
    WHERE e.src_id = CAST(:start AS uuid)
    UNION ALL
    SELECT
        e.dst_id,
        w.depth + 1,
        w.cumulative_weight * e.weight,
        w.relation_path || e.relation
    FROM walk w
    JOIN skill_edges e ON e.src_id = w.skill_id
    WHERE w.depth < :max_depth
)
SELECT DISTINCT ON (w.skill_id)
    w.skill_id,
    s.canonical_name,
    w.depth,
    w.cumulative_weight,
    w.relation_path
FROM walk w
JOIN skills s ON s.id = w.skill_id
ORDER BY w.skill_id, w.depth ASC
"""

_NEIGHBOURS_SQL_FILTERED = """
WITH RECURSIVE walk AS (
    SELECT
        e.dst_id      AS skill_id,
        1             AS depth,
        e.weight      AS cumulative_weight,
        ARRAY[e.relation]::varchar[] AS relation_path
    FROM skill_edges e
    WHERE e.src_id = CAST(:start AS uuid) AND e.relation = ANY(:relations)
    UNION ALL
    SELECT
        e.dst_id,
        w.depth + 1,
        w.cumulative_weight * e.weight,
        w.relation_path || e.relation
    FROM walk w
    JOIN skill_edges e ON e.src_id = w.skill_id
    WHERE w.depth < :max_depth AND e.relation = ANY(:relations)
)
SELECT DISTINCT ON (w.skill_id)
    w.skill_id,
    s.canonical_name,
    w.depth,
    w.cumulative_weight,
    w.relation_path
FROM walk w
JOIN skills s ON s.id = w.skill_id
ORDER BY w.skill_id, w.depth ASC
"""


class SkillGraphTraversal:
    def __init__(self, max_depth: int) -> None:
        self.max_depth = max_depth

    async def neighbours(
        self,
        session: AsyncSession,
        skill_id: uuid.UUID,
        relations: tuple[str, ...] | None = None,
        max_depth: int | None = None,
    ) -> list[TraversalHit]:
        """Return every skill reachable from skill_id within the depth limit."""
        depth = max_depth or self.max_depth
        params: dict[str, Any] = {"start": str(skill_id), "max_depth": depth}
        if relations:
            params["relations"] = list(relations)
            query = text(_NEIGHBOURS_SQL_FILTERED)
        else:
            query = text(_NEIGHBOURS_SQL_ANY)
        rows = (await session.execute(query, params)).mappings().all()
        return [
            TraversalHit(
                skill_id=uuid.UUID(str(row["skill_id"])),
                canonical_name=str(row["canonical_name"]),
                depth=int(row["depth"]),
                cumulative_weight=float(row["cumulative_weight"]),
                relation_path=list(row["relation_path"] or []),
            )
            for row in rows
        ]


_DEFAULT_MAX_DEPTH = 6


def build_skill_graph_traversal(max_depth: int = _DEFAULT_MAX_DEPTH) -> SkillGraphTraversal:
    return SkillGraphTraversal(max_depth=max_depth)
