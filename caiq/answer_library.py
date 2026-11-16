# The approved answer library itself: an extractive draft built from the real control
# objective's own specification text, never free-generated, exactly like assistant/answer.py's
# extractive drafting elsewhere in this repo. A question withholds instead of answering
# whenever its control id does not resolve in the real control corpus (a genuine version-drift
# gap between CAIQ v4.0.3 and the publicly downloadable CCM v4.1.1, see README) or when that
# control id has no committed evidence artifact attached (caiq/evidence_library.py).
from __future__ import annotations

from dataclasses import dataclass

from .corpus import Control, control_root
from .evidence_library import Evidence

SNIPPET_CHARS = 280


@dataclass(frozen=True)
class Draft:
    withheld: bool
    reason: str
    answer_text: str = ""
    cited_control_id: str | None = None
    cited_artifact_name: str | None = None


def draft_answer(question_id: str, controls: dict[str, Control], evidence: dict[str, Evidence]) -> Draft:
    root = control_root(question_id)
    control = controls.get(root)
    if control is None:
        return Draft(withheld=True, reason=f"no control objective {root} in the committed control corpus")

    artifact = evidence.get(root)
    if artifact is None:
        return Draft(withheld=True, reason=f"no committed evidence artifact for control {root}")

    spec = control.control_specification
    snippet = spec if len(spec) <= SNIPPET_CHARS else spec[:SNIPPET_CHARS].rsplit(" ", 1)[0] + "..."
    answer_text = (
        f"{snippet} (control {control.control_id}: {control.control_title}; "
        f"evidence: {artifact.artifact_name}, collected {artifact.collected_date})"
    )
    return Draft(
        withheld=False,
        reason="",
        answer_text=answer_text,
        cited_control_id=control.control_id,
        cited_artifact_name=artifact.artifact_name,
    )
