# Builds caiq/frozen_eval_set.json once and commits it, exactly like scripts/freeze_eval_set.py
# above for the BM25 gate. The real public CAIQ v4.0.3 questionnaire has only 261 questions;
# to reach the resume's frozen 300-question gate size this cycles back through the same
# 261-question pool for the remaining 39 slots, the identical undersized-corpus convention
# assistant/qagen.py's generate_eval_set already uses ("chosen = pool[:n] if len(pool) >= n
# else [pool[i % len(pool)] for i in range(n)]"), not a new design invented for this module.
# Run deliberately, never silently.
from __future__ import annotations

import json
from pathlib import Path

from caiq.corpus import control_root, load_controls, load_questions
from caiq.evidence_library import load_evidence

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "caiq" / "frozen_eval_set.json"
N = 300


def build() -> list[dict]:
    questions = load_questions()
    controls = load_controls()
    evidence = load_evidence()

    pool = questions if len(questions) >= N else [questions[i % len(questions)] for i in range(N)]
    items = []
    for q in pool[:N]:
        root = control_root(q.question_id)
        if root not in controls or root not in evidence:
            expected_control_id = None
        else:
            expected_control_id = root
        items.append({"question_id": q.question_id, "expected_control_id": expected_control_id})
    return items


if __name__ == "__main__":
    items = build()
    OUT_PATH.write_text(json.dumps(items, indent=2), encoding="utf-8")
    n_withheld = sum(1 for it in items if it["expected_control_id"] is None)
    print(f"{len(items)} frozen eval items written to {OUT_PATH}; {n_withheld} expected withheld")
