"""Portfolio excerpt, adapted. Decision-quality evaluation harness.

This is the offline gate that scores hiring-AI behavior against a labeled
dataset before a prompt or rubric change ships. It answers three questions:

  Is it right? Per-class precision, recall, F1, plus macro average and overall
  accuracy over a multi-class decision (recommend, maybe, reject).

  Is it stable? Run-to-run consistency between two runs on the same candidates,
  measured as raw agreement and Cohen's kappa (agreement corrected for chance).

  Is it fair? The selection-rate gap and mean-score gap between a traditional
  and a non-traditional group, framed as demographic parity.

Scope: the harness consumes predictions that were already produced by the
rubric-driven scorer. That scorer, its rubric, its prompts, and the model
routing that generate the labels and scores are proprietary and are not in
this excerpt. Everything below operates on labeled prediction records only, so
it reads standalone with no internal imports.

Statistical note on the fairness section: a selection-rate gap measures outcome
disparity, not causation. A nonzero gap can come from real differences in the
underlying (gold) labels, not from the model. It flags where to look; it does
not by itself prove bias. The report exposes both signed gaps (predicted and
gold) so their directions are visible; it deliberately does not subtract one
absolute gap from the other to attribute a "model-added" share, because that
subtraction is invalid when the model reverses the direction of the disparity.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# The favorable outcome for demographic-parity style analysis. In the real
# system this maps to the top decision tier; here it is the one label that
# advances a candidate.
FAVORABLE_DECISION = "recommend"


@dataclass(frozen=True)
class PredictionRecord:
    """One labeled prediction. Inputs to the harness, not produced by it."""

    candidate_id: str
    group: str  # "traditional" | "non_traditional"
    gold: str  # ground-truth decision label
    predicted: str  # decision label the system produced
    score: float  # continuous score behind the decision, higher is stronger


@dataclass(frozen=True)
class ClassMetrics:
    """Precision, recall, F1 and support for a single decision label."""

    label: str
    precision: float
    recall: float
    f1: float
    support: int  # number of gold instances of this label


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
    agreement_rate: float  # fraction of candidates with identical labels across runs
    cohens_kappa: float  # agreement corrected for chance, in [-1, 1]
    n: int


@dataclass(frozen=True)
class FairnessReport:
    group_a: str
    group_b: str
    selection_rate_a: float
    selection_rate_b: float
    # Signed gap rate_a - rate_b: positive means group_a is favored. The sign is
    # load-bearing, so the direction of any disparity is not thrown away.
    selection_rate_gap_signed: float
    selection_rate_gap: float  # |rate_a - rate_b|, demographic-parity difference
    mean_score_a: float
    mean_score_b: float
    mean_score_gap_signed: float  # score_a - score_b, signed
    mean_score_gap: float  # |mean_a - mean_b|
    # The same predicted-vs-gold comparison on the GOLD labels, for context.
    base_rate_gap_signed: float  # gold_rate_a - gold_rate_b, signed
    base_rate_gap: float  # |gold_rate_a - gold_rate_b|
    note: str


@dataclass(frozen=True)
class EvaluationReport:
    classification: ClassificationReport
    fairness: FairnessReport | None
    consistency: ConsistencyReport | None = None
    labels: list[str] = field(default_factory=list)


def _safe_div(numerator: float, denominator: float) -> float:
    """Return numerator / denominator, or 0.0 when the denominator is zero.

    Zero denominators are the normal case, not an error: a label the model never
    predicts has no precision denominator, and a label absent from the gold set
    has no recall denominator. Convention here follows scikit-learn: undefined
    ratios are reported as 0.0 rather than raising or emitting NaN, so downstream
    averaging stays finite.
    """
    return numerator / denominator if denominator else 0.0


def classification_report(records: list[PredictionRecord]) -> ClassificationReport:
    """Compute per-class precision/recall/F1, macro averages, and accuracy.

    Labels are taken from the union of gold and predicted values, so a label the
    model hallucinates (predicted but never gold) still gets a row with zero
    recall, and a label it never predicts still gets zero precision. Macro
    averaging weights every label equally, which is deliberate: the rare
    "recommend" class matters as much as the common "reject" class, and a
    frequency-weighted average would let a majority class hide failures on the
    minority one.
    """
    if not records:
        raise ValueError("classification_report requires at least one record")

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
        # F1 is the harmonic mean; guard the case where both are zero so we do
        # not divide by a zero (precision + recall).
        f1 = _safe_div(2 * precision * recall, precision + recall)
        per_class[label] = ClassMetrics(
            label=label,
            precision=precision,
            recall=recall,
            f1=f1,
            support=gold_count[label],
        )

    n_labels = len(labels)
    macro_precision = _safe_div(sum(m.precision for m in per_class.values()), n_labels)
    macro_recall = _safe_div(sum(m.recall for m in per_class.values()), n_labels)
    macro_f1 = _safe_div(sum(m.f1 for m in per_class.values()), n_labels)

    return ClassificationReport(
        accuracy=_safe_div(correct, len(records)),
        macro_precision=macro_precision,
        macro_recall=macro_recall,
        macro_f1=macro_f1,
        per_class=per_class,
        n=len(records),
    )


def consistency_report(
    run_a: list[PredictionRecord],
    run_b: list[PredictionRecord],
) -> ConsistencyReport:
    """Compare two runs on the same candidates: raw agreement and Cohen's kappa.

    The two runs are aligned by candidate_id; only candidates present in both
    are compared, and the alignment does not assume matching input order. Raw
    agreement over-credits stability when the label distribution is skewed
    (two runs that always say "reject" agree 100% while carrying no signal), so
    we also report Cohen's kappa, which subtracts the agreement expected by
    chance given each run's own label frequencies.
    """
    by_id_b = {r.candidate_id: r for r in run_b}
    pairs = [
        (a.predicted, by_id_b[a.candidate_id].predicted)
        for a in run_a
        if a.candidate_id in by_id_b
    ]
    if not pairs:
        raise ValueError("consistency_report requires overlapping candidate ids")

    n = len(pairs)
    observed_agreement = _safe_div(sum(1 for x, y in pairs if x == y), n)

    # Expected agreement under independence: for each label, multiply the two
    # runs' marginal rates of using it, then sum. This is the chance baseline
    # kappa corrects against.
    labels_a = Counter(x for x, _ in pairs)
    labels_b = Counter(y for _, y in pairs)
    all_labels = set(labels_a) | set(labels_b)
    expected_agreement = sum(
        (labels_a[label] / n) * (labels_b[label] / n) for label in all_labels
    )

    # kappa = (observed - expected) / (1 - expected). Two edge cases:
    #   expected == 1: both runs used a single, identical label everywhere, so
    #     there is no chance-corrected signal to measure. Report perfect
    #     agreement (1.0) if the runs also agreed, else 0.0.
    #   observed == 1 with expected < 1: perfect agreement, kappa is exactly 1.0.
    if expected_agreement >= 1.0:
        kappa = 1.0 if observed_agreement >= 1.0 else 0.0
    else:
        kappa = (observed_agreement - expected_agreement) / (1.0 - expected_agreement)

    return ConsistencyReport(
        agreement_rate=observed_agreement,
        cohens_kappa=kappa,
        n=n,
    )


def fairness_report(
    records: list[PredictionRecord],
    group_a: str = "traditional",
    group_b: str = "non_traditional",
) -> FairnessReport:
    """Selection-rate parity gap and mean-score gap between two groups.

    Selection rate is the fraction of a group that received the favorable
    decision. The gap between the two groups is the demographic-parity
    difference: 0.0 means both groups advance at the same rate. Each gap is
    reported both signed (rate_a - rate_b, so the direction is preserved) and as
    an absolute value (the parity magnitude). The same pair is computed on the
    GOLD labels (base_rate_gap*) for context.

    The signed forms exist because comparing only the two absolute gaps is
    misleading: if the gold labels favor group_a while the predictions favor
    group_b, both absolute gaps can be equal while the model has in fact reversed
    the disparity. Inspect the predicted and gold gaps together, with their
    signs; do not subtract one absolute gap from the other to claim a "model
    added this much" quantity.
    """
    group_records = {
        group_a: [r for r in records if r.group == group_a],
        group_b: [r for r in records if r.group == group_b],
    }

    def selection_rate(rs: list[PredictionRecord], *, on_gold: bool = False) -> float:
        label_of = (lambda r: r.gold) if on_gold else (lambda r: r.predicted)
        favorable = sum(1 for r in rs if label_of(r) == FAVORABLE_DECISION)
        return _safe_div(favorable, len(rs))

    def mean_score(rs: list[PredictionRecord]) -> float:
        return _safe_div(sum(r.score for r in rs), len(rs))

    rate_a = selection_rate(group_records[group_a])
    rate_b = selection_rate(group_records[group_b])
    gold_rate_a = selection_rate(group_records[group_a], on_gold=True)
    gold_rate_b = selection_rate(group_records[group_b], on_gold=True)
    score_a = mean_score(group_records[group_a])
    score_b = mean_score(group_records[group_b])

    note = (
        "Selection-rate gap measures outcome disparity between groups, not "
        "causation. Read the signed predicted gap and the signed gold base-rate "
        "gap together: if they point the same way the model tracks an existing "
        "disparity, and if they point opposite ways the model has reversed it. "
        "Do not subtract the absolute gaps to attribute a model-added share; "
        "that hides direction. This metric flags where to investigate and does "
        "not by itself prove bias."
    )

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
        base_rate_gap_signed=gold_rate_a - gold_rate_b,
        base_rate_gap=abs(gold_rate_a - gold_rate_b),
        note=note,
    )


def evaluate(
    records: list[PredictionRecord],
    second_run: list[PredictionRecord] | None = None,
) -> EvaluationReport:
    """Run the full evaluation and return one typed report.

    Consistency is computed only when a second run is supplied, since it is the
    one metric that needs two passes over the same candidates.
    """
    classification = classification_report(records)
    fairness = fairness_report(records)
    consistency = (
        consistency_report(records, second_run) if second_run is not None else None
    )
    labels = sorted(classification.per_class)

    return EvaluationReport(
        classification=classification,
        fairness=fairness,
        consistency=consistency,
        labels=labels,
    )


if __name__ == "__main__":
    # Tiny illustrative run. The gold labels favor the traditional group, and
    # the model widens that gap, exactly the pattern the fairness section exists
    # to surface.
    demo = [
        PredictionRecord("c1", "traditional", "recommend", "recommend", 4.6),
        PredictionRecord("c2", "traditional", "recommend", "recommend", 4.1),
        PredictionRecord("c3", "traditional", "maybe", "maybe", 3.0),
        PredictionRecord("c4", "non_traditional", "recommend", "maybe", 3.4),
        PredictionRecord("c5", "non_traditional", "maybe", "reject", 2.2),
        PredictionRecord("c6", "non_traditional", "reject", "reject", 1.5),
    ]
    report = evaluate(demo)
    c = report.classification
    print(f"accuracy={c.accuracy:.2f}  macro_f1={c.macro_f1:.2f}")
    for label in report.labels:
        m = c.per_class[label]
        print(f"  {label:<10} P={m.precision:.2f} R={m.recall:.2f} F1={m.f1:.2f} n={m.support}")
    f = report.fairness
    assert f is not None
    print(
        f"selection_rate gap signed={f.selection_rate_gap_signed:+.2f} "
        f"(pred: {f.selection_rate_a:.2f} vs {f.selection_rate_b:.2f}, "
        f"gold base-rate gap signed={f.base_rate_gap_signed:+.2f})"
    )
