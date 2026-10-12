from assistant.qagen import generate_eval_set, generate_session_questions
from assistant.retrieval import BM25Index


def test_eval_set_ground_truth_citation_is_a_real_passage(fixture_passages):
    index = BM25Index(fixture_passages)
    items = generate_eval_set(fixture_passages, index, n=5, seed=1)
    assert len(items) == 5
    passage_keys = {(p.doc_id, p.page_number) for p in fixture_passages}
    for item in items:
        assert (item.expected_doc_id, item.expected_page_number) in passage_keys
        assert item.key_phrase in item.question


def test_eval_set_samples_without_replacement_when_enough_passages(fixture_passages):
    index = BM25Index(fixture_passages)
    items = generate_eval_set(fixture_passages, index, n=len(fixture_passages), seed=2)
    keys = [(i.expected_doc_id, i.expected_page_number) for i in items]
    assert len(set(keys)) == len(fixture_passages)


def test_session_questions_sample_with_replacement(fixture_passages):
    index = BM25Index(fixture_passages)
    items = generate_session_questions(fixture_passages, index, n=20, seed=3)
    assert len(items) == 20


def test_generation_is_deterministic_for_a_fixed_seed(fixture_passages):
    index = BM25Index(fixture_passages)
    a = generate_session_questions(fixture_passages, index, n=10, seed=42)
    b = generate_session_questions(fixture_passages, index, n=10, seed=42)
    assert [i.question for i in a] == [i.question for i in b]
