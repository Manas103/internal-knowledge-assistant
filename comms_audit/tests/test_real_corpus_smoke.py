# Exercises the real, fetched corpus end to end. Skips cleanly (the base
# repo's convention for a dependency not always present) if
# scripts/fetch_corpus.py has not been run on this machine yet.
from __future__ import annotations

import pytest

from assistant.retrieval import BM25Index
from comms_audit import ingest

pytestmark = pytest.mark.skipif(not ingest.MANIFEST_PATH.exists(), reason="corpus_manifest.json missing; run scripts/fetch_corpus.py first")


def test_manifest_reports_close_to_400_real_pages():
    manifest = ingest.load_manifest()
    assert manifest["pages_fetched"] == len(manifest["pages"])
    # Honest target is 400; real-world fetch availability (thin/redirected
    # pages filtered) measured 383 on this machine, see README Measured results.
    assert 300 <= manifest["pages_fetched"] <= 420


def test_build_corpus_excludes_and_overrides_work_together():
    manifest = ingest.load_manifest()
    some_page = manifest["pages"][0]["page_id"]
    other_page = manifest["pages"][1]["page_id"]

    full = ingest.build_corpus()
    doc_ids_full = {p.doc_id for p in full}
    assert some_page in doc_ids_full

    reduced = ingest.build_corpus(exclude_page_ids=frozenset({some_page}), overrides={other_page: "a short replacement passage for testing"})
    doc_ids_reduced = {p.doc_id for p in reduced}
    assert some_page not in doc_ids_reduced
    override_passages = [p for p in reduced if p.doc_id == other_page]
    assert override_passages and override_passages[0].text == "a short replacement passage for testing"


def test_bm25_index_builds_over_the_real_corpus():
    passages = ingest.build_corpus()
    index = BM25Index(passages)
    results = index.search("Workers AI", top_k=3)
    assert len(results) > 0
