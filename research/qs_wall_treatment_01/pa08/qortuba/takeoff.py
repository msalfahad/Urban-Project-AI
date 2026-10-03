"""Sections 4-16, 18, 26: material walls, physical spaces, floor areas, wet rooms, blockwork, plaster, paint, ceiling,
skirting, openings, stairs, columns, roof / open areas, quantity trace and coverage — every line built from the frozen
blind registers of the AS-IS engine, every value with a canonical state, no vertical quantity without a source height.

Nothing here reads the DWG for new geometry except the STAIR-layer lines (plan tread lines), the DOOR-block instances
and the WINDOW-layer frame lines, which are recorded as SOURCE_OBSERVATIONS (counts and plan dimensions), never as
engine-established openings or walls.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from engine import cad_adapter as CA
from research.qs_wall_treatment_01.pa08.qortuba import common as C

STOREY = "SECOND_FLOOR (title block 'SECOND FLOOR PLAN'; engine storey HUMAN_REVIEW:CONFLICTING_FLOOR_WORDS)"
WET_CLASSES = ("BATHROOM", "WC", "KITCHEN", "LAUNDRY", "WASHROOM")


def _labels_by_space():
    txt = json.loads((C.OUT / "PA08_QORTUBA_TEXT_SEMANTIC_REGISTER.json").read_text("utf-8"))
    by = defaultdict(list)
    for r in txt["DWG_TEXTS"]:
        if not r["IN_TITLE_BLOCK_OR_SITE"] and r["ATTACHED_PHYSICAL_SPACE"]:
            by[r["ATTACHED_PHYSICAL_SPACE"]].append(r)
    return by


def _zone_name(labels):
    en = [r["CLEAN_TEXT"] for r in labels if r["LANGUAGE"] == "EN"]
    cls = sorted({r["CANONICAL_CLASS"] for r in labels if r["CANONICAL_CLASS"]})
    return (" / ".join(en) if en else "UNLABELLED"), cls


def build():
    bands = C.load_blind("PA07_MATERIAL_BAND_REGISTER")["ROWS"]; band_by = {b["BAND_ID"]: b for b in bands}
    intervals = C.load_blind("PA07_BAND_INTERVAL_REGISTER")["ROWS"]
    sites = C.load_blind("PA07_OPENING_SITE_REGISTER")["ROWS"]; site_by = {s["SITE_ID"]: s for s in sites}
    spaces = C.load_blind("PA07_PHYSICAL_SPACE_REGISTER")["ROWS"]
    faces = {f["FACE_ID"]: f for f in C.load_blind("PA07_PLANAR_FACE_REGISTER")["ROWS"]}
    brows = C.load_blind("PA07_SPACE_BOUNDARY_FACE_REGISTER")["ROWS"]
    cols = C.load_blind("PA07_COLUMN_JUNCTION_REGISTER")
    safety = C.load_blind("PA07_QUANTITY_SAFETY_REGISTER")["ROWS"]
    trace7 = C.load_blind("PA07_QUANTITY_INPUT_TRACE")["LINES"]
    labels_by = _labels_by_space()
    space_by_face = {s["FACE_ID"]: s for s in spaces}
    rows_by_space = defaultdict(list); rows_by_band = defaultdict(list)
    for r in brows:
        rows_by_band[r["BAND_ID"]].append(r)
        if r["SPACE_FACE_ID"] in space_by_face:
            rows_by_space[space_by_face[r["SPACE_FACE_ID"]]["SPACE_ID"]].append(r)
    R = {}

    # ---------------- 4 material walls
    wall_rows = []
    for b in bands:
        wall_rows.append({"BAND_ID": b["BAND_ID"], "STOREY": STOREY, "DEVELOPED_LENGTH_MM": b["DEVELOPED_LENGTH_MM"], "THICKNESS_MM": b["THICKNESS_MM"],
                          "GEOMETRY": "CURVED" if b["CURVATURE_TYPE"] == "ARC" else ("ANGLED" if b["ORIENTATION_TYPE"] == "ANGLED" else "STRAIGHT"), "BAND_TYPE": b.get("BAND_TYPE"),
                          "FACE_A": b["FACE_A_ID"], "FACE_B": b["FACE_B_ID"], "STATUS": b["MATERIAL_STATUS"], "REASON": (b.get("REJECTION_REASON") or "").split(" (")[0] or None, "MATERIAL_FILL": (b.get("MATERIAL_FILL") or {}).get("FILL")})
    acc = [w for w in wall_rows if w["STATUS"] == "ACCEPTED"]
    by_thk = defaultdict(float)
    for w in acc:
        by_thk[w["THICKNESS_MM"]] += w["DEVELOPED_LENGTH_MM"]
    R["PA08_QORTUBA_MATERIAL_WALL_REGISTER"] = {"ARTIFACT": "PA08_QORTUBA_MATERIAL_WALL_REGISTER", "ROWS": wall_rows, "COUNTS": dict(Counter(w["STATUS"] for w in wall_rows)),
        "REJECTED_BY_REASON": dict(Counter(w["REASON"] for w in wall_rows if w["STATUS"] == "REJECTED")), "UNRESOLVED_BY_REASON": dict(Counter(w["REASON"] for w in wall_rows if w["STATUS"] == "UNRESOLVED")),
        "ACCEPTED_DEVELOPED_M_BY_THICKNESS": {str(int(k)): round(v / 1000, 3) for k, v in sorted(by_thk.items())}, "ACCEPTED_BY_TYPE": dict(Counter(w["BAND_TYPE"] for w in acc)),
        "NOT_COUNTED_AS_WALLS": "door leaves and frames (block '6'), window frame lines (WINDOW layer), hatch strokes, furniture (B-FURNI / FIRNTUR), fixtures, dimension lines, annotation, stair treads, plot boundary double lines: all rejected or unresolved by the band engine",
        "STATUS_NOTE": "ACCEPTED means the band engine paired two faces with structure evidence; it is not an independent verification of the wall"}

    # ---------------- 5 physical spaces
    space_rows = []
    for s in spaces:
        rs = rows_by_space.get(s["SPACE_ID"], [])
        labels = labels_by.get(s["SPACE_ID"], [])
        name, cls = _zone_name(labels)
        n_rooms = len({r["BILINGUAL_PARTNER"] or r["TEXT_ID"] for r in labels if r["LANGUAGE"] == "EN"} | {r["TEXT_ID"] for r in labels if r["LANGUAGE"] == "EN"})
        en_labels = [r for r in labels if r["LANGUAGE"] == "EN"]
        adj = set()
        for r in rs:
            for q in rows_by_band.get(r["BAND_ID"], []):
                if q["SPACE_FACE_ID"] and q["SPACE_FACE_ID"] != s["FACE_ID"] and q["SPACE_FACE_ID"] in space_by_face:
                    adj.add(space_by_face[q["SPACE_FACE_ID"]]["SPACE_ID"])
        topo = s["GEOMETRY_STATUS"]
        if len(en_labels) > 1:
            topo = "BOUNDARY_PROVISIONAL_MULTI_ROOM_MERGED"
        space_rows.append({"SPACE_ID": s["SPACE_ID"], "ZONE_NAME": name, "CANONICAL_CLASSES": cls, "ENGLISH_LABELS_INSIDE": len(en_labels), "GEOMETRIC_AREA_M2": s["AREA_GEOMETRIC_M2"],
                           "AREA_STATE": "GEOMETRIC_REFERENCE_ONLY", "AREA_BASIS": "engine free-mask cells (50 mm) + half boundary strip; never a quantity",
                           "BOUNDARY_FACE_IDS": sorted({r["BAND_ID"] + "@" + r["SIDE"] for r in rs if r["SEAL_KIND"] in ("FACE", "COLUMN_FACE")}), "OPENING_IDS": sorted({r["SITE_ID"] for r in rs if r["SITE_ID"]}),
                           "OPEN_EDGE_IDS": sorted({r["BAND_ID"] + "@" + r["SIDE"] + "@" + str(r["AXIAL_START"]) for r in rs if r["SEAL_KIND"] == "UNRESOLVED_CHORD"}),
                           "COLUMN_RELATIONS": sorted({r["BAND_ID"] for r in rs if r["SEAL_KIND"] == "COLUMN_FACE"}), "ADJACENT_SPACES": sorted(adj),
                           "BOUNDARY_COMPOSITION_MM": s["BOUNDARY_COMPOSITION_MM"], "MATERIAL_BOUNDARY_MM": s["MATERIAL_BOUNDARY_MM"], "OPENING_MM": s["OPENING_MM"], "UNRESOLVED_MM": s["UNRESOLVED_MM"],
                           "TOPOLOGY_STATUS": topo, "SPACE_CLASS": s.get("SPACE_CLASS"), "IDENTITY_STATUS": s["SEMANTIC_IDENTITY"]["STATUS"], "ENGINE_ZONES": s["SEMANTIC_IDENTITY"]["ZONES"],
                           "READER_LABELS": [(r["TEXT_ID"], r["CLEAN_TEXT"], r["KEYBOARD_DECODED"], r["CANONICAL_CLASS"], r["IDENTITY_STATUS"]) for r in labels]})
    R["PA08_QORTUBA_PHYSICAL_SPACE_REGISTER"] = {"ARTIFACT": "PA08_QORTUBA_PHYSICAL_SPACE_REGISTER", "ROWS": space_rows, "COUNT": len(space_rows),
        "BY_TOPOLOGY_STATUS": dict(Counter(r["TOPOLOGY_STATUS"] for r in space_rows)),
        "RULE": "spaces are the engine's planar faces; labels were attached afterwards and never split or merged a cell; a door leaf missing never merged a room here (the merges come from partition faces left UNRESOLVED)"}

    # ---------------- 6 floor areas
    floor = []
    for sr in space_rows:
        merged = sr["TOPOLOGY_STATUS"].endswith("MERGED"); ext = sr["SPACE_CLASS"] in ("EXTERIOR_LABELLED", "EXTERIOR_SITE")
        status = "HUMAN_REVIEW" if (merged or ext or sr["ZONE_NAME"] == "UNLABELLED" and sr["GEOMETRIC_AREA_M2"] > 5) else ("GEOMETRIC_REFERENCE_ONLY" if sr["TOPOLOGY_STATUS"] != "ESTABLISHED" else "SOURCE_ESTABLISHED")
        cat = ("BATHROOM" if "BATHROOM" in sr["CANONICAL_CLASSES"] and not merged else "BEDROOM" if "BEDROOM" in sr["CANONICAL_CLASSES"] and not merged else "ROOF_OPEN" if ext else
               "PANTRY" if "PANTRY" in sr["CANONICAL_CLASSES"] else "MERGED_MULTI_ROOM_CELL" if merged else "UNLABELLED_CELL")
        floor.append({"ROOM_ZONE": sr["ZONE_NAME"], "SPACE_ID": sr["SPACE_ID"], "CATEGORY": cat, "PHYSICAL_SPACE_AREA_M2": sr["GEOMETRIC_AREA_M2"], "MEASUREMENT_BASIS": sr["AREA_BASIS"],
                      "FLOOR_FINISH_TRADE_ZONE_AREA_M2": None, "FLOOR_FINISH_ZONING": "NOT_ESTABLISHED (no finish schedule; one physical cell may hold several finishes)", "SOURCE": "engine planar face of the frozen blind run",
                      "STATUS": status, "WHY": ("cell holds the labels of several rooms: partitions between them are UNRESOLVED" if merged else "exterior-class label" if ext else "boundary provisional" if sr["TOPOLOGY_STATUS"] != "ESTABLISHED" else None)})
    R["PA08_QORTUBA_FLOOR_AREA_REGISTER"] = {"ARTIFACT": "PA08_QORTUBA_FLOOR_AREA_REGISTER", "ROWS": floor, "BY_STATUS": dict(Counter(r["STATUS"] for r in floor)), "BY_CATEGORY": dict(Counter(r["CATEGORY"] for r in floor)),
        "PROJECT_TOTAL": "REFUSED: coverage incomplete (no room area is SOURCE_ESTABLISHED; seven labelled rooms share one provisional cell)",
        "ROOMS_LABELLED_IN_SOURCE": ["HALL", "PAINTRY", "BED.ROOM", "BED.ROOM", "M.B.ROOM", "BATH", "BATH", "BATH", "DRESS", "ROOF"], "ROOMS_WITH_THEIR_OWN_CELL": [r["ROOM_ZONE"] for r in floor if r["CATEGORY"] in ("BATHROOM", "PANTRY", "ROOF_OPEN")]}

    # ---------------- 7 wet rooms
    wet = []
    for sr in space_rows:
        wetlabels = [r for r in sr["READER_LABELS"] if r[3] in WET_CLASSES or r[3] == "PANTRY"]
        if not wetlabels:
            continue
        rs = rows_by_space.get(sr["SPACE_ID"], [])
        merged = sr["TOPOLOGY_STATUS"].endswith("MERGED")
        host = round(sum(r["LENGTH_MM"] for r in rs if r["SEAL_KIND"] in ("FACE", "COLUMN_FACE")) / 1000, 3)
        open_edge = round(sum(r["LENGTH_MM"] for r in rs if r["SEAL_KIND"] == "UNRESOLVED_CHORD") / 1000, 3)
        doors = [r["SITE_ID"] for r in rs if r["SEAL_KIND"] == "OPENING_CHORD" and site_by.get(r["SITE_ID"], {}).get("CLASS", "").endswith("DOOR_OPENING")]
        wins = [r["SITE_ID"] for r in rs if r["SEAL_KIND"] == "OPENING_CHORD" and "WINDOW" in site_by.get(r["SITE_ID"], {}).get("CLASS", "")]
        gross = round(host + sum(r["LENGTH_MM"] for r in rs if r["SEAL_KIND"] == "OPENING_CHORD") / 1000, 3)
        st = "HUMAN_REVIEW" if merged else "GEOMETRIC_REFERENCE_ONLY"
        wet.append({"ROOM": sr["ZONE_NAME"], "SPACE_ID": sr["SPACE_ID"], "WET_LABELS": [(r[1], r[2], r[3]) for r in wetlabels], "MERGED_WITH_OTHER_ROOMS": merged,
                    "FLOOR_AREA_M2": {"VALUE": sr["GEOMETRIC_AREA_M2"], "STATUS": st}, "PHYSICAL_HOST_WALL_LM": {"VALUE": host, "STATUS": st}, "OPEN_EDGE_LM": {"VALUE": open_edge, "STATUS": st},
                    "DOOR_OPENING": doors or "NONE_ESTABLISHED", "WINDOW_OPENING": wins or "NONE_ESTABLISHED", "GROSS_WALL_LENGTH_LM": {"VALUE": gross, "STATUS": st},
                    "TILE_WALL_HEIGHT_STATUS": "SOURCE_REQUIRED (no section, no schedule, no owner Qortuba parameter; P7757 heights are not Qortuba rules)",
                    "WALL_TILE_AREA_STATUS": "NOT_ESTABLISHED", "WALL_TILE_AREA_FORMULA": "PHYSICAL_HOST_WALL_LM x TILE_WALL_HEIGHT - door / window areas within the tiled height (+ reveals per project rule)",
                    "WATERPROOFING_FLOOR_AREA_M2": {"VALUE": sr["GEOMETRIC_AREA_M2"], "STATUS": st, "NOTE": "floor waterproofing follows the floor region; upstand height is a separate vertical parameter"},
                    "VERTICAL_WATERPROOFING_STATUS": "NOT_ESTABLISHED (upstand height SOURCE_REQUIRED)"})
    R["PA08_QORTUBA_WET_ROOM_REGISTER"] = {"ARTIFACT": "PA08_QORTUBA_WET_ROOM_REGISTER", "ROWS": wet, "COUNT": len(wet),
        "NOTE": "three BATH label pairs exist in the source; one bath has its own provisional cell, two lie inside the merged cell; the pantry is listed because its finish class is a wet-room question for the owner"}

    # ---------------- 8 blockwork
    block = []
    for b in bands:
        if b["MATERIAL_STATUS"] not in ("ACCEPTED", "UNRESOLVED"):
            continue
        ivs = [i for i in intervals if i["HOST_BAND_ID"] == b["BAND_ID"]]
        opens = sorted({i.get("SITE_ID") for i in ivs if i["CLASS"] in ("OPENING", "UNRESOLVED") and i.get("SITE_ID")})
        cuts = [r for r in rows_by_band.get(b["BAND_ID"], []) if r["SEAL_KIND"] == "JUNCTION_CUT"]
        acc_ = b["MATERIAL_STATUS"] == "ACCEPTED"
        block.append({"WALL_ID": b["BAND_ID"], "PLAN_LENGTH_M": round(b["DEVELOPED_LENGTH_MM"] / 1000, 3), "PLAN_LENGTH_STATUS": "SOURCE_ESTABLISHED (band developed geometry)" if acc_ else "HUMAN_REVIEW (band UNRESOLVED: " + (b.get("REJECTION_REASON") or "").split(" (")[0] + ")",
                      "WALL_THICKNESS_MM": b["THICKNESS_MM"], "MATERIAL_TYPE_STATUS": "NOT_ESTABLISHED (thickness alone does not fix block vs concrete; no wall schedule)", "STOREY_ZONE": STOREY,
                      "OPENING_IDS": opens, "COLUMN_INTERRUPTION": [(r["SIDE"], r["AXIAL_START"], r["AXIAL_END"]) for r in cuts], "BEAM_RELATION": "UNKNOWN (no structural source)",
                      "WALL_HEIGHT_STATUS": "SOURCE_REQUIRED", "BLOCK_WALL_LENGTH_M": round(b["DEVELOPED_LENGTH_MM"] / 1000, 3), "HEIGHT_REQUIRED": True,
                      "GROSS_BLOCK_WALL_AREA_M2": {"VALUE": None, "STATUS": "NOT_ESTABLISHED", "FORMULA": "PLAN_LENGTH_M x WALL_HEIGHT"},
                      "NET_BLOCK_WALL_AREA_M2": {"VALUE": None, "STATUS": "NOT_ESTABLISHED", "FORMULA": "GROSS - opening areas per deduction rule (rule and opening heights not established)"}, "BAND_TYPE": b.get("BAND_TYPE")})
    R["PA08_QORTUBA_BLOCKWORK_REGISTER"] = {"ARTIFACT": "PA08_QORTUBA_BLOCKWORK_REGISTER", "ROWS": block,
        "ACCEPTED_PLAN_LENGTH_M_BY_THICKNESS": {str(int(k)): round(v / 1000, 3) for k, v in sorted(by_thk.items())}, "ACCEPTED_WALLS": sum(1 for r in block if r["PLAN_LENGTH_STATUS"].startswith("SOURCE")),
        "UNRESOLVED_WALL_CANDIDATES": sum(1 for r in block if r["PLAN_LENGTH_STATUS"].startswith("HUMAN")), "AREA_STATUS": "NOT_ESTABLISHED for every wall: no height in any source",
        "RULE": "walls kept separate by thickness; plan length never turned into area without a height; material never assumed from thickness"}

    # ---------------- 9/10 plaster + paint
    plaster, paint = [], []
    for sr in space_rows:
        rs = rows_by_space.get(sr["SPACE_ID"], [])
        merged = sr["TOPOLOGY_STATUS"].endswith("MERGED"); ext = sr["SPACE_CLASS"] != "INTERIOR"
        wetroom = any(c in WET_CLASSES for c in sr["CANONICAL_CLASSES"]) and not merged
        for r in rs:
            if r["SEAL_KIND"] not in ("FACE", "COLUMN_FACE") or not r["MATERIAL"]:
                continue
            b = band_by.get(r["BAND_ID"], {})
            cat = "COLUMN_BONDING" if r["SEAL_KIND"] == "COLUMN_FACE" else ("BATHROOM_WET_ROOM_TILE_PREP" if wetroom else "NORMAL_INTERNAL_PLASTER")
            st = "HUMAN_REVIEW" if (merged or ext) else "GEOMETRIC_REFERENCE_ONLY"
            fid = f"{r['BAND_ID']}@{r['SIDE']}@{r['AXIAL_START']}"
            plaster.append({"FACE_ID": fid, "ROOM_SPACE": sr["ZONE_NAME"], "SPACE_ID": sr["SPACE_ID"], "CATEGORY": cat, "DEVELOPED_LENGTH_M": round(r["LENGTH_MM"] / 1000, 3), "LENGTH_STATUS": st,
                            "BAND_STATUS": b.get("MATERIAL_STATUS"), "HEIGHT_SOURCE": "NONE (SOURCE_REQUIRED)", "GROSS_AREA_M2": None, "DOOR_DEDUCTION_M2": None, "WINDOW_DEDUCTION_M2": None, "REVEAL_AREA_M2": None,
                            "COLUMN_FACE_AREA_M2": None, "NET_AREA_M2": None, "STATUS": "NOT_ESTABLISHED" if st != "HUMAN_REVIEW" else "HUMAN_REVIEW",
                            "WHY": "vertical height not source-established; " + ("cell merged across unresolved partitions" if merged else "exterior cell" if ext else "boundary provisional")})
            paint.append({"FACE_ID": fid, "ROOM_SPACE": sr["ZONE_NAME"], "CATEGORY": "COLUMN_FACE" if r["SEAL_KIND"] == "COLUMN_FACE" else ("TILED_WALL_CANDIDATE" if wetroom else "PAINTED_WALL_CANDIDATE"),
                          "PAINT_ELIGIBLE_WALL_LM": round(r["LENGTH_MM"] / 1000, 3), "LENGTH_STATUS": st, "FINISH_ELIGIBILITY": "NOT_ESTABLISHED (no finish schedule: paint is not assumed on every plastered face)",
                          "PAINT_AREA_M2": None, "STATUS": "PAINT_AREA_NOT_ESTABLISHED"})
    def _sum(rows, key):
        out = defaultdict(float)
        for r in rows:
            out[(r["ROOM_SPACE"], r["CATEGORY"])] += r[key]
        return {f"{k[0]} | {k[1]}": round(v, 3) for k, v in sorted(out.items())}
    R["PA08_QORTUBA_PLASTER_REGISTER"] = {"ARTIFACT": "PA08_QORTUBA_PLASTER_REGISTER", "ROWS": plaster, "ELIGIBLE_LENGTH_M_BY_ROOM_AND_CATEGORY": _sum(plaster, "DEVELOPED_LENGTH_M"), "BY_STATUS": dict(Counter(r["STATUS"] for r in plaster)),
        "PLASTER_AREA": "NOT_ESTABLISHED for every face: no Qortuba height exists; P7757's 3.20 m is not reused", "RULE": "normal plaster is not applied behind wall tile unless the project rule says so; wet-room faces are listed as TILE_PREP candidates"}
    R["PA08_QORTUBA_PAINT_REGISTER"] = {"ARTIFACT": "PA08_QORTUBA_PAINT_REGISTER", "ROWS": paint, "ELIGIBLE_LENGTH_M_BY_ROOM_AND_CATEGORY": _sum(paint, "PAINT_ELIGIBLE_WALL_LM"),
        "PAINT_AREA": "NOT_ESTABLISHED: physical face known in plan only; height, opening deductions and finish eligibility absent", "CATEGORIES": ["PAINTED_WALL", "TILED_WALL", "CLAD_WALL", "GLAZING", "OPENING", "COLUMN_FACE", "CEILING"]}

    # ---------------- 11 ceiling
    ceil = []
    for sr in space_rows:
        merged = sr["TOPOLOGY_STATUS"].endswith("MERGED"); ext = sr["SPACE_CLASS"] != "INTERIOR"
        ceil.append({"ROOM": sr["ZONE_NAME"], "SPACE_ID": sr["SPACE_ID"], "BASE_FLOOR_REGION_M2": {"VALUE": sr["GEOMETRIC_AREA_M2"], "STATUS": "GEOMETRIC_REFERENCE_ONLY"},
                     "VOID_DEDUCTION": "NOT_ESTABLISHED (no section)", "STAIR_OPENING_DEDUCTION": "NOT_ESTABLISHED (stair cell not isolated by the engine)", "SHAFT_DEDUCTION": "NOT_ESTABLISHED (lift shaft on layer 'lift' not isolated by the engine)",
                     "OPEN_TO_ABOVE_DEDUCTION": "NOT_ESTABLISHED", "OTHER_NO_CEILING_ZONE": "roof / open cells have no ceiling" if ext else "NOT_ESTABLISHED",
                     "NET_CEILING_GEOMETRY_M2": {"VALUE": None, "STATUS": "NOT_APPLICABLE" if ext else ("HUMAN_REVIEW" if merged else "NOT_ESTABLISHED")},
                     "CEILING_FINISH_STATUS": "NOT_ESTABLISHED (GYPSUM / PAINTED / DECORATIVE unknown: no ceiling plan)", "RULE": "ceiling geometry is derived from the floor region only when no vertical interruption exists; that is not established here"})
    R["PA08_QORTUBA_CEILING_REGISTER"] = {"ARTIFACT": "PA08_QORTUBA_CEILING_REGISTER", "ROWS": ceil, "BY_STATUS": dict(Counter(r["NET_CEILING_GEOMETRY_M2"]["STATUS"] for r in ceil))}

    # ---------------- 12 skirting
    skirt = []
    for sr in space_rows:
        if sr["ZONE_NAME"] == "UNLABELLED" and sr["GEOMETRIC_AREA_M2"] < 5:
            continue
        rs = rows_by_space.get(sr["SPACE_ID"], [])
        merged = sr["TOPOLOGY_STATUS"].endswith("MERGED"); ext = sr["SPACE_CLASS"] != "INTERIOR"; wetroom = any(c in WET_CLASSES for c in sr["CANONICAL_CLASSES"]) and not merged
        gross = sum(r["LENGTH_MM"] for r in rs if r["SEAL_KIND"] in ("FACE", "COLUMN_FACE"))
        door = sum(r["LENGTH_MM"] for r in rs if r["SEAL_KIND"] == "OPENING_CHORD" and site_by.get(r["SITE_ID"], {}).get("CLASS", "").endswith("DOOR_OPENING"))
        open_edge = sum(r["LENGTH_MM"] for r in rs if r["SEAL_KIND"] == "UNRESOLVED_CHORD")
        non = sum(r["LENGTH_MM"] for r in rs if r["SEAL_KIND"] in ("JUNCTION_CHORD", "THICKNESS_CHORD"))
        st = "NOT_APPLICABLE_PENDING_RULE" if ext else ("HUMAN_REVIEW" if (merged or open_edge > 0) else "GEOMETRIC_REFERENCE_ONLY")
        skirt.append({"FLOOR_FINISH_ZONE": sr["ZONE_NAME"], "SPACE_ID": sr["SPACE_ID"], "SKIRTING_GROSS_LM": round(gross / 1000, 3), "DOOR_DEDUCTION_LM": round(door / 1000, 3), "OPEN_EDGE_DEDUCTION_LM": round(open_edge / 1000, 3),
                      "NON_SKIRTING_EDGE_LM": round(non / 1000, 3), "NET_SKIRTING_ELIGIBLE_LM": round(gross / 1000, 3), "BASIS": "eligible wall lines (accepted band faces) minus nothing: door chords are not wall lines; open edges listed separately",
                      "WET_ROOM_RULE": "NORMAL_SKIRTING_NOT_APPLICABLE depends on the project wall-tile rule" if wetroom else None, "PROFILE_PATH_ID": f"WALLLINE-{sr['SPACE_ID']}",
                      "PROFILE_NOTE": "the same wall-line path is exposed for a future separate profile item; no profile item is created", "STATUS": st})
    R["PA08_QORTUBA_SKIRTING_REGISTER"] = {"ARTIFACT": "PA08_QORTUBA_SKIRTING_REGISTER", "ROWS": skirt, "BY_STATUS": dict(Counter(r["STATUS"] for r in skirt)),
        "RULE": "skirting follows eligible wall lines, not the polygon perimeter; SKIRTING and any PROFILE stay separate BOQ items on the same path"}

    # ---------------- 13 openings (+ source observations)
    n = CA.normalize(C.decode(), source_file=Path(C.DECODE).name)
    scale = 10.0
    doors_obs = defaultdict(list)
    for p in n.primitives:
        if p.provenance.block_path == ("6",):
            doors_obs[p.provenance.instance_path].append(p)
    door_obs = []
    for k, segs in doors_obs.items():
        L = max(math.hypot(p.x2 - p.x1, p.y2 - p.y1) for p in segs) * scale
        xs = [v for p in segs for v in (p.x1, p.x2)]; ys = [v for p in segs for v in (p.y1, p.y2)]
        door_obs.append({"INSTANCE": str(k), "LEAF_LENGTH_MM_MAX_SEGMENT": round(L, 1), "BBOX_MM": [round(min(xs) * scale), round(min(ys) * scale), round(max(xs) * scale), round(max(ys) * scale)], "SWING_ARC": "NONE (block draws leaf + frame only)"})
    win_lines = [p for p in n.primitives if p.provenance.layer == "WINDOW"]
    groups = []
    for p in win_lines:
        cx, cy = (p.x1 + p.x2) / 2, (p.y1 + p.y2) / 2
        for g in groups:
            if abs(g["cx"] - cx) < 30 and abs(g["cy"] - cy) < 30:
                g["n"] += 1; break
        else:
            groups.append({"cx": cx, "cy": cy, "n": 1, "LENGTH_MM": round(math.hypot(p.x2 - p.x1, p.y2 - p.y1) * scale, 1)})
    opening_rows = []
    for s in sites:
        b = band_by.get(s["HOST_BAND_ID"], {})
        typ = {"CONFIRMED_DOOR_OPENING": "DOOR", "PROBABLE_DOOR_OPENING": "DOOR_PROBABLE", "CONFIRMED_WINDOW_OPENING": "WINDOW", "CONFIRMED_GLAZED_OPENING": "GLAZED", "CONFIRMED_OPEN_PASSAGE": "OPEN_PASSAGE",
               "CAD_JUNCTION": "NOT_AN_OPENING_JUNCTION", "MATERIAL_CONTINUITY": "NOT_AN_OPENING", "UNRESOLVED": "UNRESOLVED_GAP"}[s["CLASS"]]
        est = s["STATUS"] == "ESTABLISHED" and typ in ("DOOR", "WINDOW", "GLAZED", "OPEN_PASSAGE")
        opening_rows.append({"OPENING_ID": s["SITE_ID"], "TYPE": typ, "ENGINE_CLASS": s["CLASS"], "ENGINE_STATUS": s["STATUS"], "HOST_WALL": s["HOST_BAND_ID"], "HOST_THICKNESS_MM": b.get("THICKNESS_MM"),
                             "WIDTH_MM": {"VALUE": s["SPAN_MM"], "STATUS": "SOURCE_ESTABLISHED" if est else "PROVISIONAL" if s["STATUS"] == "PROVISIONAL" else "NOT_ESTABLISHED"},
                             "HEIGHT_MM": {"VALUE": None, "STATUS": "SOURCE_REQUIRED (no schedule, no elevation; no default used in the blind test)"}, "SHAPE": "NOT_ESTABLISHED", "AREA_M2": None,
                             "JAMB_LM": None, "HEAD_LM": {"VALUE": round(s["SPAN_MM"] / 1000, 3), "STATUS": "GEOMETRIC_REFERENCE_ONLY (= width)"} if est else None, "SILL_LM": None,
                             "REVEAL_DEPTH_MM": {"VALUE": b.get("THICKNESS_MM"), "STATUS": "GEOMETRIC_REFERENCE_ONLY (host wall thickness)"}, "REASON": s.get("REASON"),
                             "STATUS": "SOURCE_ESTABLISHED_WIDTH_ONLY" if est else ("PROVISIONAL" if s["STATUS"] == "PROVISIONAL" else "HUMAN_REVIEW")})
    R["PA08_QORTUBA_OPENING_REGISTER"] = {"ARTIFACT": "PA08_QORTUBA_OPENING_REGISTER", "ROWS": opening_rows, "BY_TYPE": dict(Counter(r["TYPE"] for r in opening_rows)), "BY_STATUS": dict(Counter(r["STATUS"] for r in opening_rows)),
        "SOURCE_OBSERVATIONS": {"DOOR_BLOCK_INSTANCES": door_obs, "DOOR_BLOCK_COUNT": len(door_obs), "WINDOW_FRAME_LINE_GROUPS": len(groups), "WINDOW_FRAME_GROUP_LENGTHS_MM": sorted(g["LENGTH_MM"] for g in groups),
                                "NOTE": "8 door blocks and 7 window frame groups are visible in the DWG; the engine established 1 door and 1 provisional window because the host partitions are UNRESOLVED and the door blocks carry no swing arc"},
        "RULE": "opening geometry stays separate from wall quantity; heights never defaulted in the blind test"}

    # ---------------- 14 stairs (source observation from the STAIR layer)
    st_lines = [p for p in n.primitives if p.provenance.layer == "STAIR" and p.kind == "SEGMENT"]
    horiz = [p for p in st_lines if abs(p.y1 - p.y2) < 0.5]
    flights = defaultdict(list)
    for p in horiz:
        flights[(round(min(p.x1, p.x2)), round(max(p.x1, p.x2)))].append(round(p.y1, 1))
    fl, single = [], []
    for (x0, x1), ys in sorted(flights.items()):
        ys = sorted(set(ys)); pitches = [round((b_ - a_) * scale, 1) for a_, b_ in zip(ys, ys[1:])]
        if len(ys) < 2:
            single.append({"X_RANGE_MM": [x0 * scale, x1 * scale], "Y_MM": ys[0] * scale, "NOTE": "single line across the well: landing edge or well line, not a flight"}); continue
        fl.append({"FLIGHT_X_RANGE_MM": [x0 * scale, x1 * scale], "FLIGHT_WIDTH_MM": round((x1 - x0) * scale, 1), "NOSING_LINES": len(ys), "TREADS_IN_PLAN": len(ys) - 1, "TREAD_GOING_MM": sorted(set(pitches)), "RUN_MM": round((ys[-1] - ys[0]) * scale, 1),
                   "TREAD_PLAN_AREA_M2": round((len(ys) - 1) * ((x1 - x0) * scale / 1000) * (pitches[0] / 1000), 3) if pitches else None})
    xs = [v for p in st_lines for v in (p.x1, p.x2)]; ys_ = [v for p in st_lines for v in (p.y1, p.y2)]
    R["PA08_QORTUBA_STAIR_REGISTER"] = {"ARTIFACT": "PA08_QORTUBA_STAIR_REGISTER", "SOURCE": "STAIR layer lines of the DWG (24 nosing lines + 4 well lines); plan reading only",
        "FLIGHTS": fl, "FLIGHT_COUNT": len(fl), "OTHER_STAIR_LINES": single, "TREAD_COUNT_IN_PLAN": sum(f["TREADS_IN_PLAN"] for f in fl), "TREAD_DEPTH_MM": sorted({g for f in fl for g in f["TREAD_GOING_MM"]}),
        "RISER_COUNT": "NOT_ESTABLISHED (plan only; a riser count needs the section or the floor-to-floor height)", "RISER_HEIGHT": "NOT_ESTABLISHED",
        "LANDING_GEOMETRY": "HUMAN_REVIEW (the well polyline between the flights is not separated as a landing by the engine)",
        "STAIR_OPENING_BBOX_MM": [round(min(xs) * scale), round(min(ys_) * scale), round(max(xs) * scale), round(max(ys_) * scale)], "STAIR_OPENING_AREA_STATUS": "GEOMETRIC_REFERENCE_ONLY (bbox of the stair lines, not a slab opening)",
        "ADJACENT_STAIR_WALLS": "HUMAN_REVIEW (bands around the well are ACCEPTED 200 mm envelope pieces and UNRESOLVED 150 mm partitions)", "RAILING_OPEN_SIDE": "NOT_ESTABLISHED", "SLAB_BEAM_RELATIONSHIPS": "NOT_ESTABLISHED (no structural source)",
        "OUTPUTS": {"TREAD_AREA_M2": {"VALUE": round(sum(f["TREAD_PLAN_AREA_M2"] or 0 for f in fl), 3), "STATUS": "GEOMETRIC_REFERENCE_ONLY (plan going x width, both flights)"}, "RISER_AREA": "NOT_ESTABLISHED", "LANDING_AREA": "HUMAN_REVIEW",
                    "STAIR_WALL_LM": "HUMAN_REVIEW", "STAIR_WALL_AREA": "NOT_ESTABLISHED", "STAIR_OPENING_AREA": "GEOMETRIC_REFERENCE_ONLY", "SOFFIT_AREA": "NOT_ESTABLISHED"},
        "RULE": "no vertical stair quantity from plan alone"}

    # ---------------- 15 columns
    col_rows = []
    for c in cols["ROWS"]:
        col_rows.append({"COLUMN_ID": c["COLUMN_ID"], "OBJECT_EXISTS": c["OBJECT_EXISTS"]["STATUS"], "GEOMETRY": c["OBJECT_GEOMETRY"], "ROOM_EXPOSURE": c["EXPOSED_TO_SPACE"], "WALL_TERMINATION": {"HOSTS": c["HOSTS_WALL"], "TERMINATES": c["TERMINATES_WALL"]},
                         "FINISH_FACE": "NOT_ESTABLISHED (finish schedule absent)", "TRADE_ELIGIBILITY": c["TRADE_ELIGIBILITY"], "EXPOSED_FACE_LM": {"VALUE": round(c["EXPOSED_TO_SPACE"]["EXPOSED_MM_STRUCTURE_ONLY"] / 1000, 3), "STATUS": "GEOMETRIC_REFERENCE_ONLY (adjacent cells provisional)"},
                         "GIRTH_RULE": "full girth never counted; only exposed stretches; embedded faces never double counted with wall faces (JUNCTION_CUT ownership)"})
    R["PA08_QORTUBA_COLUMN_REGISTER"] = {"ARTIFACT": "PA08_QORTUBA_COLUMN_REGISTER", "ROWS": col_rows, "COUNT": len(col_rows), "CANDIDATES_UNCONFIRMED": cols.get("CANDIDATES_UNCONFIRMED", []), "SUMMARY": cols["SUMMARY"],
        "SOURCE_NOTE": "COL layer holds 40 segments and A-COL-HAT 10 hatches (≈10 hatched column outlines); the engine accepted 4 column bands and listed 2 candidates; the rest are inside rejected / unresolved candidates: HUMAN_REVIEW"}

    # ---------------- 16 roof / open areas
    roof = []
    for sr in space_rows:
        cls = "ENCLOSED_INTERIOR_CANDIDATE"
        if sr["SPACE_CLASS"] in ("EXTERIOR_LABELLED",):
            cls = "OPEN_ROOF"
        elif sr["GEOMETRIC_AREA_M2"] > 300:
            cls = "SITE_REGION_BETWEEN_PLOT_BOUNDARY_AND_BUILDING"
        elif sr["ZONE_NAME"] == "UNLABELLED":
            cls = "UNLABELLED_CELL (interior / shaft / well / sliver undetermined)"
        roof.append({"SPACE_ID": sr["SPACE_ID"], "ZONE": sr["ZONE_NAME"], "CLASSIFICATION": cls, "ENGINE_SPACE_CLASS": sr["SPACE_CLASS"], "PLAN_AREA_M2": {"VALUE": sr["GEOMETRIC_AREA_M2"], "STATUS": "GEOMETRIC_REFERENCE_ONLY"},
                     "STATUS": "HUMAN_REVIEW" if cls.startswith(("SITE", "UNLABELLED")) else ("GEOMETRIC_REFERENCE_ONLY" if cls == "OPEN_ROOF" else "HUMAN_REVIEW"),
                     "NOTE": "the ROOF-labelled cell is a fragment: its other sides are unresolved chords of the plot boundary lines" if cls == "OPEN_ROOF" else None})
    R["PA08_QORTUBA_ROOF_OPEN_AREA_REGISTER"] = {"ARTIFACT": "PA08_QORTUBA_ROOF_OPEN_AREA_REGISTER", "ROWS": roof, "FINISH_AND_WATERPROOFING": "separate trade questions, NOT_ESTABLISHED", "ENGINE_DEFECT_NOTE": "the 636 m2 site region is classed INTERIOR by the engine (blocked by SPACE_STATUS provisional; see PA08_BLIND_DEFECTS)"}

    # ---------------- 18 quantity trace
    trace = []
    for l in trace7:
        trace.append({"QUANTITY_ID": l["LINE_ID"], "TRADE": l["TRADE"], "ROOM_ZONE": l["SPACE_ID"], "GEOMETRY_IDS": [l["SPACE_ID"]], "LENGTH_SOURCE": "PA07 boundary rows (band developed geometry)", "HEIGHT_SOURCE": "NONE (UNKNOWN in the blind registry)",
                      "OPENING_SOURCE": "PA07 opening sites", "RULE_SOURCE": "URBAN_RULES_PA08_QORTUBA_BLIND (generic)", "MEASUREMENT_BASIS": l["MEASUREMENT_BASIS"],
                      "FORMULA": "eligible developed wall length x approved height - opening deductions + reveals (not evaluated: gates blocked)", "VALUE": None, "UNIT": "m2", "STATUS": l["QUANTITY_STATUS"], "BLOCKED_BY": l["BLOCKED_BY"], "REGION_STATUS": l["REGION_STATUS"]})
    # deterministic horizontal lines of this research layer
    for thk, mm in sorted(by_thk.items()):
        trace.append({"QUANTITY_ID": f"QL-BLOCK-LENGTH-{int(thk)}", "TRADE": "BLOCKWORK", "ROOM_ZONE": "ALL_ACCEPTED_BANDS", "GEOMETRY_IDS": [w["BAND_ID"] for w in acc if w["THICKNESS_MM"] == thk], "LENGTH_SOURCE": "PA07 accepted bands (developed geometry)",
                      "HEIGHT_SOURCE": "NONE", "OPENING_SOURCE": "not deducted from length", "RULE_SOURCE": "generic", "MEASUREMENT_BASIS": "AXIS developed length", "FORMULA": "sum of accepted band developed lengths of this thickness", "VALUE": round(mm / 1000, 3), "UNIT": "m",
                      "STATUS": "SOURCE_ESTABLISHED_PLAN_LENGTH_ONLY", "NOTE": "a plan length, not a wall area"})
    for f in fl:
        trace.append({"QUANTITY_ID": f"QL-STAIR-TREAD-{f['FLIGHT_X_RANGE_MM'][0]}", "TRADE": "STAIR", "ROOM_ZONE": "STAIR", "GEOMETRY_IDS": ["STAIR layer nosing lines"], "LENGTH_SOURCE": "DWG STAIR layer (plan)", "HEIGHT_SOURCE": "NONE",
                      "OPENING_SOURCE": "n/a", "RULE_SOURCE": "generic", "MEASUREMENT_BASIS": "plan going x flight width", "FORMULA": f"{f['TREADS_IN_PLAN']} treads x {f['FLIGHT_WIDTH_MM']} mm x {f['TREAD_GOING_MM']} mm", "VALUE": f["TREAD_PLAN_AREA_M2"], "UNIT": "m2", "STATUS": "GEOMETRIC_REFERENCE_ONLY"})
    for fr in floor:
        trace.append({"QUANTITY_ID": f"QL-FLOOR-{fr['SPACE_ID']}", "TRADE": "FLOOR_AREA", "ROOM_ZONE": fr["ROOM_ZONE"], "GEOMETRY_IDS": [fr["SPACE_ID"]], "LENGTH_SOURCE": "PA07 planar face", "HEIGHT_SOURCE": "n/a", "OPENING_SOURCE": "n/a", "RULE_SOURCE": "generic",
                      "MEASUREMENT_BASIS": fr["MEASUREMENT_BASIS"], "FORMULA": "free-mask cell count x 0.0025 m2 + half boundary strip", "VALUE": fr["PHYSICAL_SPACE_AREA_M2"], "UNIT": "m2", "STATUS": fr["STATUS"]})
    R["PA08_QORTUBA_QUANTITY_TRACE"] = {"ARTIFACT": "PA08_QORTUBA_QUANTITY_TRACE", "LINES": trace, "COUNT": len(trace), "BY_STATUS": dict(Counter(l["STATUS"] for l in trace)), "TOTALS": None,
        "SAFETY": {"ENGINE_SAFETY_ROWS": len(safety), "BRIDGE_ALLOWED": sum(1 for r in safety if r["BRIDGE_ALLOWED"]), "BLOCKED_BY_GATE": dict(Counter(g for r in safety for g in r["BLOCKED_BY"]))},
        "RULE": "no naked number: every line carries its state, sources and formula; no total"}

    # ---------------- 26 coverage
    rooms = ["HALL", "PAINTRY", "BED.ROOM (1)", "BED.ROOM (2)", "M.B.ROOM", "BATH (1)", "BATH (2)", "BATH (3)", "DRESS", "ROOF", "STAIR", "LIFT SHAFT"]
    own_cell = {"BATH": 1, "PAINTRY": 1, "ROOF": 1}
    def cover(trade, per_room_state):
        return {"TRADE": trade, "TOTAL_EXPECTED_COMPONENTS": len(rooms), "BY_STATE": dict(Counter(per_room_state.values())), "BY_ROOM": per_room_state}
    def states(default, special=None):
        out = {}
        for r in rooms:
            key = r.split(" ")[0]
            out[r] = (special or {}).get(key, default)
        return out
    cov = [cover("FLOOR_AREA", states("HUMAN_REVIEW", {"BATH": "GEOMETRIC_REFERENCE_ONLY (one of three baths)", "PAINTRY": "GEOMETRIC_REFERENCE_ONLY", "ROOF": "GEOMETRIC_REFERENCE_ONLY (fragment)", "STAIR": "GEOMETRIC_REFERENCE_ONLY (tread plan)", "LIFT": "NOT_ESTABLISHED"})),
           cover("WET_ROOM_WALL_TILE", states("NOT_APPLICABLE", {"BATH": "NOT_ESTABLISHED (host length known for one bath; height SOURCE_REQUIRED)", "PAINTRY": "HUMAN_REVIEW (finish class)"})),
           cover("BLOCKWORK_AREA", states("NOT_ESTABLISHED (height SOURCE_REQUIRED)")), cover("BLOCKWORK_PLAN_LENGTH", states("HUMAN_REVIEW (partitions unresolved)", {"ROOF": "SOURCE_ESTABLISHED (200 mm envelope bands)"})),
           cover("INTERNAL_PLASTER", states("NOT_ESTABLISHED (height SOURCE_REQUIRED; cell merged)", {"BATH": "NOT_ESTABLISHED (length known for one bath)", "PAINTRY": "NOT_ESTABLISHED (length known)", "ROOF": "NOT_APPLICABLE"})),
           cover("PAINT", states("NOT_ESTABLISHED", {"ROOF": "NOT_APPLICABLE"})), cover("CEILING", states("NOT_ESTABLISHED", {"ROOF": "NOT_APPLICABLE"})),
           cover("SKIRTING_ELIGIBLE_LENGTH", states("HUMAN_REVIEW", {"BATH": "GEOMETRIC_REFERENCE_ONLY (one bath) / rule pending", "PAINTRY": "GEOMETRIC_REFERENCE_ONLY", "ROOF": "NOT_APPLICABLE"})),
           cover("OPENINGS", states("HUMAN_REVIEW (1 door + 1 window established of 8 door blocks and 7 window groups)")), cover("STAIR", states("NOT_APPLICABLE", {"STAIR": "GEOMETRIC_REFERENCE_ONLY (plan) / NOT_ESTABLISHED (vertical)"})),
           cover("COLUMNS", states("HUMAN_REVIEW"))]
    R["PA08_QORTUBA_COVERAGE"] = {"ARTIFACT": "PA08_QORTUBA_COVERAGE", "ROOMS_ZONES": rooms, "BY_TRADE": cov, "OVERALL_ACCURACY_SCORE": "REFUSED (no independent truth opened)",
        "SOURCE_ESTABLISHED_QUANTITY_LINES": 0, "SOURCE_ESTABLISHED_PLAN_LENGTHS": {"ACCEPTED_WALL_BANDS": len(acc), "METRES": round(sum(by_thk.values()) / 1000, 3)}}
    for name, obj in R.items():
        C.write(name, obj)
    return R


if __name__ == "__main__":
    R = build()
    print(json.dumps({k: (v.get("COUNTS") or v.get("BY_STATUS") or v.get("COUNT") or v.get("BY_TYPE")) for k, v in R.items()}, default=str)[:2500])
    print(json.dumps(R["PA08_QORTUBA_STAIR_REGISTER"]["FLIGHTS"], default=str)[:600])
    print(json.dumps(R["PA08_QORTUBA_OPENING_REGISTER"]["SOURCE_OBSERVATIONS"], default=str)[:900])
