"""Split controller metadata from reader metadata, and prove the split.

Source selection decides WHICH sheets a reader gets. It must not tell the
reader WHAT the pre-reader thinks those sheets prove. The first packet I
built failed that badly: its TASK.json told the reader that the curved
main stair appears on the north-east elevation, that A-A cuts the service
stair, and which dimension figures to look for. That is the answer, not
the source.

So there are two records now:

  CONTROLLER_SOURCE_REQUIREMENTS   every reason, every disagreement,
                                   every pre-read interpretation.
                                   NEVER mounted.
  A21_READER_SOURCE_MANIFEST       neutral facts only: what the sheet is,
                                   where it came from, whether it exists.

and a screen that fails the build if any pre-read sentence survives into
anything a reader can open.

    python3 -m research.a21_trace_sufficiency_01.reader_manifest
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from research.a21_trace_sufficiency_01 import protocol as P
from research.a21_trace_sufficiency_01 import source_sufficiency as S

OUT = Path("data/experiments/A21_TRACE_SUFFICIENCY_01")
CASE_BOX = OUT / "case_sandbox"

DOCUMENT_TYPE = {
    "GROUND_FLOOR_PLAN": "PLAN", "FIRST_FLOOR_PLAN": "PLAN",
    "SECOND_FLOOR_ROOF_PLAN": "PLAN",
    "SECTION_A_A": "SECTION", "SECTION_B_B": "SECTION",
    "SOUTH_EAST_ELEVATION": "ELEVATION",
    "SOUTH_WEST_ELEVATION": "ELEVATION",
    "NORTH_WEST_ELEVATION": "ELEVATION",
    "NORTH_EAST_ELEVATION": "ELEVATION",
    "FENCE_ELEVATION_AND_SECTION": "ELEVATION_AND_SECTION",
}

# A missing DOCUMENT TYPE is a neutral fact the reader needs, so it does
# not silently substitute a default. A missing document DESCRIPTION can
# leak a finding - "the curved main stair" tells the reader a curved main
# stair exists - so descriptions are normalised to types here and the
# original wording is kept controller-side.
MISSING_AS_DOCUMENT_TYPE = {
    "FINISHES_SCHEDULE": "FINISHES_SPECIFICATION",
    "FINISHES_SPECIFICATION": "FINISHES_SPECIFICATION",
    "DOOR_SCHEDULE": "DOOR_SCHEDULE",
    "WINDOW_SCHEDULE": "WINDOW_SCHEDULE",
    "DOOR_AND_WINDOW_SCHEDULE": "DOOR_AND_WINDOW_SCHEDULE",
    "JAMB_SILL_AND_HEAD_DETAILS": "OPENING_JAMB_SILL_HEAD_DETAIL",
    "DIMENSIONED_STAIR_SECTION_DETAIL_FOR_THE_CURVED_MAIN_STAIR":
        "STAIR_SECTION_DETAIL",
    "PARAPET_COPING_CAPPING_DETAIL": "PARAPET_COPING_DETAIL",
}

READER_VISIBLE_FIELDS = (
    "CASE_ID", "QUESTION", "SHEET_ID", "FILE", "PAGE_ID", "SOURCE_HASH",
    "PRESENTATION_HASH", "DOCUMENT_TYPE", "AVAILABILITY",
)


def _shingles(text: str, n: int = 6) -> set:
    w = re.findall(r"[a-z0-9]+", (text or "").lower())
    return {" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}


def build() -> dict:
    req = json.loads((OUT / "CASE_SOURCE_REQUIREMENTS.json").read_text("utf-8"))
    idx = json.loads((OUT / "SHEET_INDEX.json").read_text("utf-8"))["SHEETS"]

    # ---- A. controller record: everything, mounted nowhere -------
    controller = {
        "PHASE_ID": P.PHASE_ID,
        "ARTIFACT": "CONTROLLER_SOURCE_REQUIREMENTS",
        "READER_VISIBLE": False,
        "WHY_THIS_EXISTS": (
            "selection reasoning, pre-read interpretations and path "
            "disagreements are controller knowledge. Handing them to the "
            "reader would answer the question it is being asked"),
        "CASE_SOURCE_REQUIREMENTS": req,
    }
    cp = OUT / "CONTROLLER_SOURCE_REQUIREMENTS.json"
    cp.write_text(json.dumps(controller, indent=2, ensure_ascii=False) + "\n",
                  encoding="utf-8")

    # ---- B. reader manifest: neutral facts only ------------------
    cases = []
    for c in req["CASES"]:
        cid = c["CASE_ID"]
        sheets = []
        for sid in c["CONSERVATIVE_UNION_MOUNTED"]:
            rec = idx[sid]
            sheets.append({
                "SHEET_ID": sid,
                "FILE": f"{sid}.jpeg",
                "PAGE_ID": rec["ORIGINAL_PAGE_ID"],
                "ORIGINAL_PDF_PAGE": rec["ORIGINAL_PDF_PAGE"],
                "SOURCE_HASH": rec["ORIGINAL_HASH"],
                "PRESENTATION_HASH": rec["SOURCE_PRESENTATION_HASH"],
                "DOCUMENT_TYPE": DOCUMENT_TYPE[sid],
                # neutral fact, and the reader needs it: trace
                # coordinates are meaningless without the pixel space
                # they are expressed in
                "IMAGE_SIZE_PX": rec["FINAL_SIZE_PX"],
                "AVAILABILITY": "AVAILABLE",
            })
        missing = sorted({MISSING_AS_DOCUMENT_TYPE.get(m, m)
                          for m in c["MISSING_SOURCE"]})
        cases.append({
            "CASE_ID": cid,
            "QUESTION": c["QUESTION"],
            "SHEETS": sheets,
            "MISSING_DOCUMENT_TYPES": [
                {"DOCUMENT_TYPE": m, "AVAILABILITY": "MISSING"}
                for m in missing],
            "CASE_SOURCE_STATUS": c["CASE_SOURCE_STATUS"],
        })
    reader = {
        "PHASE_ID": P.PHASE_ID,
        "ARTIFACT": "A21_READER_SOURCE_MANIFEST",
        "READER_VISIBLE": True,
        "CONTAINS_ONLY": list(READER_VISIBLE_FIELDS),
        "CONTAINS_NO_PRE_READ_INTERPRETATION": True,
        "CASES": cases,
    }
    rp = OUT / "A21_READER_SOURCE_MANIFEST.json"
    rp.write_text(json.dumps(reader, indent=2, ensure_ascii=False) + "\n",
                  encoding="utf-8")

    # ---- rewrite every TASK.json with neutral facts only ---------
    for c in cases:
        d = CASE_BOX / c["CASE_ID"]
        (d / "TASK.json").write_text(json.dumps({
            "CASE_ID": c["CASE_ID"],
            "QUESTION": c["QUESTION"],
            "SOURCES": [s["FILE"] for s in c["SHEETS"]],
            "SHEETS": [{k: s[k] for k in
                        ("SHEET_ID", "FILE", "PAGE_ID", "DOCUMENT_TYPE",
                         "IMAGE_SIZE_PX", "AVAILABILITY")}
                       for s in c["SHEETS"]],
            "COORDINATE_SPACE": (
                "give every pixel coordinate in the FULL image pixel "
                "space listed as IMAGE_SIZE_PX for that sheet, with "
                "(0,0) at top-left. If your viewer shows you a reduced "
                "copy, scale your readings back up before reporting"),
            "MISSING_DOCUMENT_TYPES": c["MISSING_DOCUMENT_TYPES"],
            "CASE_SOURCE_STATUS": c["CASE_SOURCE_STATUS"],
            "WHAT_THAT_STATUS_MEANS": (
                "one or more document TYPES that this question would "
                "normally rely on are not present anywhere in the drawing "
                "set. You may trace and establish whatever the sheets you "
                "do have genuinely establish. You may not upgrade anything "
                "to ESTABLISHED because a missing document was "
                "unavailable, and you may not substitute a default for it"),
            "NOBODY_HAS_TOLD_YOU_WHAT_THESE_SHEETS_SHOW": (
                "the sheets here were selected as legitimate sources for "
                "this question. No statement has been made about what any "
                "of them contains. Every interpretation is yours to make "
                "from the drawing"),
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # ---- the screen: no pre-read sentence may survive ------------
    leak_sources = []
    for c in req["CASES"]:
        for r in c["SOURCE_REQUIREMENTS"]:
            for k in ("REASON_VISUAL_PREREAD", "REASON_DOCUMENT_GRAPH"):
                if r.get(k):
                    leak_sources.append(r[k])
    forbidden = set()
    for t in leak_sources:
        forbidden |= _shingles(t)
    # plus the descriptive missing-source wording
    for k in MISSING_AS_DOCUMENT_TYPE:
        forbidden |= _shingles(k.replace("_", " "))

    # The QUESTION is an authorised reader-visible input and predates the
    # pre-read, which quoted it back in its reasons. Phrases that come
    # from the question are not leaks, so they are subtracted - otherwise
    # the screen fires on the reader being told what it is being asked.
    authorised = set()
    for q in S.QUESTIONS.values():
        authorised |= _shingles(q)
    for c in cases:
        authorised |= _shingles(c["QUESTION"])
    forbidden -= authorised

    hits = []
    for p in sorted(CASE_BOX.rglob("*")):
        if p.is_file() and p.suffix == ".json":
            got = _shingles(p.read_text("utf-8"))
            for s in sorted(got & forbidden):
                hits.append({"file": str(p.relative_to(CASE_BOX)),
                             "phrase": s})
    if hits:
        raise SystemExit(f"pre-read interpretation leaked to a reader: "
                         f"{hits[:6]}")

    return {
        "CONTROLLER_SOURCE_REQUIREMENTS_SHA256":
            hashlib.sha256(cp.read_bytes()).hexdigest(),
        "A21_READER_SOURCE_MANIFEST_SHA256":
            hashlib.sha256(rp.read_bytes()).hexdigest(),
        "TASK_SHA256": {c["CASE_ID"]: hashlib.sha256(
            (CASE_BOX / c["CASE_ID"] / "TASK.json").read_bytes()).hexdigest()
            for c in cases},
        "PRE_READ_PHRASES_SCREENED": len(forbidden),
        "LEAKS": 0,
    }


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
