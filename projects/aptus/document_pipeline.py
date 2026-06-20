# Portfolio excerpt, adapted. Multi-strategy document ingestion.
# upload bytes + mime -> engine-routed extraction -> sections -> ParsedDocument.
# PDFs with a text layer take the native glyph path; scans fall back to OCR.

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# extraction strategies stubbed here; real impls are PyMuPDF / OCR toolkit / docx


@dataclass(frozen=True, slots=True)
class _Page:
    page: int
    text: str
    confidence: float = 1.0


@dataclass(frozen=True, slots=True)
class _Probe:
    has_text: bool


def probe_pdf_text_layer(data: bytes) -> _Probe:  # pragma: no cover - stub
    raise NotImplementedError


def extract_pdf_via_pymupdf(data: bytes, *, filename: str) -> list[_Page]:  # pragma: no cover
    raise NotImplementedError


def extract_pdf_via_ocr_toolkit(data: bytes, *, filename: str) -> list[_Page]:  # pragma: no cover
    raise NotImplementedError


# rule-based section detection, Italian and English headings

_HEADING_PATTERNS: dict[str, tuple[str, ...]] = {
    "summary": ("summary", "profile", "about me", "profilo", "obiettivo"),
    "experience": (
        "experience",
        "work experience",
        "employment",
        "professional experience",
        "esperienze lavorative",
        "esperienza professionale",
    ),
    "education": ("education", "formazione", "istruzione", "studi"),
    "skills": ("skills", "competenze", "competenze tecniche", "technical skills"),
    "languages": ("languages", "lingue"),
    "certifications": ("certifications", "certificazioni"),
    "projects": ("projects", "progetti"),
}

_HEADING_RE = re.compile(r"^[\s•\-\*]*(?P<text>[A-Za-zÀ-ÿ' ]{2,40})\s*[:\-—]?\s*$")


@dataclass(frozen=True, slots=True)
class DetectedSection:
    label: str
    start_line: int
    end_line: int
    title: str


def _classify_heading(candidate: str) -> str | None:
    for label, patterns in _HEADING_PATTERNS.items():
        for pat in patterns:
            if candidate == pat or candidate.startswith(pat + " "):
                return label
    return None


def detect_sections(text: str) -> list[DetectedSection]:
    if not text or not text.strip():
        return []
    lines = text.splitlines()
    boundaries: list[tuple[int, str, str]] = []
    for idx, line in enumerate(lines):
        m = _HEADING_RE.match(line)
        if not m:
            continue
        candidate = m.group("text").strip().lower()
        label = _classify_heading(candidate)
        if label is not None:
            boundaries.append((idx, label, m.group("text").strip()))

    sections: list[DetectedSection] = []
    for i, (start, label, title) in enumerate(boundaries):
        # a section runs to the line before the next heading, or to EOF
        end = boundaries[i + 1][0] - 1 if i + 1 < len(boundaries) else len(lines) - 1
        sections.append(DetectedSection(label=label, start_line=start, end_line=end, title=title))
    return sections


# top-level pipeline


@dataclass(frozen=True, slots=True)
class ParsedSection:
    label: str
    title: str
    start_line: int
    end_line: int
    text: str


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    mime: str
    page_count: int
    full_text: str
    sections: tuple[ParsedSection, ...]
    engine: str
    extra: dict[str, Any] = field(default_factory=dict)


def _build_sections(text: str, detected: list[DetectedSection]) -> tuple[ParsedSection, ...]:
    if not detected:
        return ()
    lines = text.splitlines()
    out: list[ParsedSection] = []
    for s in detected:
        # body excludes the heading line itself
        body = "\n".join(lines[s.start_line + 1 : s.end_line + 1])
        out.append(
            ParsedSection(
                label=s.label,
                title=s.title,
                start_line=s.start_line,
                end_line=s.end_line,
                text=body,
            )
        )
    return tuple(out)


def parse_bytes(data: bytes, mime: str, *, filename: str = "upload") -> ParsedDocument:
    """Parse upload bytes into a ParsedDocument; raise ValueError on unsupported mime."""
    if mime == "application/pdf":
        # one probe decides the path: native glyph extraction needs no GPU, OCR does
        if probe_pdf_text_layer(data).has_text:
            pages = extract_pdf_via_pymupdf(data, filename=filename)
            engine = "pymupdf"
        else:
            pages = extract_pdf_via_ocr_toolkit(data, filename=filename)
            engine = "ocr_toolkit"
        full_text = "\n\n".join(p.text for p in pages)
        page_count = len(pages)
        extra: dict[str, Any] = {
            "pages": [{"page": p.page, "confidence": p.confidence} for p in pages]
        }
    elif mime == "text/plain":
        full_text = data.decode("utf-8", errors="replace")
        page_count = 1
        engine = "plain_text"
        extra = {}
    else:
        raise ValueError(
            f"Unsupported mime type {mime!r}; expected application/pdf or text/plain"
        )

    sections = _build_sections(full_text, detect_sections(full_text))
    return ParsedDocument(
        mime=mime,
        page_count=page_count,
        full_text=full_text,
        sections=sections,
        engine=engine,
        extra=extra,
    )


__all__ = ["ParsedDocument", "ParsedSection", "DetectedSection", "detect_sections", "parse_bytes"]
