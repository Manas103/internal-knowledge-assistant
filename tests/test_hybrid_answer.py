from assistant.hybrid_answer import answer_question_hybrid, measure_hybrid_accuracy
from assistant.retrieval import BM25Index
from assistant.structured_store import CatalogRow, load_catalog
from assistant.vector_store import upsert_passages

_FIXTURE_CATALOG = [
    CatalogRow(doc_id="doc-a", title="Fixture Spec A", source_format="pdf", measured_pages=2, license_note="test"),
]


def test_structured_question_short_circuits_before_any_retrieval(pg_conn, fixture_passages):
    """Deliberately does not call upsert_passages first: if this question
    were not answered structurally, dense_search would fail against an
    empty table, proving the structured path really runs first."""
    index = BM25Index(fixture_passages)
    draft = answer_question_hybrid(
        "How many pages does Fixture Spec A have?", fixture_passages, index, _FIXTURE_CATALOG, pg_conn,
    )
    assert draft.source_kind == "row"
    assert draft.cited_doc_id == "doc-a"


def test_passage_question_fuses_bm25_and_dense(pg_conn, fixture_passages):
    index = BM25Index(fixture_passages)
    upsert_passages(pg_conn, fixture_passages, index.idf)
    draft = answer_question_hybrid(
        "What does Fixture Spec C say about cache coherency?", fixture_passages, index, _FIXTURE_CATALOG, pg_conn,
    )
    assert draft.source_kind == "passage"
    assert draft.cited_doc_id == "doc-c"
    assert draft.cited_page_number == 1


def test_measure_hybrid_accuracy_on_exact_grounded_questions(pg_conn, fixture_passages):
    index = BM25Index(fixture_passages)
    upsert_passages(pg_conn, fixture_passages, index.idf)
    items = [
        {"question": "What does Fixture Spec A say about retimer?", "expected_doc_id": "doc-a", "expected_page_number": 1},
        {"question": "What does Fixture Spec B say about flow control credits?", "expected_doc_id": "doc-b", "expected_page_number": 1},
    ]
    accuracy = measure_hybrid_accuracy(fixture_passages, index, _FIXTURE_CATALOG, pg_conn, items)
    assert accuracy == 1.0


def test_real_catalog_loads_for_hybrid_use():
    catalog = load_catalog()
    assert len(catalog) == 10
