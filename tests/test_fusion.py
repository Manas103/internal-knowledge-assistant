from assistant.fusion import fuse


def test_top_bm25_and_top_dense_agreement_wins():
    bm25 = [("docA", 1), ("docB", 2), ("docC", 3)]
    dense = [("docA", 1), ("docC", 3), ("docB", 2)]
    fused = fuse(bm25, dense)
    assert fused[0].doc_id == "docA" and fused[0].page_number == 1
    assert fused[0].bm25_rank == 1 and fused[0].dense_rank == 1


def test_result_only_in_one_list_still_scored():
    bm25 = [("docA", 1)]
    dense = [("docB", 2)]
    fused = fuse(bm25, dense)
    keys = {(r.doc_id, r.page_number) for r in fused}
    assert keys == {("docA", 1), ("docB", 2)}
    by_key = {(r.doc_id, r.page_number): r for r in fused}
    assert by_key[("docA", 1)].dense_rank is None
    assert by_key[("docB", 2)].bm25_rank is None


def test_a_result_ranked_second_in_both_lists_beats_one_ranked_first_in_only_one():
    bm25 = [("docX", 1), ("docY", 2)]
    dense = [("docZ", 3), ("docY", 2)]
    fused = fuse(bm25, dense)
    assert fused[0].doc_id == "docY"


def test_empty_inputs_give_empty_output():
    assert fuse([], []) == []
