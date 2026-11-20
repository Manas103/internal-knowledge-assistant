# Grounded question generation over the real comms-shaped corpus, the same
# synthetic-QA-from-a-real-document technique as assistant/qagen.py: every
# question quotes a real short phrase from one real passage, and the ground
# truth is exactly that passage's (doc_id, page_number). No human (and no
# generative model) authored any question text.
#
# Unlike the base module, this one can ask several questions about the same
# passage (top_k_keyphrases), because the audit's worklist targets a small,
# named set of pages (scenarios.py) and needs enough independent probes of
# each one for a page-level content fix to move the measured rate instead of
# disappearing into rounding on a single frozen question.
from __future__ import annotations

import random
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assistant.ingest import Passage  # noqa: E402
from assistant.retrieval import BM25Index  # noqa: E402

QUESTION_TEMPLATES = (
    "What does {title} say about {phrase}?",
    "According to {title}, what is the current status of {phrase}?",
    "How does {title} describe {phrase}?",
    "What number does {title} give for {phrase}?",
)

_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-]*")


@dataclass(frozen=True)
class CommsQAItem:
    question: str
    expected_doc_id: str
    expected_page_number: int
    key_phrase: str


def top_k_keyphrases(text: str, idf: dict[str, float], k: int, window: tuple[int, int] = (2, 3)) -> list[str]:
    """Non-overlapping top-k keyphrase windows by corpus-wide idf, a direct
    extension of assistant.keyphrase.extract_keyphrase's single best-window
    search: scores every window, takes the best, blocks out its word range,
    and repeats, so a long passage yields several independent, non-redundant
    questions instead of asking about the same phrase k times."""
    words = _WORD_RE.findall(text)
    if not words:
        return []
    blocked = [False] * len(words)
    phrases: list[str] = []
    for _ in range(k):
        best_span: tuple[int, int] | None = None
        best_score = -1.0
        for size in window:
            for start in range(0, max(1, len(words) - size + 1)):
                if any(blocked[start : start + size]):
                    continue
                span = words[start : start + size]
                if len(span) < size:
                    continue
                score = sum(idf.get(w.lower(), 0.0) for w in span)
                if score > best_score:
                    best_score = score
                    best_span = (start, start + size)
        if best_span is None or best_score <= 0:
            break
        start, end = best_span
        phrases.append(" ".join(words[start:end]))
        for i in range(start, end):
            blocked[i] = True
    return phrases


def build_items_for_passage(passage: Passage, idf: dict[str, float], rng: random.Random, n: int = 1) -> list[CommsQAItem]:
    phrases = top_k_keyphrases(passage.text, idf, n)
    items = []
    for phrase in phrases:
        template = rng.choice(QUESTION_TEMPLATES)
        question = template.format(title=passage.title, phrase=phrase)
        items.append(
            CommsQAItem(question=question, expected_doc_id=passage.doc_id, expected_page_number=passage.page_number, key_phrase=phrase)
        )
    return items


def build_item(passage: Passage, idf: dict[str, float], rng: random.Random) -> CommsQAItem:
    return build_items_for_passage(passage, idf, rng, n=1)[0]


def generate_candidates(passages: list[Passage], index: BM25Index, *, seed: int) -> list[CommsQAItem]:
    """One question per passage, in a fixed shuffled order; the frozen 300-question
    set (scripts/run_before_after_audit.py) is a deterministic slice of this list."""
    rng = random.Random(seed)
    pool = list(passages)
    rng.shuffle(pool)
    out = []
    for i, p in enumerate(pool):
        items = build_items_for_passage(p, index.idf, random.Random(seed * 1000 + i), n=1)
        out.extend(items)
    return out


def generate_deep_probe(passage: Passage, index: BM25Index, *, seed: int, n: int) -> list[CommsQAItem]:
    """n independent questions about the same passage, used only for the 9
    pages the audit worklist targets."""
    return build_items_for_passage(passage, index.idf, random.Random(seed), n=n)


def item_to_dict(item: CommsQAItem) -> dict:
    return asdict(item)
