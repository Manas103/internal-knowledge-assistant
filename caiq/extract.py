# Parses the two real CSA workbooks fetch_bundle.py verified into caiq/data/caiq_questions.json
# and caiq/data/ccm_controls.json (both gitignored, rebuilt, never committed; see
# caiq/manifest.json for why the full compiled question/control text is not checked in).
from __future__ import annotations

import json
from pathlib import Path

import openpyxl

from .fetch_bundle import RAW_DIR, fetch_bundle

DATA_DIR = Path(__file__).resolve().parent / "data"
SKIP_PREFIXES = {"Not Available", "End of Standard"}


def _extract_questions(xlsx_path: Path) -> list[dict]:
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    rows: list[dict] = []
    for row in ws.iter_rows(min_row=4, values_only=True):
        qid, qtext = row[0], row[1]
        if not qid or any(skip in qid for skip in SKIP_PREFIXES) or "Copyright" in qid:
            continue
        rows.append({"question_id": qid.strip(), "question": (qtext or "").strip()})
    return rows


def _extract_controls(xlsx_path: Path) -> list[dict]:
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb["CCM"]
    rows: list[dict] = []
    for row in ws.iter_rows(min_row=4, values_only=True):
        domain, title, cid, spec = row[0], row[1], row[2], row[3]
        if not cid:
            continue
        rows.append(
            {
                "domain": (domain or "").strip(),
                "control_title": (title or "").strip(),
                "control_id": cid.strip(),
                "control_specification": (spec or "").strip(),
            }
        )
    return rows


def build(raw_dir: Path = RAW_DIR, data_dir: Path = DATA_DIR) -> tuple[int, int]:
    extract_dir = fetch_bundle(raw_dir=raw_dir)
    bundle_dir = next(extract_dir.glob("CCM*CAIQv4.1 Bundle"))

    questions_xlsx = next(bundle_dir.glob("CAIQv4.0.3*Change Analysis.xlsx"))
    controls_xlsx = next(bundle_dir.glob("CCMv4.1.1*.xlsx"))

    questions = _extract_questions(questions_xlsx)
    controls = _extract_controls(controls_xlsx)

    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "caiq_questions.json").write_text(json.dumps(questions, indent=2), encoding="utf-8")
    (data_dir / "ccm_controls.json").write_text(json.dumps(controls, indent=2), encoding="utf-8")
    return len(questions), len(controls)


if __name__ == "__main__":
    n_questions, n_controls = build()
    print(f"{n_questions} real CAIQ v4.0.3 questions, {n_controls} real CCM v4.1.1 control objectives")
