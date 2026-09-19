"""PART A - the pre-read source-sufficiency stage.

Two stages, in this order, and never the other way round:

  1  a sealed PRE-READ reader is shown the sheet INDEX - every sheet in
     the set, and the measurement question - and declares which sheets
     the question requires. It sees no result, no quantity, no benchmark
     and no prior answer.
  2  the measuring sandbox is built FROM that frozen declaration and
     contains nothing else. A reader cannot wander into another case's
     directory because no undeclared file is mounted anywhere.

If a required source does not exist in the set, the case fails here with
SOURCE_SET_INCOMPLETE - before any measuring reader is started.

    python3 -m research.a21_trace_sufficiency_01.source_sufficiency index
    python3 -m research.a21_trace_sufficiency_01.source_sufficiency build
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

from research.a21_trace_sufficiency_01 import protocol as P

PAGES = Path("data/runs/7757/blind/A18-GF-001/images")
OUT = Path("data/experiments/A21_TRACE_SUFFICIENCY_01")
INDEX_BOX = OUT / "preread_index"
CASE_BOX = OUT / "case_sandbox"

SHEETS = {
    1: "GROUND_FLOOR_PLAN", 2: "FIRST_FLOOR_PLAN",
    3: "SECOND_FLOOR_ROOF_PLAN", 4: "SOUTH_EAST_ELEVATION",
    5: "SOUTH_WEST_ELEVATION", 6: "NORTH_WEST_ELEVATION",
    7: "NORTH_EAST_ELEVATION", 8: "SECTION_A_A", 9: "SECTION_B_B",
    10: "FENCE_ELEVATION_AND_SECTION",
}

# Every one of the ten pages was rendered at +90 CCW and inspected before
# this stage ran. All ten need it; none was assumed from the others.
VERIFIED_ROTATION_CCW = {pg: 90 for pg in SHEETS}
ROTATION_EVIDENCE = (
    "pages 1, 3, 4, 8 and 9 were inspected individually during the "
    "presentation experiment; pages 2, 5, 6, 7 and 10 were inspected here "
    "before the index was built. In every case the Arabic title block, "
    "the English sheet title and the dimension figures read upright")

RUNTIME_LONG_EDGE_CAP_PX = 2000
INK_MARGIN_PX = 280
INK_THRESHOLD = 160

# Nothing carrying a result, a quantity or a prior answer may exist in
# the pre-read directory. The pre-read decides what is NEEDED, not what
# anything measures.
FORBIDDEN = (
    "E1_4", "E1.4", "benchmark", "BENCHMARK", "PLASTER_HEIGHT",
    "NOT_ESTABLISHED", "A21_reader", "IMP_PASS", "a21_raw", "improved_raw",
    "3.20", "3,20", "reconciliation", "RECONCILIATION", "QUANTITY",
    "m2", "TARTUSHA",
)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _content_box(img: Image.Image):
    import numpy as np
    a = np.asarray(img.convert("L"))
    ink = a < INK_THRESHOLD
    m = INK_MARGIN_PX
    sub = ink[m:a.shape[0] - m, m:a.shape[1] - m]
    rows = np.where(sub.sum(1) > max(6, int(0.002 * sub.shape[1])))[0]
    cols = np.where(sub.sum(0) > max(6, int(0.002 * sub.shape[0])))[0]
    pad = 40
    return (max(0, int(cols.min()) + m - pad), max(0, int(rows.min()) + m - pad),
            min(img.width, int(cols.max()) + m + pad),
            min(img.height, int(rows.max()) + m + pad))


def prepare(pg: int):
    """Rotate, trim, reduce once. Returns (image, full-rotated, record)."""
    src = PAGES / f"page-{pg:02d}.jpeg"
    img = Image.open(src).convert("RGB")
    w0, h0 = img.size
    rot = img.transpose(Image.ROTATE_90)
    box = _content_box(rot)
    trimmed = rot.crop(box)
    k = min(1.0, RUNTIME_LONG_EDGE_CAP_PX / float(max(trimmed.size)))
    out = trimmed if k == 1.0 else trimmed.resize(
        (max(1, round(trimmed.width * k)), max(1, round(trimmed.height * k))),
        Image.LANCZOS)
    rec = {
        "SHEET_ID": SHEETS[pg],
        "ORIGINAL_PAGE_ID": f"page-{pg:02d}.jpeg",
        "ORIGINAL_PDF_PAGE": pg,
        "ORIGINAL_HASH": sha(src),
        "ORIGINAL_SIZE_PX": [w0, h0],
        "ROTATION_DEGREES": VERIFIED_ROTATION_CCW[pg],
        "ROTATION_SENSE": "COUNTER_CLOCKWISE",
        "TRIM_BOX_IN_ROTATED_PX": list(box),
        "SCALE_AFTER_TRIM": round(k, 8),
        "FINAL_SIZE_PX": list(out.size),
        "SOURCE_COORDINATE_SYSTEM": "PROCESSED_SHEET_PX",
        "ORIGINAL_PAGE_COORDINATE_TRANSFORM": {
            "FORWARD": ("x_rot = y_orig ; y_rot = (W_orig - 1) - x_orig ; "
                        "x_out = (x_rot - trim_x0) * scale ; "
                        "y_out = (y_rot - trim_y0) * scale"),
            "INVERSE": ("x_rot = x_out / scale + trim_x0 ; "
                        "y_rot = y_out / scale + trim_y0 ; "
                        "x_orig = (W_orig - 1) - y_rot ; y_orig = x_rot"),
            "W_orig": w0, "H_orig": h0,
            "trim_x0": box[0], "trim_y0": box[1], "scale": k,
        },
    }
    return out, rot, rec


QUESTIONS = {
    "CASE-1-NORMAL-PLASTER":
        "What is the wall area to receive normal internal plaster in the "
        "room labelled RECEPTION on the ground floor?",
    "CASE-3-DOOR-AND-WINDOW":
        "What are the door and window deductions, the reveal returns and "
        "the edge profiles for the room labelled SALOON on the ground "
        "floor?",
    "CASE-4-STAIR":
        "What are the wall surfaces alongside the stair rising from the "
        "ground floor, and separately the area of its underside?",
    "CASE-6-ROOF-PARAPET":
        "What are the external face, the roof-side face and the capping "
        "of the roof parapet on the south-east facade?",
}


def build_index() -> dict:
    """Stage 1 input: the whole sheet set, and the questions. Nothing else."""
    if INDEX_BOX.exists():
        shutil.rmtree(INDEX_BOX)
    INDEX_BOX.mkdir(parents=True)
    records, files = {}, {}
    for pg in sorted(SHEETS):
        img, _, rec = prepare(pg)
        name = f"{SHEETS[pg]}.jpeg"
        img.save(INDEX_BOX / name, quality=95, subsampling=0)
        rec["PREPARED_FILE"] = name
        rec["SOURCE_PRESENTATION_HASH"] = sha(INDEX_BOX / name)
        records[SHEETS[pg]] = rec
        files[name] = rec["SOURCE_PRESENTATION_HASH"]

    (INDEX_BOX / "QUESTIONS.json").write_text(json.dumps({
        "WHAT_YOU_ARE_DOING": (
            "deciding WHICH SHEETS each question needs. You are not "
            "measuring anything and you must not attempt to"),
        "QUESTIONS": QUESTIONS,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    leaks = [b for p in INDEX_BOX.glob("*.json")
             for b in FORBIDDEN if b in p.read_text("utf-8")]
    if leaks:
        raise SystemExit(f"the pre-read index is not clean: {leaks[:5]}")

    body = {
        "PHASE_ID": P.PHASE_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "ARTIFACT": "SHEET_INDEX",
        "WHY_IT_IS_A_READER_AND_NOT_CODE": P.WHY_IT_IS_A_READER_AND_NOT_CODE,
        "PRE_READ_MAY_INSPECT": list(P.PRE_READ_MAY_INSPECT),
        "PRE_READ_MUST_NOT_INSPECT": list(P.PRE_READ_MUST_NOT_INSPECT),
        "ROTATION_EVIDENCE": ROTATION_EVIDENCE,
        "SHEETS": records,
        "QUESTIONS": QUESTIONS,
        "SCREENED_FOR": list(FORBIDDEN),
        "NOTHING_FORBIDDEN_WAS_FOUND": True,
    }
    p = OUT / "SHEET_INDEX.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    return {"sheets": len(records), "SHEET_INDEX_SHA256": sha(p),
            "files": files}


def build_case_sandboxes() -> dict:
    """Stage 2: mount ONLY what the frozen requirement list declares."""
    req_path = OUT / "CASE_SOURCE_REQUIREMENTS.json"
    if not req_path.exists():
        raise SystemExit("CASE_SOURCE_REQUIREMENTS is not frozen yet")
    req = json.loads(req_path.read_text("utf-8"))
    index = json.loads((OUT / "SHEET_INDEX.json").read_text("utf-8"))

    if CASE_BOX.exists():
        shutil.rmtree(CASE_BOX)
    CASE_BOX.mkdir(parents=True)

    manifests, failed = [], []
    for c in req["CASES"]:
        cid = c["CASE_ID"]
        declared = ([c["PRIMARY_PLAN"]] + list(c.get("REQUIRED_SECTIONS") or [])
                    + list(c.get("REQUIRED_ELEVATIONS") or [])
                    + list(c.get("REQUIRED_DETAILS") or [])
                    + list(c.get("OPTIONAL_CONTEXT") or []))
        declared = [s for s in declared if s]
        missing = [s for s in declared if s not in index["SHEETS"]]
        unavailable = list(c.get("MISSING_SOURCE") or [])
        if missing:
            failed.append({"CASE_ID": cid, "DECLARED_BUT_NOT_IN_SET": missing,
                           "STATUS": "SOURCE_SET_INCOMPLETE"})
            continue
        d = CASE_BOX / cid
        d.mkdir(parents=True)
        mounted = {}
        for s in dict.fromkeys(declared):
            name = f"{s}.jpeg"
            shutil.copy(INDEX_BOX / name, d / name)
            mounted[name] = sha(d / name)
        (d / "TASK.json").write_text(json.dumps({
            "CASE_ID": cid,
            "QUESTION": c["QUESTION"],
            "SOURCES": sorted(mounted),
            "WHY_EACH_SOURCE_IS_HERE": c.get("WHY_EACH_SOURCE_IS_REQUIRED"),
            "SOURCES_KNOWN_TO_BE_MISSING_FROM_THE_DRAWING_SET": unavailable,
            "THIS_PACKET_WAS_DECLARED_BEFORE_ANY_MEASURING_BEGAN": (
                "a pre-read stage decided which sheets this question needs "
                "and this directory contains exactly those. If something "
                "you need is genuinely absent, say so with a REQUIRED code "
                "- do not look for it elsewhere, because nothing else is "
                "mounted"),
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        manifests.append({
            "CASE_ID": cid,
            "QUESTION": c["QUESTION"],
            "MOUNTED": mounted,
            "MOUNTED_COUNT": len(mounted),
            "DECLARED_MISSING_FROM_THE_SET": unavailable,
            "STATUS": ("SOURCE_SET_INCOMPLETE_BUT_RUNNABLE" if unavailable
                       else "SOURCE_SET_COMPLETE"),
            "TASK_SHA256": sha(d / "TASK.json"),
        })

    body = {
        "PHASE_ID": P.PHASE_ID,
        "ARTIFACT": "CASE_SANDBOX_MANIFESTS",
        "THE_SANDBOX_RULE": P.THE_SANDBOX_RULE,
        "BUILT_FROM": "CASE_SOURCE_REQUIREMENTS.json",
        "CASE_SOURCE_REQUIREMENTS_SHA256": sha(req_path),
        "SHEET_INDEX_SHA256": sha(OUT / "SHEET_INDEX.json"),
        "CASES": manifests,
        "FAILED_BEFORE_ANY_READER": failed,
        "NO_UNDECLARED_FILE_IS_MOUNTED_ANYWHERE": True,
    }
    p = OUT / "CASE_SANDBOX_MANIFESTS.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    return {"cases": len(manifests), "failed": len(failed),
            "SHA256": sha(p),
            "MOUNTED": {m["CASE_ID"]: m["MOUNTED_COUNT"] for m in manifests}}


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "index"
    print(json.dumps(build_index() if what == "index"
                     else build_case_sandboxes(), indent=2))
