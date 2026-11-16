# The frozen 300-question gate measured through the exact caiq.eval_gate.measure_citation_accuracy
# function scripts/run_caiq_eval_gate.py runs, plus 2 seeded regressions proving the gate would
# have failed the build on each, mirroring tests/test_eval_gate_regressions.py's contract above.
# Skips cleanly if the real corpus or the frozen eval set has not been built yet.
from __future__ import annotations

import pytest

from caiq.corpus import corpus_available, load_controls
from caiq.eval_gate import (
    FROZEN_EVAL_SET_PATH,
    PASS_THRESHOLD,
    cite_wrong_control,
    load_frozen_eval_set,
    measure_citation_accuracy,
    never_withhold,
)
from caiq.evidence_library import load_evidence

pytestmark = pytest.mark.skipif(
    not (corpus_available() and FROZEN_EVAL_SET_PATH.exists()),
    reason="caiq/data/*.json or caiq/frozen_eval_set.json missing; run scripts/fetch_caiq_corpus.py "
    "and scripts/freeze_caiq_eval_set.py first",
)


@pytest.fixture(scope="module")
def controls():
    return load_controls()


@pytest.fixture(scope="module")
def evidence():
    return load_evidence()


@pytest.fixture(scope="module")
def eval_items():
    return load_frozen_eval_set()


def test_baseline_gate_passes(controls, evidence, eval_items):
    accuracy = measure_citation_accuracy(eval_items, controls, evidence)
    assert accuracy >= PASS_THRESHOLD


def test_eval_set_is_exactly_300_items(eval_items):
    assert len(eval_items) == 300


def test_regression_citing_the_wrong_control_caught(controls, evidence, eval_items):
    accuracy = measure_citation_accuracy(eval_items, controls, evidence, draft_fn=cite_wrong_control)
    assert accuracy < PASS_THRESHOLD


def test_regression_skipping_the_withhold_check_caught(controls, evidence, eval_items):
    accuracy = measure_citation_accuracy(eval_items, controls, evidence, draft_fn=never_withhold)
    assert accuracy < PASS_THRESHOLD


def test_two_of_two_regressions_caught(controls, evidence, eval_items):
    caught = 0
    if measure_citation_accuracy(eval_items, controls, evidence, draft_fn=cite_wrong_control) < PASS_THRESHOLD:
        caught += 1
    if measure_citation_accuracy(eval_items, controls, evidence, draft_fn=never_withhold) < PASS_THRESHOLD:
        caught += 1
    assert caught == 2
