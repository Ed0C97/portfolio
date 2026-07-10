"""Portfolio excerpt, adapted. Decision-quality evaluation harness.

The offline gate that scores hiring-AI behavior against a labeled dataset before
a prompt or rubric change ships. It answers three questions:
  Is it right? Per-class precision, recall, F1, plus macro average and accuracy.
  Is it stable? Run-to-run raw agreement and Cohen's kappa (chance-corrected).
  Is it fair? Selection-rate and mean-score gaps between a traditional and a
    non-traditional group, framed as demographic parity. FAIRNESS_NOTE carries
    the one authoritative caveat on how to read that gap.

Scope: the harness consumes predictions already produced by the rubric-driven
scorer. That scorer, its rubric, its prompts, and the model routing behind the
labels and scores are proprietary and not in this excerpt. Everything below
operates on labeled prediction records only, so it reads standalone.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# The favorable outcome for demographic-parity analysis: the one label that
# advances a candidate (the top decision tier in the real system).
FAVORABLE_DECISION = "recommend"

# The single authoritative fairness caveat, referenced (not repeated) elsewhere
# and carried on the report so callers read it at the point of use.
FAIRNESS_NOTE = (
    "Selection-rate gap measures outcome disparity, not causation. Read the "
    "signed predicted gap and the signed gold base-rate gap together; do not "
    "subtract the absolute gaps to attribute a model-added share. Flags where "
    "to investigate, does not prove bias."
)


@dataclass(frozen=True)
class PredictionRecord:
    """One labeled prediction. Input to the harness, not produced by it."""
    candidate_id: str
    group: str  # "traditional" | "non_traditional"
    gold: str  # ground-truth decision label
    predicted: str  # decision label the system produced
    score: float  # continuous score behind the decision, higher is stronger


@dataclass(frozen=True)
class ClassMetrics:
    """Precision, recall, F1 and gold support for a single decision label."""
    label: str
    precision: float
    recall: float
    f1: float
    support: int


@dataclass(frozen=True)
class ClassificationReport:
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    per_class: dict[str, ClassMetrics]
    n: int


@dataclass(frozen=True)
class ConsistencyReport:
    agreement_rate: float  # fraction labeled identically across the two runs
    cohens_kappa: float  # agreement corrected for chance, in [-1, 1]
    n: int


@dataclass(frozen=True)
class FairnessReport:
    group_a: str
    group_b: str
    selection_rate_a: float
    selection_rate_b: float
    # Signed gaps (a - b) preserve direction; absolute gaps give parity
    # magnitude; base_rate_* is the same pair on the GOLD labels. See FAIRNESS_NOTE.
    selection_rate_gap_signed: float
    selection_rate_gap: float
    mean_score_a: float
    mean_score_b: float
    mean_score_gap_signed: float
    mean_score_gap: float
    base_rate_gap_signed: float
    base_rate_gap: float
    note: str  # FAIRNESS_NOTE, carried to the point of use


@dataclass(frozen=True)
class EvaluationReport:
    classification: ClassificationReport
    fairness: FairnessReport | None
    consistency: ConsistencyReport | None = None
    labels: list[str] = field(default_factory=list)


def _safe_div(numerator: float, denominator: float) -> float:
    # Zero denominators are normal here (a label never predicted, or absent from
    # gold); returning 0.0 rather than NaN keeps downstream averaging finite,
    # following the scikit-learn convention for undefined ratios.
    return numerator / denominator if denominator else 0.0


def classification_report(records: list[PredictionRecord]) -> ClassificationReport:
    """Per-class precision/recall/F1, macro averages, and accuracy."""
    if not records:
        raise ValueError("classification_report requires at least one record")

    # Union of gold and predicted, so a hallucinated label still gets a
    # zero-recall row and one never predicted gets a zero-precision row.
    labels = sorted({r.gold for r in records} | {r.predicted for r in records})
    true_positive: Counter[str] = Counter()
    predicted_count: Counter[str] = Counter()  # true positives + false positives
    gold_count: Counter[str] = Counter()  # true positives + false negatives
    correct = 0

    for r in records:
        gold_count[r.gold] += 1
        predicted_count[r.predicted] += 1
        if r.gold == r.predicted:
            true_positive[r.gold] += 1
            correct += 1

    per_class: dict[str, ClassMetrics] = {}
    for label in labels:
        tp = true_positive[label]
        precision = _safe_div(tp, predicted_count[label])
        recall = _safe_div(tp, gold_count[label])
        # F1 is the harmonic mean; _safe_div also guards the both-zero case so we
        # never divide by a zero (precision + recall).
        f1 = _safe_div(2 * precision * recall, precision + recall)
        per_class[label] = ClassMetrics(label, precision, recall, f1, gold_count[label])

    # Macro averaging weights labels equally on purpose: the rare "recommend"
    # class matters as much as the common "reject" one, where a frequency-
    # weighted average would let the majority hide minority failures.
    n_labels = len(labels)
    return ClassificationReport(
        accuracy=_safe_div(correct, len(records)),
        macro_precision=_safe_div(sum(m.precision for m in per_class.values()), n_labels),
        macro_recall=_safe_div(sum(m.recall for m in per_class.values()), n_labels),
        macro_f1=_safe_div(sum(m.f1 for m in per_class.values()), n_labels),
        per_class=per_class,
        n=len(records),
    )


def consistency_report(
    run_a: list[PredictionRecord],
    run_b: list[PredictionRecord],
) -> ConsistencyReport:
    """Compare two runs on the same candidates: raw agreement and Cohen's kappa.

    Raw agreement over-credits stability on skewed distributions (always saying
    "reject" agrees 100% with no signal), so we also report kappa, chance-corrected.
    """
    # Align by candidate_id (order need not match); compare only ids in both runs.
    by_id_b = {r.candidate_id: r for r in run_b}
    pairs = [
        (a.predicted, by_id_b[a.candidate_id].predicted)
        for a in run_a
        if a.candidate_id in by_id_b
    ]
    if not pairs:
        raise ValueError("consistency_report requires overlapping candidate ids")

    n = len(pairs)
    observed = _safe_div(sum(1 for x, y in pairs if x == y), n)

    # Expected agreement under independence: for each label, multiply the runs'
    # marginal rates of using it, then sum. This is the chance baseline.
    labels_a = Counter(x for x, _ in pairs)
    labels_b = Counter(y for _, y in pairs)
    expected = sum(
        (labels_a[label] / n) * (labels_b[label] / n)
        for label in set(labels_a) | set(labels_b)
    )

    # kappa = (observed - expected) / (1 - expected). Edge case: expected == 1
    # means both runs used one identical label everywhere, so there is no
    # chance-corrected signal; report 1.0 if they also agreed, else 0.0.
    if expected >= 1.0:
        kappa = 1.0 if observed >= 1.0 else 0.0
    else:
        kappa = (observed - expected) / (1.0 - expected)

    return ConsistencyReport(agreement_rate=observed, cohens_kappa=kappa, n=n)


def fairness_report(
    records: list[PredictionRecord],
    group_a: str = "traditional",
    group_b: str = "non_traditional",
) -> FairnessReport:
    """Selection-rate parity gap and mean-score gap between two groups.

    Each gap is signed (a - b, direction kept) and absolute, with the same pair on
    the GOLD labels (base_rate_gap*) for context. See FAIRNESS_NOTE to read them.
    """
    # Records whose group is neither group_a nor group_b are excluded here.
    rows_a = [r for r in records if r.group == group_a]
    rows_b = [r for r in records if r.group == group_b]

    def selection_rate(rs: list[PredictionRecord], *, on_gold: bool = False) -> float:
        label_of = (lambda r: r.gold) if on_gold else (lambda r: r.predicted)
        return _safe_div(sum(1 for r in rs if label_of(r) == FAVORABLE_DECISION), len(rs))

    def mean_score(rs: list[PredictionRecord]) -> float:
        return _safe_div(sum(r.score for r in rs), len(rs))

    rate_a, rate_b = selection_rate(rows_a), selection_rate(rows_b)
    gold_a = selection_rate(rows_a, on_gold=True)
    gold_b = selection_rate(rows_b, on_gold=True)
    score_a, score_b = mean_score(rows_a), mean_score(rows_b)

    return FairnessReport(
        group_a=group_a,
        group_b=group_b,
        selection_rate_a=rate_a,
        selection_rate_b=rate_b,
        selection_rate_gap_signed=rate_a - rate_b,
        selection_rate_gap=abs(rate_a - rate_b),
        mean_score_a=score_a,
        mean_score_b=score_b,
        mean_score_gap_signed=score_a - score_b,
        mean_score_gap=abs(score_a - score_b),
        base_rate_gap_signed=gold_a - gold_b,
        base_rate_gap=abs(gold_a - gold_b),
        note=FAIRNESS_NOTE,
    )


def evaluate(
    records: list[PredictionRecord],
    second_run: list[PredictionRecord] | None = None,
) -> EvaluationReport:
    """Run the full evaluation and return one typed report.

    Consistency is computed only when a second run is supplied, the one metric
    that needs two passes; fairness uses the two default groups (see above).
    """
    classification = classification_report(records)
    consistency = (
        consistency_report(records, second_run) if second_run is not None else None
    )
    return EvaluationReport(
        classification=classification,
        fairness=fairness_report(records),
        consistency=consistency,
        labels=sorted(classification.per_class),
    )


if __name__ == "__main__":
    # Tiny run where the gold labels favor the traditional group and the model
    # widens the gap, the exact pattern the fairness section exists to surface.
    demo = [
        PredictionRecord("c1", "traditional", "recommend", "recommend", 4.6),
        PredictionRecord("c2", "traditional", "recommend", "recommend", 4.1),
        PredictionRecord("c3", "traditional", "maybe", "maybe", 3.0),
        PredictionRecord("c4", "non_traditional", "recommend", "maybe", 3.4),
        PredictionRecord("c5", "non_traditional", "maybe", "reject", 2.2),
        PredictionRecord("c6", "non_traditional", "reject", "reject", 1.5),
    ]
    report = evaluate(demo)
    c, f = report.classification, report.fairness
    assert f is not None
    print(f"accuracy={c.accuracy:.2f}  macro_f1={c.macro_f1:.2f}")
    print(
        f"selection_rate gap {f.selection_rate_gap_signed:+.2f} "
        f"(pred {f.selection_rate_a:.2f} vs {f.selection_rate_b:.2f}, "
        f"gold base-rate {f.base_rate_gap_signed:+.2f})"
    )
