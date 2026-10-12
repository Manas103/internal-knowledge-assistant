# 4 seeded regressions run through the exact same assistant.eval_gate.measure_accuracy the
# real merge gate uses, each proving the gate would have failed: two break the BM25 ranking
# formula itself (k1 zeroed, idf inverted to favor common terms), one breaks citation
# indexing (every page off by one), one breaks result selection (citing the runner-up
# instead of the top-1 hit). All 4 are measured against the real frozen eval set, not a
# toy fixture, since the claim is about this project's own gate on its own corpus.
from __future__ import annotations

import json
from dataclasses import replace

import pytest

from assistant import retrieval as retrieval_module
from assistant.eval_gate import EVAL_SET_PATH, PASS_THRESHOLD, cite_runner_up, load_eval_set, measure_accuracy
from assistant.ingest import load_corpus
from assistant.retrieval import BM25Index

pytestmark = pytest.mark.skipif(
    not EVAL_SET_PATH.exists(), reason="eval/eval_set.json missing; run scripts/freeze_eval_set.py first"
)


@pytest.fixture(scope="module")
def corpus():
    return load_corpus()


@pytest.fixture(scope="module")
def eval_items():
    return load_eval_set()


def test_baseline_gate_passes(corpus, eval_items):
    index = BM25Index(corpus)
    accuracy = measure_accuracy(index, eval_items)
    assert accuracy >= PASS_THRESHOLD


def test_regression_k1_zeroed_caught(corpus, eval_items):
    original_k1 = BM25Index.K1
    BM25Index.K1 = 0.0
    try:
        index = BM25Index(corpus)
        accuracy = measure_accuracy(index, eval_items)
    finally:
        BM25Index.K1 = original_k1
    assert accuracy < PASS_THRESHOLD


def test_regression_idf_inverted_caught(corpus, eval_items):
    index = BM25Index(corpus)
    doc_freq: dict[str, int] = {}
    for tf in index._term_freqs:
        for term in tf:
            doc_freq[term] = doc_freq.get(term, 0) + 1
    index._idf = dict(doc_freq)  # regression: common terms now score highest, not rarest
    accuracy = measure_accuracy(index, eval_items)
    assert accuracy < PASS_THRESHOLD


def test_regression_page_numbers_off_by_one_caught(corpus, eval_items):
    shifted = [replace(p, page_number=p.page_number - 1) for p in corpus]
    index = BM25Index(shifted)
    accuracy = measure_accuracy(index, eval_items)
    assert accuracy < PASS_THRESHOLD


def test_regression_cites_runner_up_caught(corpus, eval_items):
    index = BM25Index(corpus)
    accuracy = measure_accuracy(index, eval_items, answer_fn=cite_runner_up)
    assert accuracy < PASS_THRESHOLD


def test_four_of_four_regressions_caught(corpus, eval_items):
    """The headline claim as one assertion: every one of the 4 seeded regressions above
    independently drops accuracy below PASS_THRESHOLD, i.e. the merge gate would have
    failed the build on each of them."""
    index = BM25Index(corpus)
    caught = 0

    original_k1 = BM25Index.K1
    BM25Index.K1 = 0.0
    try:
        if measure_accuracy(BM25Index(corpus), eval_items) < PASS_THRESHOLD:
            caught += 1
    finally:
        BM25Index.K1 = original_k1

    doc_freq: dict[str, int] = {}
    for tf in index._term_freqs:
        for term in tf:
            doc_freq[term] = doc_freq.get(term, 0) + 1
    inverted_index = BM25Index(corpus)
    inverted_index._idf = dict(doc_freq)
    if measure_accuracy(inverted_index, eval_items) < PASS_THRESHOLD:
        caught += 1

    shifted = [replace(p, page_number=p.page_number - 1) for p in corpus]
    if measure_accuracy(BM25Index(shifted), eval_items) < PASS_THRESHOLD:
        caught += 1

    if measure_accuracy(index, eval_items, answer_fn=cite_runner_up) < PASS_THRESHOLD:
        caught += 1

    assert caught == 4
