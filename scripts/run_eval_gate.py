#!/usr/bin/env python
# The frozen 300-question eval set (eval/eval_set.json, built once by
# scripts/freeze_eval_set.py and never regenerated silently) run as a merge gate: measures
# citation accuracy against the real corpus and exits non-zero if it drops below
# PASS_THRESHOLD. tests/test_eval_gate_regressions.py calls this exact measure_accuracy
# function against 4 seeded regressions to prove the gate would actually have failed.
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from assistant.eval_gate import EVAL_SET_PATH, PASS_THRESHOLD, load_eval_set, measure_accuracy
from assistant.ingest import load_corpus
from assistant.retrieval import BM25Index


def main() -> int:
    if not EVAL_SET_PATH.exists():
        print(json.dumps({"status": "skipped", "reason": f"{EVAL_SET_PATH} missing; run scripts/freeze_eval_set.py first"}))
        return 0
    items = load_eval_set()
    index = BM25Index(load_corpus())
    accuracy = measure_accuracy(index, items)
    passed = accuracy >= PASS_THRESHOLD
    report = {
        "n_questions": len(items),
        "citation_accuracy": round(accuracy, 4),
        "pass_threshold": PASS_THRESHOLD,
        "gate_passed": passed,
    }
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
