# Extractive drafting: no generative model writes these answers, the top BM25 passage's
# own text is truncated and quoted with its citation attached. confidence is the retrieval
# score margin between the top-1 and top-2 results, the one signal this project uses to
# decide whether a draft is confident enough to simulate going out unedited
# (scripts/run_session_benchmark.py); a narrow margin means the index itself was unsure
# which passage actually answers the question, which is exactly when a human reviewer
# would be expected to step in.
from __future__ import annotations

from dataclasses import dataclass

from .retrieval import BM25Index

SNIPPET_CHARS = 280


@dataclass(frozen=True)
class Draft:
    answer_text: str
    cited_doc_id: str
    cited_page_number: int
    confidence: float


def answer_question(question: str, index: BM25Index, *, top_k: int = 3) -> Draft:
    results = index.search(question, top_k=top_k)
    if not results:
        return Draft("No supporting passage was found for this question.", "", -1, 0.0)
    top = results[0]
    runner_up_score = results[1].score if len(results) > 1 else 0.0
    confidence = top.score - runner_up_score

    text = top.passage.text
    snippet = text if len(text) <= SNIPPET_CHARS else text[:SNIPPET_CHARS].rsplit(" ", 1)[0] + "..."
    answer_text = f"{snippet} (source: {top.passage.title}, page {top.passage.page_number})"
    return Draft(
        answer_text=answer_text,
        cited_doc_id=top.passage.doc_id,
        cited_page_number=top.passage.page_number,
        confidence=confidence,
    )
