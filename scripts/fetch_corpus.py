#!/usr/bin/env python
# Downloads exactly the public URLs named in corpus_manifest.json into data/raw/ (gitignored)
# and verifies each file's sha256 against the manifest. This is the one network-touching
# step in the project; everything downstream (ingest.py, the retrieval index, every
# benchmark) runs against data/raw/ once this has been run. Re-run this to regenerate
# data/raw/ from the same real sources: `python scripts/fetch_corpus.py`.
from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "corpus_manifest.json"
RAW_DIR = ROOT / "data" / "raw"

_EXT = {"pdf": ".pdf", "wikitext": ".wikitext"}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_all(manifest_path: Path = MANIFEST_PATH, raw_dir: Path = RAW_DIR) -> list[dict]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for source in manifest["sources"]:
        dest = raw_dir / f"{source['id']}{_EXT[source['format']]}"
        if not dest.exists():
            req = urllib.request.Request(source["url"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                dest.write_bytes(resp.read())
        digest = _sha256(dest)
        ok = digest == source["sha256"]
        results.append({"id": source["id"], "path": str(dest.relative_to(ROOT)), "sha256_match": ok, "sha256": digest})
        if not ok:
            raise ValueError(f"{source['id']}: sha256 mismatch (got {digest}, manifest says {source['sha256']})")
    return results


if __name__ == "__main__":
    report = fetch_all()
    print(json.dumps(report, indent=2))
    sys.exit(0 if all(r["sha256_match"] for r in report) else 1)
