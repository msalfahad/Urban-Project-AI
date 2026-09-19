"""Mechanical metrics for the twelve declared comparison axes.

Written and validated against the BASELINE before any improved result
existed, so the measuring instrument cannot have been shaped by what it
was later asked to measure.

Everything here is a COUNT over what a reading says about its own
sources. None of it judges whether a reading is correct - nothing in this
experiment can, and the moment a count is treated as a score for
correctness the whole apparatus is lying.

    python3 -m research.a21_visual_qs_pilot_01.presentation_metrics
"""

from __future__ import annotations

import json
import re
from pathlib import Path

RUN_DIR = Path("data/experiments/A21_VISUAL_QS_PILOT_01")

SOURCE_TYPES = (
    "DRAWING_PRINTED_DIMENSION", "DRAWING_SCALED_MEASUREMENT",
    "DRAWING_SCHEDULE", "PROJECT_SPECIFICATION", "TEMPORARY_OWNER_DEFAULT",
    "VISUAL_INTERPRETATION",
)

REFUSAL_CODES = (
    "PLASTER_HEIGHT_NOT_ESTABLISHED", "WINDOW_SCHEDULE_REQUIRED",
    "DOOR_SCHEDULE_REQUIRED", "STAIR_GEOMETRY_REQUIRED",
    "FINISH_TREATMENT_REQUIRED", "SOURCE_REQUIRED",
    "OWNER_INPUT_REQUIRED", "HUMAN_REVIEW",
)

SHEETS = ("GROUND_FLOOR_PLAN", "SECOND_FLOOR_ROOF_PLAN", "SECTION_A_A",
          "SECTION_B_B", "SOUTH_EAST_ELEVATION", "PLAN_ZOOM", "PLAN_DETAIL")


def _norm(s: str) -> str:
    """Readers write 'SECTION A-A', the file is SECTION_A_A. The citation
    axis measures whether a source names a SHEET, not how it spells it."""
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


NORM_SHEETS = {s: _norm(s) for s in SHEETS}

HEIGHT_FIELDS = ("STOREY_HEIGHT", "STRUCTURAL_HEIGHT", "CLEAR_HEIGHT",
                 "APPLICABLE_PLASTER_HEIGHT")


def _walk(o):
    """Every (key, value) pair anywhere in the structure."""
    if isinstance(o, dict):
        for k, v in o.items():
            yield k, v
            yield from _walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from _walk(v)


def _text(o) -> str:
    return json.dumps(o, ensure_ascii=False)


def _first(o, key):
    for k, v in _walk(o):
        if k == key:
            return v
    return None


