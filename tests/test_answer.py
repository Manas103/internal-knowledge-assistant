from assistant.answer import answer_question
from assistant.retrieval import BM25Index


def test_answer_cites_the_top_retrieved_passage(fixture_passages):
    index = BM25Index(fixture_passages)
    draft = answer_question("CXL memory pooling expansion device", index)
    assert draft.cited_doc_id == "doc-a"
    assert draft.cited_page_number == 2
    assert "source: Fixture Spec A, page 2" in draft.answer_text


def test_answer_confidence_is_higher_for_a_specific_than_a_generic_query(fixture_passages):
    index = BM25Index(fixture_passages)
    specific = answer_question("flow control credits receiver buffer drains", index)
    generic = answer_question("the", index)
    assert specific.confidence > generic.confidence


def test_answer_handles_empty_corpus_gracefully():
    index = BM25Index([])
    draft = answer_question("anything", index)
    assert draft.cited_page_number == -1
