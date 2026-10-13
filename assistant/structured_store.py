# The relational half of "a passage or a row": a document_catalog table
# built straight from corpus_manifest.json's own fields (format, measured
# page count, license note), not from anything inside the copyrighted PDFs.
# A handful of factual questions ("how many pages", "what format") are
# answered directly from one row, cited as that row rather than a passage,
# which is the other half of this project's "every answer cites the passage
# or row it came from" claim.
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

from .answer import Draft

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "corpus_manifest.json"


@dataclass(frozen=True)
class CatalogRow:
    doc_id: str
    title: str
    source_format: str
    measured_pages: int | None
    license_note: str


def load_catalog(path: Path = MANIFEST_PATH) -> list[CatalogRow]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        CatalogRow(
            doc_id=s["id"], title=s["title"], source_format=s["format"],
            measured_pages=s.get("measured_pages"), license_note=s["license_note"],
        )
        for s in data["sources"]
    ]


_PAGE_COUNT_TEMPLATE = "How many pages does {title} have?"
_FORMAT_TEMPLATE = "What format is {title} distributed in?"


@dataclass(frozen=True)
class StructuredQAItem:
    question: str
    expected_doc_id: str
    field: str  # "measured_pages" or "source_format"


def generate_structured_questions(catalog: list[CatalogRow], *, seed: int) -> list[StructuredQAItem]:
    """One page-count question for every row with a known page count (the
    two Wikipedia rows have none, see corpus_manifest.json, and are skipped
    for that question rather than asked with a fabricated answer), plus one
    format question per row. Small and exhaustive rather than sampled,
    since the catalog itself is only 10 rows."""
    rng = random.Random(seed)
    items = []
    for row in catalog:
        if row.measured_pages is not None:
            items.append(StructuredQAItem(_PAGE_COUNT_TEMPLATE.format(title=row.title), row.doc_id, "measured_pages"))
        items.append(StructuredQAItem(_FORMAT_TEMPLATE.format(title=row.title), row.doc_id, "source_format"))
    rng.shuffle(items)
    return items


def answer_structured_question(question: str, catalog: list[CatalogRow]) -> Draft | None:
    """Returns a row-cited Draft if the question matches one of this
    module's two templates against a real title in the catalog, else None
    (meaning: not a structured question, try the passage path instead).
    Matching is exact-template, not fuzzy; see the README's Honest framing
    for why that is the honest scope of this piece."""
    for row in catalog:
        if question == _PAGE_COUNT_TEMPLATE.format(title=row.title) and row.measured_pages is not None:
            text = f"{row.title} is measured at {row.measured_pages} pages (source: catalog row {row.doc_id})."
            return Draft(text, row.doc_id, -1, confidence=1.0, source_kind="row")
        if question == _FORMAT_TEMPLATE.format(title=row.title):
            text = f"{row.title} is distributed as {row.source_format} (source: catalog row {row.doc_id})."
            return Draft(text, row.doc_id, -1, confidence=1.0, source_kind="row")
    return None
