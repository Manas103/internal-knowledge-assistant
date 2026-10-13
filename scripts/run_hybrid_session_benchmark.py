#!/usr/bin/env python
# The hybrid-path counterpart of run_session_benchmark.py: the same 1,000
# simulated sessions (assistant.qagen), answered through
# assistant.hybrid_answer instead of pure BM25. CONFIDENCE_THRESHOLD is this
# project's own fused-score margin, re-derived the same way the base
# repo's threshold was (this run's own confidence distribution's 38th
# percentile), not copied from the BM25-only run, since reciprocal-rank
# fusion scores (bounded, small) are not on the same scale as BM25 scores.
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from assistant.hybrid_answer import answer_question_hybrid
from assistant.ingest import load_corpus
from assistant.qagen import generate_session_questions
from assistant.retrieval import BM25Index
from assistant.structured_store import load_catalog
from assistant.vector_store import get_connection, init_schema, is_available, reset, upsert_passages

N_SESSIONS = 1000
SEED = 20260801


def main() -> int:
    if not is_available():
        print(json.dumps({"status": "skipped", "reason": "pgvector Postgres unreachable"}))
        return 0

    passages = load_corpus()
    index = BM25Index(passages)
    catalog = load_catalog()
    questions = generate_session_questions(passages, index, n=N_SESSIONS, seed=SEED)

    conn = get_connection()
    try:
        init_schema(conn)
        reset(conn)
        upsert_passages(conn, passages, index.idf)

        drafts = [answer_question_hybrid(q.question, passages, index, catalog, conn) for q in questions]
    finally:
        conn.close()

    confidences = sorted(d.confidence for d in drafts)
    threshold_index = int(len(confidences) * 0.38)
    confidence_threshold = confidences[threshold_index]

    cited_correctly = 0
    sent_unedited = 0
    cited_correctly_among_unedited = 0
    for q, draft in zip(questions, drafts):
        correct = draft.cited_doc_id == q.expected_doc_id and draft.cited_page_number == q.expected_page_number
        unedited = draft.confidence >= confidence_threshold
        if correct:
            cited_correctly += 1
        if unedited:
            sent_unedited += 1
            if correct:
                cited_correctly_among_unedited += 1

    report = {
        "n_sessions": N_SESSIONS,
        "confidence_threshold": round(confidence_threshold, 6),
        "cited_supporting_passage": cited_correctly,
        "pct_cited_supporting_passage": round(100 * cited_correctly / N_SESSIONS, 2),
        "sent_unedited": sent_unedited,
        "pct_sent_unedited": round(100 * sent_unedited / N_SESSIONS, 2),
        "pct_cited_correctly_among_unedited": round(100 * cited_correctly_among_unedited / sent_unedited, 2) if sent_unedited else None,
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
