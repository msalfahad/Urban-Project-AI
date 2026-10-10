"""Build the IMPROVED source packets for A21.

Same six cases, same rules, same seeds. What changes is how the drawing
reaches the reader:

  * rotated to the orientation verified for THAT page, never assumed
  * trimmed mechanically to drawn content - blank paper carries nothing
  * reduced here, with LANCZOS, to the runtime's own ceiling, so the
    image is not downscaled twice by two different resamplers
  * a NATIVE-resolution lossless detail crop for the cases that have a
    seed point predating this run

Sections and elevations are supplied WHOLE. I have read the baseline, so
I know where the height evidence sits; narrowing a section towards it
would be feeding a result back as a pointer, not improving presentation.

    python3 -m research.a21_visual_qs_pilot_01.improved_sandbox
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image

from research.a21_visual_qs_pilot_01 import decisions as D
from research.a21_visual_qs_pilot_01 import improved_protocol as IP
from research.a21_visual_qs_pilot_01 import protocol as P
from research.a21_visual_qs_pilot_01.sandbox import (
    FORBIDDEN, PAGES, SHEETS, sha, write, _mapping)

OUT = Path("data/experiments/A21_VISUAL_QS_PILOT_01")
BOX = OUT / "a21_sandbox_improved"

# ------------------------------------------------------------------
# rotation, verified page by page by looking at each one
# ------------------------------------------------------------------
# Every page was rendered at +90 CCW and inspected: title block, room
# names, dimension figures and the drawing title all read naturally.
# Recorded per page rather than as one blanket value, because a wrong
# rotation measured WORSE than no rotation.
VERIFIED_ROTATION_CCW = {
    1: 90, 3: 90, 4: 90, 8: 90, 9: 90,
}
ROTATION_EVIDENCE = (
    "each page rendered at +90 CCW and visually inspected before any "
    "reader ran: the Arabic title block, the English sheet title, the "
    "room labels and the dimension figures all read upright")

# drawn-content box inside the sheet frame, measured mechanically from
# the ink profile (see the commit message). Not chosen by eye.
INK_MARGIN_PX = 280
INK_THRESHOLD = 160


def content_box(img: Image.Image) -> tuple:
    """The drawn content, found by ink profile. Nothing is selected."""
    import numpy as np
    a = np.asarray(img.convert("L"))
    ink = a < INK_THRESHOLD
    m = INK_MARGIN_PX
    sub = ink[m:a.shape[0] - m, m:a.shape[1] - m]
    rt = max(6, int(0.002 * sub.shape[1]))
    ct = max(6, int(0.002 * sub.shape[0]))
    rows = np.where(sub.sum(1) > rt)[0]
    cols = np.where(sub.sum(0) > ct)[0]
    pad = 40
    return (max(0, int(cols.min()) + m - pad),
            max(0, int(rows.min()) + m - pad),
            min(img.width, int(cols.max()) + m + pad),
            min(img.height, int(rows.max()) + m + pad))


def prepared_sheet(pg: int):
    """Rotate, trim to content, reduce once with LANCZOS. Records how."""
    src = PAGES / f"page-{pg:02d}.jpeg"
    img = Image.open(src).convert("RGB")
    w0, h0 = img.size
    deg = VERIFIED_ROTATION_CCW[pg]
    assert deg == 90, "only the verified 90 CCW transform is implemented"
    rot = img.transpose(Image.ROTATE_90)          # lossless 90 CCW
    box = content_box(rot)
    trimmed = rot.crop(box)
    long_edge = max(trimmed.size)
    k = min(1.0, IP.RUNTIME_LONG_EDGE_CAP_PX / float(long_edge))
    out = (trimmed if k == 1.0 else trimmed.resize(
        (max(1, round(trimmed.width * k)), max(1, round(trimmed.height * k))),
        Image.LANCZOS))
    record = {
        "ORIGINAL_PAGE_ID": f"page-{pg:02d}.jpeg",
        "ORIGINAL_HASH": sha(src),
        "ORIGINAL_SIZE_PX": [w0, h0],
        "ROTATION_DEGREES": deg,
        "ROTATION_SENSE": "COUNTER_CLOCKWISE",
        "ROTATION_IS_LOSSLESS_TRANSPOSE": True,
        "CONTENT_TRIM_BOX_IN_ROTATED_PX": list(box),
        "SCALE_AFTER_TRIM": round(k, 6),
        "FINAL_SIZE_PX": list(out.size),
        "ASPECT_RATIO_PRESERVED": True,
        # original (x, y) -> rotated (y, w0 - 1 - x) -> minus trim origin
        # -> times SCALE_AFTER_TRIM
        "COORDINATE_TRANSFORM": (
            "x_rot = y_orig ; y_rot = (W_orig - 1) - x_orig ; "
            "x_out = (x_rot - trim_x0) * SCALE_AFTER_TRIM ; "
            "y_out = (y_rot - trim_y0) * SCALE_AFTER_TRIM"),
        "EFFECTIVE_SCALE_VS_BASELINE": round(
            k / (IP.RUNTIME_LONG_EDGE_CAP_PX / float(max(w0, h0))), 3),
    }
    return out, rot, box, record


def detail_crop(rot: Image.Image, box, reg, seed, page_w0: int):
    """Native-pixel crop, sized in metres of building, on the rotated sheet."""
    half_mm = IP.DETAIL_CROP_METRES * 1000.0 / 2.0
    # seed -> original page px (registration runs at a working resolution)
    k = page_w0 / float(reg.image_px[0]) if reg.image_px else 1.0
    pts = [reg.to_px(seed[0] + dx, seed[1] + dy)
           for dx, dy in ((-half_mm, half_mm), (half_mm, -half_mm))]
    xs = [p[0] * k for p in pts]
    ys = [p[1] * k for p in pts]
    # same transform the record declares
    rx = [y for y in ys]
    ry = [(page_w0 - 1) - x for x in xs]
    cb = (max(0, int(min(rx))), max(0, int(min(ry))),
          min(rot.width, int(max(rx))), min(rot.height, int(max(ry))))
    return rot.crop(cb), cb


def main() -> int:
    IP.assert_baseline_intact()
    if BOX.exists():
        shutil.rmtree(BOX)
    BOX.mkdir(parents=True)

    sel = json.loads((OUT / "PILOT_CASE_SELECTION.json").read_text("utf-8"))
    room_cases = [c for c in sel["ROOM_CASES"] if c.get("CANDIDATE_ID")]
    ch = json.loads(Path("data/runs/7757/e1_4/"
                         "E1_4_PHYSICAL_BOUNDARY_CHAIN_REGISTER.json")
                    .read_text("utf-8"))
    seeds = {c["CANDIDATE_ID"]: c.get("SEED_MM") for c in ch["CANDIDATES"]}
    reg, _ = _mapping()

    prepared, rotations = {}, {}
    for pg in sorted(VERIFIED_ROTATION_CCW):
        out, rot, box, rec = prepared_sheet(pg)
        prepared[pg] = (out, rot, box)
        rotations[SHEETS[pg]] = rec

    def put(d: Path, pg: int) -> str:
        name = f"{SHEETS[pg]}.jpeg"
        prepared[pg][0].save(d / name, quality=95, subsampling=0)
        return name

    # the packets. SOURCES mirror the baseline exactly, except CASE-6,
    # which gains SECTION_B_B as the recorded packet correction.
    PACKETS = {
        "CASE-1-NORMAL-PLASTER": (1, (8, 9)),
        "CASE-2-TILE-PREP": (1, (8, 9)),
        "CASE-3-DOOR-AND-WINDOW": (1, (8, 9)),
        "CASE-4-STAIR": (1, (8, 9)),
        "CASE-5-EXTERNAL-FACADE": (4, (1, 8)),
        "CASE-6-ROOF-PARAPET": (3, (4, 8, 9)),
    }

    base_tasks = {c["CASE_ID"]: c for c in room_cases}
    manifest, cases = [], []

    for cid, (primary, cross) in PACKETS.items():
        d = BOX / cid
        d.mkdir(parents=True)
        sources = [put(d, primary)]
        detail = None
        if cid in base_tasks:
            seed = seeds[base_tasks[cid]["CANDIDATE_ID"]]
            _, rot, _ = prepared[primary]
            im, cb = detail_crop(rot, None, reg, seed, 4672)
            im.save(d / "PLAN_DETAIL.png")          # lossless, native px
            sources.append("PLAN_DETAIL.png")
            detail = {"NATIVE_PIXELS": True, "LOSSLESS": True,
                      "METRES_ACROSS": IP.DETAIL_CROP_METRES,
                      "CROP_BOX_IN_ROTATED_PX": list(cb),
                      "SIZE_PX": list(im.size)}
        for pg in cross:
            sources.append(put(d, pg))

        # TASK.json: baseline text, carried across, plus the packet note
        if cid in base_tasks:
            c = base_tasks[cid]
            subject = str(c.get("IDENTITY_AS_DRAWN") or "").strip()
            task = {
                "CASE_ID": cid,
                "WHAT_YOU_ARE_MEASURING": c["WHAT_IT_TESTS"],
                "THE_SUBJECT": (
                    f"the room labelled {subject} on the ground floor "
                    "plan. Find it yourself on the sheet; PLAN_DETAIL.png "
                    "is a convenience crop of that part of the plan and "
                    "the room is NOT necessarily at its centre"),
                "THE_NAME_IS_ALL_YOU_HAVE_BEEN_GIVEN": (
                    "you have been told which room to measure and nothing "
                    "else about it: no area, no dimensions, no wall "
                    "count, no opening count and no height"),
                "SOURCES": sources,
                "WHY_THE_SECTIONS_ARE_HERE": (
                    "SECTION_A_A and SECTION_B_B are provided so you can "
                    "attempt to establish a height. They may or may not "
                    "settle it"),
                "NO_ONE_HAS_TOLD_YOU_THE_ANSWER": (
                    "no area, no quantity, no room polygon, no opening "
                    "count and no height figure has been supplied. "
                    "Everything you report must come from these images "
                    "or from the rules"),
            }
        elif cid == "CASE-4-STAIR":
            task = {
                "CASE_ID": cid,
                "WHAT_YOU_ARE_MEASURING": (
                    "the stair rising from the ground floor: its adjacent "
                    "wall surfaces, and separately its underside"),
                "THE_SUBJECT": "find the stair on the ground floor plan "
                               "yourself",
                "SOURCES": sources,
                "KEEP_THEM_APART": (
                    "STAIR_WALL_PLASTER and STAIR_UNDERSIDE_TREATMENT are "
                    "different items and are never combined"),
                "IF_THE_GEOMETRY_IS_INSUFFICIENT": (
                    "return STAIR_GEOMETRY_REQUIRED rather than "
                    "approximating a slope"),
            }
        elif cid == "CASE-5-EXTERNAL-FACADE":
            task = {
                "CASE_ID": cid,
                "WHAT_YOU_ARE_MEASURING": (
                    "external plaster on ONE facade, for the GROUND FLOOR "
                    "only"),
                "THE_SUBJECT": "the elevation sheet supplied here",
                "SOURCES": sources,
                "FLOOR_BY_FLOOR": (
                    "each floor owns its own exterior envelope. Do not "
                    "infer an upper floor's wall lengths from the ground "
                    "floor, and do not multiply a whole-house perimeter "
                    "by a whole-house height"),
                "ALSO_REPORT": (
                    "candidate control or movement joint locations you "
                    "can SEE. Required spacing must come from a drawing, "
                    "a specification or a rule - never from you"),
            }
        else:
            task = {
                "CASE_ID": cid,
                "WHAT_YOU_ARE_MEASURING": (
                    "the roof parapet on the SAME facade as CASE-5: its "
                    "external face, its internal roof-side face, and its "
                    "capping"),
                "THE_SUBJECT": "the parapet, as the drawing shows it",
                "SOURCES": sources,
                "INSPECT_THE_DRAWING_FIRST": (
                    "establish the parapet height from the drawing if you "
                    "can. If you cannot, say so - do not assume a course "
                    "count or a capping thickness"),
                "DO_NOT_DOUBLE_COUNT_CORNERS": True,
            }

        task["HOW_THESE_IMAGES_WERE_PREPARED"] = (
            "every sheet has been rotated to its natural reading "
            "orientation and trimmed to the drawn area. A .png is a "
            "full-resolution detail crop; a .jpeg is a whole sheet. "
            "Nothing has been added to, removed from or marked on any "
            "drawing")
        write(d / "TASK.json", task)

        cases.append(cid)
        manifest.append({
            "CASE_ID": cid,
            "PRIMARY_SHEET": SHEETS[primary],
            "CROSS_SHEET": [SHEETS[p] for p in cross],
            "SOURCES": sources,
            "LEVEL_2_DETAIL": detail,
            "COMPARABILITY": (IP.CASE_6_CLASSIFICATION
                              if cid == "CASE-6-ROOF-PARAPET"
                              else IP.CASES_1_TO_5_CLASSIFICATION),
            "SHA256": {s: sha(d / s) for s in sources},
        })

    # ---- screens -------------------------------------------------
    leaks = []
    for p in sorted(BOX.rglob("*")):
        if p.is_file() and p.suffix in (".json", ".txt"):
            t = p.read_text("utf-8", errors="replace")
            for bad in tuple(FORBIDDEN) + tuple(IP.FEEDBACK_SCREEN):
                if bad in t:
                    leaks.append({"file": str(p.relative_to(BOX)),
                                  "carries": bad})
    if leaks:
        raise SystemExit(f"the improved sandbox is not blind: {leaks[:5]}")

    man_hash = write(OUT / "IMPROVED_INPUT_MANIFEST.json", {
        "EXPERIMENT_ID": IP.EXPERIMENT_ID,
        "RUN_ID": IP.RUN_ID,
        "IMPROVED_PROTOCOL_HASH": IP.protocol_hash(),
        "APPROVED_PROTOCOL_HASH": P.protocol_hash(),
        "SELECTION_RULE_HASH": D.APPROVED_SELECTION_RULE_HASH,
        "DECISIONS_HASH": D.decisions_hash(),
        "BASELINE_RUN_ID": IP.BASELINE_RUN_ID,
        "BASELINE_IS_UNTOUCHED": True,
        "THE_ONE_VARIABLE": "source presentation",
        "PACKET_LEVELS": {k: v for k, v in IP.PACKET_LEVELS},
        "ROTATION_RULE": IP.ROTATION_RULE,
        "ROTATION_EVIDENCE": ROTATION_EVIDENCE,
        "ROTATION_RECORDS": rotations,
        "RESOLUTION_RULES": list(IP.RESOLUTION_RULES),
        "CROSS_SHEET_SOURCES_ARE_NEVER_CROPPED_SELECTIVELY":
            IP.CROSS_SHEET_SOURCES_ARE_NEVER_CROPPED_SELECTIVELY,
        "NO_SELECTIVE_DETAIL_CROP_FOR": list(IP.NO_SELECTIVE_DETAIL_CROP_FOR),
        "WHY_NOT_FOR_THOSE_THREE": IP.WHY_NOT_FOR_THOSE_THREE,
        "CASE_PACKET_CORRECTION": IP.CASE_PACKET_CORRECTION,
        "CASE_6_IS_NOT_A_ONE_VARIABLE_COMPARISON":
            IP.CASE_6_IS_NOT_A_ONE_VARIABLE_COMPARISON,
        "UNCHANGED_FROM_BASELINE": list(IP.UNCHANGED_FROM_BASELINE),
        "WITHHELD_FROM_A21": list(D.WITHHELD_FROM_A21),
        "SCREENED_FOR": list(FORBIDDEN) + list(IP.FEEDBACK_SCREEN),
        "NOTHING_FORBIDDEN_WAS_FOUND": True,
        "NO_BASELINE_RESULT_REACHED_A_READER_VISIBLE_FILE": True,
        "cases": len(cases),
        "CASES": manifest,
    })

    print(json.dumps({
        "cases": len(cases),
        "leaks": 0,
        "IMPROVED_INPUT_MANIFEST_SHA256": man_hash,
        "IMPROVED_PROTOCOL_HASH": IP.protocol_hash(),
        "EFFECTIVE_SCALE_VS_BASELINE": {
            k: v["EFFECTIVE_SCALE_VS_BASELINE"] for k, v in rotations.items()},
        "DETAIL_CROPS": {m["CASE_ID"]: (m["LEVEL_2_DETAIL"] or {}).get("SIZE_PX")
                         for m in manifest},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
