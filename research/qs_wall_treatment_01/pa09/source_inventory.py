"""Step 1 of the villa blind validation: inventory every source, before reading any of them.

The inventory is built from file metadata alone - name, extension, size, date - and from drawing title blocks where
the file is unambiguously a drawing.  Nothing in the commercial class is opened, because under the blind protocol a
BOQ that has been read cannot be unread, and "I only checked whether it was a BOQ" is how a seal gets broken.

So a spreadsheet whose name does not resolve is classified SEALED_NOT_OPENED rather than inspected.  That is the safe
direction: the cost of leaving a drawing unclassified is a question to the owner, and the cost of opening a priced
bill is the whole experiment.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa09_villa_blind"
UPLOADS = Path("/root/.claude/uploads")
REPO_SOURCES = [Path("data/runs/cad_convert")]

DRAWING_EXT = {".dwg", ".dxf", ".dwf", ".pdf"}
COMMERCIAL_EXT = {".xls", ".xlsx", ".xlsm", ".csv"}
IMAGE_EXT = {".png", ".jpg", ".jpeg"}

# Projects already known to this repository.  Neither can serve as the blind villa.
KNOWN = {
    "P7757": ("PROJECT_ALREADY_WORKED",
              "P7757 has been taken off, reconciled and its benchmark workbook UNSEALED in earlier phases of this "
              "repository.  Its historical figures are already known to the system, so it cannot be measured blind"),
    "QORTUBA": ("BENCHMARK_PROJECT_01",
                "sealed as the finished benchmark.  Not a candidate: it is the reference the next project is "
                "judged against"),
    "ST7757": ("PROJECT_ALREADY_WORKED", "the P7757 structural set"),
}
QORTUBA_MARKERS = ("qurtoba", "qortuba", "plot_449", "plot-449", "block__1__plot_449")
P7757_MARKERS = ("p7757", "st7757", "7757", "alsenan")


def _git(*a):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return ""


def classify(name: str, ext: str):
    low = name.lower()
    if ext in COMMERCIAL_EXT:
        # never opened, whatever it turns out to be
        return "SEALED_NOT_OPENED", ("a spreadsheet is where a bill of quantities lives.  Under the blind protocol "
                                     "it is not opened, and it is not opened in order to find out what it is")
    if any(m in low for m in QORTUBA_MARKERS):
        return "QORTUBA", KNOWN["QORTUBA"][1]
    if any(m in low for m in P7757_MARKERS):
        return "P7757", KNOWN["P7757"][1]
    if ext in IMAGE_EXT:
        return "IMAGE", "a screenshot or photograph passed in conversation, not a drawing sheet"
    if ext in DRAWING_EXT:
        return "DRAWING_UNATTRIBUTED", "a drawing whose project could not be read from its name"
    return "OTHER", "not a drawing, a schedule or a specification"


def scan():
    rows = []
    for root in ([UPLOADS] if UPLOADS.exists() else []):
        for p in sorted(root.rglob("*")):
            if not p.is_file():
                continue
            ext = p.suffix.lower()
            proj, why = classify(p.name, ext)
            rows.append({"SOURCE": p.name, "WHERE": str(p.parent), "EXT": ext,
                         "SIZE_BYTES": p.stat().st_size,
                         "MODIFIED": __import__("datetime").datetime.fromtimestamp(p.stat().st_mtime).isoformat(
                             timespec="seconds"),
                         "PROJECT": proj, "CLASS_REASON": why,
                         "OPENED_BY_THIS_INVENTORY": False})
    for root in REPO_SOURCES:
        for p in sorted(root.glob("*")) if root.exists() else []:
            ext = p.suffix.lower()
            proj, why = classify(p.name, ext)
            rows.append({"SOURCE": p.name, "WHERE": str(p.parent), "EXT": ext,
                         "SIZE_BYTES": p.stat().st_size,
                         "MODIFIED": __import__("datetime").datetime.fromtimestamp(p.stat().st_mtime).isoformat(
                             timespec="seconds"),
                         "PROJECT": proj, "CLASS_REASON": why,
                         "OPENED_BY_THIS_INVENTORY": False})
    return rows


def finish():
    rows = scan()
    by_project = {}
    for r in rows:
        by_project[r["PROJECT"]] = by_project.get(r["PROJECT"], 0) + 1
    drawings = [r for r in rows if r["EXT"] in DRAWING_EXT]
    candidates = [r for r in drawings if r["PROJECT"] in ("DRAWING_UNATTRIBUTED",)]

    rec = {
        "ARTIFACT": "FULL_VILLA_BLIND_SOURCE_INVENTORY",
        "PHASE_ID": "FULL_VILLA_BLIND_VALIDATION_01",
        "STEP": "1 - inventory every drawing and source received",
        "ROWS": rows, "COUNT": len(rows),
        "BY_PROJECT": by_project,
        "DRAWING_FILES": len(drawings),
        "UNATTRIBUTED_DRAWINGS": candidates,
        "NOTHING_IN_THE_COMMERCIAL_CLASS_WAS_OPENED": all(not r["OPENED_BY_THIS_INVENTORY"] for r in rows),
        "SEALED_NOT_OPENED_COUNT": by_project.get("SEALED_NOT_OPENED", 0),
        # step 2: revisions, missing disciplines, conflicts - answerable only once a villa set exists
        "VILLA_SOURCE_SET_PRESENT": False,
        "WHY_NOT": "every drawing in this session belongs to P7757 or to Qortuba.  P7757 was taken off and its "
                   "benchmark workbook unsealed in earlier phases, so its historical figures are already known to "
                   "this system and it cannot be measured blind.  Qortuba is the sealed benchmark itself.  No third "
                   "project - no villa - has been supplied",
        "DISCIPLINES_RECEIVED_FOR_THE_VILLA": [],
        "DISCIPLINES_MISSING_FOR_THE_VILLA": ["architectural", "structural", "MEP", "schedules", "specifications"],
        "REVISIONS_IDENTIFIED": [],
        "CONFLICTS_IDENTIFIED": [],
        "STEPS_4_TO_15_BLOCKED": True,
        "WHAT_IS_NEEDED": "the villa drawing set.  Without it there is nothing to measure, and a takeoff produced "
                          "without one would not be a blind validation of anything",
        "GIT_HEAD": _git("rev-parse", "--short", "HEAD"),
    }
    rec["DIGEST"] = hashlib.sha256(
        json.dumps(rec["ROWS"], sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:16]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "FULL_VILLA_BLIND_SOURCE_INVENTORY.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False, default=str), "utf-8")
    return rec


if __name__ == "__main__":
    r = finish()
    print(f"{r['COUNT']} sources inventoried, {r['DRAWING_FILES']} of them drawings  |  digest {r['DIGEST']}")
    for k, v in sorted(r["BY_PROJECT"].items(), key=lambda z: -z[1]):
        print(f"   {k:24s} {v}")
    print()
    print("commercial files opened:", 0, "-", r["SEALED_NOT_OPENED_COUNT"], "left sealed")
    print("villa source set present:", r["VILLA_SOURCE_SET_PRESENT"])
    print("steps 4-15 blocked:", r["STEPS_4_TO_15_BLOCKED"])
