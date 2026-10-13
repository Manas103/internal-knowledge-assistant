# The hybrid answer path: try the structured catalog first (a question that
# matches one of its two templates is answered from a row, full stop), else
# fuse BM25 and pgvector dense retrieval by reciprocal rank and answer
# extractively from the fused top passage, exactly like assistant.answer's
# pure-BM25 path but over the fused ranking instead of BM25 alone.
from __future__ import annotations

from dataclasses import dataclass

from .answer import SNIPPET_CHARS, Draft
from .fusion import fuse
from .ingest import Passage
from .retrieval import BM25Index
from .structured_store import CatalogRow, answer_structured_question
from .vector_store import dense_search


def _passage_lookup(passages: list[Passage]) -> dict[tuple[str, int], Passage]:
    return {(p.doc_id, p.page_number): p for p in passages}


BM25_WEIGHT = 10.0
DENSE_WEIGHT = 1.0


def answer_question_hybrid(
    question: str,
    passages: list[Passage],
    index: BM25Index,
    catalog: list[CatalogRow],
    conn,
    *,
    top_k: int = 10,
    bm25_weight: float = BM25_WEIGHT,
    dense_weight: float = DENSE_WEIGHT,
) -> Draft:
    structured = answer_structured_question(question, catalog)
    if structured is not None:
        return structured

    bm25_results = index.search(question, top_k=top_k)
    bm25_ranked = [(r.passage.doc_id, r.passage.page_number) for r in bm25_results]

    dense_rows = dense_search(conn, question, index.idf, top_k=top_k)
    dense_ranked = [(r["doc_id"], r["page_number"]) for r in dense_rows]

    fused = fuse(bm25_ranked, dense_ranked, bm25_weight=bm25_weight, dense_weight=dense_weight)
    if not fused:
        return Draft("No supporting passage was found for this question.", "", -1, 0.0)

    lookup = _passage_lookup(passages)
    top = fused[0]
    passage = lookup.get((top.doc_id, top.page_number))
    if passage is None:
        return Draft("No supporting passage was found for this question.", "", -1, 0.0)

    confidence = top.score - (fused[1].score if len(fused) > 1 else 0.0)
    text = passage.text
    snippet = text if len(text) <= SNIPPET_CHARS else text[:SNIPPET_CHARS].rsplit(" ", 1)[0] + "..."
    answer_text = f"{snippet} (source: {passage.title}, page {passage.page_number})"
    return Draft(
        answer_text=answer_text, cited_doc_id=passage.doc_id, cited_page_number=passage.page_number,
        confidence=confidence, source_kind="passage",
    )


def measure_hybrid_accuracy(
    passages: list[Passage], index: BM25Index, catalog: list[CatalogRow], conn, items: list[dict],
) -> float:
    """The hybrid-path counterpart of assistant.eval_gate.measure_accuracy,
    kept separate rather than overloading that function's signature (which
    tests/test_eval_gate_regressions.py and scripts/run_eval_gate.py both
    call against the pure-BM25 path and must keep working unchanged)."""
    if not items:
        return 0.0
    correct = 0
    for it in items:
        draft = answer_question_hybrid(it["question"], passages, index, catalog, conn)
        if draft.cited_doc_id == it["expected_doc_id"] and draft.cited_page_number == it["expected_page_number"]:
            correct += 1
    return correct / len(items)
