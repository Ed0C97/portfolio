"""Does the verification layer actually earn its cost? Measure it.

The analysis pipeline runs verification judges after extraction: they can
drop a finding, recalibrate its severity, or adjust the aggregate. Judges
are the expensive part of the run, and "the reviewer agrees it feels more
accurate" is not a reason to keep paying for them.

This module holds the two pieces that keep that question answerable:

1.  **Benchmark runner**: runs the same document set twice, judges OFF then
    judges ON, against a labelled ground truth, and reports the accuracy
    delta, the false-positive reduction, and the latency overhead as one
    record. Explicit targets turn it into a gate: `judges_pass` is False
    when the quality gain no longer justifies the latency it costs.

2.  **Audit timeline**: decomposes a single finding's final score into the
    contributions that produced it (hard rule, taxonomy match, raw agent
    score, each judge's delta) and renders a plain-language explanation.
    Explainability is a property of how the score is assembled, not a
    narration generated after the fact.

**Hermetic by design.** The runner takes a `PipelineFn` callable rather
than importing the pipeline, so tests inject a stub returning canned runs
and production injects the real graph. That seam is why this benchmark can
run in CI at all: no model calls, no database, no fixtures on disk.

Note on ground truth: labelled corpora are built per tenant and held in
object storage, never in the repository, so the runner is written to
receive them rather than to find them.

Portfolio excerpt: standalone, no project imports, no external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Any, Awaitable, Callable, Optional

# ---------------------------------------------------------------------------
# Data carried between the pipeline and the benchmark
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GroundTruthFinding:
    """One labelled finding: was the system right to raise it?"""

    finding_id: str
    is_true_positive: bool
    severity: str = ""


@dataclass
class PipelineFinding:
    """A finding as the pipeline emitted it, with its score decomposition intact.

    The per-stage deltas are kept separate rather than folded into `score`
    on the way out. Once they are summed they cannot be recovered, and the
    audit timeline below is the reason they are worth carrying.
    """

    finding_id: str
    severity: str
    score: float
    raised_by: str = ""                       # which agent raised it
    raw_agent_score: float = 0.0
    judge_finding_delta: float = 0.0          # finding-level judge
    judge_severity_delta: float = 0.0         # severity-level judge
    judge_meta_delta: float = 0.0             # meta-level judge
    hard_rule_triggered: Optional[str] = None
    taxonomy_match: Optional[str] = None
    final_verdict: str = ""


@dataclass
class PipelineRun:
    findings: list[PipelineFinding] = field(default_factory=list)
    latency_seconds: float = 0.0
    judges_active: bool = False


@dataclass
class JudgeBenchmarkRun:
    """One benchmark result, serialisable straight into a report."""

    accuracy_off: float
    accuracy_on: float
    accuracy_delta: float
    false_positive_off: float
    false_positive_on: float
    false_positive_reduction: float
    latency_overhead_pct: float
    samples: int
    judges_pass: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "accuracy_off": round(self.accuracy_off, 4),
            "accuracy_on": round(self.accuracy_on, 4),
            "accuracy_delta": round(self.accuracy_delta, 4),
            "false_positive_off": round(self.false_positive_off, 4),
            "false_positive_on": round(self.false_positive_on, 4),
            "false_positive_reduction": round(self.false_positive_reduction, 4),
            "latency_overhead_pct": round(self.latency_overhead_pct, 4),
            "samples": self.samples,
            "judges_pass": self.judges_pass,
        }


PipelineFn = Callable[[str, bool], Awaitable[PipelineRun]]
"""(document_id, judges_active) -> PipelineRun"""


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------


async def run_judge_benchmark(
    documents: list[str],
    ground_truth: dict[str, list[GroundTruthFinding]],
    pipeline: PipelineFn,
    *,
    accuracy_target: float = 0.10,
    fp_reduction_target: float = 0.15,
    latency_overhead_max: float = 0.35,
) -> JudgeBenchmarkRun:
    """Run the document set with judges off and on, and compare.

    The three targets encode the trade the verification layer has to win:
    it must add at least `accuracy_target` accuracy AND remove at least
    `fp_reduction_target` of the false positives AND stay under
    `latency_overhead_max` extra latency. All three, not the best of three,
    because a layer that buys accuracy by doubling latency is a regression
    for an interactive reviewer.
    """
    if not documents:
        raise ValueError("documents list is empty")

    runs_off: list[PipelineRun] = []
    runs_on: list[PipelineRun] = []
    for document_id in documents:
        runs_off.append(await pipeline(document_id, False))
        runs_on.append(await pipeline(document_id, True))

    def truth_for(document_id: str) -> list[GroundTruthFinding]:
        return ground_truth.get(document_id, [])

    accuracy_off = mean(_accuracy(r, truth_for(d)) for d, r in zip(documents, runs_off))
    accuracy_on = mean(_accuracy(r, truth_for(d)) for d, r in zip(documents, runs_on))

    fp_off = mean(_false_positive_rate(r, truth_for(d)) for d, r in zip(documents, runs_off))
    fp_on = mean(_false_positive_rate(r, truth_for(d)) for d, r in zip(documents, runs_on))

    # Floor the baseline so a suspiciously fast stub run cannot divide by ~0
    # and report an overhead of several thousand percent.
    latency_off = max(0.001, mean(r.latency_seconds for r in runs_off))
    latency_on = mean(r.latency_seconds for r in runs_on)
    latency_overhead = (latency_on - latency_off) / latency_off

    fp_reduction = (fp_off - fp_on) / fp_off if fp_off > 0 else 0.0

    judges_pass = (
        (accuracy_on - accuracy_off) >= accuracy_target
        and fp_reduction >= fp_reduction_target
        and latency_overhead <= latency_overhead_max
    )

    return JudgeBenchmarkRun(
        accuracy_off=accuracy_off,
        accuracy_on=accuracy_on,
        accuracy_delta=accuracy_on - accuracy_off,
        false_positive_off=fp_off,
        false_positive_on=fp_on,
        false_positive_reduction=fp_reduction,
        latency_overhead_pct=latency_overhead,
        samples=len(documents),
        judges_pass=judges_pass,
    )


def _accuracy(run: PipelineRun, truth: list[GroundTruthFinding]) -> float:
    """Share of raised findings that ground truth confirms.

    Findings the system raised that appear nowhere in the labelled set count
    against it: an unlabelled finding is treated as unsupported, not as
    neutral. Without that term a system could inflate the score by raising
    everything it can think of.
    """
    if not truth:
        return 0.0
    labels = {t.finding_id: t.is_true_positive for t in truth}

    confirmed = sum(1 for f in run.findings if labels.get(f.finding_id) is True)
    raised = len(run.findings)
    return confirmed / raised if raised else 0.0


def _false_positive_rate(run: PipelineRun, truth: list[GroundTruthFinding]) -> float:
    """Share of raised findings that are wrong: labelled false, or unlabelled."""
    if not run.findings:
        return 0.0
    labels = {t.finding_id: t.is_true_positive for t in truth}
    wrong = sum(1 for f in run.findings if labels.get(f.finding_id) is not True)
    return wrong / len(run.findings)


# ---------------------------------------------------------------------------
# Audit timeline: why this finding got this score
# ---------------------------------------------------------------------------


@dataclass
class AuditEvent:
    step: str
    contribution: float
    rationale: str = ""


@dataclass
class AuditTimeline:
    finding_id: str
    final_score: float
    final_verdict: str
    events: list[AuditEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "final_score": round(self.final_score, 4),
            "final_verdict": self.final_verdict,
            "events": [
                {
                    "step": e.step,
                    "contribution": round(e.contribution, 4),
                    "rationale": e.rationale,
                }
                for e in self.events
            ],
        }


def build_audit_timeline(finding: PipelineFinding) -> AuditTimeline:
    """Decompose a finding's final score into the steps that produced it.

    Order matters: deterministic contributions (hard rule, taxonomy) come
    first, then the model's raw score, then each judge's adjustment. Reading
    top to bottom reconstructs how the number was reached.
    """
    timeline = AuditTimeline(
        finding_id=finding.finding_id,
        final_score=finding.score,
        final_verdict=finding.final_verdict,
    )

    if finding.hard_rule_triggered:
        timeline.events.append(
            AuditEvent(
                step="hard_rule",
                contribution=0.0,
                rationale=f"Triggered: {finding.hard_rule_triggered}",
            )
        )
    if finding.taxonomy_match:
        timeline.events.append(
            AuditEvent(
                step="taxonomy_match",
                contribution=0.0,
                rationale=f"Matched taxonomy: {finding.taxonomy_match}",
            )
        )

    timeline.events.append(
        AuditEvent(
            step="agent_raw",
            contribution=finding.raw_agent_score,
            rationale=f"Agent {finding.raised_by or 'unknown'} produced raw score",
        )
    )

    for step, delta, rationale in (
        ("judge_finding", finding.judge_finding_delta, "Finding-level judge adjustment"),
        ("judge_severity", finding.judge_severity_delta, "Severity-level judge adjustment"),
        ("judge_meta", finding.judge_meta_delta, "Meta-level judge adjustment"),
    ):
        if delta:
            timeline.events.append(
                AuditEvent(step=step, contribution=delta, rationale=rationale)
            )

    return timeline


def explain_verdict(timeline: AuditTimeline) -> str:
    """Render a timeline as the plain-language answer to "why this verdict?"."""
    lines = [
        f"Finding {timeline.finding_id}: final score {round(timeline.final_score, 2)}; "
        f"verdict {timeline.final_verdict or 'N/A'}."
    ]
    for event in timeline.events:
        lines.append(
            f"- {event.step}: {event.rationale} "
            f"(contribution {round(event.contribution, 2)})."
        )
    return "\n".join(lines)


__all__ = [
    "AuditEvent",
    "AuditTimeline",
    "GroundTruthFinding",
    "JudgeBenchmarkRun",
    "PipelineFinding",
    "PipelineFn",
    "PipelineRun",
    "build_audit_timeline",
    "explain_verdict",
    "run_judge_benchmark",
]
