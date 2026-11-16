# Loads the real, rebuilt CAIQ v4.0.3 questions and CCM v4.1.1 control objectives
# (caiq/extract.py's output). control_root() is the whole mapping mechanism this project
# uses in place of retrieval: a CAIQ question id already names its control objective
# (e.g. "A&A-01.2" names control "A&A-01"), so matching a question to the control
# objective its draft must cite is a deterministic parse, not a search.
from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

DATA_DIR = Path(__file__).resolve().parent / "data"
QUESTIONS_PATH = DATA_DIR / "caiq_questions.json"
CONTROLS_PATH = DATA_DIR / "ccm_controls.json"


class Question(NamedTuple):
    question_id: str
    question: str


class Control(NamedTuple):
    control_id: str
    domain: str
    control_title: str
    control_specification: str


def control_root(question_id: str) -> str:
    return question_id.rsplit(".", 1)[0]


def load_questions(path: Path = QUESTIONS_PATH) -> list[Question]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Question(r["question_id"], r["question"]) for r in raw]


def load_controls(path: Path = CONTROLS_PATH) -> dict[str, Control]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {
        r["control_id"]: Control(r["control_id"], r["domain"], r["control_title"], r["control_specification"])
        for r in raw
    }


def corpus_available(questions_path: Path = QUESTIONS_PATH, controls_path: Path = CONTROLS_PATH) -> bool:
    return questions_path.exists() and controls_path.exists()
