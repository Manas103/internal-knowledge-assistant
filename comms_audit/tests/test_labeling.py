from __future__ import annotations

from assistant.ingest import Passage
from assistant.retrieval import BM25Index
from comms_audit import labeling

PASSAGES = [
    Passage(doc_id="docs-vectorize", title="Vectorize", page_number=1, text="Vectorize stores vector embeddings for similarity search at the edge.", source_format="html"),
    Passage(doc_id="docs-r2", title="R2", page_number=1, text="R2 is S3-compatible object storage with no egress fees.", source_format="html"),
    Passage(doc_id="docs-workers-ai", title="Workers AI", page_number=1, text="Workers AI runs machine learning inference models on the Cloudflare network.", source_format="html"),
]


def make_index(passages=PASSAGES) -> BM25Index:
    return BM25Index(passages)


def test_supported_when_citation_matches_and_not_stale():
    index = make_index()
    item = {"question": "What does Vectorize say about similarity search?", "expected_doc_id": "docs-vectorize", "expected_page_number": 1}
    result = labeling.label_answer(item, index, excluded_page_ids=frozenset(), stale_page_ids=frozenset())
    assert result.label == "supported"
    assert result.failure_cause is None


def test_stale_when_citation_matches_but_page_is_marked_stale():
    index = make_index()
    item = {"question": "What does Vectorize say about similarity search?", "expected_doc_id": "docs-vectorize", "expected_page_number": 1}
    result = labeling.label_answer(item, index, excluded_page_ids=frozenset(), stale_page_ids=frozenset({"docs-vectorize"}))
    assert result.label == "stale"
    assert result.failure_cause == "stale_number"


def test_unsupported_missing_page_when_expected_doc_excluded():
    # The excluded page's own passage is removed from the index entirely, so the
    # retriever is forced onto a different document; the cause must read missing_page.
    without_vectorize = [p for p in PASSAGES if p.doc_id != "docs-vectorize"]
    index = make_index(without_vectorize)
    item = {"question": "What does Vectorize say about similarity search?", "expected_doc_id": "docs-vectorize", "expected_page_number": 1}
    result = labeling.label_answer(item, index, excluded_page_ids=frozenset({"docs-vectorize"}), stale_page_ids=frozenset())
    assert result.label == "unsupported"
    assert result.failure_cause == "missing_page"


def test_unsupported_retrieval_miss_when_page_present_but_not_top_ranked():
    index = make_index()
    # A question engineered to actually match R2's text better than Vectorize's,
    # while still claiming Vectorize as the expected citation: a genuine ranking miss.
    item = {"question": "What does R2 say about object storage?", "expected_doc_id": "docs-vectorize", "expected_page_number": 1}
    result = labeling.label_answer(item, index, excluded_page_ids=frozenset(), stale_page_ids=frozenset())
    assert result.label == "unsupported"
    assert result.failure_cause == "retrieval_miss"


def test_citation_supported_rate_and_failure_breakdown():
    labels = [
        labeling.LabeledAnswer("q1", "a", 1, "a", 1, "supported", None),
        labeling.LabeledAnswer("q2", "b", 1, "b", 1, "stale", "stale_number"),
        labeling.LabeledAnswer("q3", "c", 1, "d", 1, "unsupported", "missing_page"),
        labeling.LabeledAnswer("q4", "e", 1, "f", 1, "unsupported", "retrieval_miss"),
    ]
    assert labeling.citation_supported_rate(labels) == 0.25
    assert labeling.failure_breakdown(labels) == {"missing_page": 1, "stale_number": 1, "retrieval_miss": 1}
