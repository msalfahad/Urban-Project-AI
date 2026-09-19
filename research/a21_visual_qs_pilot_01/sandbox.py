"""Build A21's sealed sandbox for the six frozen cases.

The harness knows WHICH room each case is. It tells A21 nothing about WHAT
the room is: no boundary, no polygon, no area, no opening count, no region
assignment. A21 receives drawing sheets, a zoom crop centred on the room's
own printed name, and the rules - and does its own reading.

    python3 -m research.a21_visual_qs_pilot_01.sandbox
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from research.a21_visual_qs_pilot_01 import decisions as D
from research.a21_visual_qs_pilot_01 import protocol as P

OUT = Path("data/experiments/A21_VISUAL_QS_PILOT_01")
BOX = OUT / "a21_sandbox"
PAGES = Path("data/runs/7757/blind/A18-GF-001/images")

SHEETS = {
    1: "GROUND_FLOOR_PLAN", 2: "FIRST_FLOOR_PLAN",
    3: "SECOND_FLOOR_ROOF_PLAN", 4: "SOUTH_EAST_ELEVATION",
    5: "SOUTH_WEST_ELEVATION", 6: "NORTH_WEST_ELEVATION",
    7: "NORTH_EAST_ELEVATION", 8: "SECTION_A_A", 9: "SECTION_B_B",
    10: "FENCE_ELEVATION_AND_SECTION",
}

# Anything with one of these in it must never reach the sandbox.
FORBIDDEN = (
    "E1_4", "E1.4", "BOUNDARY_CHAIN", "PHYSICAL_REGION_KEY",
    "CANDIDATE_ID", "ENCLOSED_BY_DRAWN_MATERIAL", "benchmark", "BENCHMARK",
    "3.20", "3,20", "4.50", "0.90", "SWIMMING POOL IS", "LG-0",
    "target", "TARGET_AREA", "reconciliation", "RECONCILIATION",
)

CROP_HALF_MM = 9000.0


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(path: Path, body) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False,
                               default=str) + "\n", encoding="utf-8")
    return sha(path)


def _mapping():
    """CAD mm -> pixel on the ground-floor sheet, from the frozen
    registration. Used only to PLACE a crop; no geometry is drawn."""
    from tools import run_e1_2 as r12
    from tools import run_e1_3 as r13

    class A:
        decode = "data/runs/cad_convert/P7757_ARCHITECTURAL.json"
        a18_dir = "data/runs/7757/blind/A18-GF-001"
        raster = "data/runs/7757/blind/A18-GF-001/images/page-01.jpeg"
    prep = r12.prepare(A.decode)
    gf = r12.ground_floor(prep)
    reg, sheet = r13._registered_sheet(A(), gf)
    return reg, sheet


def main() -> int:
    if BOX.exists():
        shutil.rmtree(BOX)
    BOX.mkdir(parents=True)

    sel = json.loads((OUT / "PILOT_CASE_SELECTION.json").read_text("utf-8"))
    room_cases = [c for c in sel["ROOM_CASES"] if c.get("CANDIDATE_ID")]
    seeds = {}
    ch = json.loads(Path("data/runs/7757/e1_4/"
                         "E1_4_PHYSICAL_BOUNDARY_CHAIN_REGISTER.json")
                    .read_text("utf-8"))
    for c in ch["CANDIDATES"]:
        seeds[c["CANDIDATE_ID"]] = c.get("SEED_MM")

    reg, sheet = _mapping()
    from PIL import Image

    def crop_for(seed, page=1, half=CROP_HALF_MM):
        img = Image.open(PAGES / f"page-{page:02d}.jpeg").convert("RGB")
        # registration runs at a working resolution; scale its pixels up
        # to the full page before cropping
        k = img.width / float(reg.image_px[0]) if reg.image_px else 1.0
        x0, y0 = [v * k for v in reg.to_px(seed[0] - half, seed[1] + half)]
        x1, y1 = [v * k for v in reg.to_px(seed[0] + half, seed[1] - half)]
        bx = (max(0, int(min(x0, x1))), max(0, int(min(y0, y1))),
              min(img.width, int(max(x0, x1))),
              min(img.height, int(max(y0, y1))))
        return img.crop(bx), bx

    cases, manifest = [], []
    # ---- the three room cases ------------------------------------
    for c in room_cases:
        cid = c["CASE_ID"]
        d = BOX / cid
        d.mkdir(parents=True)
        seed = seeds[c["CANDIDATE_ID"]]
        subject = str(c.get("IDENTITY_AS_DRAWN") or "").strip()
        im, bx = crop_for(seed)
        im.save(d / "PLAN_ZOOM.jpeg", quality=92)
        shutil.copy(PAGES / "page-01.jpeg", d / "GROUND_FLOOR_PLAN.jpeg")
        sources = ["GROUND_FLOOR_PLAN.jpeg", "PLAN_ZOOM.jpeg"]
        for pg in (8, 9):
            shutil.copy(PAGES / f"page-{pg:02d}.jpeg", d / f"{SHEETS[pg]}.jpeg")
            sources.append(f"{SHEETS[pg]}.jpeg")
        task = {
            "CASE_ID": cid,
            "WHAT_YOU_ARE_MEASURING": c["WHAT_IT_TESTS"],
            # The crop is a convenience, not the instruction: the plan is
            # rotated on the sheet and the subject is not reliably centred.
            # Naming the room leaks nothing - the name is printed on the
            # drawing - and it stops A21 measuring a neighbour by mistake.
            "THE_SUBJECT": (
                f"the room labelled {subject} on the ground floor plan. "
                "Find it yourself on the sheet; PLAN_ZOOM.jpeg is a "
                "convenience crop of that part of the plan and the room "
                "is NOT necessarily at its centre"),
            "THE_NAME_IS_ALL_YOU_HAVE_BEEN_GIVEN": (
                "you have been told which room to measure and nothing "
                "else about it: no area, no dimensions, no wall count, no "
                "opening count and no height"),
            "SOURCES": sources,
            "WHY_THE_SECTIONS_ARE_HERE": (
                "SECTION_A_A and SECTION_B_B are provided so you can "
                "attempt to establish a height. They may or may not "
                "settle it"),
            "NO_ONE_HAS_TOLD_YOU_THE_ANSWER": (
                "no area, no quantity, no room polygon, no opening count "
                "and no height figure has been supplied. Everything you "
                "report must come from these images or from the rules"),
        }
        write(d / "TASK.json", task)
        cases.append(cid)
        manifest.append({"CASE_ID": cid, "SOURCES": sources,
                         "crop_box_px": list(bx),
                         "SHA256": {s: sha(d / s) for s in sources}})

    # ---- case 4: the stair ---------------------------------------
    d = BOX / "CASE-4-STAIR"
    d.mkdir(parents=True)
    src4 = []
    for pg in (1, 8, 9):
        shutil.copy(PAGES / f"page-{pg:02d}.jpeg", d / f"{SHEETS[pg]}.jpeg")
        src4.append(f"{SHEETS[pg]}.jpeg")
    write(d / "TASK.json", {
        "CASE_ID": "CASE-4-STAIR",
        "WHAT_YOU_ARE_MEASURING": (
            "the stair rising from the ground floor: its adjacent wall "
            "surfaces, and separately its underside"),
        "THE_SUBJECT": "find the stair on the ground floor plan yourself",
        "SOURCES": src4,
        "KEEP_THEM_APART": (
            "STAIR_WALL_PLASTER and STAIR_UNDERSIDE_TREATMENT are "
            "different items and are never combined"),
        "IF_THE_GEOMETRY_IS_INSUFFICIENT": (
            "return STAIR_GEOMETRY_REQUIRED rather than approximating a "
            "slope"),
    })
    cases.append("CASE-4-STAIR")
    manifest.append({"CASE_ID": "CASE-4-STAIR", "SOURCES": src4,
                     "SHA256": {s: sha(d / s) for s in src4}})

    # ---- case 5: the facade --------------------------------------
    d = BOX / "CASE-5-EXTERNAL-FACADE"
    d.mkdir(parents=True)
    src5 = []
    for pg in (4, 1, 8):
        shutil.copy(PAGES / f"page-{pg:02d}.jpeg", d / f"{SHEETS[pg]}.jpeg")
        src5.append(f"{SHEETS[pg]}.jpeg")
    write(d / "TASK.json", {
        "CASE_ID": "CASE-5-EXTERNAL-FACADE",
        "WHAT_YOU_ARE_MEASURING": (
            "external plaster on ONE facade, for the GROUND FLOOR only"),
        "THE_SUBJECT": "the elevation sheet supplied here",
        "SOURCES": src5,
        "FLOOR_BY_FLOOR": (
            "each floor owns its own exterior envelope. Do not infer an "
            "upper floor's wall lengths from the ground floor, and do not "
            "multiply a whole-house perimeter by a whole-house height"),
        "ALSO_REPORT": (
            "candidate control or movement joint locations you can SEE. "
            "Required spacing must come from a drawing, a specification "
            "or a rule - never from you"),
    })
    cases.append("CASE-5-EXTERNAL-FACADE")
    manifest.append({"CASE_ID": "CASE-5-EXTERNAL-FACADE", "SOURCES": src5,
                     "SHA256": {s: sha(d / s) for s in src5}})

    # ---- case 6: the parapet -------------------------------------
    d = BOX / "CASE-6-ROOF-PARAPET"
    d.mkdir(parents=True)
    src6 = []
    for pg in (3, 4, 8):
        shutil.copy(PAGES / f"page-{pg:02d}.jpeg", d / f"{SHEETS[pg]}.jpeg")
        src6.append(f"{SHEETS[pg]}.jpeg")
    write(d / "TASK.json", {
        "CASE_ID": "CASE-6-ROOF-PARAPET",
        "WHAT_YOU_ARE_MEASURING": (
            "the roof parapet on the SAME facade as CASE-5: its external "
            "face, its internal roof-side face, and its capping"),
        "THE_SUBJECT": "the parapet, as the drawing shows it",
        "SOURCES": src6,
        "INSPECT_THE_DRAWING_FIRST": (
            "establish the parapet height from the drawing if you can. If "
            "you cannot, say so - do not assume a course count or a "
            "capping thickness"),
        "DO_NOT_DOUBLE_COUNT_CORNERS": True,
    })
    cases.append("CASE-6-ROOF-PARAPET")
    manifest.append({"CASE_ID": "CASE-6-ROOF-PARAPET", "SOURCES": src6,
                     "SHA256": {s: sha(d / s) for s in src6}})

    # ---- leak screen ---------------------------------------------
    leaks = []
    for p in sorted(BOX.rglob("*")):
        if p.is_file() and p.suffix in (".json", ".txt"):
            t = p.read_text("utf-8", errors="replace")
            for bad in FORBIDDEN:
                if bad in t:
                    leaks.append({"file": str(p.relative_to(BOX)),
                                  "carries": bad})
    if leaks:
        raise SystemExit(f"the A21 sandbox is not blind: {leaks[:5]}")

    man_hash = write(OUT / "A21_INPUT_MANIFEST.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "SELECTION_RULE_HASH": D.APPROVED_SELECTION_RULE_HASH,
        "DECISIONS_HASH": D.decisions_hash(),
        "the_selection_harness_is_not_the_observation_input":
            D.THE_SELECTION_HARNESS_IS_NOT_THE_OBSERVATION_INPUT,
        "A21_MAY_RECEIVE": list(D.A21_MAY_RECEIVE),
        "A21_MAY_NOT_RECEIVE": list(D.A21_MAY_NOT_RECEIVE),
        "WITHHELD_FROM_A21": list(D.WITHHELD_FROM_A21),
        "why_they_are_withheld": D.WHY_THEY_ARE_WITHHELD,
        "SHEET_ROLES": {str(k): v for k, v in SHEETS.items()},
        "THE_SANDBOX_WAS_SCREENED_FOR": list(FORBIDDEN),
        "NOTHING_FORBIDDEN_WAS_FOUND": True,
        "cases": len(cases),
        "CASES": manifest,
    })
    print(json.dumps({"cases": len(cases), "CASE_IDS": cases,
                      "leaks": 0, "A21_INPUT_MANIFEST_SHA256": man_hash},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
