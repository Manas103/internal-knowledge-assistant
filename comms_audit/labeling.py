# Labels one answer against its own cited passage: supported, unsupported, or
# stale, and for every failure (unsupported or stale), the one cause: a missing
# page, a stale number, or a passage the retriever never reached. The label is
# computed from what the retriever actually returned on this corpus build, never
# from the scenario's own seeded intent, so a matching bug would show up as a
# wrong label rather than being hidden by the generator's own bookkeeping.
from __future__ import annotations

from dataclasses import dataclass

from assistant.answer import Draft, answer_question
from assistant.retrieval import BM25Index


@dataclass(frozen=True)
class LabeledAnswer:
    question: str
    expected_doc_id: str
    expected_page_number: int
    cited_doc_id: str
    cited_page_number: int
    label: str  # "supported" | "unsupported" | "stale"
    failure_cause: str | None  # None | "missing_page" | "stale_number" | "retrieval_miss"


def label_answer(
    item: dict,
    index: BM25Index,
    *,
    excluded_page_ids: frozenset[str],
    stale_page_ids: frozenset[str],
) -> LabeledAnswer:
    draft: Draft = answer_question(item["question"], index)
    citation_matches = draft.cited_doc_id == item["expected_doc_id"] and draft.cited_page_number == item["expected_page_number"]

    if citation_matches and item["expected_doc_id"] in stale_page_ids:
        return LabeledAnswer(
            question=item["question"],
            expected_doc_id=item["expected_doc_id"],
            expected_page_number=item["expected_page_number"],
            cited_doc_id=draft.cited_doc_id,
            cited_page_number=draft.cited_page_number,
            label="stale",
            failure_cause="stale_number",
        )
    if citation_matches:
        return LabeledAnswer(
            question=item["question"],
            expected_doc_id=item["expected_doc_id"],
            expected_page_number=item["expected_page_number"],
            cited_doc_id=draft.cited_doc_id,
            cited_page_number=draft.cited_page_number,
            label="supported",
            failure_cause=None,
        )

    cause = "missing_page" if item["expected_doc_id"] in excluded_page_ids else "retrieval_miss"
    return LabeledAnswer(
        question=item["question"],
        expected_doc_id=item["expected_doc_id"],
        expected_page_number=item["expected_page_number"],
        cited_doc_id=draft.cited_doc_id,
        cited_page_number=draft.cited_page_number,
        label="unsupported",
        failure_cause=cause,
    )


def citation_supported_rate(labels: list[LabeledAnswer]) -> float:
    if not labels:
        return 0.0
    return sum(1 for l in labels if l.label == "supported") / len(labels)


def failure_breakdown(labels: list[LabeledAnswer]) -> dict[str, int]:
    out = {"missing_page": 0, "stale_number": 0, "retrieval_miss": 0}
    for l in labels:
        if l.failure_cause:
            out[l.failure_cause] += 1
    return out
