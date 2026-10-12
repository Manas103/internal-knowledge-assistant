from assistant.keyphrase import extract_keyphrase
from assistant.retrieval import BM25Index


def test_keyphrase_is_quoted_verbatim_from_the_passage(fixture_passages):
    index = BM25Index(fixture_passages)
    passage = next(p for p in fixture_passages if p.doc_id == "doc-c")
    phrase = extract_keyphrase(passage.text, index.idf)
    assert phrase in passage.text


def test_keyphrase_picks_a_distinctive_term_not_a_stopword_run():
    idf = {"coherency": 3.0, "protocols": 0.1, "keep": 0.0, "a": 0.0}
    phrase = extract_keyphrase("keep a coherency protocols check", idf, window=(1, 1))
    assert phrase == "coherency"
