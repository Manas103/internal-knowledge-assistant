# Generates evaluation and session questions from the real corpus, not from any user. Each
# question is a template filled with a real document title and a real short phrase
# (assistant/keyphrase.py) quoted verbatim from one real passage; the ground truth
# citation is exactly that passage's (doc_id, page_number), so grading is always exact,
# not another model's judgment call. This is a synthetic-question-from-real-document
# technique (the RAG-evaluation literature calls this "synthetic QA generation"), not a
# claim that these read like a real user's own phrasing; the resume's "simulated sessions"
# wording is about exactly this generation step.
from __future__ import annotations

import random
from dataclasses import dataclass

from .ingest import Passage
from .keyphrase import extract_keyphrase
from .retrieval import BM25Index

QUESTION_TEMPLATES = (
    "What does {title} say about {phrase}?",
    "According to {title}, what is the role of {phrase}?",
    "How does {title} describe {phrase}?",
)


@dataclass(frozen=True)
class QAItem:
    question: str
    expected_doc_id: str
    expected_page_number: int
    key_phrase: str


def _build_item(passage: Passage, idf: dict[str, float], rng: random.Random) -> QAItem:
    phrase = extract_keyphrase(passage.text, idf)
    template = rng.choice(QUESTION_TEMPLATES)
    question = template.format(title=passage.title, phrase=phrase)
    return QAItem(question=question, expected_doc_id=passage.doc_id, expected_page_number=passage.page_number, key_phrase=phrase)


def generate_eval_set(passages: list[Passage], index: BM25Index, *, n: int, seed: int) -> list[QAItem]:
    """Samples n distinct passages without replacement (one question per passage) when the
    corpus has at least n passages; this is the frozen set a merge gate checks against, so
    it is built once and then written to disk, never regenerated silently."""
    rng = random.Random(seed)
    pool = list(passages)
    rng.shuffle(pool)
    chosen = pool[:n] if len(pool) >= n else [pool[i % len(pool)] for i in range(n)]
    return [_build_item(p, index.idf, random.Random(seed * 1000 + i)) for i, p in enumerate(chosen)]


def generate_session_questions(passages: list[Passage], index: BM25Index, *, n: int, seed: int) -> list[QAItem]:
    """Samples n passages with replacement, standing in for 1,000 simulated user sessions
    each asking one grounded question; clearly simulated, not real colleague traffic."""
    rng = random.Random(seed)
    return [_build_item(rng.choice(passages), index.idf, random.Random(seed * 1000 + i)) for i in range(n)]
