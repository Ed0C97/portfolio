"""Portfolio excerpt, adapted. Resume-screening pipeline on LangGraph.

Patterns worth pointing at:

  errors is Annotated[list[str], operator.add], so a degraded stage appends a
  non-fatal error and the reducer merges it instead of clobbering. The run
  finishes either way.

  Nodes and edges are explicit (parse -> screen -> decide). No string-keyed
  callbacks, no hidden state.

  Batch screening fans out with asyncio.gather but sorts before returning, so
  output order does not depend on task completion order.

  The real scoring heuristics and LLM prompts are not in this excerpt.
  screen_node is a placeholder that emits neutral scores so the graph runs
  standalone.
"""

import asyncio
import logging
import operator
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)


class ScreeningState(TypedDict):
    """Shared state threaded through every node."""
    resume_text: str
    job_id: int
    job_requirements: str
    # filled in by pipeline stages
    parsed_resume: dict
    screening_scores: dict
    decision: str
    confidence: str
    summary: str
    # reducer-merged: any node may append, nothing overwrites
    errors: Annotated[list[str], operator.add]


async def parse_node(state: ScreeningState) -> dict:
    """Parse raw resume text into structured data.

    On failure, return an empty dict plus an error rather than raising, so the
    reducer records it in errors and later stages decide what to do with
    partial data.
    """
    from mcp_server.tools.resume_parser import parse_resume

    try:
        parsed = await parse_resume(state["resume_text"])
        return {"parsed_resume": parsed}
    except Exception as e:  # noqa: BLE001 - degrade, don't crash the run
        logger.error("Parse failed: %s", e)
        return {"parsed_resume": {}, "errors": [f"Parse error: {e}"]}


async def screen_node(state: ScreeningState) -> dict:
    """Score the parsed resume against the role's dimensions.

    Placeholder. The real version scores each dimension with an LLM against a
    role rubric, which is not part of this excerpt. Here every dimension gets a
    neutral mid-score so the graph runs end to end.
    """
    parsed = state.get("parsed_resume", {})
    if not parsed:
        return {"screening_scores": {}, "errors": ["No parsed resume to screen"]}

    dimensions = ("technical_skills", "experience_level", "role_fit")
    scores = {dim: 3 for dim in dimensions}  # placeholder, see screen_node docstring
    return {"screening_scores": scores}


async def decide_node(state: ScreeningState) -> dict:
    """Collapse dimension scores into a single recommendation."""
    scores = state.get("screening_scores", {})
    if not scores:
        return {
            "decision": "maybe",
            "confidence": "low",
            "summary": "Insufficient data to make a decision.",
        }

    avg = sum(scores.values()) / max(len(scores), 1)

    if avg >= 3.8:
        decision, confidence = "recommend", ("high" if avg >= 4.2 else "medium")
    elif avg >= 2.5:
        decision, confidence = "maybe", "medium"
    else:
        decision, confidence = "reject", ("high" if avg < 2.0 else "medium")

    name = state.get("parsed_resume", {}).get("name", "Unknown")
    summary = f"{name}: {decision} ({confidence} confidence). Avg score: {avg:.1f}/5."
    return {"decision": decision, "confidence": confidence, "summary": summary}


def build_screening_graph():
    """Compile the screening pipeline into a runnable StateGraph."""
    graph = StateGraph(ScreeningState)

    graph.add_node("parse", parse_node)
    graph.add_node("screen", screen_node)
    graph.add_node("decide", decide_node)

    graph.set_entry_point("parse")
    graph.add_edge("parse", "screen")
    graph.add_edge("screen", "decide")
    graph.add_edge("decide", END)

    return graph.compile()


async def screen_candidate(
    resume_text: str,
    job_id: int = 1001,
    job_requirements: str = "",
) -> dict:
    """Run the full pipeline for one candidate and return the final state."""
    graph = build_screening_graph()

    initial_state: ScreeningState = {
        "resume_text": resume_text,
        "job_id": job_id,
        "job_requirements": job_requirements,
        "parsed_resume": {},
        "screening_scores": {},
        "decision": "",
        "confidence": "",
        "summary": "",
        "errors": [],
    }
    result = await graph.ainvoke(initial_state)
    return dict(result)


async def screen_batch(resumes: list[str], job_id: int = 1001) -> list[dict]:
    """Screen multiple candidates concurrently, best-first.

    gather keeps input order; the sort below is the only thing that sets output
    order, so the result is the same no matter which task finishes first.
    """
    results = await asyncio.gather(
        *(screen_candidate(resume, job_id) for resume in resumes)
    )

    rank = {"recommend": 0, "maybe": 1, "reject": 2}
    return sorted(results, key=lambda r: rank.get(r.get("decision", "maybe"), 1))
