"""Portfolio excerpt, adapted. Confidence-gated OCR field extraction.

bot-garage imports a vehicle from a registration document, and work items from an
invoice, by running a local vision-language OCR model over the scanned PDF and
then pulling structured fields out of the raw OCR output. The discipline that
keeps the database trustworthy lives here: a field is persisted only when the OCR
confidence behind it clears a threshold. Anything weaker is never silently
accepted, it is routed to a review queue for a human to confirm, so a smudged
plate never becomes a wrong record.

The input is OCR output (recognized tokens, each with a confidence), not the
image: the on-device model that produces those tokens is out of scope and
stubbed. The field patterns use illustrative Italian registration formats; the
real system carries a larger, locale-aware rule set and tolerates common OCR
confusions.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

# Default gate. A field whose aggregated confidence is below this is never
# auto-persisted; it is surfaced for manual confirmation instead.
DEFAULT_MIN_CONFIDENCE = 0.80


class ReviewReason(Enum):
    LOW_CONFIDENCE = "low_confidence"  # a value matched, but the OCR is too weak to trust
    NOT_FOUND = "not_found"            # no token matched the field


@dataclass(frozen=True)
class OcrToken:
    """One token from the OCR pass: recognized text plus the model's confidence."""

    text: str
    confidence: float  # in [0.0, 1.0]
    # (x0, y0, x1, y1) page coordinates, kept for provenance; unused in this excerpt
    bbox: tuple[float, float, float, float] | None = None


@dataclass(frozen=True)
class ExtractedField:
    """A field recovered from the tokens, with the confidence behind it."""

    name: str
    value: str
    confidence: float
    source_text: str  # the raw token span the value came from, for audit


@dataclass(frozen=True)
class ReviewItem:
    """A field that was not accepted. Never persisted without human confirmation."""

    name: str
    reason: ReviewReason
    candidate_value: str | None  # best guess when low-confidence, None when not found
    confidence: float


@dataclass(frozen=True)
class ExtractionResult:
    """Split outcome: only `accepted` is safe to persist; `needs_review` is not."""

    accepted: dict[str, ExtractedField]
    needs_review: list[ReviewItem]


# --- Field formats (illustrative Italian registration) --------------------

# Post-1994 plate: two letters, three digits, two letters, for example AB123CD.
_PLATE_RE = re.compile(r"[A-Z]{2}\d{3}[A-Z]{2}")
# VIN: 17 characters, letters and digits, excluding I, O, Q per ISO 3779.
_VIN_RE = re.compile(r"[A-HJ-NPR-Z0-9]{17}")
# Date separators seen on scans: slash, dot, or hyphen.
_DATE_RE = re.compile(r"([0-3]?\d)[/.\-]([01]?\d)[/.\-](\d{4})")


def _compact(text: str) -> str:
    """Uppercase and drop the stray spaces OCR injects into codes like plates."""
    return re.sub(r"\s+", "", text).upper()


def _valid_date(text: str) -> str | None:
    """Return a normalized day, month, year date if text parses and ranges hold.

    The regex alone is too permissive (it would accept 39.19.2020), so day and
    month are range-checked. Returns None when the token is not a real date, which
    lets the caller keep scanning nearby tokens instead of trusting a false match.
    """
    m = _DATE_RE.fullmatch(text.strip())
    if not m:
        return None
    day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= day <= 31 and 1 <= month <= 12):
        return None
    return f"{day:02d}/{month:02d}/{year:04d}"


# An extractor takes the token list and returns (value, confidence, source) or None.
Extractor = Callable[[list[OcrToken]], "tuple[str, float, str] | None"]


def _pattern_field(pattern: re.Pattern[str]) -> Extractor:
    """Match a self-identifying code (plate, VIN) against a single compacted token.

    Confidence is just that token's confidence: the value comes from one token, so
    there is nothing weaker to bound it. Kept single-token on purpose; a code split
    across tokens by the OCR is a known limitation left to the review path.
    """

    def extract(tokens: list[OcrToken]) -> tuple[str, float, str] | None:
        for token in tokens:
            compact = _compact(token.text)
            if pattern.fullmatch(compact):
                return compact, token.confidence, token.text
        return None

    return extract


