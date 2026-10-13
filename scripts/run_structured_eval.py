#!/usr/bin/env python
# Exercises the other half of "every answer cites the passage or row it
# came from": every structured question assistant.structured_store can
# generate from corpus_manifest.json's 10 rows, answered by
# answer_structured_question and checked against the row it should have
# cited. No Postgres needed; this path never touches retrieval.
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from assistant.structured_store import generate_structured_questions, load_catalog, answer_structured_question

SEED = 20260801


def main() -> int:
    catalog = load_catalog()
    items = generate_structured_questions(catalog, seed=SEED)

    correct = 0
    for it in items:
        draft = answer_structured_question(it.question, catalog)
        if draft is not None and draft.source_kind == "row" and draft.cited_doc_id == it.expected_doc_id:
            correct += 1

    report = {
        "n_questions": len(items),
        "n_catalog_rows": len(catalog),
        "correctly_cited_row": correct,
        "pct_correct": round(100 * correct / len(items), 2) if items else None,
    }
    print(json.dumps(report, indent=2))
    return 0 if correct == len(items) else 1


if __name__ == "__main__":
    sys.exit(main())
