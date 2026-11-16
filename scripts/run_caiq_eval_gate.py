# The real merge gate for the CAIQ answer library: the frozen 300-question eval set
# against the real control corpus and the committed evidence library.
from __future__ import annotations

from caiq.corpus import load_controls
from caiq.eval_gate import PASS_THRESHOLD, load_frozen_eval_set, measure_citation_accuracy
from caiq.evidence_library import load_evidence

if __name__ == "__main__":
    controls = load_controls()
    evidence = load_evidence()
    items = load_frozen_eval_set()
    accuracy = measure_citation_accuracy(items, controls, evidence)

    n_withheld_expected = sum(1 for it in items if it["expected_control_id"] is None)
    print(f"frozen eval set size: {len(items)}")
    print(f"controls in corpus: {len(controls)}; controls with committed evidence: {len(evidence)}")
    print(f"expected-withheld items: {n_withheld_expected}")
    print(f"citation accuracy: {accuracy:.4f}")
    print(f"pass threshold: {PASS_THRESHOLD}")
    print("PASS" if accuracy >= PASS_THRESHOLD else "FAIL")
