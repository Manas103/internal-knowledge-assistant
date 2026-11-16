# Structural checks against the real, rebuilt CAIQ/CCM corpus; skip cleanly if it has not
# been built yet (run scripts/fetch_caiq_corpus.py first), mirroring tests/test_ingest.py's
# own skip-if-missing contract for the PCIe/CXL corpus above.
from __future__ import annotations

import pytest

from caiq.corpus import control_root, corpus_available, load_controls, load_questions

pytestmark = pytest.mark.skipif(not corpus_available(), reason="caiq/data/*.json missing; run scripts/fetch_caiq_corpus.py first")


def test_real_question_count_matches_resume_claim():
    questions = load_questions()
    assert len(questions) == 261


def test_control_root_parses_the_sub_question_suffix_off():
    assert control_root("A&A-01.2") == "A&A-01"
    assert control_root("DSP-14.1") == "DSP-14"


def test_every_question_id_is_unique():
    questions = load_questions()
    ids = [q.question_id for q in questions]
    assert len(ids) == len(set(ids))


def test_controls_cover_17_domains():
    controls = load_controls()
    domains = {c.domain for c in controls.values()}
    assert len(domains) == 17


def test_ivs_domain_questions_have_no_matching_control_in_this_corpus():
    """The disclosed version-drift gap: CAIQ v4.0.3 names IVS-01..IVS-09; the publicly
    downloadable CCM v4.1.1 renamed that domain to I&S-01..I&S-09, so these roots are
    genuinely absent from this corpus, which is exactly why they are always withheld."""
    controls = load_controls()
    assert "IVS-01" not in controls
    assert "I&S-01" in controls
