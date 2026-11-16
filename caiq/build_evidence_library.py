# Builds caiq/data/evidence_library.json once, from a fixed seed, and the result is
# committed (unlike caiq_questions.json/ccm_controls.json, this file is this project's own
# synthetic evidence register, not a reproduction of CSA's compiled question/control text,
# so there is no licensing reason to gitignore it). It is explicitly synthetic: no real
# company's actual compliance evidence exists here, the same disclosed-synthetic framing
# this repo already uses for its other generated fixtures. Run deliberately, never
# silently, exactly like scripts/freeze_eval_set.py.
from __future__ import annotations

import json
import random
from pathlib import Path

from .corpus import load_controls

DATA_DIR = Path(__file__).resolve().parent / "data"
EVIDENCE_PATH = DATA_DIR / "evidence_library.json"
SEED = 20261116
COVERAGE_FRACTION = 150 / 207  # see README Honest framing for why coverage is deliberately partial

ARTIFACTS_BY_DOMAIN = {
    "Audit & Assurance": ("SOC 2 Type II Report", "2026-08-15"),
    "Application & Interface Security": ("Secure SDLC Standard v4", "2026-05-01"),
    "Business Continuity Management and Operational Resilience": ("Business Continuity Plan v5", "2026-03-10"),
    "Change Control and Configuration Management": ("Change Management Policy v3", "2026-02-20"),
    "Cryptography, Encryption & Key Management": ("Key Management Standard v2", "2026-04-12"),
    "Datacenter Security": ("Datacenter Physical Security Assessment", "2026-07-01"),
    "Data Security and Privacy Lifecycle Management": ("Data Classification and Handling Policy v4", "2026-06-18"),
    "Governance, Risk and Compliance": ("Enterprise Risk Register, Q3 2026", "2026-09-01"),
    "Human Resources": ("Personnel Security Policy v3", "2026-01-22"),
    "Identity & Access Management": ("Access Control Standard v5", "2026-05-30"),
    "Infrastructure Security": ("Network Security Architecture Review", "2026-08-01"),
    "Interoperability & Portability": ("Data Portability and Interoperability Standard v2", "2026-02-05"),
    "Logging and Monitoring": ("Logging and Monitoring Standard v3", "2026-06-01"),
    "Security Incident Management, E-Discovery, & Cloud Forensics": ("Incident Response Plan v6", "2026-07-20"),
    "Supply Chain Management, Transparency, and Accountability": ("Vendor Risk Management Program v3", "2026-03-28"),
    "Threat & Vulnerability Management": ("Penetration Test Report, Q2 2026", "2026-04-30"),
    "Universal Endpoint Management": ("Endpoint Management Standard v4", "2026-05-15"),
}


def build(seed: int = SEED, coverage_fraction: float = COVERAGE_FRACTION) -> list[dict]:
    controls = load_controls()
    control_ids = sorted(controls)
    rng = random.Random(seed)
    n_covered = round(len(control_ids) * coverage_fraction)
    covered = set(rng.sample(control_ids, n_covered))

    entries = []
    for control_id in control_ids:
        if control_id not in covered:
            continue
        domain = controls[control_id].domain
        artifact_name, collected_date = ARTIFACTS_BY_DOMAIN.get(domain, ("General Control Evidence Register", "2026-01-01"))
        entries.append(
            {
                "control_id": control_id,
                "artifact_name": artifact_name,
                "collected_date": collected_date,
            }
        )
    return entries


if __name__ == "__main__":
    entries = build()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    print(f"{len(entries)} controls covered by committed evidence (of {len(load_controls())} total)")
