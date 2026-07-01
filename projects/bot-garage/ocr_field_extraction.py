"""Portfolio excerpt, adapted. Confidence-gated OCR field extraction from a
vehicle registration document (the Italian "libretto", the carta di circolazione).

The honesty-of-data discipline is the point: every field the extractor recovers
carries a confidence, and only fields at or above a threshold are trusted;
weaker reads are surfaced for manual confirmation rather than written to the
database. Extraction is deterministic and positional, anchored on the harmonized
EU registration codes ((A) plate, (D.1) make, (E) VIN, ...), with regex
validators that can correct or downgrade a positional read.

Stubbed so the excerpt reads standalone: the OCR itself (a local vision-language
and Tesseract pipeline) sits behind `transcribe`; the full official code table
lives in the real `libretto_fields` module and is inlined here as a small
illustrative subset. The invoice-parsing flow is omitted.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Harmonized EU vehicle-registration codes, an illustrative subset of the real
# table. These are the public "codici comunitari armonizzati", not product data:
# a "(code)" is printed next to each field on the document.
_CODE_FIELDS: dict[str, str] = {
    "A": "plate",
    "B": "first_registration",
    "D.1": "make",
    "D.3": "model",
    "E": "vin",
    "V.9": "emissions",
}

# The confidence gate. Illustrative default, not a tuned product value.
_MIN_CONFIDENCE = 0.70

_VIN_RE = re.compile(r"\b([A-HJ-NPR-Z0-9]{17})\b")            # ISO 3779: 17 chars, no I, O, Q
_PLATE_CAR_RE = re.compile(r"\b([A-Z]{2})\s?(\d{3})\s?([A-Z]{2})\b")  # AA000AA
_PLATE_MOTO_RE = re.compile(r"\b([A-Z]{2})\s?(\d{5})\b")      # AA00000
_YEAR_RE = re.compile(r"\b(19[5-9]\d|20[0-4]\d)\b")
_PAREN_TOKEN_RE = re.compile(r"[(\[]\s*([A-Za-z][0-9A-Za-z.,:\- ]{0,7}?)\s*[)\]]")

# The registration has a legend page ("SIGNIFICATO DEI CODICI") that DEFINES the
# codes; if it is not cut, extraction reads the definitions instead of the values.
_LEGEND_MARKERS = (r"SIGNIFICATO\s+DEI\s+CODICI", r"CODICI\s+COMUNITARI\s+ARMONIZZATI")


def transcribe(document_path: str) -> str:
    """Run the local OCR pipeline over a scanned registration PDF.

    Omitted from this excerpt: the on-device vision-language and Tesseract OCR,
    page rendering, and layout decoding. Callers pass the resulting text to
    extract_registration; this stub only marks the boundary.
    """
    raise NotImplementedError("local OCR pipeline omitted from portfolio excerpt")


def _norm_code(raw: str) -> str:
    """Canonicalize an OCR-mangled code: 'D..1', 'd 1', and 'D:1' all become 'D.1'."""
    parts = re.findall(r"[A-Za-z]+|[0-9]+", raw.upper())
    return ".".join(parts) if parts else ""


def _cut_legend(text: str) -> str:
    """Drop the code-legend section so values, not definitions, are read."""
    cut = len(text)
    for pattern in _LEGEND_MARKERS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            cut = min(cut, m.start())
    return text[:cut]


def _clean(value: str) -> str:
    """Drop OCR noise; reject a value that is only digits or punctuation."""
    value = re.sub(r"\s{2,}", " ", value).strip(" .:-|\t")
    return value if re.search(r"[A-Za-z]", value) else ""


def _pairs_by_parens(text: str) -> dict[str, str]:
    """Biunivocal map, code to value: each "(code)" is a field and the text that
    follows it, up to the next known code, is its value.

    Only codes on the official whitelist become pairs, so an incidental "(kg)" or
    "(EURO 4)" neither invents a field nor truncates the previous one. The first
    occurrence wins, because the data page precedes any later repetition.
    """
    tokens = [m for m in _PAREN_TOKEN_RE.finditer(text) if _norm_code(m.group(1)) in _CODE_FIELDS]
    pairs: dict[str, str] = {}
    for i, m in enumerate(tokens):
        code = _norm_code(m.group(1))
        end = tokens[i + 1].start() if i + 1 < len(tokens) else len(text)
        value = text[m.end():end].split("\n", 1)[0]   # keep the value on the code's own line
        value = re.sub(r"\s+", " ", value).strip(" .:;,-|\t")
        if value and code not in pairs:
            pairs[code] = value[:60]
    return pairs


@dataclass
class Field:
    """One recovered field: its value and the confidence behind the read."""

    value: str
    confidence: float


@dataclass
class RegistrationExtract:
    fields: dict[str, Field] = field(default_factory=dict)

    def set(self, name: str, value: str, confidence: float) -> None:
        if value:
            self.fields[name] = Field(value, confidence)

    def accepted(self, threshold: float = _MIN_CONFIDENCE) -> dict[str, str]:
        """Fields safe to persist: confidence at or above the gate."""
        return {k: f.value for k, f in self.fields.items() if f.confidence >= threshold}

    def needs_review(self, threshold: float = _MIN_CONFIDENCE) -> dict[str, str]:
        """Weaker reads: surfaced for a human to confirm, never auto-persisted."""
        return {k: f.value for k, f in self.fields.items() if f.confidence < threshold}


def extract_registration(source: str) -> RegistrationExtract:
    """Extract vehicle fields from the OCR text of a registration document.

    Conservative by design: a field is filled only when its value is reasonably
    certain, and every value keeps the confidence behind it so the caller can
    gate on it. The positional parens map is the primary source; the regex
    validators below correct or downgrade it. A 17-character VIN is trusted; a
    plate read off its own (A) code beats a loose page scan that could otherwise
    grab a "KM 23450" odometer reading.
    """
    text = _cut_legend(source)
    up = text.upper()
    out = RegistrationExtract()
    pairs = {_CODE_FIELDS[c]: v for c, v in _pairs_by_parens(text).items()}

    # VIN (E): the charset validator can correct the positional read. A full 17
    # characters is high confidence; a short read is kept but flagged for review.
    m = re.search(r"(?:^|[\s|(\[])E[\s.:)\]|>\-]{1,4}([A-HJ-NPR-Z0-9]{11,17})", up, re.MULTILINE)
    fallback = _VIN_RE.search(up)
    vin = (m.group(1) if m else (fallback.group(1) if fallback else "")) or pairs.get("vin", "")
    if vin:
        out.set("vin", vin, 0.9 if len(vin) == 17 else 0.5)

    # Plate (A): prefer the value beside its own code; the loose scan is only a
    # fallback and must skip "KM", so an odometer line is not read as a plate.
    plate_a = pairs.get("plate", "").replace(" ", "").upper()
    if re.fullmatch(r"[A-Z]{2}\d{3}[A-Z]{2}|[A-Z]{2}\d{5}", plate_a):
        out.set("plate", plate_a, 0.9)
    else:
        car = _PLATE_CAR_RE.search(up)
        moto = next((mm for mm in _PLATE_MOTO_RE.finditer(up) if mm.group(1) != "KM"), None)
        if car:
            out.set("plate", f"{car.group(1)}{car.group(2)}{car.group(3)}", 0.85)
        elif moto:
            out.set("plate", f"{moto.group(1)}{moto.group(2)}", 0.7)

    # Make (D.1) and model (D.3): the parens value, lightly cleaned.
    for name, confidence in (("make", 0.7), ("model", 0.6)):
        out.set(name, _clean(pairs.get(name, "")), confidence)

    # First registration (B) to year, keeping the four-digit year off the date.
    year_match = _YEAR_RE.search(pairs.get("first_registration", ""))
    if year_match:
        out.set("year", year_match.group(1), 0.7)

    # Emissions class (V.9): the Euro rating, tolerant of OCR spacing.
    emissions = re.search(r"\bEURO[\s:]*(\d[A-Z0-9\-]{0,7})", up)
    if emissions:
        out.set("emissions", f"Euro {emissions.group(1).strip('-')}", 0.5)

    return out


if __name__ == "__main__":
    # A short synthetic libretto-like text: a clean VIN and make, a plate read
    # off its (A) code, and an odometer "KM" line the plate scan must not grab.
    sample = (
        "(A) AB123CD\n"
        "(D.1) FIAT\n"
        "(D.3) PANDA\n"
        "(E) ZFA312000A1234567\n"
        "(B) 14.03.2019\n"
        "(V.9) EURO 6B\n"
        "KM 23450\n"
    )
    extract = extract_registration(sample)
    print("accepted:", extract.accepted())
    for name, value in extract.needs_review().items():
        print(f"review:   {name} = {value!r} (conf {extract.fields[name].confidence:.2f})")
