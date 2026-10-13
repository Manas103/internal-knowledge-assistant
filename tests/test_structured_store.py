from assistant.structured_store import (
    answer_structured_question,
    generate_structured_questions,
    load_catalog,
)


def test_load_catalog_has_ten_rows_matching_the_manifest():
    catalog = load_catalog()
    assert len(catalog) == 10
    assert {row.doc_id for row in catalog} == {
        "cxl11_spec", "cxl20_errata", "astera_aries_brief", "arxiv_cxl_survey",
        "arxiv_disaggregated_memory_survey", "arxiv_memory_disaggregation",
        "astera_scorpio_brief", "astera_leo_brief", "wikipedia_pci_express", "wikipedia_cxl",
    }


def test_page_count_question_answered_from_the_row():
    catalog = load_catalog()
    row = next(r for r in catalog if r.doc_id == "cxl11_spec")
    question = f"How many pages does {row.title} have?"
    draft = answer_structured_question(question, catalog)
    assert draft is not None
    assert draft.source_kind == "row"
    assert draft.cited_doc_id == "cxl11_spec"
    assert "250" in draft.answer_text


def test_wikipedia_rows_have_no_page_count_question():
    """measured_pages is null for both Wikipedia rows in corpus_manifest.json;
    this must not silently answer "None pages" for them."""
    catalog = load_catalog()
    wiki = next(r for r in catalog if r.doc_id == "wikipedia_cxl")
    question = f"How many pages does {wiki.title} have?"
    assert answer_structured_question(question, catalog) is None


def test_format_question_answered_from_the_row():
    catalog = load_catalog()
    row = next(r for r in catalog if r.doc_id == "wikipedia_cxl")
    question = f"What format is {row.title} distributed in?"
    draft = answer_structured_question(question, catalog)
    assert draft is not None
    assert draft.cited_doc_id == "wikipedia_cxl"
    assert "wikitext" in draft.answer_text


def test_unmatched_question_returns_none():
    catalog = load_catalog()
    assert answer_structured_question("What is the airspeed velocity of an unladen swallow?", catalog) is None


def test_generate_structured_questions_covers_every_row_and_is_deterministic():
    catalog = load_catalog()
    items_a = generate_structured_questions(catalog, seed=1)
    items_b = generate_structured_questions(catalog, seed=1)
    assert items_a == items_b
    doc_ids_with_page_questions = {it.expected_doc_id for it in items_a if it.field == "measured_pages"}
    assert doc_ids_with_page_questions == {r.doc_id for r in catalog if r.measured_pages is not None}
    doc_ids_with_format_questions = {it.expected_doc_id for it in items_a if it.field == "source_format"}
    assert doc_ids_with_format_questions == {r.doc_id for r in catalog}