def metrics_for_case(case: dict) -> dict:
    blob = _text(case)

    # axis 1 + 7: what kind of source each number claims
    src = {t: len(re.findall(re.escape(t), blob)) for t in SOURCE_TYPES}

    # axis 2: does a cited source say WHERE on the drawing
    locs = [v for k, v in _walk(case)
            if k in ("SOURCE_LOCATION", "SOURCE") and isinstance(v, str) and v]
    named = [v for v in locs
             if any(n in _norm(v) for n in NORM_SHEETS.values())]

    # axis 5: how many distinct sheets a reading actually reaches into
    nblob = _norm(blob)
    sheets_cited = sorted({s for s, n in NORM_SHEETS.items() if n in nblob})

    # axis 6: the four height fields, kept apart
    h = case.get("HEIGHT") or {}
    heights = {f: {"VALUE": (h.get(f) or {}).get("VALUE"),
                   "STATUS": (h.get(f) or {}).get("STATUS")}
               for f in HEIGHT_FIELDS}

    # axis 3 + 4
    segs = case.get("WALL_SEGMENTS") or case.get("SEGMENTS") or []
    lens = [s.get("LENGTH_M") for s in segs
            if isinstance(s, dict) and isinstance(s.get("LENGTH_M"),
                                                  (int, float))]
    ops = case.get("OPENINGS") or []
    ops_w = [o for o in ops if isinstance(o, dict)
             and isinstance(o.get("WIDTH"), (int, float))]
    ops_h = [o for o in ops if isinstance(o, dict)
             and isinstance(o.get("HEIGHT"), (int, float))]

    # axis 8: the refusal ledger
    unres = case.get("UNRESOLVED") or []
    codes = {}
    for u in unres:
        if isinstance(u, dict):
            codes[u.get("CODE")] = codes.get(u.get("CODE"), 0) + 1

    # axis 10 + 11
    contras = case.get("CONTRADICTIONS_BETWEEN_SHEETS") or []
    wimbw = case.get("WHERE_I_MIGHT_BE_WRONG") or []

    # the established-quantity ledger, reported but never scored
    est = case.get("SOURCE_ESTABLISHED_RESULT")
    est_statuses = sorted({v for k, v in _walk(est)
                           if k == "QUANTITY_STATUS" and isinstance(v, str)}
                          ) if est is not None else []

    return {
        "SOURCE_TYPE_COUNTS": src,
        "PRINTED_DIMENSION_CITATIONS": src["DRAWING_PRINTED_DIMENSION"],
        "SCALED_MEASUREMENT_CITATIONS": src["DRAWING_SCALED_MEASUREMENT"],
        "UNSUPPORTED_ASSUMPTION_CITATIONS": (
            src["VISUAL_INTERPRETATION"] + src["TEMPORARY_OWNER_DEFAULT"]),
        "SOURCE_LOCATIONS_GIVEN": len(locs),
        "SOURCE_LOCATIONS_NAMING_A_SHEET": len(named),
        "SHEETS_CITED": sheets_cited,
        "CROSS_SHEET_LINKAGE": len(sheets_cited),
        "HEIGHTS": heights,
        "SEGMENTS": len(segs),
        "SEGMENTS_WITH_A_LENGTH": len(lens),
        "TOTAL_SEGMENT_LENGTH_M": round(sum(lens), 2) if lens else None,
        "OPENINGS": len(ops),
        "OPENINGS_WITH_A_WIDTH": len(ops_w),
        "OPENINGS_WITH_A_HEIGHT": len(ops_h),
        "UNRESOLVED_ITEMS": len(unres),
        "UNRESOLVED_CODES": codes,
        "CONTRADICTIONS_DECLARED": len(contras),
        "SELF_DECLARED_DOUBTS": len(wimbw),
        "QUANTITY_STATUSES_PRESENT": est_statuses,
    }


def metrics_for_file(path: Path) -> dict:
    return {c.get("CASE_ID"): metrics_for_case(c)
            for c in json.loads(path.read_text("utf-8"))}


def collect(files: dict) -> dict:
    out = {}
    for label, rel in files.items():
        p = RUN_DIR / rel
        if p.exists():
            out[label] = metrics_for_file(p)
    return out


BASELINE_FILES = {
    "BASELINE_PASS_1": "a21_raw/A21_reader1.json",
    "BASELINE_PASS_1_B": "a21_raw/A21_reader2.json",
    "BASELINE_PASS_2": "a21_raw/PASS2_cases_1_3.json",
    "BASELINE_PASS_2_B": "a21_raw/PASS2_cases_4_6.json",
}
IMPROVED_FILES = {
    "IMPROVED_PASS_1": "improved_raw/IMP_PASS1_cases_1_3.json",
    "IMPROVED_PASS_1_B": "improved_raw/IMP_PASS1_cases_4_6.json",
    "IMPROVED_PASS_2": "improved_raw/IMP_PASS2_cases_1_3.json",
    "IMPROVED_PASS_2_B": "improved_raw/IMP_PASS2_cases_4_6.json",
}


def by_case(bundle: dict) -> dict:
    """Flatten reader files into {case: {pass: metrics}}."""
    out = {}
    for label, cases in bundle.items():
        p = "PASS_1" if "PASS_1" in label else "PASS_2"
        for cid, m in cases.items():
            out.setdefault(cid, {})[p] = m
    return out


if __name__ == "__main__":
    base = by_case(collect(BASELINE_FILES))
    imp = by_case(collect(IMPROVED_FILES))
    print(json.dumps({
        "VALIDATED_ON": "the frozen baseline",
        "BASELINE_CASES_MEASURED": sorted(base),
        "IMPROVED_CASES_MEASURED": sorted(imp),
        "SAMPLE": base.get("CASE-2-TILE-PREP", {}).get("PASS_1"),
    }, indent=2, ensure_ascii=False))
