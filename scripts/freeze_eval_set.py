#!/usr/bin/env python
# Builds eval/eval_set.json once from the real corpus and freezes it there. This script is
# run exactly once per intentional change to the eval set (never automatically): the
# frozen file, not a live regeneration, is what run_eval_gate.py checks the merge gate
# against, which is the point of "frozen" in the resume claim. Each entry stores only a
# question and a short (2-3 word) quoted phrase, never a full passage, since the
# CXL/PCIe source PDFs are copyrighted and this repo does not redistribute their text.
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from assistant.ingest import load_corpus
from assistant.qagen import generate_eval_set
from assistant.retrieval import BM25Index

ROOT = Path(__file__).resolve().parents[1]
EVAL_SET_PATH = ROOT / "eval" / "eval_set.json"
N_QUESTIONS = 300
SEED = 20260801


def main() -> None:
    passages = load_corpus()
    index = BM25Index(passages)
    items = generate_eval_set(passages, index, n=N_QUESTIONS, seed=SEED)
    EVAL_SET_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVAL_SET_PATH.write_text(json.dumps([asdict(i) for i in items], indent=2), encoding="utf-8")
    print(f"wrote {len(items)} questions to {EVAL_SET_PATH}")


if __name__ == "__main__":
    main()
