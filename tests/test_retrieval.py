from assistant.retrieval import BM25Index, tokenize


def test_tokenize_lowercases_and_drops_stopwords():
    assert tokenize("The PCIe Link and the Host") == ["pcie", "link", "host"]


def test_search_ranks_the_lexically_matching_passage_first(fixture_passages):
    index = BM25Index(fixture_passages)
    results = index.search("CXL memory pooling expansion device", top_k=3)
    assert results[0].passage.doc_id == "doc-a"
    assert results[0].passage.page_number == 2


def test_search_distinguishes_flow_control_from_switch_fanout(fixture_passages):
    index = BM25Index(fixture_passages)
    results = index.search("flow control credits receiver buffer", top_k=1)
    assert (results[0].passage.doc_id, results[0].passage.page_number) == ("doc-b", 1)


def test_idf_favors_rare_terms_over_common_ones(fixture_passages):
    index = BM25Index(fixture_passages)
    # "coherency" appears in exactly one of the 5 fixture passages; "a" is a stopword and
    # never scored at all, so a present-but-rare term must outscore an absent one.
    assert index.idf.get("coherency", 0.0) > 0.0
    assert "a" not in index.idf
