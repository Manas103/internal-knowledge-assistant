# The merge-gate logic, imported by both scripts/run_caiq_eval_gate.py (the real gate) and
# tests/test_caiq_eval_gate_regressions.py, exactly the shared-function contract
# assistant/eval_gate.py already uses for the sibling BM25 gate above (see that module's
# own comment for why one function, not two copies of the metric, matters).
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from .answer_library import Draft, draft_answer
from .corpus import Control
from .evidence_library import Evidence

ROOT = Path(__file__).resolve().parent
FROZEN_EVAL_SET_PATH = ROOT / "frozen_eval_set.json"
PASS_THRESHOLD = 0.70  # the resume's "70% citation floor"; see docs/caiq_eval_gate_output.txt for the measured value


def load_frozen_eval_set(path: Path = FROZEN_EVAL_SET_PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def measure_citation_accuracy(
    items: list[dict],
    controls: dict[str, Control],
    evidence: dict[str, Evidence],
    draft_fn: Callable[[str, dict[str, Control], dict[str, Evidence]], Draft] = draft_answer,
) -> float:
    if not items:
        return 0.0
    correct = 0
    for item in items:
        drafted = draft_fn(item["question_id"], controls, evidence)
        expected_control_id = item["expected_control_id"]
        if expected_control_id is None:
            if drafted.withheld:
                correct += 1
        else:
            if not drafted.withheld and drafted.cited_control_id == expected_control_id:
                correct += 1
    return correct / len(items)


def cite_wrong_control(question_id: str, controls: dict[str, Control], evidence: dict[str, Evidence]) -> Draft:
    """A seeded regression: always answers from an unrelated control objective (the
    alphabetically-first one with evidence) instead of the question's own control,
    the shape of a routing bug that returns a real, resolving citation that is simply
    the wrong one."""
    covered = sorted(cid for cid in controls if cid in evidence)
    wrong_id = covered[0]
    control = controls[wrong_id]
    artifact = evidence[wrong_id]
    return Draft(
        withheld=False,
        reason="",
        answer_text=control.control_specification,
        cited_control_id=wrong_id,
        cited_artifact_name=artifact.artifact_name,
    )


def never_withhold(question_id: str, controls: dict[str, Control], evidence: dict[str, Evidence]) -> Draft:
    """A seeded regression: the withholding check removed entirely, the shape of a gate
    that was wired up but never actually called. It always answers, citing the question's
    own control root, even when that control has no entry in the corpus and even when it
    has no evidence artifact, exactly the failure mode the withhold check exists to prevent."""
    from .corpus import control_root

    root = control_root(question_id)
    control = controls.get(root)
    text = control.control_specification if control is not None else "(no matching control objective in corpus)"
    return Draft(
        withheld=False,
        reason="",
        answer_text=text,
        cited_control_id=root,
        cited_artifact_name="(fabricated: no evidence actually attached)",
    )
