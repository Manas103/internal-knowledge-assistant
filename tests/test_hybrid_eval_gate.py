# Locks in the honest finding from scripts/run_hybrid_eval_gate.py: fusing a
# 128-dim feature-hashed dense embedding into BM25 by unweighted reciprocal
# rank measurably hurts citation accuracy on this corpus (49.33%, down from
# BM25-only's 74.33%), because these eval/session questions are built by
# dropping a passage's own highest-idf exact phrase into a template
# (assistant/qagen.py), which is close to unbeatable for exact lexical
# match and offers no edge to a noisy dense proxy. Weighting BM25 10x
# heavier in the RRF formula recovers much of the loss (64.67%) but still
# does not clear the shared 70% PASS_THRESHOLD; see the README's Findings.
# This is exactly why assistant.eval_gate's unweighted, BM25-only gate
# remains this repository's actual merge gate: the hybrid path is a real,
# measured, additional capability, not a drop-in replacement for it.
from __future__ import annotations

import pytest

from assistant.eval_gate import EVAL_SET_PATH, PASS_THRESHOLD, load_eval_set
from assistant.ingest import load_corpus
from assistant.retrieval import BM25Index
from assistant.structured_store import answer_structured_question, generate_structured_questions, load_catalog
from assistant.vector_store import init_schema, reset, upsert_passages

pytestmark = pytest.mark.skipif(
    not EVAL_SET_PATH.exists(), reason="eval/eval_set.json missing; run scripts/freeze_eval_set.py first"
)


@pytest.fixture
def real_corpus_hybrid_setup(pg_conn):
    passages = load_corpus()
    index = BM25Index(passages)
    catalog = load_catalog()
    init_schema(pg_conn)
    reset(pg_conn)
    upsert_passages(pg_conn, passages, index.idf)
    return passages, index, catalog


def test_unweighted_fusion_measurably_hurts_accuracy_on_this_corpus(real_corpus_hybrid_setup, pg_conn):
    passages, index, catalog = real_corpus_hybrid_setup
    items = load_eval_set()

    def accuracy(bm25_weight: float) -> float:
        correct = 0
        for it in items:
            from assistant.hybrid_answer import answer_question_hybrid

            draft = answer_question_hybrid(
                it["question"], passages, index, catalog, pg_conn, bm25_weight=bm25_weight, dense_weight=1.0,
            )
            if draft.cited_doc_id == it["expected_doc_id"] and draft.cited_page_number == it["expected_page_number"]:
                correct += 1
        return correct / len(items)

    unweighted = accuracy(1.0)
    weighted = accuracy(10.0)
    bm25_only = 0.7433  # measured by scripts/run_eval_gate.py, unchanged; see docs/eval_gate_output.txt

    assert unweighted < PASS_THRESHOLD
    assert weighted > unweighted, "weighting BM25 more heavily should recover some of the loss"
    assert weighted < bm25_only, "disclosed: weighting does not fully recover BM25-only's accuracy on this corpus"


def test_structured_eval_is_exhaustively_correct():
    catalog = load_catalog()
    items = generate_structured_questions(catalog, seed=20260801)
    correct = sum(
        1 for it in items
        if (d := answer_structured_question(it.question, catalog)) is not None
        and d.source_kind == "row" and d.cited_doc_id == it.expected_doc_id
    )
    assert correct == len(items)
