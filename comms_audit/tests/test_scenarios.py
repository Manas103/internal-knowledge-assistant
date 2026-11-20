from __future__ import annotations

import random

from assistant.answer import answer_question
from assistant.ingest import Passage
from assistant.retrieval import BM25Index
from comms_audit import scenarios


def test_inject_stale_numbers_replaces_distinct_values_and_differs_from_original():
    text = "This limit is 100 requests per minute, with a 5 second timeout and a 25 MB cap."
    staled, fixes = scenarios.inject_stale_numbers(text, random.Random(1), max_fixes=3)
    assert staled != text
    assert len(fixes) == 3
    for f in fixes:
        assert f.old_value != f.new_value
        assert f.old_value in text


def test_inject_stale_numbers_handles_text_with_no_numbers():
    text = "This page has no digits anywhere in it at all."
    staled, fixes = scenarios.inject_stale_numbers(text, random.Random(1))
    assert staled == text
    assert fixes == []


def test_add_heading_puts_phrase_at_the_very_start():
    text = "The original first sentence of the page."
    headed = scenarios.add_heading(text, "edge caching", title="Example Docs")
    assert headed.startswith("Edge caching.")
    assert text in headed


def test_discover_retrieval_misses_only_returns_genuine_mismatches():
    passages = [
        Passage(doc_id="docs-a", title="A", page_number=1, text="Alpha beta gamma delta epsilon zeta eta theta.", source_format="html"),
        Passage(doc_id="docs-b", title="B", page_number=1, text="Iota kappa lambda mu nu xi omicron pi.", source_format="html"),
    ]
    index = BM25Index(passages)
    candidates = [
        {"question": "What does A say about alpha beta?", "expected_doc_id": "docs-a", "expected_page_number": 1, "key_phrase": "alpha beta"},
        {"question": "What does B say about iota kappa?", "expected_doc_id": "docs-b", "expected_page_number": 1, "key_phrase": "iota kappa"},
    ]
    found = scenarios.discover_retrieval_misses(candidates, passages, index, exclude_page_ids=set(), n_needed=5)
    # Both of these questions actually retrieve their own expected page correctly
    # (disjoint vocabularies), so a correct implementation finds zero misses.
    for item in candidates:
        draft = answer_question(item["question"], index)
        assert draft.cited_doc_id == item["expected_doc_id"]
    assert found == []
