# people-os

Three excerpts from an AI-native people-operations toolkit, chosen to show the *supporting craft*: how the system is wired, orchestrated, and tested, without exposing the prompts or scoring rubrics that make it work.

**Context:** see [../people-os.md](../people-os.md) for the project overview.

## Stack

Python 3.11+, [FastMCP](https://github.com/jlowin/fastmcp) (Model Context Protocol), [LangGraph](https://langchain-ai.github.io/langgraph/) for typed pipeline orchestration, Pydantic for validation, the Anthropic SDK, and `asyncio` throughout.

## What each file shows

- **`evaluation.py`**: the offline decision-quality gate run before a prompt or rubric change ships. Over already-labeled prediction records it computes three metric families: multi-class quality (per-class precision, recall, and F1 with macro averaging and accuracy, taking labels from the union of gold and predicted so a hallucinated class still scores zero), run-to-run stability (raw agreement plus Cohen's kappa, aligning two runs by candidate id and correcting for chance), and group fairness (selection-rate and mean-score gaps, signed and absolute, alongside the gold base-rate gaps, framed as demographic parity). The scorer that produces the labels is out of scope.
- **`server.py`**: FastMCP composition. Nine tools and two resources registered through one standardized interface, grouped by concern with zero coupling between the server wiring and the capabilities it exposes. Stays under about 90 lines no matter how many tools the system grows; note the `scorecard://{job_id}` resource URI template.
- **`screening_pipeline.py`**: a typed LangGraph `StateGraph` (parse, then screen, then decide). The state is a `TypedDict` whose `errors` field uses `Annotated[list[str], operator.add]`, so a degraded stage appends a non-fatal error and the run still completes instead of crashing. Includes async batch fan-out with deterministic, best-first result ordering.
- **`synthetic_candidates.py`**: a seeded, stratified synthetic-data generator. It produces labeled candidate profiles across a controlled distribution (30% strong, 30% borderline, 25% weak, 15% non-traditional) so an eval suite can run reproducibly without ever touching real, PII-sensitive hiring data.

## Deliberately omitted

This is a portfolio excerpt, not a replication blueprint. Left out on purpose:

- **Prompt templates**: the resume-extraction and screening prompts are the product's moat and are not shared.
- **Scoring rubrics**: the real weighted scorecard dimensions, signal examples, and the score-to-decision thresholds live in private modules; the pipeline's `screen_node` here is a transparent placeholder.
- **The rubric-driven scorer**: the prompts, the weighted rubric, the model routing that assigns labels and continuous scores, and any tuned decision thresholds. `evaluation.py` consumes already-labeled prediction records and never reproduces that scoring path; its fairness metrics are a standard demographic-parity implementation, to be verified against the real system's fairness definition.
- **Integrations and secrets**: ATS API clients, company context, credentials, and `.env` values.

Files here are faithful excerpts with light trimming and stubbed imports; identifiers and example data have been anonymized.

_© 2026 Edoardo Caciolo, all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
