from __future__ import annotations

import random
import re

from assistant.ingest import Passage
from assistant.retrieval import BM25Index
from comms_audit import qagen

PASSAGES = [
    Passage(
        doc_id="docs-example",
        title="Example Docs",
        page_number=1,
        text=(
            "Vectorize indexes embeddings for similarity search. Workers AI runs inference models. "
            "R2 provides object storage. D1 is a serverless SQL database. Pages hosts static sites. "
            "Durable Objects coordinate stateful actors across the edge network globally."
        ),
        source_format="html",
    )
]


def test_top_k_keyphrases_are_non_overlapping_and_distinct():
    idf = BM25Index(PASSAGES).idf
    phrases = qagen.top_k_keyphrases(PASSAGES[0].text, idf, k=6)
    assert len(phrases) == len(set(phrases))
    words_seen: set[str] = set()
    for phrase in phrases:
        for w in phrase.lower().split():
            assert w not in words_seen, f"word '{w}' reused across two keyphrases: {phrases}"
            words_seen.add(w)


def test_top_k_keyphrases_stops_when_passage_runs_out_of_signal():
    idf = BM25Index(PASSAGES).idf
    phrases = qagen.top_k_keyphrases("one two", idf, k=10)
    assert len(phrases) <= 1


def test_build_items_for_passage_grounds_every_question_in_the_same_passage():
    index = BM25Index(PASSAGES)
    items = qagen.build_items_for_passage(PASSAGES[0], index.idf, random.Random(1), n=5)
    assert len(items) >= 1
    text_words = set(re.findall(r"[a-z0-9]+", PASSAGES[0].text.lower()))
    for item in items:
        assert item.expected_doc_id == "docs-example"
        assert item.expected_page_number == 1
        # the phrase's words are drawn, in order, from the passage; punctuation
        # between them (e.g. a sentence boundary) means it is not always a
        # literal substring of the raw text, so check word membership instead.
        for w in item.key_phrase.lower().split():
            assert w in text_words


def test_generate_candidates_covers_every_passage_exactly_once():
    passages = PASSAGES * 3
    passages = [
        Passage(doc_id=f"docs-{i}", title=f"Doc {i}", page_number=1, text=p.text, source_format="html")
        for i, p in enumerate(passages)
    ]
    index = BM25Index(passages)
    candidates = qagen.generate_candidates(passages, index, seed=42)
    assert len(candidates) == len(passages)
    assert {c.expected_doc_id for c in candidates} == {p.doc_id for p in passages}
