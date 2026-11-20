# Turns the real pages fetched by scripts/fetch_corpus.py (data/raw/*.txt, manifest
# in corpus_manifest.json) into Passage records, reusing the base assistant's Passage
# shape (doc_id, title, page_number, text, source_format) so retrieval.BM25Index works
# unmodified over this corpus. Web pages have no natural page breaks the way a PDF
# does, so each page is chunked into fixed-size word windows, the same technique
# assistant/ingest.py uses for the Wikipedia sources.
from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assistant.ingest import Passage  # noqa: E402

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"
MANIFEST_PATH = ROOT / "corpus_manifest.json"
CORPUS_PATH = ROOT / "data" / "corpus.jsonl"

# 320 and 150 words/chunk were both tried first and measured worse (natural
# BM25 citation accuracy 79.5% and 68.5% respectively on this real corpus,
# via comms_audit/scripts/debug_natural_misses.py): most of those misses were
# a page's own first chunk out-scoring the chunk that actually answers the
# question, because a short chunk's intro sentence tends to repeat the page
# title's terms and BM25's length normalization favors it. 700-word chunks
# (closer to one chunk per page) measured 88.7% and were kept; see README
# Findings for the full account.
CHUNK_WORDS = 700


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _chunk(text: str, doc_id: str, title: str, source_format: str) -> list[Passage]:
    words = text.split(" ")
    passages = []
    for i, start in enumerate(range(0, len(words), CHUNK_WORDS), start=1):
        chunk = " ".join(words[start : start + CHUNK_WORDS]).strip()
        if chunk:
            passages.append(Passage(doc_id=doc_id, title=title, page_number=i, text=chunk, source_format=source_format))
    return passages


def build_corpus(
    raw_dir: Path = RAW_DIR,
    manifest_path: Path = MANIFEST_PATH,
    corpus_path: Path = CORPUS_PATH,
    overrides: dict[str, str] | None = None,
    exclude_page_ids: frozenset[str] = frozenset(),
) -> list[Passage]:
    """overrides maps page_id -> replacement full text (used to apply the 28 structural
    fixes without re-fetching the live page); exclude_page_ids simulates a page not
    having been ingested yet (the "missing page" failure cause). A fix never changes
    a page's chunk count or numbering, only its text, so a frozen question's expected
    (doc_id, page_number) stays valid across the before and after corpus builds."""
    manifest = load_manifest(manifest_path)
    overrides = overrides or {}
    passages: list[Passage] = []
    for page in manifest["pages"]:
        page_id = page["page_id"]
        if page_id in exclude_page_ids:
            continue
        if page_id in overrides:
            text = overrides[page_id]
        else:
            path = raw_dir / f"{page_id}.txt"
            if not path.exists():
                raise FileNotFoundError(f"{path} missing; run scripts/fetch_corpus.py first")
            text = path.read_text(encoding="utf-8")
        passages.extend(_chunk(text, page_id, page["title"], page["source_type"]))

    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    with open(corpus_path, "w", encoding="utf-8") as f:
        for p in passages:
            f.write(json.dumps(asdict(p)) + "\n")
    return passages


def raw_text(page_id: str, raw_dir: Path = RAW_DIR) -> str:
    return (raw_dir / f"{page_id}.txt").read_text(encoding="utf-8")


if __name__ == "__main__":
    built = build_corpus()
    by_type: dict[str, int] = {}
    pages = {p.doc_id for p in built}
    manifest = load_manifest()
    for page in manifest["pages"]:
        by_type[page["source_type"]] = by_type.get(page["source_type"], 0) + 1
    print(
        json.dumps(
            {"pages_in_manifest": len(manifest["pages"]), "pages_with_passages": len(pages), "total_passages": len(built), "by_source_type": by_type},
            indent=2,
        )
    )
