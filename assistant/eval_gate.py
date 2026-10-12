# The merge-gate logic itself, imported by both scripts/run_eval_gate.py (the real gate) and
# tests/test_eval_gate_regressions.py (which calls the exact same measure_accuracy function
# against 4 seeded regressions to prove the gate would actually have failed on each one, not
# a separate copy of the metric that could silently drift from what the gate runs).
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from .answer import Draft, answer_question
from .retrieval import BM25Index, ScoredPassage

ROOT = Path(__file__).resolve().parents[1]
EVAL_SET_PATH = ROOT / "eval" / "eval_set.json"
PASS_THRESHOLD = 0.70  # baseline measured 0.7433 on this corpus; see docs/eval_gate_output.txt


def load_eval_set(path: Path = EVAL_SET_PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def measure_accuracy(index: BM25Index, items: list[dict], answer_fn: Callable[[str, BM25Index], Draft] = answer_question) -> float:
    if not items:
        return 0.0
    correct = sum(
        1
        for it in items
        if (lambda d: d.cited_doc_id == it["expected_doc_id"] and d.cited_page_number == it["expected_page_number"])(
            answer_fn(it["question"], index)
        )
    )
    return correct / len(items)


def cite_runner_up(question: str, index: BM25Index, *, top_k: int = 3) -> Draft:
    """A seeded regression: cites the second-best result instead of the top-1, the shape of
    an off-by-one bug in result selection rather than in the ranking formula itself."""
    results: list[ScoredPassage] = index.search(question, top_k=top_k)
    pick = results[1] if len(results) > 1 else results[0]
    return Draft(answer_text="", cited_doc_id=pick.passage.doc_id, cited_page_number=pick.passage.page_number, confidence=0.0)
