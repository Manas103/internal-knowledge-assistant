# Unit tests against a small synthetic fixture (3 controls, 2 with evidence), not the real
# CSA corpus, so these run everywhere regardless of whether caiq/data/*.json has been built.
from __future__ import annotations

from caiq.answer_library import draft_answer
from caiq.corpus import Control
from caiq.evidence_library import Evidence

CONTROLS = {
    "AAA-01": Control("AAA-01", "Test Domain", "Test Control One", "Do the first thing, documented and reviewed."),
    "AAA-02": Control("AAA-02", "Test Domain", "Test Control Two", "Do the second thing, with an owner named."),
}
EVIDENCE = {
    "AAA-01": Evidence("AAA-01", "Test Policy v1", "2026-01-01"),
}


def test_answered_when_control_and_evidence_both_exist():
    draft = draft_answer("AAA-01.1", CONTROLS, EVIDENCE)
    assert draft.withheld is False
    assert draft.cited_control_id == "AAA-01"
    assert draft.cited_artifact_name == "Test Policy v1"
    assert "Do the first thing" in draft.answer_text


def test_withheld_when_control_exists_but_no_evidence():
    draft = draft_answer("AAA-02.1", CONTROLS, EVIDENCE)
    assert draft.withheld is True
    assert "no committed evidence" in draft.reason
    assert draft.cited_control_id is None


def test_withheld_when_control_id_does_not_resolve_at_all():
    draft = draft_answer("ZZZ-99.1", CONTROLS, EVIDENCE)
    assert draft.withheld is True
    assert "no control objective" in draft.reason


def test_citation_always_names_a_real_resolving_control_when_answered():
    for question_id in ("AAA-01.1", "AAA-01.2"):
        draft = draft_answer(question_id, CONTROLS, EVIDENCE)
        if not draft.withheld:
            assert draft.cited_control_id in CONTROLS
