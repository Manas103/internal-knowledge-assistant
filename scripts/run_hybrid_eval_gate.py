#!/usr/bin/env python
# The hybrid-path counterpart of run_eval_gate.py: the same frozen 300-question
# eval set, answered through assistant.hybrid_answer (structured catalog first,
# then BM25 fused with pgvector dense retrieval by reciprocal rank) instead of
# pure BM25. Skips cleanly if pgvector is unreachable, matching this
# portfolio's convention; see the README for why the measured number here can
# differ from run_eval_gate.py's and why that is reported honestly either way.
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from assistant.eval_gate import EVAL_SET_PATH, PASS_THRESHOLD, load_eval_set
from assistant.hybrid_answer import measure_hybrid_accuracy
from assistant.ingest import load_corpus
from assistant.retrieval import BM25Index
from assistant.structured_store import load_catalog
from assistant.vector_store import get_connection, init_schema, is_available, reset, upsert_passages


def main() -> int:
    if not EVAL_SET_PATH.exists():
        print(json.dumps({"status": "skipped", "reason": f"{EVAL_SET_PATH} missing; run scripts/freeze_eval_set.py first"}))
        return 0
    if not is_available():
        print(json.dumps({"status": "skipped", "reason": "pgvector Postgres unreachable"}))
        return 0

    items = load_eval_set()
    passages = load_corpus()
    index = BM25Index(passages)
    catalog = load_catalog()

    conn = get_connection()
    try:
        init_schema(conn)
        reset(conn)
        n_embedded = upsert_passages(conn, passages, index.idf)

        accuracy = measure_hybrid_accuracy(passages, index, catalog, conn, items)
        passed = accuracy >= PASS_THRESHOLD
        report = {
            "n_questions": len(items),
            "n_passages_embedded": n_embedded,
            "citation_accuracy": round(accuracy, 4),
            "pass_threshold": PASS_THRESHOLD,
            "gate_passed": passed,
        }
        print(json.dumps(report, indent=2))
        return 0 if passed else 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