def _date_after(anchor: str, window: int = 4) -> Extractor:
    """Find a valid date in the few tokens after a label like 'Immatricolazione'.

    Anchored on the label because a registration document carries several dates;
    the one that matters is the one next to its caption. Scans a small window after
    the anchor and takes the first token that parses as a real date.
    """
    needle = anchor.lower()

    def extract(tokens: list[OcrToken]) -> tuple[str, float, str] | None:
        for i, token in enumerate(tokens):
            if needle in token.text.lower():
                for following in tokens[i + 1 : i + 1 + window]:
                    normalized = _valid_date(following.text)
                    if normalized is not None:
                        return normalized, following.confidence, following.text
        return None

    return extract


def _name_after(anchor: str, max_tokens: int = 3) -> Extractor:
    """Take the words after a label like 'Intestatario' as a name.

    The value can span several tokens, so its confidence is the MINIMUM over the
    tokens that form it: a name is only as trustworthy as its least certain word,
    and averaging would let one crisp token paper over a smudged one.
    """
    needle = anchor.lower()

    def extract(tokens: list[OcrToken]) -> tuple[str, float, str] | None:
        for i, token in enumerate(tokens):
            if needle in token.text.lower():
                words = [t for t in tokens[i + 1 : i + 1 + max_tokens] if t.text.strip()]
                if not words:
                    continue
                value = " ".join(t.text.strip() for t in words)
                confidence = min(t.confidence for t in words)
                return value, confidence, value
        return None

    return extract


@dataclass(frozen=True)
class FieldSpec:
    """A field to extract and the confidence gate it must clear to be accepted."""

    name: str
    extractor: Extractor
    min_confidence: float = DEFAULT_MIN_CONFIDENCE


_REGISTRATION_FIELDS: list[FieldSpec] = [
    FieldSpec("plate", _pattern_field(_PLATE_RE)),
    FieldSpec("vin", _pattern_field(_VIN_RE)),
    FieldSpec("first_registration_date", _date_after("immatricolaz")),
    FieldSpec("owner_name", _name_after("intestatario")),
]


def extract_fields(
    tokens: list[OcrToken],
    specs: list[FieldSpec] | None = None,
) -> ExtractionResult:
    """Extract each spec's field, gating every result on confidence.

    A field clears the gate only when it both matches and its aggregated confidence
    reaches the spec threshold; then it is accepted and safe to persist. A weak
    match is returned as a LOW_CONFIDENCE review item carrying its best guess, and a
    missing field as NOT_FOUND. The accepted set and the review set are disjoint by
    construction, so a caller can persist `accepted` without re-checking anything.
    """
    specs = specs if specs is not None else _REGISTRATION_FIELDS
    accepted: dict[str, ExtractedField] = {}
    needs_review: list[ReviewItem] = []

    for spec in specs:
        found = spec.extractor(tokens) if tokens else None
        if found is None:
            needs_review.append(ReviewItem(spec.name, ReviewReason.NOT_FOUND, None, 0.0))
            continue
        value, confidence, source = found
        if confidence >= spec.min_confidence:
            accepted[spec.name] = ExtractedField(spec.name, value, confidence, source)
        else:
            needs_review.append(
                ReviewItem(spec.name, ReviewReason.LOW_CONFIDENCE, value, confidence)
            )

    return ExtractionResult(accepted=accepted, needs_review=needs_review)


def run_ocr(document_path: str) -> list[OcrToken]:
    """Run the local vision-language OCR model over a scanned page.

    Omitted from this excerpt: the on-device model, its image preprocessing, and
    the token-and-confidence decoding. Callers feed the resulting tokens to
    extract_fields; this stub only marks the boundary.
    """
    raise NotImplementedError(
        "local vision-language OCR model omitted from portfolio excerpt"
    )


if __name__ == "__main__":
    # A crisp plate, a low-confidence VIN, a dated registration line, and no owner.
    sample = [
        OcrToken("Targa", 0.99),
        OcrToken("AB123CD", 0.96),
        OcrToken("Telaio", 0.98),
        OcrToken("ZFA19200000A11111", 0.62),  # weak: below the gate, goes to review
        OcrToken("Immatricolazione", 0.97),
        OcrToken("14/03/2019", 0.93),
    ]
    result = extract_fields(sample)
    for name, f in result.accepted.items():
        print(f"accepted   {name:<24} {f.value!r} (conf {f.confidence:.2f})")
    for item in result.needs_review:
        print(f"review     {item.name:<24} {item.reason.value} (conf {item.confidence:.2f})")
