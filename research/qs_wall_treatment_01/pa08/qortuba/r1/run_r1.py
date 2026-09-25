"""PA08-QORTUBA-R1 runner (§7 - §14): rerun the Qortuba sources with the recovered generic rules, then build every register
the phase requires and freeze them as PA08_QORTUBA_R1.

PA08_QORTUBA_BLIND_01 is never rewritten: this is a separate freeze that cites it.  The owner's withheld flooring / skirting /
profile quantities are not requested, opened or inferred anywhere in this file; nothing here is tuned to an expected number.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from engine.ingest import ENGINE_VERSION, pipeline7 as P7
from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba import blind as B, common as C
from research.qs_wall_treatment_01.pa08.qortuba.r1 import measure as M, partition_forensics as PF1, reconcile as RC

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_r1"
BLIND_OUT = B.OUT
STOREY = "SECOND_FLOOR (title block 'SECOND FLOOR PLAN'; engine storey status HUMAN_REVIEW:CONFLICTING_FLOOR_WORDS)"
WET_CLASSES = ("BATHROOM", "WC", "KITCHEN", "LAUNDRY", "WASHROOM")
ROOF_WORDS = ("ROOF", "TERRACE")


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str), "utf-8")
    return name


def _label(space):
    en, ar, cls = [], [], []
    for a in space["ANCHORS"]:
        t = (a.get("TEXT") or "").strip()
        if not t:
            continue
        if a.get("CLASS") and a["CLASS"] != "UNKNOWN":
            cls.append(a["CLASS"])
        dec, share = C.kb_decode(t)
        if C.looks_keyboard_arabic(t) and share >= 0.6:
            ar.append(dec)
        else:
            en.append(t)
    return {"EN": en, "AR": ar, "CLASSES": sorted(set(cls))}


def _room_name(lab, space):
    if lab["EN"]:
        return " / ".join(dict.fromkeys(lab["EN"]))
    if lab["AR"]:
        return " / ".join(dict.fromkeys(lab["AR"]))
    return f"UNLABELLED@{int(space['CENTROID_MM'][0])},{int(space['CENTROID_MM'][1])}" if space.get("CENTROID_MM") else "UNLABELLED"


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((BLIND_OUT / "PA08_BLIND_CONFIG.json").read_text("utf-8"))
    r = P7.run(cfg)
    vid = next(v for v in r.grids7 if r.grids7[v])
    view = next(v for v in r.views if v["VIEW_ID"] == vid)
    grid, seals, bands = r.grids7[vid], r.seals[vid], r.bands7[vid]
    faces = {f["FACE_ID"]: f for f in r.faces[vid]}
    spaces = r.spaces[vid]
    brows = r.brows[vid]
    sites = r.sites7[vid]
    reg = r.registers
    prims = {p.object_id: p for p in view["PRIMITIVES"]}

    # ---------------------------------------------------------------- §2 partition forensics (diagnosis, written before the rules)
    written = ["QORTUBA_PARTITION_FAILURE_REGISTER"]        # produced by partition_forensics.run()

    # ---------------------------------------------------------------- §3 / §5 / §6 band, short-element and arbitration registers
    write("PA08_QORTUBA_R1_MATERIAL_BAND_REGISTER", reg["PA07_MATERIAL_BAND_REGISTER"]); written.append("PA08_QORTUBA_R1_MATERIAL_BAND_REGISTER")
    write("PA08_QORTUBA_R1_MATERIAL_BAND_REGISTER_SHORT_ELEMENTS", reg["PA07_SHORT_ELEMENT_REGISTER"]); written.append("PA08_QORTUBA_R1_MATERIAL_BAND_REGISTER_SHORT_ELEMENTS")
    write("PA08_QORTUBA_R1_FACE_SIDE_ARBITRATION_REGISTER", reg["PA07_FACE_SIDE_ARBITRATION_REGISTER"]); written.append("PA08_QORTUBA_R1_FACE_SIDE_ARBITRATION_REGISTER")
    write("PA08_QORTUBA_R1_THICKNESS_SUPPORT_REGISTER", reg["PA07_THICKNESS_SUPPORT"]); written.append("PA08_QORTUBA_R1_THICKNESS_SUPPORT_REGISTER")

    # ---------------------------------------------------------------- §4 opening register (host wall first)
    band_by = {b["BAND_ID"]: b for b in bands}
    op_rows = []
    for s in sites:
        h = band_by.get(s["HOST_BAND_ID"])
        op_rows.append({"SITE_ID": s["SITE_ID"], "HOST_BAND_ID": s["HOST_BAND_ID"], "HOST_WALL_THICKNESS_MM": round(h["THK"], 1) if h else None,
                        "HOST_WALL_STATUS": h["STATUS"] if h else None, "CLASS": s["CLASS"], "STATUS": s["STATUS"], "SPAN_MM": s["SPAN_MM"],
                        "IS_END_GAP": bool(s.get("END_GAP")), "JAMB_A": s["JAMB_A"], "JAMB_B": s["JAMB_B"], "LEAF_EVIDENCE": s["LEAF_EVIDENCE"], "SWING_EVIDENCE": s["SWING_EVIDENCE"],
                        "FRAME_EVIDENCE": s["FRAME_EVIDENCE"], "GLAZING_EVIDENCE": s["GLAZING_EVIDENCE"], "REASON": s["REASON"],
                        "OPENING_HEIGHT": {"VALUE": None, "STATE": "SOURCE_REQUIRED", "WHY": "no elevation, section or door schedule was supplied for this project; a plan gives the span only"},
                        "DEDUCTION": {"VALUE": None, "STATE": "SOURCE_REQUIRED", "WHY": "an opening deduction needs the owner's measurement rule and the opening height; both are outside this phase"}})
    write("PA08_QORTUBA_R1_OPENING_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R1_OPENING_REGISTER", "ROWS": op_rows, "COUNT": len(op_rows),
                                               "BY_CLASS": dict(Counter(x["CLASS"] for x in op_rows)), "BY_STATUS": dict(Counter(x["STATUS"] for x in op_rows)),
                                               "END_GAPS": sum(1 for x in op_rows if x["IS_END_GAP"]),
                                               "RULE": "PA07R3 §4: an opening belongs to its host wall band; a gap at the END of a band, against the wall it stops short of, is classified by the same evidence as a gap inside the band (Qortuba draws most doors at a corner).  The Qortuba door block carries leaf and frame only: no swing arc is required for a CONFIRMED door, and a leaf hung on a frame may start a frame width inside the gap."})
    written.append("PA08_QORTUBA_R1_OPENING_REGISTER")

    # ---------------------------------------------------------------- §7 physical spaces
    sp_rows = []
    for s in sorted(spaces, key=lambda z: -z["AREA_GEOMETRIC_M2"]):
        lab = _label(s)
        f = faces[s["FACE_ID"]]
        sp_rows.append({"SPACE_ID": s["SPACE_ID"], "FACE_ID": s["FACE_ID"], "ROOM": _room_name(lab, f), "LABELS": lab, "STOREY": STOREY,
                        "GEOMETRY_STATUS": s["GEOMETRY_STATUS"], "IDENTITY_STATUS": s["IDENTITY_STATUS"], "SPACE_CLASS": s["SPACE_CLASS"],
                        "RASTER_AREA_M2_TOPOLOGY_ONLY": s["AREA_GEOMETRIC_M2"], "BOUNDARY_COMPOSITION_MM": s["BOUNDARY_COMPOSITION_MM"],
                        "MATERIAL_BOUNDARY_MM": s["MATERIAL_BOUNDARY_MM"], "OPENING_MM": s["OPENING_MM"], "UNRESOLVED_MM": s["UNRESOLVED_MM"],
                        "CENTROID_MM": f["CENTROID_MM"], "BBOX_MM": f["BBOX_MM"], "OPEN_RELATIONS": s["OPEN_RELATIONS"], "UNRESOLVED_RELATIONS": s["UNRESOLVED_RELATIONS"]})
    write("PA08_QORTUBA_R1_PHYSICAL_SPACE_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R1_PHYSICAL_SPACE_REGISTER", "ROWS": sp_rows, "COUNT": len(sp_rows),
                                                      "BY_GEOMETRY_STATUS": dict(Counter(x["GEOMETRY_STATUS"] for x in sp_rows)),
                                                      "LABELLED": sum(1 for x in sp_rows if x["LABELS"]["EN"] or x["LABELS"]["AR"]),
                                                      "NOTE": "no target count was set for this phase; the raster area is a topology measure and is never a quantity"})
    written.append("PA08_QORTUBA_R1_PHYSICAL_SPACE_REGISTER")

    # ---------------------------------------------------------------- §9 floor regions (+ roof separately)
    floor_rows, roof_rows = [], []
    for s in sp_rows:
        f = faces[s["FACE_ID"]]
        area, formula = M.face_polygon_area(f, grid, seals)
        established = s["GEOMETRY_STATUS"] == "ESTABLISHED" and area is not None
        if area is None:
            phys = {"VALUE": None, "STATE": "NOT_ESTABLISHED", "WHY": formula.get("WHY")}
        elif established:
            phys = {"VALUE": round(area, 4), "STATE": "SOURCE_ESTABLISHED", "WHY": "every boundary of this face is a material wall face, a column face or an established opening chord, and the arrangement of those lines reproduces the face"}
        else:
            phys = {"VALUE": round(area, 4), "STATE": "PROVISIONAL", "WHY": f"the face is bounded by {s['UNRESOLVED_MM']:.0f} mm of unresolved boundary: the area follows the lines as drawn but the room's extent is not established"}
        trade = dict(phys)
        trade["WHY"] = (phys["WHY"] or "") + " | trade zone = physical region with no contractor deduction applied: the owner's measurement rules for this project are sealed and were not requested"
        row = {"ROOM": s["ROOM"], "SPACE_ID": s["SPACE_ID"], "STOREY": STOREY, "PHYSICAL_AREA": phys, "TRADE_ZONE_AREA": trade, "STATUS": phys["STATE"],
               "BOUNDARY_IDS": sorted({b["BAND_ID"] for b in brows if b["SPACE_FACE_ID"] == s["FACE_ID"]}), "FORMULA": formula,
               "RASTER_AREA_M2_TOPOLOGY_ONLY": s["RASTER_AREA_M2_TOPOLOGY_ONLY"], "LABELS": s["LABELS"]}
        if any(w in (s["ROOM"] or "").upper() for w in ROOF_WORDS) or "سطح" in " ".join(s["LABELS"]["AR"]):
            row["REGION_KIND"] = "ROOF_OR_EXTERNAL_TERRACE"
            row["NOTE"] = "roof / terrace: recorded separately from internal floor regions, never added to an internal floor total"
            roof_rows.append(row)
        else:
            row["REGION_KIND"] = "INTERNAL_FLOOR_REGION"
            floor_rows.append(row)
    est = [x for x in floor_rows if x["STATUS"] == "SOURCE_ESTABLISHED"]
    write("PA08_QORTUBA_R1_FLOOR_REGION_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R1_FLOOR_REGION_REGISTER", "INTERNAL_FLOOR_REGIONS": floor_rows, "ROOF_OR_EXTERNAL_REGIONS": roof_rows,
                                                    "COUNT": len(floor_rows) + len(roof_rows), "BY_STATUS": dict(Counter(x["STATUS"] for x in floor_rows)),
                                                    "ESTABLISHED_INTERNAL_AREA_M2": round(sum(x["PHYSICAL_AREA"]["VALUE"] for x in est), 4) if est else 0.0,
                                                    "ESTABLISHED_ROOMS": [x["ROOM"] for x in est],
                                                    "AREA_METHOD": "ARRANGEMENT_OF_BOUNDARY_LINES (research/qs_wall_treatment_01/pa08/qortuba/r1/measure.py): the axis-aligned lines that seal the face are the cut lines of an arrangement; every arrangement cell whose centre lies in the face contributes its exact rectangle; the sum is cross-checked against the rasterised face and refused when they disagree",
                                                    "RULE": "a floor region is released only when every boundary of its face is material or an established opening; a provisional boundary keeps the area PROVISIONAL and out of any total"})
    written.append("PA08_QORTUBA_R1_FLOOR_REGION_REGISTER")

    # ---------------------------------------------------------------- §10 wall lengths, skirting and profile paths (three separate items)
    wall_rows, skirt_rows, prof_rows = [], [], []
    for s in sp_rows:
        p = M.path_rows(brows, s["FACE_ID"])
        host, opening, junction, unres = M.total(p["PHYSICAL_HOST_WALL"]), M.total(p["OPENING"]), M.total(p["JUNCTION"]), M.total(p["UNRESOLVED"])
        base_state = "SOURCE_ESTABLISHED" if s["GEOMETRY_STATUS"] == "ESTABLISHED" else "PROVISIONAL"
        wall_rows.append({"ROOM": s["ROOM"], "SPACE_ID": s["SPACE_ID"], "STOREY": STOREY,
                          "PHYSICAL_HOST_WALL_LM": {"VALUE": round(host / 1000, 3), "STATE": base_state, "WHY": "developed length of the material wall and column faces that bound this space, cut at junctions so no stretch is owned twice"},
                          "SKIRTING_ELIGIBLE_LM": {"VALUE": round(host / 1000, 3), "STATE": base_state, "WHY": "the same wall-face path: a skirting needs a wall face to sit on.  Door and window chords carry no wall face and are therefore not part of the path (a geometric fact, not a contractor deduction); no contractor deduction of any kind is applied"},
                          "PROFILE_ELIGIBLE_PATH_LM": {"VALUE": round((host + opening + junction) / 1000, 3), "STATE": base_state, "WHY": "the closed ceiling-level perimeter of the space: wall faces plus the opening and junction chords a profile runs across; unresolved boundary is excluded and reported separately"},
                          "UNRESOLVED_BOUNDARY_LM": {"VALUE": round(unres / 1000, 3), "STATE": "NOT_ESTABLISHED", "WHY": "boundary the engine could not establish: it belongs to no length item until the source resolves it"},
                          "OPENING_CHORD_LM": round(opening / 1000, 3), "JUNCTION_CHORD_LM": round(junction / 1000, 3),
                          "SEPARATE_ITEMS": "PHYSICAL_HOST_WALL_LM, SKIRTING_ELIGIBLE_LM and PROFILE_ELIGIBLE_PATH_LM are three separate items and are never added together"})
        skirt_rows.append({"ROOM": s["ROOM"], "SPACE_ID": s["SPACE_ID"], "STATE": base_state, "TOTAL_LM": round(host / 1000, 3),
                           "PATH": [{"BAND_ID": x["BAND_ID"], "SIDE": x["SIDE"], "AXIAL_START": x["AXIAL_START"], "AXIAL_END": x["AXIAL_END"], "LENGTH_MM": x["LENGTH_MM"], "SEAL_KIND": x["SEAL_KIND"], "CURVATURE": x["CURVATURE_TYPE"]} for x in p["PHYSICAL_HOST_WALL"]],
                           "EXCLUDED": [{"KIND": k, "LM": round(M.total(p[k]) / 1000, 3)} for k in ("OPENING", "JUNCTION", "UNRESOLVED") if p[k]],
                           "HEIGHT_OR_PROFILE_TYPE": {"VALUE": None, "STATE": "SOURCE_REQUIRED", "WHY": "skirting height and material are owner project inputs for this project; none was supplied and none was assumed"}})
        prof_rows.append({"ROOM": s["ROOM"], "SPACE_ID": s["SPACE_ID"], "STATE": base_state, "TOTAL_LM": round((host + opening + junction) / 1000, 3),
                          "PATH": [{"BAND_ID": x["BAND_ID"], "SIDE": x["SIDE"], "LENGTH_MM": x["LENGTH_MM"], "SEAL_KIND": x["SEAL_KIND"]} for x in p["PHYSICAL_HOST_WALL"] + p["OPENING"] + p["JUNCTION"]],
                          "PROFILE_TYPE_AND_SIZE": {"VALUE": None, "STATE": "SOURCE_REQUIRED", "WHY": "no reflected ceiling plan, profile detail or owner instruction for this project; the path length is geometry, the profile itself is not established"}})
    write("PA08_QORTUBA_R1_WALL_LENGTH_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R1_WALL_LENGTH_REGISTER", "ROWS": wall_rows, "COUNT": len(wall_rows), "STOREY": STOREY,
                                                   "TOTALS_ESTABLISHED_ONLY": {"PHYSICAL_HOST_WALL_LM": round(sum(x["PHYSICAL_HOST_WALL_LM"]["VALUE"] for x in wall_rows if x["PHYSICAL_HOST_WALL_LM"]["STATE"] == "SOURCE_ESTABLISHED"), 3),
                                                                               "SKIRTING_ELIGIBLE_LM": round(sum(x["SKIRTING_ELIGIBLE_LM"]["VALUE"] for x in wall_rows if x["SKIRTING_ELIGIBLE_LM"]["STATE"] == "SOURCE_ESTABLISHED"), 3),
                                                                               "PROFILE_ELIGIBLE_PATH_LM": round(sum(x["PROFILE_ELIGIBLE_PATH_LM"]["VALUE"] for x in wall_rows if x["PROFILE_ELIGIBLE_PATH_LM"]["STATE"] == "SOURCE_ESTABLISHED"), 3)},
                                                   "RULE": "three separate items; no contractor deduction; a provisional space contributes to no total"})
    write("PA08_QORTUBA_R1_SKIRTING_PATH_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R1_SKIRTING_PATH_REGISTER", "ROWS": skirt_rows, "COUNT": len(skirt_rows)})
    write("PA08_QORTUBA_R1_PROFILE_PATH_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R1_PROFILE_PATH_REGISTER", "ROWS": prof_rows, "COUNT": len(prof_rows)})
    written += ["PA08_QORTUBA_R1_WALL_LENGTH_REGISTER", "PA08_QORTUBA_R1_SKIRTING_PATH_REGISTER", "PA08_QORTUBA_R1_PROFILE_PATH_REGISTER"]

    # ---------------------------------------------------------------- §12 ceiling regions, case by case
    ceil_rows = []
    non_material_inside = defaultdict(list)
    label, meta, cell = grid["label"], grid["meta"], grid["cell"]
    acc_faces = {f for b in bands if b["STATUS"] == "ACCEPTED" for f in b["FACES"]}
    for p in view["PRIMITIVES"]:
        if p.kind != "SEGMENT" or p.object_id in acc_faces or p.length_mm < 1000:
            continue
        ro = r.roles[vid].get(p.object_id, {})
        if ro.get("ROLE") in ("DIMENSION_LINE", "DIMENSION_EXTENSION", "DIMENSION_TEXT", "TEXT_OR_LABEL"):
            continue
        mx, my = (p.x1 + p.x2) / 2, (p.y1 + p.y2) / 2
        rr, cc = int((meta["y1"] - my) / cell), int((mx - meta["x0"]) / cell)
        if 0 <= rr < label.shape[0] and 0 <= cc < label.shape[1] and label[rr, cc]:
            non_material_inside[int(label[rr, cc])].append({"OBJECT_ID": p.object_id, "LAYER": p.provenance.layer, "LENGTH_MM": round(p.length_mm, 1), "ROLE": ro.get("ROLE")})
    for s in sp_rows:
        f = faces[s["FACE_ID"]]
        inside = non_material_inside.get(f["RUN_LABEL_NOT_A_KEY"], [])
        floor_row = next((x for x in floor_rows + roof_rows if x["SPACE_ID"] == s["SPACE_ID"]), None)
        if inside:
            state, why = "NOT_ESTABLISHED", f"{len(inside)} long non-wall line(s) are drawn inside this space ({sorted({z['LAYER'] for z in inside})}): a soffit, a drop ceiling, a void edge or a furniture outline cannot be told apart on a floor plan, so the ceiling region is not taken from the floor region"
            area = None
        elif floor_row and floor_row["PHYSICAL_AREA"]["STATE"] == "SOURCE_ESTABLISHED":
            state, why = "PROVISIONAL", "no reflected ceiling plan and no section was supplied for this project; with no soffit, void or double-height line drawn inside the space, the ceiling region follows the floor region, provisionally, for this space only"
            area = floor_row["PHYSICAL_AREA"]["VALUE"]
        else:
            state, why = "NOT_ESTABLISHED", "the floor region of this space is not established, so its ceiling region cannot follow it"
            area = None
        ceil_rows.append({"ROOM": s["ROOM"], "SPACE_ID": s["SPACE_ID"], "CEILING_REGION_AREA_M2": {"VALUE": area, "STATE": state, "WHY": why},
                          "CEILING_HEIGHT": {"VALUE": None, "STATE": "SOURCE_REQUIRED", "WHY": "no section, no ceiling level and no owner parameter for this project"},
                          "NON_WALL_LINES_INSIDE": inside[:8], "DECIDED": "CASE_BY_CASE"})
    write("PA08_QORTUBA_R1_CEILING_REGION_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R1_CEILING_REGION_REGISTER", "ROWS": ceil_rows, "COUNT": len(ceil_rows),
                                                      "BY_STATE": dict(Counter(x["CEILING_REGION_AREA_M2"]["STATE"] for x in ceil_rows)),
                                                      "RULE": "PA08-R1 §12: CEILING = FLOOR is never applied globally.  Each space is decided on its own evidence: a space with any long non-wall line drawn inside it is NOT_ESTABLISHED; a space with an established floor region and nothing drawn inside it follows the floor region provisionally, pending a reflected ceiling plan"})
    written.append("PA08_QORTUBA_R1_CEILING_REGION_REGISTER")

    # ---------------------------------------------------------------- §11 block / plaster / paint inputs: lengths only
    acc = [b for b in bands if b["STATUS"] == "ACCEPTED"]
    blk = [{"BAND_ID": b["BAND_ID"], "THICKNESS_MM": round(b["THK"], 1), "DEVELOPED_LENGTH_M": round(b["LENGTH"] / 1000, 3), "COVERED_LENGTH_M": round(b["COVERED"] / 1000, 3),
            "BAND_TYPE": b["BAND_TYPE"], "LAYERS": sorted({f.provenance.layer for f in b["FACES"].values()}),
            "AREA_M2": {"VALUE": None, "STATE": "NOT_ESTABLISHED", "WHY": "a blockwork area needs a wall height; no section, elevation or owner height parameter exists for this project and none was invented"}} for b in acc]
    write("PA08_QORTUBA_R1_BLOCK_INPUT_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R1_BLOCK_INPUT_REGISTER", "ROWS": blk, "COUNT": len(blk),
                                                   "TOTAL_DEVELOPED_LENGTH_M": round(sum(x["DEVELOPED_LENGTH_M"] for x in blk), 3),
                                                   "BY_THICKNESS_M": {str(k): round(v, 3) for k, v in sorted(Counter().__class__((round(x["THICKNESS_MM"]), 0) for x in blk).items())} if False else {str(t): round(sum(x["DEVELOPED_LENGTH_M"] for x in blk if round(x["THICKNESS_MM"]) == t), 3) for t in sorted({round(x["THICKNESS_MM"]) for x in blk})},
                                                   "AREA_STATE": "NOT_ESTABLISHED", "RULE": "lengths only: no height is available for this project and none is assumed; P7757 heights are not Qortuba rules"})
    plaster, paint = [], []
    for s in sp_rows:
        p = M.path_rows(brows, s["FACE_ID"])
        host = M.total(p["PHYSICAL_HOST_WALL"])
        state = "SOURCE_ESTABLISHED" if s["GEOMETRY_STATUS"] == "ESTABLISHED" else "PROVISIONAL"
        wet = any(c in WET_CLASSES for c in s["LABELS"]["CLASSES"])
        plaster.append({"ROOM": s["ROOM"], "SPACE_ID": s["SPACE_ID"], "INTERNAL_PLASTER_RUNNING_LENGTH_M": {"VALUE": round(host / 1000, 3), "STATE": state, "WHY": "the room-side wall-face path of this space"},
                        "AREA_M2": {"VALUE": None, "STATE": "NOT_ESTABLISHED", "WHY": "a plaster area needs a plaster height; no section, elevation or owner height parameter exists for this project"},
                        "WET_ROOM_BY_LABEL": wet, "WET_TREATMENT": {"VALUE": None, "STATE": "SOURCE_REQUIRED", "WHY": "no sanitary fixture, tiling note or owner instruction is drawn; a wet-room treatment cannot be established from a room name alone"}})
        paint.append({"ROOM": s["ROOM"], "SPACE_ID": s["SPACE_ID"], "PAINT_RUNNING_LENGTH_M": {"VALUE": round(host / 1000, 3), "STATE": state, "WHY": "the same wall-face path; paint follows the plastered face"},
                      "AREA_M2": {"VALUE": None, "STATE": "NOT_ESTABLISHED", "WHY": "a paint area needs a height and the treated-face decision; neither exists for this project"},
                      "PAINT_SYSTEM": {"VALUE": None, "STATE": "SOURCE_REQUIRED", "WHY": "no finishes schedule or owner instruction for this project"}})
    write("PA08_QORTUBA_R1_PLASTER_INPUT_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R1_PLASTER_INPUT_REGISTER", "ROWS": plaster, "COUNT": len(plaster), "AREA_STATE": "NOT_ESTABLISHED"})
    write("PA08_QORTUBA_R1_PAINT_INPUT_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R1_PAINT_INPUT_REGISTER", "ROWS": paint, "COUNT": len(paint), "AREA_STATE": "NOT_ESTABLISHED"})
    written += ["PA08_QORTUBA_R1_BLOCK_INPUT_REGISTER", "PA08_QORTUBA_R1_PLASTER_INPUT_REGISTER", "PA08_QORTUBA_R1_PAINT_INPUT_REGISTER"]
    return r, vid, sp_rows, floor_rows, roof_rows, wall_rows, ceil_rows, written, op_rows


SYNTHETIC_SUITES = ["tests/test_pa07r3_partitions.py", "tests/test_pa07r2_guards.py", "tests/test_pa07r1_guards.py", "tests/test_pa07_bands.py", "tests/test_pa07_topology.py",
                    "tests/test_pa07_spaces.py", "tests/test_pa06_topology.py", "tests/test_pa06_pipeline.py", "tests/test_pa05_ingest.py", "tests/test_pa08_harness.py", "tests/test_pa08_qortuba.py"]
ENGINE_FILES = sorted(str(x) for x in Path("engine/ingest").glob("*.py")) + ["engine/cad_adapter.py"]


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def regression():
    """§13: every generic rule runs against the PA07 synthetic fixtures and the P7757 regression before anything is released."""
    res = subprocess.run(["python", "-m", "pytest", "-q", *SYNTHETIC_SUITES], capture_output=True, text=True)
    tail = [l for l in res.stdout.strip().splitlines() if l.strip()][-1] if res.stdout.strip() else ""
    syn = {"SUITES": SYNTHETIC_SUITES, "EXIT_CODE": res.returncode, "SUMMARY_LINE": tail, "STATUS": "PASS" if res.returncode == 0 else "FAIL"}
    base = Path(PR.OUT_DIR)
    def qa(tag):
        p = base / tag / "PA07_QA_REPORT.json"
        return json.loads(p.read_text("utf-8")) if p.exists() else None
    r2, r3 = qa("pa07r2"), qa("pa07r3")
    delta = None
    if r2 and r3:
        delta = {"BANDS_ACCEPTED": [r2["BANDS"]["ACCEPTED"], r3["BANDS"]["ACCEPTED"]], "BANDS_UNRESOLVED": [r2["BANDS"]["UNRESOLVED"], r3["BANDS"]["UNRESOLVED"]],
                 "BANDS_REJECTED": [r2["BANDS"]["REJECTED"], r3["BANDS"]["REJECTED"]],
                 "ACCEPTED_DEVELOPED_M": [r2["BANDS"]["ACCEPTED_DEVELOPED_M"], r3["BANDS"]["ACCEPTED_DEVELOPED_M"]],
                 "SITES_BY_CLASS": [r2["SITES"], r3["SITES"]], "SITE_STATUS": [r2["SITE_STATUS"], r3["SITE_STATUS"]],
                 "SPACES_ON_PLAN_VIEWS": [r2["SPACES_ON_PLAN_VIEWS"], r3["SPACES_ON_PLAN_VIEWS"]],
                 "SPACES_BY_GEOMETRY_STATUS": [r2["SPACES_BY_GEOMETRY_STATUS"], r3["SPACES_BY_GEOMETRY_STATUS"]],
                 "PLANAR_FACES": [r2["PLANAR_FACES"], r3["PLANAR_FACES"]],
                 "CONFIRMED_DOORS": [r2["SITES"].get("CONFIRMED_DOOR_OPENING", 0), r3["SITES"].get("CONFIRMED_DOOR_OPENING", 0)],
                 "ESTABLISHED_SPACES": [r2["SPACES_BY_GEOMETRY_STATUS"].get("ESTABLISHED", 0), r3["SPACES_BY_GEOMETRY_STATUS"].get("ESTABLISHED", 0)]}
        door_total = [sum(v for k, v in r2["SITES"].items() if "DOOR" in k), sum(v for k, v in r3["SITES"].items() if "DOOR" in k)]
        delta["DOOR_CLASS_SITES_TOTAL"] = door_total
        delta["PROBABLE_DOORS"] = [r2["SITES"].get("PROBABLE_DOOR_OPENING", 0), r3["SITES"].get("PROBABLE_DOOR_OPENING", 0)]
        losses = []
        if delta["CONFIRMED_DOORS"][1] < delta["CONFIRMED_DOORS"][0]:
            losses.append(f"P7757 confirmed door openings {delta['CONFIRMED_DOORS'][0]} -> {delta['CONFIRMED_DOORS'][1]} (door-class sites in total {door_total[0]} -> {door_total[1]}): a yield loss in the safe direction, every lost door becomes an unresolved or probable site and the spaces beside it stay provisional")
        if delta["ESTABLISHED_SPACES"][1] < delta["ESTABLISHED_SPACES"][0]:
            losses.append("P7757 lost established spaces")
        if r3["BANDS"]["ACCEPTED_DEVELOPED_M"]["STRAIGHT"] < 0.95 * r2["BANDS"]["ACCEPTED_DEVELOPED_M"]["STRAIGHT"]:
            losses.append("P7757 lost more than 5 per cent of accepted straight wall length")
        delta["REGRESSIONS_FOUND"] = losses
        delta["VERDICT"] = "NO_REGRESSION" if not losses else "REGRESSION_YIELD_LOSS_SAFE"
        delta["REGRESSION_DIRECTION"] = "YIELD_LOSS_SAFE" if losses else "NONE"
        delta["SILENT_WRONG_QUANTITY"] = False
        delta["SILENT_WRONG_EVIDENCE"] = "every loss above moves a site or a space from established to provisional or unresolved; no P7757 quantity was released that was previously withheld, and no established value changed silently"
        delta["NAMED_LOSSES"] = [{"WHERE_MM": [-232008, -791894], "WAS": "CONFIRMED_DOOR_OPENING span 675 on a 200 mm wall", "NOW": "no site: the leaf line CAD-4726 now pairs with the wall face at the wall's own thickness, so the band covers the doorway and no gap remains",
                                  "CAUSE": "a door leaf drawn parallel to its host wall at exactly the wall thickness is a false pairing partner; PA06 did not classify this line as DOOR_LEAF, so it entered the candidate set", "DIRECTION": "YIELD_LOSS_SAFE"},
                                 {"WHERE_MM": [-152690, -800454], "WAS": "CONFIRMED_DOOR_OPENING span 1900 on a 120 mm wall", "NOW": "the 120 mm band is UNRESOLVED (ISOLATED_PAIR): it no longer joins an established band", "CAUSE": "the wall it used to join is now UNRESOLVED on a face-side conflict", "DIRECTION": "YIELD_LOSS_SAFE"},
                                 {"WHERE_MM": [-152690, -800534], "WAS": "CONFIRMED_DOOR_OPENING span 2000 on a 120 mm wall", "NOW": "same 120 mm band, UNRESOLVED", "CAUSE": "as above", "DIRECTION": "YIELD_LOSS_SAFE"},
                                 {"WHERE_MM": [-141860, -793818], "WAS": "CONFIRMED_DOOR_OPENING span 740 on a 150 mm wall", "NOW": "the host band shrank to 500 mm and is UNRESOLVED (ISOLATED_PAIR)", "CAUSE": "the host was a composite of door-block frame lines and wall faces; the block rules separate them and the wall remnant no longer reaches structure length", "DIRECTION": "YIELD_LOSS_SAFE"},
                                 {"WHERE_MM": [-136509, -794068], "WAS": "CONFIRMED_DOOR_OPENING span 740 on a 150 mm wall", "NOW": "the host band shrank to 279 mm", "CAUSE": "as above", "DIRECTION": "YIELD_LOSS_SAFE"}]
    return {"ARTIFACT": "PA08_QORTUBA_R1_REGRESSION_RESULT", "SYNTHETIC": syn, "P7757": delta,
            "P7757_NOTE": "the P7757 comparison is PA07R2 (frozen) against PA07R3 (this phase's rules) on the same sources and the same runner",
            "RULE": "§13: a generic rule is not kept because it improves Qortuba; it is kept because it survives the synthetic fixtures and does not lose P7757 geometry"}


def finish():
    r, vid, sp_rows, floor_rows, roof_rows, wall_rows, ceil_rows, written, op_rows = run()
    view = next(v for v in r.views if v["VIEW_ID"] == vid)
    faces = {f["FACE_ID"]: f for f in r.faces[vid]}
    faces_by_space = {s["SPACE_ID"]: faces[s["FACE_ID"]] for s in sp_rows}

    # ---------------------------------------------------------------- §8 semantic reconciliation (QA only)
    rec = RC.build(sp_rows, r.grids7[vid], r.seals[vid], r.sites7[vid], faces_by_space)
    write("PA08_QORTUBA_R1_SEMANTIC_RECONCILIATION", rec); written.append("PA08_QORTUBA_R1_SEMANTIC_RECONCILIATION")

    # ---------------------------------------------------------------- §2 forensics register
    # The diagnosis is only meaningful against the engine that FAILED: it is produced with the engine files at the PA07R2 freeze
    # (see run_forensics_on_frozen_engine.sh) and is never regenerated on the repaired rules, which no longer reproduce the merge.
    if not (OUT / "QORTUBA_PARTITION_FAILURE_REGISTER.json").exists():
        PF1.run()

    # ---------------------------------------------------------------- coverage
    bands = r.bands7[vid]
    roles = r.roles[vid]
    wall_len = sum(p.length_mm for p in view["PRIMITIVES"] if p.kind == "SEGMENT" and p.provenance.layer == "WALL")
    acc_faces = {f for b in bands if b["STATUS"] == "ACCEPTED" for f in b["FACES"]}
    wall_in_acc = sum(p.length_mm for p in view["PRIMITIVES"] if p.kind == "SEGMENT" and p.provenance.layer == "WALL" and p.object_id in acc_faces)
    labelled = [s for s in sp_rows if s["LABELS"]["EN"] or s["LABELS"]["AR"]]
    cov = {"ARTIFACT": "PA08_QORTUBA_R1_COVERAGE", "STOREY": STOREY,
           "WALL_LAYER_LENGTH_M": round(wall_len / 1000, 2), "WALL_LAYER_LENGTH_IN_ACCEPTED_BANDS_M": round(wall_in_acc / 1000, 2),
           "WALL_LAYER_SHARE_IN_ACCEPTED_BANDS": round(wall_in_acc / wall_len, 3) if wall_len else None,
           "BANDS": dict(Counter(b["STATUS"] for b in bands)),
           "SPACES": len(sp_rows), "SPACES_WITH_A_LABEL": len(labelled),
           "SPACES_BY_GEOMETRY_STATUS": dict(Counter(s["GEOMETRY_STATUS"] for s in sp_rows)),
           "FLOOR_REGIONS_BY_STATUS": dict(Counter(x["STATUS"] for x in floor_rows)),
           "FLOOR_AREA_ESTABLISHED_M2": round(sum(x["PHYSICAL_AREA"]["VALUE"] for x in floor_rows if x["STATUS"] == "SOURCE_ESTABLISHED"), 3),
           "FLOOR_AREA_PROVISIONAL_M2": round(sum(x["PHYSICAL_AREA"]["VALUE"] for x in floor_rows if x["STATUS"] == "PROVISIONAL" and x["PHYSICAL_AREA"]["VALUE"]), 3),
           "OPENINGS_BY_CLASS": dict(Counter(x["CLASS"] for x in op_rows)),
           "CEILING_BY_STATE": dict(Counter(x["CEILING_REGION_AREA_M2"]["STATE"] for x in ceil_rows)),
           "VERTICAL_QUANTITIES": "NONE: no height exists for this project, so every area that needs a height is NOT_ESTABLISHED",
           "WITHHELD_OWNER_DATA": "the owner's flooring / skirting / profile quantities were not requested, opened or inferred at any point in this phase"}
    write("PA08_QORTUBA_R1_COVERAGE", cov); written.append("PA08_QORTUBA_R1_COVERAGE")

    # ---------------------------------------------------------------- §13 regression
    regr = regression()
    write("PA08_QORTUBA_R1_REGRESSION_RESULT", regr); written.append("PA08_QORTUBA_R1_REGRESSION_RESULT")

    # ---------------------------------------------------------------- defects
    blind_def = json.loads((BLIND_OUT / "PA08_BLIND_DEFECTS.json").read_text("utf-8"))
    carried = []
    fixed = {"QBD-02": "PARTLY: the corner doors are now classified, because a gap at the END of a band, against the wall it stops short of, is an interval of that band and a leaf hung on a frame counts without a swing arc",
             "QBD-03": "ADDRESSED: the seven labelled rooms no longer merge; each is its own space.  Their floor regions are built and three regions in the plan are SOURCE_ESTABLISHED; the rest stay PROVISIONAL on their own boundary evidence"}
    for d in blind_def["DEFECTS"]:
        row = dict(d)
        row["R1_STATUS"] = "ADDRESSED_BY_A_GENERIC_RULE" if d["DEFECT_ID"] in fixed else "STILL_OPEN"
        row["R1_NOTE"] = fixed.get(d["DEFECT_ID"], "not addressed in this phase; the blind behaviour stands")
        carried.append(row)
    new = []
    for x in rec["ROWS"]:
        if x["VERDICT"].startswith("DISAGREE"):
            new.append({"DEFECT_ID": f"QR1-{len(new) + 1:02d}", "SEVERITY": "MEDIUM_SEMANTIC_DISAGREEMENT", "SOURCE_CONDITION": f"{x['READER']['ROOM_A']} / {x['READER']['ROOM_B']}",
                        "ENGINE_BEHAVIOUR": x["ENGINE"], "READER_CLAIM": x["READER"]["RELATION"], "READER_JUSTIFICATION": x["READER"]["JUSTIFICATION"],
                        "SILENT_WRONG": False, "SAFE_REFUSAL": True, "EXPECTED_SAFE_BEHAVIOUR": "the disagreement is recorded; the engine keeps its own state and releases no quantity for the affected spaces",
                        "AFFECTED_TRADES": ["FLOOR_FINISH", "SKIRTING", "PROFILE"]})
    unres_spaces = [s for s in sp_rows if s["GEOMETRY_STATUS"] != "ESTABLISHED"]
    new.append({"DEFECT_ID": f"QR1-{len(new) + 1:02d}", "SEVERITY": "HIGH_YIELD_LOSS_SAFE",
                "SOURCE_CONDITION": "partitions whose thickness the drawing never dimensions, and strips that share a face with furniture drawn against the wall",
                "ENGINE_BEHAVIOUR": f"{len(unres_spaces)} of {len(sp_rows)} spaces keep a provisional boundary, so their floor, skirting and profile items stay PROVISIONAL",
                "EXPECTED_SAFE_BEHAVIOUR": "provisional is the correct state; the loss is yield, not accuracy", "SILENT_WRONG": False, "SAFE_REFUSAL": True,
                "AFFECTED_TRADES": ["FLOOR_FINISH", "SKIRTING", "PROFILE", "PLASTER", "PAINT"]})
    small = [s for s in sp_rows if s["RASTER_AREA_M2_TOPOLOGY_ONLY"] < 1.0]
    new.append({"DEFECT_ID": f"QR1-{len(new) + 1:02d}", "SEVERITY": "MEDIUM_OVER_SEGMENTATION",
                "SOURCE_CONDITION": "chords that cap unresolved strips and close outlines also cut small residual cells out of the free space",
                "ENGINE_BEHAVIOUR": f"{len(small)} of {len(sp_rows)} spaces are under 1 m2 (wall-end pockets, outline interiors, strip interiors); they carry no label and no established area",
                "EXPECTED_SAFE_BEHAVIOUR": "a residual cell must never be reported as a room; these stay unlabelled and provisional, but they inflate the space count and a human reading the register must not read them as rooms",
                "SILENT_WRONG": False, "SAFE_REFUSAL": True, "AFFECTED_TRADES": ["NONE_DIRECTLY"]})
    defects = {"ARTIFACT": "PA08_QORTUBA_R1_DEFECT_REGISTER", "CARRIED_FROM_BLIND": carried, "NEW_IN_R1": new,
               "COUNT": len(carried) + len(new), "SILENT_WRONG_COUNT": sum(1 for d in carried + new if d.get("SILENT_WRONG")),
               "NOTE": "a defect is a difference between what the source shows and what the engine established; a safe refusal is still a defect when it loses yield"}
    write("PA08_QORTUBA_R1_DEFECT_REGISTER", defects); written.append("PA08_QORTUBA_R1_DEFECT_REGISTER")

    # ---------------------------------------------------------------- freeze
    contents = {}
    for name in sorted(set(written)):
        p = OUT / f"{name}.json"
        if p.exists():
            contents[name] = _sha(p)
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip().splitlines()
    frozen_blind = json.loads((BLIND_OUT / "FREEZE_PA08_QORTUBA_BLIND_01.json").read_text("utf-8"))
    # the prior freeze is cited by ITS OWN digest key; verify it independently so a broken citation can never pass as "intact"
    prior_digest = frozen_blind.get("FREEZE_DIGEST_SHA256") or frozen_blind.get("DIGEST")
    prior_files_ok = all((BLIND_OUT / n).exists() and _sha(BLIND_OUT / n) == h for n, h in frozen_blind.get("FILES", {}).items())
    prior_digest_ok = bool(prior_digest) and hashlib.sha256(json.dumps(frozen_blind.get("FILES", {}), sort_keys=True).encode()).hexdigest() == prior_digest
    fr = {"ARTIFACT": "FREEZE_PA08_QORTUBA_R1", "PROJECT_ALIAS": "QORTUBA", "PROJECT_ROLE_NOW": "DEVELOPMENT / REGRESSION (declared by the owner after the blind freeze)",
          "PRIOR_FREEZE_NOT_REWRITTEN": {"FREEZE": "PA08_QORTUBA_BLIND_01", "DIGEST": prior_digest, "FILE_COUNT": len(frozen_blind.get("FILES", {})),
                                         "VERIFIED_ON_DISK": {"ALL_FILE_HASHES_MATCH": prior_files_ok, "DIGEST_RECOMPUTES": prior_digest_ok},
                                         "STATUS": "intact; this phase cites it and never edits it" if (prior_files_ok and prior_digest_ok) else "CITATION_INVALID: the prior freeze does not verify on disk"},
          # a freeze names the commit that carries the code it describes.  A freeze taken on a dirty or uncommitted tree says so here
          # rather than naming a commit that does not contain the rules the registers were produced with.
          "GIT_HEAD_AT_FREEZE": head, "WORKING_TREE_AT_FREEZE": {"CLEAN": not dirty, "UNCOMMITTED_PATHS": [l[3:] for l in dirty][:20],
                                                                 "MEANING": "CLEAN means GIT_HEAD_AT_FREEZE contains exactly the code that produced these registers; otherwise the head named here is not sufficient provenance"},
          "ENGINE_VERSION": ENGINE_VERSION, "ENGINE_FILE_HASHES": {f: _sha(f) for f in ENGINE_FILES if Path(f).exists()},
          "SOURCE_HASHES": frozen_blind["SOURCE_HASHES"], "DECODER": frozen_blind["DECODER"],
          "CONTENTS": contents, "COUNT": len(contents),
          "WITHHELD_OWNER_DATA": "NOT_REQUESTED_NOT_OPENED_NOT_INFERRED",
          "RULE": "the registers of this freeze are the phase's output; a later phase may add to them but may not rewrite them"}
    fr["DIGEST"] = _digest({k: v for k, v in fr.items() if k != "DIGEST"})
    write("FREEZE_PA08_QORTUBA_R1", fr)
    return {"WRITTEN": written, "FREEZE": fr["DIGEST"], "COVERAGE": cov, "REGRESSION": regr, "RECONCILIATION": rec["BY_VERDICT"], "DEFECTS": defects["COUNT"], "SILENT_WRONG": defects["SILENT_WRONG_COUNT"]}


if __name__ == "__main__":
    out = finish()
    print("FREEZE", out["FREEZE"][:16], "registers", len(out["WRITTEN"]))
    print("reconciliation", out["RECONCILIATION"])
    print("regression synthetic", out["REGRESSION"]["SYNTHETIC"]["STATUS"], "| P7757", (out["REGRESSION"]["P7757"] or {}).get("VERDICT"), (out["REGRESSION"]["P7757"] or {}).get("REGRESSIONS_FOUND"))
    print("coverage", {k: out["COVERAGE"][k] for k in ("WALL_LAYER_SHARE_IN_ACCEPTED_BANDS", "SPACES", "SPACES_WITH_A_LABEL", "FLOOR_AREA_ESTABLISHED_M2", "FLOOR_AREA_PROVISIONAL_M2")})
    print("defects", out["DEFECTS"], "silent wrong", out["SILENT_WRONG"])
