# Picks which real pages carry which "before" failure cause, and defines the
# structural content fix for each. Missing-page and stale-number pages are
# deliberately seeded (the same seeded-and-measured pattern the base repo uses
# for schema drift and publish-gate scenarios); retrieval-miss pages are
# discovered, not seeded: they are real BM25 ranking misses this project found
# by running the generated questions against the real, unmodified corpus and
# checking which ones the retriever actually got wrong on its own.
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assistant.answer import answer_question  # noqa: E402
from assistant.ingest import Passage  # noqa: E402
from assistant.retrieval import BM25Index  # noqa: E402

NUMERIC_RE = re.compile(r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b")


@dataclass(frozen=True)
class StaleFix:
    page_id: str
    old_value: str
    new_value: str


@dataclass(frozen=True)
class StructuralFix:
    page_id: str
    kind: str  # "add_missing_page" | "correct_stale_number" | "add_heading" | "finer_chunking"
    description: str


def inject_stale_numbers(text: str, rng, max_fixes: int = 3) -> tuple[str, list[StaleFix]]:
    """Replaces up to max_fixes distinct numeric tokens with a different number
    (a deliberately wrong, old-looking figure), simulating a page whose stats
    have not been updated since a product changed. Returns the staled text and
    the list of corrections a later fix would need to make."""
    matches = list(NUMERIC_RE.finditer(text))
    if not matches:
        return text, []
    chosen = matches[: max_fixes] if len(matches) <= max_fixes else rng.sample(matches, max_fixes)
    chosen.sort(key=lambda m: m.start())
    fixes: list[StaleFix] = []
    out = []
    cursor = 0
    for m in chosen:
        out.append(text[cursor : m.start()])
        old_value = m.group(0)
        numeric = old_value.replace(",", "")
        try:
            n = float(numeric)
            staled = n * 0.5 if n > 1 else n
            new_value = str(int(staled)) if staled == int(staled) else f"{staled:.1f}"
        except ValueError:
            new_value = old_value
        if new_value == old_value:
            new_value = old_value + "0"
        out.append(new_value)
        fixes.append(StaleFix(page_id="", old_value=old_value, new_value=new_value))
        cursor = m.end()
    out.append(text[cursor:])
    return "".join(out), fixes


def add_heading(text: str, phrase: str, title: str = "") -> str:
    """A real editor's fix for a page that exists but never ranks first for its
    own topic: give the topic an explicit heading-style sentence at the very
    top, naming it plainly instead of leaving it implicit in the middle of a
    paragraph. One short sentence (attempt 1) was tried first and measured in
    README Findings; it was not enough to move the ranking for most of the
    affected pages, so this is the two-sentence version (attempt 2)."""
    clean = phrase.strip().capitalize()
    lead = f"{clean}. About {clean.lower()}: this page, {title.strip() or 'this document'}, is the primary reference for {clean.lower()}."
    return f"{lead} {text}"


@dataclass(frozen=True)
class ScenarioPlan:
    missing_page_ids: list[str]
    stale_page_ids: list[str]
    stale_fixes: dict[str, list[StaleFix]]  # page_id -> fixes applied to its raw text
    retrieval_miss_page_ids: list[str]
    retrieval_miss_phrases: dict[str, str]  # page_id -> keyphrase to add as a heading


def discover_retrieval_misses(
    candidates: list[dict],
    passages: list[Passage],
    index: BM25Index,
    exclude_page_ids: set[str],
    n_needed: int,
) -> list[tuple[str, str]]:
    """Runs each candidate question against the real, unmodified index and
    returns up to n_needed (page_id, phrase) pairs where the retriever's
    actual top-1 result is NOT the expected passage, excluding pages already
    used for another scenario. This is a measurement, not a seed: it only
    returns pages where a real miss was observed."""
    found: list[tuple[str, str]] = []
    seen_pages: set[str] = set()
    for item in candidates:
        page_id = item["expected_doc_id"]
        if page_id in exclude_page_ids or page_id in seen_pages:
            continue
        draft = answer_question(item["question"], index)
        if draft.cited_doc_id != page_id or draft.cited_page_number != item["expected_page_number"]:
            found.append((page_id, item["key_phrase"]))
            seen_pages.add(page_id)
        if len(found) >= n_needed:
            break
    return found
