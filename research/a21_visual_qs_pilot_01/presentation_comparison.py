"""BASELINE vs IMPROVED - built only after both improved passes freeze.

No averaging. No winner. No quantity is selected for being more
plausible. For every axis this reports what each run did, per case, per
pass, and leaves the two runs standing side by side.

The classification for each field comes from the pre-declared vocabulary
and every claimed improvement must NAME the evidence that caused it -
"the reader said a better thing" is not a finding.

    python3 -m research.a21_visual_qs_pilot_01.presentation_comparison
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.a21_visual_qs_pilot_01 import improved_protocol as IP
from research.a21_visual_qs_pilot_01 import presentation_metrics as M

RUN_DIR = Path("data/experiments/A21_VISUAL_QS_PILOT_01")

COUNT_AXES = (
    ("printed dimension extraction", "PRINTED_DIMENSION_CITATIONS"),
    ("source citation quality", "SOURCE_LOCATIONS_NAMING_A_SHEET"),
    ("room / boundary interpretation", "SEGMENTS_WITH_A_LENGTH"),
    ("opening identification", "OPENINGS_WITH_A_WIDTH"),
    ("cross-sheet linkage", "CROSS_SHEET_LINKAGE"),
    ("unsupported assumptions", "UNSUPPORTED_ASSUMPTION_CITATIONS"),
    ("SOURCE_REQUIRED and other unresolved fields", "UNRESOLVED_ITEMS"),
    ("contradictions detected", "CONTRADICTIONS_DECLARED"),
    ("accidental inference beyond evidence", "SCALED_MEASUREMENT_CITATIONS"),
    ("self-declared doubts", "SELF_DECLARED_DOUBTS"),
)


def _pair(d: dict, key: str):
    return {p: (m or {}).get(key) for p, m in sorted(d.items())}


def build() -> dict:
    IP.assert_baseline_intact()
    for n in (1, 2):
        f = RUN_DIR / f"IMPROVED_PASS{n}_FREEZE.json"
        if not f.exists():
            raise SystemExit(
                f"pass {n} is not frozen; no comparison may be built yet")

    base = M.by_case(M.collect(M.BASELINE_FILES))
    imp = M.by_case(M.collect(M.IMPROVED_FILES))

    cases = []
    for cid in sorted(set(base) | set(imp)):
        b, i = base.get(cid, {}), imp.get(cid, {})
        axes = []
        for label, key in COUNT_AXES:
            axes.append({
                "AXIS": label,
                "BASELINE": _pair(b, key),
                "IMPROVED": _pair(i, key),
            })
        heights = {
            "BASELINE": {p: (m or {}).get("HEIGHTS") for p, m in sorted(b.items())},
            "IMPROVED": {p: (m or {}).get("HEIGHTS") for p, m in sorted(i.items())},
        }
        # refusal stability: does a run agree with ITSELF across its passes
        def stable(d):
            vals = [((m or {}).get("HEIGHTS") or {}).get(
                "APPLICABLE_PLASTER_HEIGHT", {}).get("STATUS")
                for m in d.values()]
            return {"STATUSES": vals,
                    "STABLE_ACROSS_PASSES": len(set(vals)) == 1 and bool(vals)}
        cases.append({
            "CASE_ID": cid,
            "COMPARABILITY": (IP.CASE_6_CLASSIFICATION
                              if cid == "CASE-6-ROOF-PARAPET"
                              else IP.CASES_1_TO_5_CLASSIFICATION),
            "COUNT_AXES": axes,
            "HEIGHT_FIELDS": heights,
            "REFUSAL_STABILITY": {"BASELINE": stable(b), "IMPROVED": stable(i)},
            "UNRESOLVED_CODES": {
                "BASELINE": {p: (m or {}).get("UNRESOLVED_CODES")
                             for p, m in sorted(b.items())},
                "IMPROVED": {p: (m or {}).get("UNRESOLVED_CODES")
                             for p, m in sorted(i.items())},
            },
            "QUANTITY_STATUSES": {
                "BASELINE": {p: (m or {}).get("QUANTITY_STATUSES_PRESENT")
                             for p, m in sorted(b.items())},
                "IMPROVED": {p: (m or {}).get("QUANTITY_STATUSES_PRESENT")
                             for p, m in sorted(i.items())},
            },
        })

    body = {
        "EXPERIMENT_ID": IP.EXPERIMENT_ID,
        "ARTIFACT": "A21_SOURCE_PRESENTATION_COMPARISON",
        "BUILT_ONLY_AFTER_BOTH_IMPROVED_PASSES_WERE_FROZEN": True,
        "BASELINE_RUN_ID": IP.BASELINE_RUN_ID,
        "IMPROVED_RUN_ID": IP.RUN_ID,
        "WHAT_THIS_IS_NOT": (
            "not a reconciliation, not an adjudication, not A22. No "
            "quantity was averaged, no answer was chosen for being more "
            "plausible, and no run is declared the winner"),
        "MORE_QUANTITIES_IS_NOT_A_METRIC": IP.MORE_QUANTITIES_IS_NOT_A_METRIC,
        "A_REFUSAL_REMAINS_CORRECT": IP.A_REFUSAL_REMAINS_CORRECT,
        "EVERY_CLAIMED_IMPROVEMENT_MUST_NAME_ITS_CAUSE":
            IP.EVERY_CLAIMED_IMPROVEMENT_MUST_NAME_ITS_CAUSE,
        "CLASSIFICATION_VOCABULARY": list(IP.CLASSIFICATION_VOCABULARY),
        "EVIDENCE_INDEPENDENCE_STATUS": IP.EVIDENCE_INDEPENDENCE_STATUS,
        "INDEPENDENCE_COMPONENTS": list(IP.INDEPENDENCE_COMPONENTS),
        "WHAT_AGREEMENT_SHOWS": IP.WHAT_AGREEMENT_SHOWS,
        "CASE_6_IS_NOT_A_ONE_VARIABLE_COMPARISON":
            IP.CASE_6_IS_NOT_A_ONE_VARIABLE_COMPARISON,
        "THE_COUNTS_ARE_NOT_SCORES": (
            "every number below is a count of what a reading says about "
            "its own sources. None of it shows that a reading is right"),
        "CASES": cases,
    }
    out = RUN_DIR / "A21_SOURCE_PRESENTATION_COMPARISON.json"
    out.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    return {"FILE": out.name,
            "SHA256": hashlib.sha256(out.read_bytes()).hexdigest(),
            "CASES": len(cases)}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
