# The committed evidence register: which control ids have a named artifact attached.
# caiq/build_evidence_library.py generates data/evidence_library.json once; this module
# only loads it. Deliberately partial coverage (see README Honest framing) is what makes
# "questions no committed evidence covers are withheld rather than answered" a real,
# falsifiable property of this project rather than a vacuously-true one.
from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

DATA_DIR = Path(__file__).resolve().parent / "data"
EVIDENCE_PATH = DATA_DIR / "evidence_library.json"


class Evidence(NamedTuple):
    control_id: str
    artifact_name: str
    collected_date: str


def load_evidence(path: Path = EVIDENCE_PATH) -> dict[str, Evidence]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {r["control_id"]: Evidence(r["control_id"], r["artifact_name"], r["collected_date"]) for r in raw}
