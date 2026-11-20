"""The benchmark behind this extension's README. Builds the real corpus, picks
9 pages to carry a "before" failure (3 missing, 3 stale, 3 real discovered
retrieval misses), freezes 300 questions, measures citation-supported rate
before any fix, applies the structural fixes, and re-measures the identical
300 questions against the fixed corpus.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path


def stable_seed(text: str) -> int:
    """A deterministic replacement for Python's built-in hash() on strings,
    which is salted per-process (PYTHONHASHSEED) and would otherwise make
    the stale-number and deep-probe choices below non-reproducible run to
    run, breaking the frozen-eval-set guarantee."""
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from assistant.ingest import Passage  # noqa: E402
from assistant.retrieval import BM25Index  # noqa: E402
from comms_audit import ingest, labeling, qagen, scenarios  # noqa: E402

AUDIT_DIR = Path(__file__).resolve().parents[1]
EVAL_DIR = AUDIT_DIR / "eval"
DOCS_DIR = AUDIT_DIR / "docs"
SEED = 920261118

N_MISSING = 3
N_STALE = 3
N_RETRIEVAL_MISS = 3
FROZEN_N = 300
# Each of the 9 worklist pages is probed with several independent questions
# (different real keyphrases from the same passage), not just one: a single
# frozen question per page would make a page-level content fix invisible
# against 300 questions. 9 pages x 8 probes = 72 scenario questions; the
# remaining 228 are the normal one-question-per-passage baseline.
DEEP_PROBES_PER_PAGE = 11


def single_chunk_page_ids(passages: list[Passage]) -> set[str]:
    counts: dict[str, int] = {}
    for p in passages:
        counts[p.doc_id] = max(counts.get(p.doc_id, 0), p.page_number)
    return {doc_id for doc_id, n in counts.items() if n == 1}


def main() -> None:
    manifest = ingest.load_manifest()
    passages_full = ingest.build_corpus()
    index_full = BM25Index(passages_full)
    candidates = qagen.generate_candidates(passages_full, index_full, seed=SEED)
    passage_by_page: dict[str, Passage] = {p.doc_id: p for p in passages_full}  # single-chunk pages only need page_number 1

    eligible = single_chunk_page_ids(passages_full)
    page_word_count = {p["page_id"]: p["word_count"] for p in manifest["pages"]}
    page_type = {p["page_id"]: p["source_type"] for p in manifest["pages"]}

    rng = random.Random(SEED)
    docs_eligible = sorted([pid for pid in eligible if page_type.get(pid) == "docs" and 200 <= page_word_count.get(pid, 0) < 650])
    rng.shuffle(docs_eligible)

    missing_page_ids = docs_eligible[:N_MISSING]
    stale_pool = docs_eligible[N_MISSING:]
    stale_page_ids: list[str] = []
    stale_fixes_by_page: dict[str, list[scenarios.StaleFix]] = {}
    staled_text_by_page: dict[str, str] = {}
    for pid in stale_pool:
        if len(stale_page_ids) >= N_STALE:
            break
        raw = ingest.raw_text(pid)
        staled, fixes = scenarios.inject_stale_numbers(raw, random.Random(SEED + stable_seed(pid) % 10000))
        if fixes:
            stale_page_ids.append(pid)
            stale_fixes_by_page[pid] = fixes
            staled_text_by_page[pid] = staled

    exclude_set = frozenset(missing_page_ids)
    before_overrides = dict(staled_text_by_page)
    passages_before = ingest.build_corpus(exclude_page_ids=exclude_set, overrides=before_overrides)
    index_before = BM25Index(passages_before)

    already_used = set(missing_page_ids) | set(stale_page_ids)
    discovered = scenarios.discover_retrieval_misses(
        [qagen.item_to_dict(c) for c in candidates],
        passages_before,
        index_before,
        exclude_page_ids=already_used,
        n_needed=N_RETRIEVAL_MISS,
    )
    retrieval_miss_page_ids = [pid for pid, _ in discovered]
    retrieval_miss_phrases = dict(discovered)

    scenario_page_ids = set(missing_page_ids) | set(stale_page_ids) | set(retrieval_miss_page_ids)

    frozen_items = []
    for pid in missing_page_ids + stale_page_ids + retrieval_miss_page_ids:
        probes = qagen.generate_deep_probe(passage_by_page[pid], index_full, seed=SEED + stable_seed(pid) % 100000, n=DEEP_PROBES_PER_PAGE)
        frozen_items.extend(qagen.item_to_dict(p) for p in probes)

    rng2 = random.Random(SEED + 7)
    filler_pool = [c for c in candidates if c.expected_doc_id not in scenario_page_ids]
    rng2.shuffle(filler_pool)
    for c in filler_pool:
        if len(frozen_items) >= FROZEN_N:
            break
        frozen_items.append(qagen.item_to_dict(c))

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    (EVAL_DIR / "frozen_eval_set.json").write_text(json.dumps(frozen_items, indent=2), encoding="utf-8")

    # --- BEFORE measurement ---
    before_labels = [
        labeling.label_answer(item, index_before, excluded_page_ids=exclude_set, stale_page_ids=frozenset(stale_page_ids))
        for item in frozen_items
    ]
    before_rate = labeling.citation_supported_rate(before_labels)
    before_breakdown = labeling.failure_breakdown(before_labels)

    # --- Apply fixes ---
    fix_log: list[scenarios.StructuralFix] = []
    for pid in missing_page_ids:
        fix_log.append(scenarios.StructuralFix(pid, "add_missing_page", f"Ingested {pid}: page was not yet in the index."))
    for pid in stale_page_ids:
        for f in stale_fixes_by_page[pid]:
            fix_log.append(
                scenarios.StructuralFix(pid, "correct_stale_number", f"Corrected stale figure on {pid}: '{f.new_value}' -> '{f.old_value}'.")
            )

    after_overrides: dict[str, str] = {}
    heading_fixed_pages: list[str] = []
    for pid in retrieval_miss_page_ids:
        raw = ingest.raw_text(pid)
        phrase = retrieval_miss_phrases[pid]
        headed = scenarios.add_heading(raw, phrase, title=passage_by_page[pid].title)
        if len(headed.split(" ")) <= ingest.CHUNK_WORDS:
            after_overrides[pid] = headed
            heading_fixed_pages.append(pid)
            fix_log.append(scenarios.StructuralFix(pid, "add_heading", f"Added an explicit topic heading to {pid} naming '{phrase}'."))
        # else: page too close to the chunk boundary already; left as a disclosed miss below.

    passages_after = ingest.build_corpus(exclude_page_ids=frozenset(), overrides=after_overrides)
    index_after = BM25Index(passages_after)

    after_labels = [
        labeling.label_answer(item, index_after, excluded_page_ids=frozenset(), stale_page_ids=frozenset())
        for item in frozen_items
    ]
    after_rate = labeling.citation_supported_rate(after_labels)
    after_breakdown = labeling.failure_breakdown(after_labels)

    still_failing_retrieval_miss = [
        pid for pid in retrieval_miss_page_ids
        if any(
            lab.expected_doc_id == pid and lab.label != "supported"
            for lab in after_labels
        )
    ]

    worklist = {
        "pages_touched": sorted(scenario_page_ids),
        "page_count": len(scenario_page_ids),
        "fix_count": len(fix_log),
        "fixes": [f.__dict__ for f in fix_log],
        "retrieval_miss_pages_still_failing_after_fix": still_failing_retrieval_miss,
    }
    (DOCS_DIR / "fix_worklist.json").write_text(json.dumps(worklist, indent=2), encoding="utf-8")
    (EVAL_DIR / "scenario_key.json").write_text(
        json.dumps(
            {
                "missing_page_ids": missing_page_ids,
                "stale_page_ids": stale_page_ids,
                "retrieval_miss_page_ids": retrieval_miss_page_ids,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    report = {
        "pages_in_corpus": len(manifest["pages"]),
        "passages_in_corpus": len(passages_full),
        "frozen_question_count": len(frozen_items),
        "scenario_pages": len(scenario_page_ids),
        "fix_count": len(fix_log),
        "before_citation_supported_rate": before_rate,
        "before_failure_breakdown": before_breakdown,
        "after_citation_supported_rate": after_rate,
        "after_failure_breakdown": after_breakdown,
        "retrieval_miss_pages_discovered": len(retrieval_miss_page_ids),
        "retrieval_miss_pages_fixed": len(heading_fixed_pages),
        "retrieval_miss_pages_still_failing_after_fix": still_failing_retrieval_miss,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
