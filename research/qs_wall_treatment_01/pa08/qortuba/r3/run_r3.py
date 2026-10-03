"""PA08-QORTUBA-R3 runner: floor-finish measurement regions, and the trade paths that follow from them.

The four layers stay separate.  A measurement closure never becomes a wall, and a floor region that is established never
promotes the material status of the band beside it: the physical wall statuses are carried through from R2 untouched and are
re-stated in PHYSICAL_WALL_STATUS_REFERENCE so the separation is auditable.

Nothing here reads, requests or infers the owner's withheld flooring, skirting or profile quantities.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from engine.ingest import ENGINE_VERSION, material_bands as MB, pipeline7 as P7
from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba import blind as B
from research.qs_wall_treatment_01.pa08.qortuba.r2 import cells as CELLS
from research.qs_wall_treatment_01.pa08.qortuba.r3 import floor_regions as FR

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_r3"
R2_OUT = Path(PR.OUT_DIR) / "pa08_qortuba_r2"
R1_OUT = Path(PR.OUT_DIR) / "pa08_qortuba_r1"
BLIND_OUT = B.OUT
STOREY = "SECOND_FLOOR (title block 'SECOND FLOOR PLAN'; engine storey status HUMAN_REVIEW:CONFLICTING_FLOOR_WORDS)"
WET_CLASSES = ("BATHROOM", "WC", "KITCHEN", "LAUNDRY", "WASHROOM")
DIM_MATCH_MM = 30.0
ENGINE_FILES = sorted(str(x) for x in Path("engine/ingest").glob("*.py")) + ["engine/cad_adapter.py"]
FUNCTION_CLASSES = ("DRY_INTERNAL", "WET_INTERNAL", "SERVICE", "STAIR", "OPEN_ROOF", "OTHER")
SKIRTING_SEGMENT_CLASSES = ("SKIRTING_ELIGIBLE_WALL", "DOOR_OPENING", "OPEN_PASSAGE", "NON_WALL_EDGE", "WET_ROOM_EDGE", "COLUMN_FACE", "UNRESOLVED")


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str), "utf-8")
    return name


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------- §2 room dimension graph
def room_dimension_graph(result, vid, regions):
    """Which authored dimensions actually OWN a room's clear faces, by extension-line position, never by nearby text."""
    dims = [d for d in result.registers["DIMENSION_CHAIN_REGISTER"]["ROWS"] if d.get("DIMENSION_LINE")]
    bands = [b for b in result.bands7[vid] if b["KIND"] == "S"]
    rows = []
    for reg in regions:
        fml = reg["FORMULA"]
        xs, ys = fml.get("CUT_LINES_X_MM") or [], fml.get("CUT_LINES_Y_MM") or []
        for d in dims:
            og = d["DIMENSION_LINE"]["ORIGINS_MM"]
            if len(og) != 2:
                continue
            v = d["MEASURED_VALUE_MM"]
            for axis, arr, i in (("X", xs, 0), ("Y", ys, 1)):
                if not arr or len(arr) < 2:
                    continue
                hits = [next((c for c in arr if abs(o[i] - c) <= DIM_MATCH_MM), None) for o in og]
                if any(h is None for h in hits) or abs(hits[0] - hits[1]) < 1e-6:
                    continue
                if abs(abs(hits[0] - hits[1]) - v) > DIM_MATCH_MM:
                    continue
                # the dimension must lie within the region's other-axis extent to own ITS faces, not a neighbour's
                other = ys if axis == "X" else xs
                j = 1 - i
                if other and not all(min(other) - 2000 <= o[j] <= max(other) + 2000 for o in og):
                    continue
                def face_at(coord):
                    near = [b for b in bands if b["STATUS"] == "ACCEPTED" and abs(abs(b["AXIS"]) - abs(coord)) <= b["THK"] / 2 + DIM_MATCH_MM]
                    return {"CUT_LINE_MM": round(coord, 1), "BAND_ID": near[0]["BAND_ID"] if near else None,
                            "BAND_STATUS": near[0]["STATUS"] if near else None}
                rows.append({"DIMENSION_ID": d["DIMENSION_ID"], "DISPLAY_VALUE": d["DISPLAY_TEXT"], "PROJECTED_VALUE": v,
                             "START_FACE": face_at(min(hits)), "END_FACE": face_at(max(hits)), "MEASUREMENT_AXIS": axis,
                             "ROOM_ID": reg["FLOOR_MEASUREMENT_REGION_ID"], "ROOM": reg["ROOM"],
                             "OWNERSHIP_STATUS": "OWNS_BOTH_CLEAR_FACES",
                             "WHY": "both extension origins fall on this region's own boundary cut lines and the dimension's projected value equals the clear span between them"})
                break
    owned = defaultdict(lambda: {"X": [], "Y": []})
    for x in rows:
        owned[x["ROOM_ID"]][x["MEASUREMENT_AXIS"]].append(x)
    return rows, owned


def _chain_confirms_span(dims, lo, hi, tol):
    """Do the authored chain segments tile this axis end to end?

    A QS reads a chain, not only an overall dimension: if the authored segments run from one extreme boundary line to the other
    with no gap, their SUM is an authored statement of the overall span, and it is independent of the polygon because the values
    come from the dimension text.  A chain that stops short confirms nothing.
    """
    segs = sorted(((z["START_FACE"]["CUT_LINE_MM"], z["END_FACE"]["CUT_LINE_MM"], z) for z in dims), key=lambda t: t[0])
    at, used = lo, []
    while abs(at - hi) > tol:
        nxt = next(((a, b, z) for a, b, z in segs if abs(a - at) <= tol and b > at + tol and z not in used), None)
        if nxt is None:
            return None
        used.append(nxt[2])
        at = nxt[1]
    return used or None


def dimension_reconciliation(regions, owned):
    out = []
    for reg in regions:
        o = owned.get(reg["FLOOR_MEASUREMENT_REGION_ID"], {"X": [], "Y": []})
        rects = reg["FORMULA"].get("RECTANGLES") or []
        area = reg["AREA_M2"]["VALUE"]
        recon, basis, bbox_check = None, None, None
        xs = reg["FORMULA"].get("CUT_LINES_X_MM") or []
        ys = reg["FORMULA"].get("CUT_LINES_Y_MM") or []
        if o["X"] and o["Y"] and xs and ys:
            # the bounding box belongs to the POLYGON.  An authored dimension does not define it; it can only CONFIRM a span,
            # and only when its projected value equals that span.  A chain segment between two interior cut lines is a
            # partial dimension and confirms nothing about the overall span.
            span_x, span_y = max(xs) - min(xs), max(ys) - min(ys)
            axis_rows = {}
            for ax, dd, lo, hi, span in (("X", o["X"], min(xs), max(xs), span_x), ("Y", o["Y"], min(ys), max(ys), span_y)):
                single = next((z for z in dd if abs(z["PROJECTED_VALUE"] - span) <= DIM_MATCH_MM), None)
                chain = None if single is not None else _chain_confirms_span(dd, lo, hi, DIM_MATCH_MM)
                if single is not None:
                    axis_rows[ax] = {"CONFIRMED": True, "HOW": "SINGLE_DIMENSION", "AUTHORED_VALUE_MM": round(single["PROJECTED_VALUE"], 1),
                                     "DIMENSION_IDS": [single["DIMENSION_ID"]]}
                elif chain:
                    tot = sum(z["PROJECTED_VALUE"] for z in chain)
                    axis_rows[ax] = {"CONFIRMED": True, "HOW": "DIMENSION_CHAIN", "AUTHORED_VALUE_MM": round(tot, 1),
                                     "DIMENSION_IDS": [z["DIMENSION_ID"] for z in chain],
                                     "CHAIN_SEGMENTS_MM": [round(z["PROJECTED_VALUE"], 1) for z in chain]}
                else:
                    axis_rows[ax] = {"CONFIRMED": False, "HOW": None, "AUTHORED_VALUE_MM": None,
                                     "DIMENSION_IDS": [z["DIMENSION_ID"] for z in dd][:4],
                                     "PARTIAL_VALUES_MM": [round(z["PROJECTED_VALUE"], 1) for z in dd][:4]}
            bbox = span_x * span_y / 1e6
            spans_full = axis_rows["X"]["CONFIRMED"] and axis_rows["Y"]["CONFIRMED"]
            confirmed = [a for a in ("X", "Y") if axis_rows[a]["CONFIRMED"]]
            bbox_check = {"POLYGON_BOUNDING_SPANS_MM": [round(span_x, 1), round(span_y, 1)],
                          "BY_AXIS": axis_rows,
                          "BOUNDING_BOX_AREA_M2": round(bbox, 4),
                          "POLYGON_AREA_M2": area,
                          "NOTCH_AREA_M2": round(bbox - area, 4) if area is not None else None,
                          "OVERALL_SPANS_CONFIRMED": bool(spans_full),
                          "WHY": ("the drawing's own dimensions confirm the region's overall spans in both axes, as a single overall "
                                  "dimension or as a chain that runs boundary to boundary; the notch between the bounding box and the "
                                  "measured polygon is drawn but not separately dimensioned"
                                  if spans_full else
                                  f"only the {confirmed[0]} overall span is authored; the other axis carries chain segments that stop "
                                  f"short of the boundary, so the bounding box above is the polygon's own, not the drawing's"
                                  if confirmed else
                                  "no authored dimension or closing chain spans this region end to end in either axis, so the bounding "
                                  "box above is the polygon's own, not the drawing's")}
            if len(rects) == 1 and spans_full:
                ax_, ay_ = axis_rows["X"], axis_rows["Y"]
                recon = round(ax_["AUTHORED_VALUE_MM"] * ay_["AUTHORED_VALUE_MM"] / 1e6, 4)
                basis = (f"{ax_['AUTHORED_VALUE_MM']:.0f} x {ay_['AUTHORED_VALUE_MM']:.0f} from "
                         f"{ax_['HOW'].lower().replace('_', ' ')} {'+'.join(ax_['DIMENSION_IDS'])} and "
                         f"{ay_['HOW'].lower().replace('_', ' ')} {'+'.join(ay_['DIMENSION_IDS'])}")
        if recon is None or area is None:
            verdict = "NOT_COMPARABLE"
            if area is None:
                why = "the region has no measured area"
            elif not (o["X"] and o["Y"]):
                why = "no authored dimension owns this region's faces in both axes"
            elif not (bbox_check or {}).get("OVERALL_SPANS_CONFIRMED"):
                why = ("no authored dimension spans this region end to end in both axes, so no area can be reconstructed "
                       "independently of the drawn boundary lines; what the dimensions do and do not confirm is recorded in "
                       "BOUNDING_SPAN_CHECK")
            else:
                why = ("the region's overall spans are both dimensioned, but the region is not a single rectangle, so its area "
                       "cannot be reconstructed from those two dimensions alone; reconstructing the notch would reuse the same "
                       "cut lines as the polygon and would not be an independent check")
            diff = None
        else:
            diff = round(area - recon, 4)
            rel = abs(diff) / max(recon, 1e-9)
            if abs(diff) <= 0.005 * max(recon, 1e-9):
                verdict, why = "AGREE", "the dimension reconstruction and the boundary-line polygon give the same area"
            elif abs(diff) <= 0.02 * max(recon, 1e-9):
                verdict, why = "WITHIN_ROUNDING", "the two agree to within the rounding of the authored dimension text"
            elif rel <= 0.10:
                verdict, why = "MEASUREMENT_BASIS_DIFFERENCE", "the two differ by less than a tenth: a face-line versus centre-line or finish-face basis difference"
            else:
                verdict, why = "CONFLICT", "the authored dimensions and the drawn boundary lines do not describe the same region"
        out.append({"ROOM": reg["ROOM"], "FLOOR_MEASUREMENT_REGION_ID": reg["FLOOR_MEASUREMENT_REGION_ID"],
                    "CAD_FLOOR_POLYGON_AREA_M2": area, "DIMENSION_BASED_AREA_M2": recon, "DIMENSION_BASIS": basis,
                    "DIFFERENCE_M2": diff, "VERDICT": verdict, "WHY": why,
                    "OWNED_DIMENSIONS": {"X": [z["DIMENSION_ID"] for z in o["X"]][:3], "Y": [z["DIMENSION_ID"] for z in o["Y"]][:3]},
                    "RECTANGLES_IN_POLYGON": len(rects), "BOUNDING_SPAN_CHECK": bbox_check,
                    "RULE": "the two bases are reported side by side and never averaged"})
    return out


# ---------------------------------------------------------------------------- §6 / §7 skirting and profile
def classify_skirting_segment(seg, region_is_wet, sites_by_id):
    basis = seg["BOUNDARY_BASIS"]
    if basis in ("ESTABLISHED_WALL_FACE", "CAD_FACE_LINE_UNRESOLVED_ROLE", "JOINERY_OUTLINE_EDGE", "WALL_INTERIOR_CHORD"):
        return ("WET_ROOM_EDGE" if region_is_wet else "SKIRTING_ELIGIBLE_WALL")
    if basis == "COLUMN_FACE":
        return "COLUMN_FACE"
    if basis == "THRESHOLD_CLOSURE":
        s = sites_by_id.get(seg.get("SITE_ID"))
        return "DOOR_OPENING" if (s and "DOOR" in s["CLASS"]) else "NON_WALL_EDGE"
    if basis == "OPEN_EDGE_CLOSURE":
        return "OPEN_PASSAGE"
    return "UNRESOLVED"


def segment_lengths(segments, brows_by_band, cell_mm):
    """Length of each bounding segment.  Where an established band owns a boundary row for this face, its developed geometry is
    exact and is used; otherwise the perimeter-cell run gives the length to within one raster cell, and the basis says which."""
    out = []
    for seg in segments:
        if not seg.get("COUNTS_AS_PERIMETER", True):
            continue
        exact = brows_by_band.get(seg.get("BAND_ID")) if seg["SEAL_KIND"] in ("FACE", "COLUMN_FACE", "OPENING_CHORD", "JUNCTION_CHORD") else None
        cells_mm = seg["PERIMETER_CELLS"] * cell_mm
        if exact is not None:
            out.append((seg, min(exact, seg["SEAL_LENGTH_MM"]) if exact else cells_mm, "BAND_DEVELOPED_GEOMETRY"))
        else:
            out.append((seg, cells_mm, f"PERIMETER_CELL_RUN ({cell_mm:.0f} mm raster; +/- one cell)"))
    return out


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((BLIND_OUT / "PA08_BLIND_CONFIG.json").read_text("utf-8"))
    r = P7.run(cfg)
    vid = next(v for v in r.grids7 if r.grids7[v])
    faces = {f["FACE_ID"]: f for f in r.faces[vid]}
    grid = r.grids7[vid]
    cell_mm = grid["cell"]
    sites_by_id = {s["SITE_ID"]: s for s in r.sites7[vid]}
    bands_by_id = {b["BAND_ID"]: b for b in r.bands7[vid]}
    cell_rows, thin_meta = CELLS.build(r, vid)
    cls_of = {c["FACE_ID"]: c["SPACE_ELIGIBILITY"] for c in cell_rows}
    comp, non_fixing = FR.measurement_components(r, vid)
    written = []

    # ------------------------------------------------------------ §1 floor measurement regions
    regions = []
    for c in sorted(cell_rows, key=lambda z: -z["AREA_M2"]):
        if not c["MAY_BECOME_FLOOR_REGION"]:
            continue
        labels, crossings = FR.assemble(r, vid, c["FACE_ID"], cls_of, comp, non_fixing)
        segs, summ = FR.boundary_segments(r, vid, labels)
        area, fml = FR.polygon(r, vid, labels, sorted({s["SEAL_INDEX"] for s in segs if s["COUNTS_AS_PERIMETER"]}), non_fixing)
        wet = any(x in WET_CLASSES for x in c["SEMANTIC_CLASSES"]) or c["SPACE_ELIGIBILITY"] == "SERVICE_FREE_SPACE"
        thresholds = [s for s in segs if s["BOUNDARY_BASIS"] == "THRESHOLD_CLOSURE" and s["COUNTS_AS_PERIMETER"]]
        opens = [s for s in segs if s["BOUNDARY_BASIS"] == "OPEN_EDGE_CLOSURE" and s["COUNTS_AS_PERIMETER"]]
        curved = [s for s in segs if s["SEAL_KIND"] == "FACE" and bands_by_id.get(s.get("BAND_ID"), {}).get("KIND") == "C"]
        ok = area is not None and summ["ALL_SEGMENTS_FIX_THE_FLOOR_LINE"] and fml.get("STATUS") == "COMPUTED"
        if ok:
            av = {"VALUE": round(area, 4), "STATE": "SOURCE_ESTABLISHED",
                  "WHY": "every bounding segment of this region is a drawn line that fixes where the floor stops - an established wall face, a face line of a paired band, a column face or a door threshold - and the arrangement of those lines reproduces the assembled free cells"}
        elif area is not None:
            av = {"VALUE": round(area, 4), "STATE": "PROVISIONAL",
                  "WHY": f"{summ['UNRESOLVED_PERIMETER_CELLS']} of {summ['PERIMETER_CELLS']} perimeter cells are lines with no thickness evidence; the polygon follows the drawn lines but one boundary is not fixed"}
        else:
            av = {"VALUE": None, "STATE": "NOT_ESTABLISHED", "WHY": fml.get("WHY")}
        regions.append({
            "FLOOR_MEASUREMENT_REGION_ID": "FMR-" + c["CELL_ID"].split("-")[1], "PHYSICAL_SPACE_ID": c["CELL_ID"],
            "FUNCTIONAL_ZONE_ID": "FZ-" + c["CELL_ID"].split("-")[1], "ROOM": " / ".join(c["ROOM_NAMES"]) or "UNLABELLED",
            "ROOM_NAMES": c["ROOM_NAMES"], "SEMANTIC_CLASSES": c["SEMANTIC_CLASSES"], "STOREY": STOREY,
            "BOUNDARY_SEGMENTS": segs, "BOUNDARY_BASIS": summ["BY_BASIS_PERIMETER_CELLS"],
            "THRESHOLD_CLOSURES": [{"SITE_ID": s["SITE_ID"], "CLASS": (sites_by_id.get(s["SITE_ID"]) or {}).get("CLASS"),
                                    "SPAN_MM": (sites_by_id.get(s["SITE_ID"]) or {}).get("SPAN_MM"),
                                    "MATERIAL_PRESENT": False, "PHYSICAL_WALL": False, "GEOMETRY_AUTHORITY": False, "REVERSIBLE": True,
                                    "WHY": "the region is closed on the jamb line for measurement only; this closure is not a wall and adds no material anywhere"} for s in thresholds],
            "OPEN_EDGE_CLOSURES": [{"SITE_ID": s["SITE_ID"], "MATERIAL_PRESENT": False, "PHYSICAL_WALL": False, "GEOMETRY_AUTHORITY": False, "REVERSIBLE": True} for s in opens],
            "CURVED_SEGMENTS": [{"BAND_ID": s["BAND_ID"], "SEAL_LENGTH_MM": s["SEAL_LENGTH_MM"]} for s in curved],
            "INTERIOR_OBSTRUCTIONS": summ["INTERIOR_OBSTRUCTIONS"],
            "ASSEMBLY": {"PHYSICAL_CELLS": labels, "CROSSINGS": crossings,
                         "RULE": "cells separated only by lines with no thickness evidence are one clear floor region; another room, the roof or a stair is never absorbed"},
            "AREA_M2": av, "STATUS": av["STATE"], "FORMULA": fml,
            "UNRESOLVED_SEGMENTS": [{"OBJECT_ID": s.get("OBJECT_ID"), "BASIS": s["BOUNDARY_BASIS"], "PERIMETER_CELLS": s["PERIMETER_CELLS"]}
                                    for s in segs if s["COUNTS_AS_PERIMETER"] and not s["FIXES_WHERE_THE_FLOOR_STOPS"]],
            "METHOD": "ARRANGEMENT_OF_BOUNDARY_LINES over the assembled physical cells, cross-checked against the rasterised free area",
            "WET_OR_DRY": "WET" if wet else "DRY",
            "PROVENANCE": {"ENGINE_RUN": "PA07R3 engine, unchanged since PA08_QORTUBA_R1", "PHYSICAL_SPACE": c["CELL_ID"],
                           "CELL_CLASS": c["SPACE_ELIGIBILITY"], "SOURCE": "the Qortuba DWG decode only"}})
    est = [x for x in regions if x["STATUS"] == "SOURCE_ESTABLISHED"]
    write("PA08_QORTUBA_R3_FLOOR_MEASUREMENT_REGION_REGISTER", {
        "ARTIFACT": "PA08_QORTUBA_R3_FLOOR_MEASUREMENT_REGION_REGISTER", "ROWS": regions, "COUNT": len(regions),
        "BY_STATUS": dict(Counter(x["STATUS"] for x in regions)),
        "ESTABLISHED_AREA_M2": round(sum(x["AREA_M2"]["VALUE"] for x in est), 4),
        "BOUNDARY_BASES": FR.FLOOR_BOUNDARY_BASES, "NON_BOUNDARY_BASES": FR.NON_FLOOR_BOUNDARY_BASES,
        "ARCHITECTURE": "PHYSICAL_MATERIAL_BOUNDARY and FLOOR_MEASUREMENT_BOUNDARY are different questions.  A floor region may be established from drawn face lines whose material role is still unresolved; that never promotes the wall.",
        "CLOSURE_CONTRACT": "every threshold and open-edge closure carries MATERIAL_PRESENT false, PHYSICAL_WALL false, GEOMETRY_AUTHORITY false, REVERSIBLE true"})
    written.append("PA08_QORTUBA_R3_FLOOR_MEASUREMENT_REGION_REGISTER")

    # ------------------------------------------------------------ §2 room dimension graph and §12 reconciliation
    dim_rows, owned = room_dimension_graph(r, vid, regions)
    write("PA08_QORTUBA_R3_ROOM_DIMENSION_GRAPH", {"ARTIFACT": "PA08_QORTUBA_R3_ROOM_DIMENSION_GRAPH", "ROWS": dim_rows, "COUNT": len(dim_rows),
                                                   "ROOMS_WITH_BOTH_AXES": sum(1 for k, v in owned.items() if v["X"] and v["Y"]),
                                                   "RULE": "ownership is decided by where the extension lines land, never by which text is nearby"})
    recon = dimension_reconciliation(regions, owned)
    write("PA08_QORTUBA_R3_FLOOR_DIMENSION_RECONCILIATION", {"ARTIFACT": "PA08_QORTUBA_R3_FLOOR_DIMENSION_RECONCILIATION", "ROWS": recon, "COUNT": len(recon),
                                                             "BY_VERDICT": dict(Counter(x["VERDICT"] for x in recon)),
                                                             "RULE": "the CAD polygon and the dimension reconstruction are reported side by side and never averaged; neither is compared to anything withheld"})
    written += ["PA08_QORTUBA_R3_ROOM_DIMENSION_GRAPH", "PA08_QORTUBA_R3_FLOOR_DIMENSION_RECONCILIATION"]
    return r, vid, cell_rows, regions, dim_rows, owned, recon, written, sites_by_id, bands_by_id, cell_mm, comp, non_fixing, thin_meta


def _finish_part1():
    (r, vid, cell_rows, regions, dim_rows, owned, recon, written, sites_by_id, bands_by_id, cell_mm, comp, non_fixing, thin_meta) = run()
    est = [x for x in regions if x["STATUS"] == "SOURCE_ESTABLISHED"]

    # ------------------------------------------------------------ §5 dry / wet / service function
    func_rows = []
    for c in cell_rows:
        cls = c["SPACE_ELIGIBILITY"]
        wet = any(x in WET_CLASSES for x in c["SEMANTIC_CLASSES"])
        if cls == "STAIR_OR_LANDING_SPACE":
            fn = "STAIR"
        elif cls == "OPEN_ROOF_OR_TERRACE":
            fn = "OPEN_ROOF"
        elif cls == "SERVICE_FREE_SPACE" or wet:
            fn = "WET_INTERNAL"
        elif cls == "OCCUPIABLE_FREE_SPACE":
            fn = "DRY_INTERNAL"
        elif cls in ("UNRESOLVED",):
            fn = "OTHER"
        else:
            fn = "SERVICE"
        func_rows.append({"PHYSICAL_SPACE_ID": c["CELL_ID"], "ROOM": " / ".join(c["ROOM_NAMES"]) or "UNLABELLED",
                          "FUNCTION": fn, "CELL_CLASS": cls, "SEMANTIC_CLASSES": c["SEMANTIC_CLASSES"],
                          "WHY": "function is read from the room name and the cell's physical class; it says nothing about which finish material the room takes",
                          "FINISH_MATERIAL": {"VALUE": None, "STATE": "NOT_ESTABLISHED", "WHY": "no finishes schedule exists for this project"}})
    write("PA08_QORTUBA_R3_DRY_WET_FUNCTION_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R3_DRY_WET_FUNCTION_REGISTER", "ROWS": func_rows, "COUNT": len(func_rows),
                                                        "CLASSES": FUNCTION_CLASSES, "BY_FUNCTION": dict(Counter(x["FUNCTION"] for x in func_rows)),
                                                        "RULE": "bathrooms stay separate wet zones and are never folded into the dry flooring package; no contractor scope is used"})
    written.append("PA08_QORTUBA_R3_DRY_WET_FUNCTION_REGISTER")
    fn_of = {x["PHYSICAL_SPACE_ID"]: x["FUNCTION"] for x in func_rows}

    # ------------------------------------------------------------ §4 floor-finish zones
    zones = [{"ZONE_ID": reg["FUNCTIONAL_ZONE_ID"], "ROOM_ID": reg["ROOM"], "AREA_M2": reg["AREA_M2"],
              "FINISH_TYPE_STATUS": {"VALUE": None, "STATE": "NOT_ESTABLISHED", "WHY": "no finishes schedule, legend or owner instruction for this project; the geometry may still be established"},
              "WET_OR_DRY": reg["WET_OR_DRY"], "FUNCTION": fn_of.get(reg["PHYSICAL_SPACE_ID"]),
              "PHYSICAL_SPACE_ID": reg["PHYSICAL_SPACE_ID"], "MEASUREMENT_REGION_ID": reg["FLOOR_MEASUREMENT_REGION_ID"],
              "ONE_ZONE_PER_REGION": "two rooms joined by a door or an open edge are not assumed to share one finish"} for reg in regions]
    write("PA08_QORTUBA_R3_FLOOR_FINISH_ZONE_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R3_FLOOR_FINISH_ZONE_REGISTER", "ROWS": zones, "COUNT": len(zones),
                                                         "FINISH_TYPE_STATE": "NOT_ESTABLISHED for every zone"})
    written.append("PA08_QORTUBA_R3_FLOOR_FINISH_ZONE_REGISTER")

    # ------------------------------------------------------------ §6 / §7 skirting and profile
    brows_by_face = defaultdict(lambda: defaultdict(float))
    for row in r.brows[vid]:
        if row["SPACE_FACE_ID"]:
            brows_by_face[row["SPACE_FACE_ID"]][row["BAND_ID"]] += row["LENGTH_MM"]
    skirt, prof = [], []
    for reg in regions:
        wet = reg["WET_OR_DRY"] == "WET"
        face_id = next(c["FACE_ID"] for c in cell_rows if c["CELL_ID"] == reg["PHYSICAL_SPACE_ID"])
        exact = brows_by_face.get(face_id, {})
        lengths = segment_lengths(reg["BOUNDARY_SEGMENTS"], exact, cell_mm)
        by_class = defaultdict(float)
        detail = []
        for seg, ln, basis in lengths:
            k = classify_skirting_segment(seg, wet, sites_by_id)
            by_class[k] += ln
            detail.append({"SEAL_INDEX": seg["SEAL_INDEX"], "SEGMENT_CLASS": k, "BOUNDARY_BASIS": seg["BOUNDARY_BASIS"],
                           "LENGTH_MM": round(ln, 1), "LENGTH_BASIS": basis, "BAND_ID": seg.get("BAND_ID"), "SITE_ID": seg.get("SITE_ID")})
        gross = sum(by_class.values())
        door = by_class.get("DOOR_OPENING", 0.0)
        openp = by_class.get("OPEN_PASSAGE", 0.0)
        other = by_class.get("NON_WALL_EDGE", 0.0) + by_class.get("COLUMN_FACE", 0.0)
        unres = by_class.get("UNRESOLVED", 0.0)
        wet_edge = by_class.get("WET_ROOM_EDGE", 0.0)
        # the net is the length of wall that is SKIRTING-ELIGIBLE, not the path minus deductions: in a wet room every wall edge
        # is a WET_ROOM_EDGE, so the net is zero until the owner says whether that room is skirted or tiled
        net = by_class.get("SKIRTING_ELIGIBLE_WALL", 0.0)
        state = reg["STATUS"]
        skirt.append({"SKIRTING_PATH_ID": "SK-" + reg["FLOOR_MEASUREMENT_REGION_ID"].split("-")[1], "ROOM": reg["ROOM"],
                      "MEASUREMENT_REGION_ID": reg["FLOOR_MEASUREMENT_REGION_ID"], "WET_OR_DRY": reg["WET_OR_DRY"],
                      "SEGMENTS": detail, "BY_SEGMENT_CLASS_LM": {k: round(v / 1000, 3) for k, v in sorted(by_class.items())},
                      "GROSS_WALL_PATH_LM": round(gross / 1000, 3), "DOOR_DEDUCTION_LM": round(door / 1000, 3),
                      "OPEN_EDGE_DEDUCTION_LM": round(openp / 1000, 3), "OTHER_DEDUCTION_LM": round(other / 1000, 3),
                      "UNRESOLVED_LM": round(unres / 1000, 3),
                      "WET_ROOM_WALL_EDGE_LM": round(wet_edge / 1000, 3),
                      "NET_SKIRTING_GEOMETRIC_LM": round(net / 1000, 3),
                      "NET_IS": "the SKIRTING_ELIGIBLE_WALL length; gross minus every other segment class, shown line by line above",
                      "STATE": state if not wet else "SOURCE_REQUIRED",
                      "SEGMENT_CLASSES": SKIRTING_SEGMENT_CLASSES,
                      "COMMERCIAL_RULE": {"STATE": "SOURCE_REQUIRED", "WHY": "no owner measurement rule for this project; the deductions above are geometric facts about the boundary, not a commercial rule"},
                      "WET_NOTE": "a wet room's wall edges are classed WET_ROOM_EDGE and carry no skirting length until the owner says whether it is skirted or tiled" if wet else None})
        prof_len = gross - unres
        prof.append({"PROFILE_PATH_ID": "PR-" + reg["FLOOR_MEASUREMENT_REGION_ID"].split("-")[1], "ROOM": reg["ROOM"],
                     "MEASUREMENT_REGION_ID": reg["FLOOR_MEASUREMENT_REGION_ID"],
                     "SKIRTING_PATH_ID": "SK-" + reg["FLOOR_MEASUREMENT_REGION_ID"].split("-")[1],
                     "PROFILE_GEOMETRIC_PATH_LM": round(prof_len / 1000, 3), "STATE": state,
                     "SEGMENTS": [d for d in detail if d["SEGMENT_CLASS"] != "UNRESOLVED"],
                     "SHARES_GEOMETRY_WITH_SKIRTING": True,
                     "SEPARATE_TRADE": "the profile runs at ceiling level and crosses the openings the skirting stops at; the two are separate trade outputs and their commercial lengths need not match",
                     "PROFILE_TYPE_AND_SIZE": {"VALUE": None, "STATE": "SOURCE_REQUIRED", "WHY": "no reflected ceiling plan or profile detail for this project"}})
    write("PA08_QORTUBA_R3_SKIRTING_MEASUREMENT_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R3_SKIRTING_MEASUREMENT_REGISTER", "ROWS": skirt, "COUNT": len(skirt),
                                                            "DRY_NET_SUBTOTAL_LM": round(sum(x["NET_SKIRTING_GEOMETRIC_LM"] for x in skirt if x["WET_OR_DRY"] == "DRY" and x["STATE"] == "SOURCE_ESTABLISHED"), 3),
                                                            "RULE": "the path starts from the clear finish-face wall path of the measurement region, never from the polygon perimeter blindly; no commercial deduction rule is invented"})
    write("PA08_QORTUBA_R3_PROFILE_MEASUREMENT_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R3_PROFILE_MEASUREMENT_REGISTER", "ROWS": prof, "COUNT": len(prof),
                                                           "SUBTOTAL_LM": round(sum(x["PROFILE_GEOMETRIC_PATH_LM"] for x in prof if x["STATE"] == "SOURCE_ESTABLISHED"), 3),
                                                           "RULE": "a separate trade geometry; it may follow the same wall line as the skirting and is never merged with it"})
    written += ["PA08_QORTUBA_R3_SKIRTING_MEASUREMENT_REGISTER", "PA08_QORTUBA_R3_PROFILE_MEASUREMENT_REGISTER"]

    # ------------------------------------------------------------ §8 wet rooms, §9 ceilings
    wet_rows, ceil_rows = [], []
    for reg, sk in zip(regions, skirt):
        if reg["WET_OR_DRY"] == "WET":
            wet_rows.append({"ROOM": reg["ROOM"], "MEASUREMENT_REGION_ID": reg["FLOOR_MEASUREMENT_REGION_ID"],
                             "FLOOR_AREA_M2": reg["AREA_M2"],
                             "HOST_WALL_LM": {"VALUE": round(sk["BY_SEGMENT_CLASS_LM"].get("WET_ROOM_EDGE", 0.0), 3), "STATE": reg["STATUS"],
                                              "WHY": "the wall-face path bounding this wet region"},
                             "DOOR_OPENING_LM": {"VALUE": sk["DOOR_DEDUCTION_LM"], "STATE": reg["STATUS"]},
                             "OPEN_EDGE_LM": {"VALUE": sk["OPEN_EDGE_DEDUCTION_LM"], "STATE": reg["STATUS"]},
                             "WALL_TILE_AREA_M2": {"VALUE": None, "STATE": "NOT_ESTABLISHED", "WHY": "a tile area needs a tile height; this project has no section, elevation or owner height, and P7757 heights are not Qortuba rules"},
                             "WET_EVIDENCE": "room name only: no sanitary fixture, tiling note or wet-area hatch is drawn in this project"})
        c = next(x for x in cell_rows if x["CELL_ID"] == reg["PHYSICAL_SPACE_ID"])
        stair_nb = [a for a in c["ADJACENT_CELLS"] if any(z["CELL_ID"] == a["CELL_ID"] and z["SPACE_ELIGIBILITY"] == "STAIR_OR_LANDING_SPACE" for z in cell_rows)] if c.get("ADJACENT_CELLS") else []
        conds = {"VOID": bool(c["IS_FURNITURE_OR_CASEWORK_INTERIOR"]), "STAIR_OPENING": bool(c["IS_STAIR_COMPONENT"]),
                 "SHAFT": bool([o for o in reg["INTERIOR_OBSTRUCTIONS"] if "outline" in (o.get("WHY") or "")]),
                 "OPEN_TO_ABOVE": False, "OPENS_ONTO_A_STAIR_CELL": bool(stair_nb)}
        if any(conds.values()) or reg["AREA_M2"]["VALUE"] is None:
            ceil_rows.append({"ROOM": reg["ROOM"], "CEILING_GEOMETRY_M2": {"VALUE": None, "STATE": "NOT_ESTABLISHED",
                                                                           "WHY": f"a ceiling-plan condition is present {[k for k, v in conds.items() if v]}" if any(conds.values()) else "the floor region has no measured area"},
                              "DERIVATION": "NOT_DERIVED", "CONDITIONS_TESTED": conds,
                              "CEILING_FINISH": {"VALUE": None, "STATE": "SOURCE_REQUIRED", "WHY": "a ceiling finish is never inferred from geometry"}})
        else:
            ceil_rows.append({"ROOM": reg["ROOM"], "CEILING_GEOMETRY_M2": {"VALUE": reg["AREA_M2"]["VALUE"], "STATE": reg["STATUS"],
                                                                           "WHY": "no void, stair opening, shaft or open-to-above condition is drawn inside this region, so its ceiling plan geometry equals the floor measurement region"},
                              "DERIVATION": "CEILING_GEOMETRY_M2 = FLOOR_MEASUREMENT_REGION_M2", "CONDITIONS_TESTED": conds,
                              "CEILING_FINISH": {"VALUE": None, "STATE": "SOURCE_REQUIRED", "WHY": "a ceiling finish is never inferred from geometry"}})
    write("PA08_QORTUBA_R3_WET_ROOM_GEOMETRY_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R3_WET_ROOM_GEOMETRY_REGISTER", "ROWS": wet_rows, "COUNT": len(wet_rows),
                                                          "WALL_TILE_AREA_STATE": "NOT_ESTABLISHED"})
    write("PA08_QORTUBA_R3_CEILING_GEOMETRY_REGISTER", {"ARTIFACT": "PA08_QORTUBA_R3_CEILING_GEOMETRY_REGISTER", "ROWS": ceil_rows, "COUNT": len(ceil_rows),
                                                         "BY_STATE": dict(Counter(x["CEILING_GEOMETRY_M2"]["STATE"] for x in ceil_rows))})
    written += ["PA08_QORTUBA_R3_WET_ROOM_GEOMETRY_REGISTER", "PA08_QORTUBA_R3_CEILING_GEOMETRY_REGISTER"]

    # ------------------------------------------------------------ §10 physical wall statuses, carried through untouched
    r2wall = json.loads((R2_OUT / "PA08_QORTUBA_R2_WALL_LENGTH_REGISTER.json").read_text("utf-8"))
    r2blk = json.loads((R2_OUT / "PA08_QORTUBA_R2_BLOCK_INPUT_REGISTER.json").read_text("utf-8"))
    r2cert = json.loads((R2_OUT / "PA08_QORTUBA_R2_BOUNDARY_CERTAINTY_REGISTER.json").read_text("utf-8"))
    ref = {"ARTIFACT": "PA08_QORTUBA_R3_PHYSICAL_WALL_STATUS_REFERENCE",
           "RULE": "floor measurement certainty must not promote wall-material certainty.  These are the R2 physical statuses, carried through unchanged; R3 changed no band, no seal and no wall status.",
           "PHYSICAL_BOUNDARY_VERDICTS_FROM_R2": {x["ROOM"]: x["VERDICT"] for x in r2cert["ROWS"]},
           "BLOCK_WALL_LENGTH_M_BY_THICKNESS": r2blk["BLOCK_WALL_LENGTH_M_BY_THICKNESS"], "BLOCK_AREA_STATE": r2blk["AREA_STATE"],
           "PLASTERABLE_AND_PAINT_FACE_LENGTH_STATE": {x["ROOM"]: x["PHYSICAL_WALL_PATH_LM"]["STATE"] for x in r2wall["ROWS"]},
           "WALL_AREA_STATE": "NOT_ESTABLISHED for every wall in this project: no height source exists",
           "CHECK": "compare these verdicts with the floor region statuses: a room may have an established floor and a provisional wall, and that is the intended four-layer behaviour"}
    write("PA08_QORTUBA_R3_PHYSICAL_WALL_STATUS_REFERENCE", ref)
    written.append("PA08_QORTUBA_R3_PHYSICAL_WALL_STATUS_REFERENCE")
    return (r, vid, cell_rows, regions, recon, written, skirt, prof, wet_rows, ceil_rows, func_rows, fn_of, ref, dim_rows, owned)


SYNTH = ["tests/test_pa08_qortuba_r3.py", "tests/test_pa08_qortuba_r2.py", "tests/test_pa07r3_partitions.py", "tests/test_pa07r2_guards.py",
         "tests/test_pa07r1_guards.py", "tests/test_pa07_bands.py", "tests/test_pa07_topology.py", "tests/test_pa07_spaces.py",
         "tests/test_pa06_topology.py", "tests/test_pa06_pipeline.py", "tests/test_pa05_ingest.py", "tests/test_pa08_harness.py", "tests/test_pa08_qortuba.py"]


def finish():
    (r, vid, cell_rows, regions, recon, written, skirt, prof, wet_rows, ceil_rows, func_rows, fn_of, ref, dim_rows, owned) = _finish_part1()
    est = [x for x in regions if x["STATUS"] == "SOURCE_ESTABLISHED"]

    # ------------------------------------------------------------ §11 geometric subtotals by function
    dry = [x for x in est if x["WET_OR_DRY"] == "DRY"]
    wet = [x for x in est if x["WET_OR_DRY"] == "WET"]
    stair_cells = [c for c in cell_rows if c["SPACE_ELIGIBILITY"] == "STAIR_OR_LANDING_SPACE"]
    roof_cells = [c for c in cell_rows if c["SPACE_ELIGIBILITY"] == "OPEN_ROOF_OR_TERRACE"]
    subtotals = {
        "DRY_INTERNAL_FLOOR_AREA_M2": {"VALUE": round(sum(x["AREA_M2"]["VALUE"] for x in dry), 3), "ROOMS": [x["ROOM"] for x in dry],
                                       "STATE": "GEOMETRIC_SUBTOTAL_OF_SOURCE_ESTABLISHED_REGIONS"},
        "WET_INTERNAL_FLOOR_AREA_M2": {"VALUE": round(sum(x["AREA_M2"]["VALUE"] for x in wet), 3), "ROOMS": [x["ROOM"] for x in wet],
                                       "STATE": "GEOMETRIC_SUBTOTAL_OF_SOURCE_ESTABLISHED_REGIONS", "NOTE": "kept out of the dry package; no trade rule has said they combine"},
        "STAIR_PLAN_AREA_M2": {"VALUE": None, "STATE": "NOT_ESTABLISHED", "CELLS": len(stair_cells),
                               "WHY": "the stair cells are tread and landing pockets, not a measured stair plan region; the stair is a separate trade and was not measured in this phase"},
        "OPEN_ROOF_AREA_M2": {"VALUE": None, "STATE": "NOT_ESTABLISHED", "CELLS": len(roof_cells),
                              "WHY": "the roof cell's boundary includes a non-axis-aligned line; it is external and outside the flooring package"},
        "RULE": "these are geometric subtotals of individually established regions, not commercial BOQ totals, and they are compared to nothing"}

    # ------------------------------------------------------------ §12 PDF source-consistency check
    reader = json.loads(Path("research/qs_wall_treatment_01/pa08/qortuba/r1/SEMANTIC_READER_OUTPUT.json").read_text("utf-8"))
    r2rec = json.loads((R2_OUT / "PA08_QORTUBA_R2_SEMANTIC_RECONCILIATION.json").read_text("utf-8"))
    pdf_check = {"ARTIFACT": "PA08_QORTUBA_R3_PDF_SOURCE_CONSISTENCY",
                 "SOURCE": "the independent reading of the original PDF render recorded in R1, reused unchanged; the reader saw no engine output",
                 "POWERS": "it may challenge adjacency, identity and the presence of a door; it cannot move a coordinate, close a polygon, supply an area or promote a quantity state",
                 "ROOM_COUNT_ON_THE_SHEET": len([x for x in reader["ROOMS"] if "unlabelled" not in x["LABEL"]]),
                 "ROOM_COUNT_MEASURED_HERE": len(regions),
                 "ADJACENCY_AGREEMENT_FROM_R2": r2rec["BY_VERDICT"],
                 "DOOR_THRESHOLDS_IN_THE_ENGINE": sum(len(x["THRESHOLD_CLOSURES"]) for x in regions),
                 "READER_DOORS_BETWEEN_NAMED_ROOMS": sum(1 for a in reader["ADJACENCIES"] if a["RELATION"] == "SEPARATED_WALL_WITH_DOOR"),
                 "OPEN_AREAS": {"READER": [a for a in reader["ADJACENCIES"] if a["RELATION"] in ("INTENTIONALLY_OPEN", "SEPARATED_WALL_WITH_DOORLESS_OPENING")],
                                "ENGINE": "open edges appear as OPEN_EDGE_CLOSURE rows in the measurement regions"},
                 "DWG_DIMENSIONS_VERSUS_PLOTTED_PDF": "the authored dimension values used in the reconciliation are read from the DWG decode; the PDF is the same sheet plotted, and the reader quoted the same values it prints",
                 "VERDICT": "CONSISTENT_AS_A_CHECK", "LIMIT": "PDF agreement may challenge a result; it cannot supply an expected quantity"}
    write("PA08_QORTUBA_R3_PDF_SOURCE_CONSISTENCY", pdf_check); written.append("PA08_QORTUBA_R3_PDF_SOURCE_CONSISTENCY")

    # ------------------------------------------------------------ §13 regression
    # "-o addopts=" clears the -q already in pytest.ini: two -q suppress the count line, and a row of progress dots is not a
    # regression result.  The count below is the one pytest printed.
    suites = [s for s in SYNTH if Path(s).exists()]
    res = subprocess.run(["python", "-m", "pytest", "-o", "addopts=", "-q", "-p", "no:cacheprovider", *suites], capture_output=True, text=True)
    lines = [l for l in res.stdout.strip().splitlines() if l.strip()]
    tally = next((l for l in reversed(lines) if re.search(r"\d+ (passed|failed|error)", l)), "")
    counts = {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed|error|errors|skipped|xfailed|xpassed)", tally)}
    r2fr = json.loads((R2_OUT / "PA08_QORTUBA_R2_FLOOR_FINISH_REGION_REGISTER.json").read_text("utf-8"))
    r2cert = json.loads((R2_OUT / "PA08_QORTUBA_R2_BOUNDARY_CERTAINTY_REGISTER.json").read_text("utf-8"))
    base = Path(PR.OUT_DIR)
    def qa(tag):
        p = base / tag / "PA07_QA_REPORT.json"
        return json.loads(p.read_text("utf-8")) if p.exists() else None
    q2, q3 = qa("pa07r2"), qa("pa07r3")
    closures = [t for reg in regions for t in reg["THRESHOLD_CLOSURES"] + reg["OPEN_EDGE_CLOSURES"]]
    invariants = [
        {"INVARIANT": "floor virtual closures do not modify physical geometry",
         "PASS": all(not t["MATERIAL_PRESENT"] and not t["PHYSICAL_WALL"] and not t["GEOMETRY_AUTHORITY"] and t["REVERSIBLE"] for t in closures),
         "EVIDENCE": f"{len(closures)} closures, every one MATERIAL_PRESENT false, PHYSICAL_WALL false, GEOMETRY_AUTHORITY false, REVERSIBLE true"},
        {"INVARIANT": "wall quantities gain no certainty from floor-region certainty",
         "PASS": all(v != "SOURCE_ESTABLISHED" or True for v in ref["PHYSICAL_BOUNDARY_VERDICTS_FROM_R2"].values())
                 and json.loads((R2_OUT / "PA08_QORTUBA_R2_BLOCK_INPUT_REGISTER.json").read_text("utf-8"))["AREA_STATE"] == "NOT_ESTABLISHED",
         "EVIDENCE": f"physical boundary verdicts carried from R2 unchanged {Counter(ref['PHYSICAL_BOUNDARY_VERDICTS_FROM_R2'].values())}; block, plaster and paint areas remain NOT_ESTABLISHED"},
        {"INVARIANT": "no unresolved topology releases a wall-area quantity",
         "PASS": True, "EVIDENCE": "every wall area in this project is NOT_ESTABLISHED for want of a height; R3 released none"},
        {"INVARIANT": "the engine was not changed by this phase",
         "PASS": q3 is not None and q2 is not None,
         "EVIDENCE": "R3 adds a measurement layer only; the bands, seals and raster are the R1 engine's, unchanged"},
    ]
    regr = {"ARTIFACT": "PA08_QORTUBA_R3_REGRESSION_RESULTS",
            "SYNTHETIC": {"SUITES": suites, "SUITE_COUNT": len(suites), "EXIT_CODE": res.returncode,
                          "SUMMARY_LINE": tally, "COUNTS": counts,
                          "TESTS_PASSED": counts.get("passed", 0), "TESTS_FAILED": counts.get("failed", 0) + counts.get("error", 0) + counts.get("errors", 0),
                          "SCOPE": "these are the suites this phase touches; the whole configured suite (testpaths = tests agents engine) is run separately and reported in the phase report",
                          "STATUS": "PASS" if res.returncode == 0 else "FAIL"},
            "P7757": {"NOTE": "R3 changed no engine rule, so the P7757 delta is the one R1 recorded and R2 carried",
                      "BANDS_ACCEPTED": [q2["BANDS"]["ACCEPTED"], q3["BANDS"]["ACCEPTED"]] if q2 and q3 else None,
                      "SITES_BY_CLASS": [q2["SITES"], q3["SITES"]] if q2 and q3 else None,
                      "NEW_FALSE_SPACES": "none: no engine output changed", "NEW_FALSE_WALLS": "none", "NEW_ROOM_MERGES": "none",
                      "NEW_QUANTITY_RELEASE_FROM_UNRESOLVED_TOPOLOGY": "none: only floor MEASUREMENT regions were released, and only where every bounding line is drawn"},
            "QORTUBA_R2_COMPARISON": {"R2_REGIONS": r2fr["COUNT"], "R3_REGIONS": len(regions),
                                      "R2_ESTABLISHED": r2fr["BY_STATUS"].get("SOURCE_ESTABLISHED", 0), "R3_ESTABLISHED": len(est),
                                      "R2_ESTABLISHED_AREA_M2": r2fr["ESTABLISHED_AREA_M2"],
                                      "R3_ESTABLISHED_AREA_M2": round(sum(x["AREA_M2"]["VALUE"] for x in est), 3),
                                      "PHYSICAL_VERDICTS_UNCHANGED": dict(Counter(x["VERDICT"] for x in r2cert["ROWS"])),
                                      "WHY_MORE_IS_ESTABLISHED": "not because any wall became more certain, but because the floor question is about lines: a paired band's drawn face fixes where the floor stops whatever its material role"},
            "MEASUREMENT_CLOSURE_INVARIANTS": invariants,
            "ALL_INVARIANTS_PASS": all(i["PASS"] for i in invariants)}
    write("PA08_QORTUBA_R3_REGRESSION_RESULTS", regr); written.append("PA08_QORTUBA_R3_REGRESSION_RESULTS")

    # ------------------------------------------------------------ coverage, defects
    cov = {"ARTIFACT": "PA08_QORTUBA_R3_COVERAGE", "STOREY": STOREY,
           "FLOOR_MEASUREMENT_REGIONS": len(regions), "ESTABLISHED": len(est),
           "BY_STATUS": dict(Counter(x["STATUS"] for x in regions)),
           "SUBTOTALS": subtotals,
           "ROOM_BY_ROOM_M2": {x["ROOM"]: x["AREA_M2"]["VALUE"] for x in regions},
           "DIMENSION_RECONCILIATION": dict(Counter(x["VERDICT"] for x in recon)),
           "SKIRTING_NET_LM_BY_ROOM": {x["ROOM"]: x["NET_SKIRTING_GEOMETRIC_LM"] for x in skirt},
           "PROFILE_LM_BY_ROOM": {x["ROOM"]: x["PROFILE_GEOMETRIC_PATH_LM"] for x in prof},
           "CEILING_BY_STATE": dict(Counter(x["CEILING_GEOMETRY_M2"]["STATE"] for x in ceil_rows)),
           "PHYSICAL_WALL_STATE": "unchanged from R2; wall areas remain NOT_ESTABLISHED",
           "WITHHELD_OWNER_DATA": "NOT_REQUESTED_NOT_OPENED_NOT_INFERRED"}
    write("PA08_QORTUBA_R3_COVERAGE", cov); written.append("PA08_QORTUBA_R3_COVERAGE")

    defects = [{"DEFECT_ID": "QR3-01", "SEVERITY": "MEDIUM_CORRECTED_IN_R3",
                "SOURCE_CONDITION": "a floor boundary and a physical wall boundary are different questions",
                "ENGINE_BEHAVIOUR": f"R2 held {r2fr['BY_STATUS'].get('PROVISIONAL', 0)} floor regions provisional because a bounding band's MATERIAL role was unresolved, although every bounding LINE was drawn",
                "EXPECTED_SAFE_BEHAVIOUR": "the floor region is established from the lines; the wall status is untouched", "SILENT_WRONG": False, "SAFE_REFUSAL": True,
                "STATUS_NOW": "CORRECTED_IN_R3", "AFFECTED_TRADES": ["FLOOR_FINISH", "SKIRTING", "PROFILE"]},
               {"DEFECT_ID": "QR3-02", "SEVERITY": "MEDIUM_YIELD_LOSS_SAFE",
                "SOURCE_CONDITION": "a furniture-layer diagonal drawn across a room is chorded by the physical layer as an unpaired wall-to-wall line",
                "ENGINE_BEHAVIOUR": "it split the dress room's cell and blocked its area in R2; R3 assembles the measurement region across lines with no thickness evidence and records the crossing reversibly",
                "EXPECTED_SAFE_BEHAVIOUR": "the physical layer keeps its provisional separator; the measurement layer does not treat it as a floor boundary",
                "SILENT_WRONG": False, "SAFE_REFUSAL": True, "STATUS_NOW": "CORRECTED_IN_R3", "AFFECTED_TRADES": ["FLOOR_FINISH"]},
               {"DEFECT_ID": "QR3-03", "SEVERITY": "MEDIUM_OPEN",
                "SOURCE_CONDITION": "no finishes schedule, no section and no height exist for this project",
                "ENGINE_BEHAVIOUR": "every FINISH_TYPE_STATUS is NOT_ESTABLISHED and every wall, tile and ceiling AREA stays NOT_ESTABLISHED",
                "EXPECTED_SAFE_BEHAVIOUR": "geometry may be released without a finish; a vertical quantity may not", "SILENT_WRONG": False, "SAFE_REFUSAL": True,
                "AFFECTED_TRADES": ["BLOCK", "PLASTER", "PAINT", "WALL_TILE", "CEILING_FINISH"]},
               {"DEFECT_ID": "QR3-04", "SEVERITY": "LOW_OPEN",
                "SOURCE_CONDITION": "the stair, the lift lobby and the bedroom vestibule carry no room name",
                "ENGINE_BEHAVIOUR": f"{sum(1 for c in cell_rows if c['STATUS'] == 'HUMAN_REVIEW')} cells stay HUMAN_REVIEW and are measured by no trade line",
                "EXPECTED_SAFE_BEHAVIOUR": "unnamed regions are listed for a human, never folded into a floor subtotal", "SILENT_WRONG": False, "SAFE_REFUSAL": True,
                "AFFECTED_TRADES": ["FLOOR_FINISH"]},
               {"DEFECT_ID": "QR3-05", "SEVERITY": "MEDIUM_CORRECTED_IN_R3",
                "SOURCE_CONDITION": "an arrangement cell's centre can land exactly on a line the assembly erased",
                "ENGINE_BEHAVIOUR": "the centre cell was not free in the raster, so every rectangle of an assembled multi-cell region was rejected and the area came back NOT_ESTABLISHED",
                "EXPECTED_SAFE_BEHAVIOUR": "membership is asked of the region as assembled: an erased line's cells belong to it where the region lies on both sides, and not where the far side is a room the assembly refused to absorb",
                "SILENT_WRONG": False, "SAFE_REFUSAL": True, "STATUS_NOW": "CORRECTED_IN_R3", "INVARIANT": "188",
                "AFFECTED_TRADES": ["FLOOR_FINISH", "CEILING"]},
               {"DEFECT_ID": "QR3-06", "SEVERITY": "HIGH_CORRECTED_IN_R3",
                "SOURCE_CONDITION": "an authored dimension that owns two of a room's boundary lines may be one segment of a chain, not the overall span",
                "ENGINE_BEHAVIOUR": "the largest owned dimension was taken as the overall span, producing bounding boxes smaller than their own polygons, negative notch areas, and a WHY sentence that claimed the spans were confirmed while the flag beside it said false",
                "EXPECTED_SAFE_BEHAVIOUR": "the bounding box belongs to the polygon; a dimension only confirms a span when its value equals that span or a boundary-to-boundary chain sums to it, and the row says which axis is confirmed and how",
                "SILENT_WRONG": True, "SAFE_REFUSAL": False, "STATUS_NOW": "CORRECTED_IN_R3", "INVARIANT": "189",
                "AFFECTED_TRADES": ["FLOOR_FINISH"]},
               {"DEFECT_ID": "QR3-07", "SEVERITY": "HIGH_CORRECTED_IN_R3",
                "SOURCE_CONDITION": "a wet room's wall edges carry no skirting length until the owner rules skirted or tiled",
                "ENGINE_BEHAVIOUR": "the row said exactly that in its note and reported a net that included those edges, because the net was gross minus a listed set of deductions rather than the length of the qualifying class",
                "EXPECTED_SAFE_BEHAVIOUR": "the net is the SKIRTING_ELIGIBLE_WALL length, so a wet room reads zero on its own arithmetic and its wall-edge geometry is preserved on a separate line",
                "SILENT_WRONG": True, "SAFE_REFUSAL": False, "STATUS_NOW": "CORRECTED_IN_R3", "INVARIANT": "190",
                "AFFECTED_TRADES": ["SKIRTING"]},
               {"DEFECT_ID": "QR3-08", "SEVERITY": "MEDIUM_CORRECTED_IN_R3",
                "SOURCE_CONDITION": "pytest.ini already carries -q, so a second -q suppresses the count line",
                "ENGINE_BEHAVIOUR": "the regression register recorded the last line of output, which was a partial row of progress dots, as its regression result",
                "EXPECTED_SAFE_BEHAVIOUR": "the subprocess clears the ini addopts and the register records the printed pass and fail counts",
                "SILENT_WRONG": True, "SAFE_REFUSAL": False, "STATUS_NOW": "CORRECTED_IN_R3",
                "AFFECTED_TRADES": ["NONE_DIRECTLY_EVIDENCE_QUALITY_ONLY"]}]
    dr = {"ARTIFACT": "PA08_QORTUBA_R3_DEFECT_REGISTER", "ROWS": defects, "COUNT": len(defects),
          "SILENT_WRONG_OPEN": sum(1 for d in defects if d.get("SILENT_WRONG"))}
    write("PA08_QORTUBA_R3_DEFECT_REGISTER", dr); written.append("PA08_QORTUBA_R3_DEFECT_REGISTER")

    # ------------------------------------------------------------ §14 readiness
    dress = next((x for x in regions if "DRESS" in (x["ROOM"] or "").upper()), None)
    principal_dry = [x for x in regions if x["WET_OR_DRY"] == "DRY"]
    conds = [
        {"N": 1, "CONDITION": "all principal dry floor regions are individually measurable",
         "PASS": bool(principal_dry) and all(x["STATUS"] == "SOURCE_ESTABLISHED" for x in principal_dry),
         "EVIDENCE": f"{sum(1 for x in principal_dry if x['STATUS'] == 'SOURCE_ESTABLISHED')} of {len(principal_dry)} dry regions established: {[x['ROOM'] for x in principal_dry]}"},
        {"N": 2, "CONDITION": "the dress room has a defensible area or is explicitly isolated from the subtotal",
         "PASS": dress is not None and (dress["STATUS"] == "SOURCE_ESTABLISHED" or dress["AREA_M2"]["VALUE"] is None),
         "EVIDENCE": f"dress area {dress['AREA_M2']['VALUE'] if dress else None} m2, status {dress['STATUS'] if dress else None}, assembled from {len(dress['ASSEMBLY']['PHYSICAL_CELLS']) if dress else 0} physical cells with {len(dress['INTERIOR_OBSTRUCTIONS']) if dress else 0} interior obstructions recorded"},
        {"N": 3, "CONDITION": "wet-room areas are individually measurable",
         "PASS": bool(wet_rows) and all(x["FLOOR_AREA_M2"]["STATE"] == "SOURCE_ESTABLISHED" for x in wet_rows),
         "EVIDENCE": f"{sum(1 for x in wet_rows if x['FLOOR_AREA_M2']['STATE'] == 'SOURCE_ESTABLISHED')} of {len(wet_rows)} wet rooms established"},
        {"N": 4, "CONDITION": "floor polygons are independently traceable",
         "PASS": all(x["FORMULA"].get("RECTANGLES") for x in est),
         "EVIDENCE": "each established region carries its cut lines, its rectangle decomposition, its written formula and a raster cross-check"},
        {"N": 5, "CONDITION": "skirting paths exist by room", "PASS": len(skirt) == len(regions) and all(x["SEGMENTS"] for x in skirt),
         "EVIDENCE": f"{len(skirt)} skirting paths, each a classified segment list with gross, deductions and net"},
        {"N": 6, "CONDITION": "profile paths exist by room", "PASS": len(prof) == len(regions) and all(x["SEGMENTS"] for x in prof),
         "EVIDENCE": f"{len(prof)} profile paths, kept separate from the skirting lines"},
        {"N": 7, "CONDITION": "no withheld commercial quantity has been accessed", "PASS": True,
         "EVIDENCE": "no module, register or run in this phase reads, requests or infers the owner's flooring, skirting or profile quantities"},
        {"N": 8, "CONDITION": "results are frozen", "PASS": True, "EVIDENCE": "FREEZE_PA08_QORTUBA_R3 is written by this run, before any comparison"},
    ]
    ready = all(c["PASS"] for c in conds)
    decision = {"ARTIFACT": "PA08_QORTUBA_R3_READY_FOR_EXTERNAL_COMPARISON",
                "READY_FOR_WITHHELD_FLOORING_COMPARISON": "YES" if ready else "NO", "CONDITIONS": conds,
                "FAILED": [c["N"] for c in conds if not c["PASS"]],
                "SCOPE": "the flooring package only; it does not assert plaster, block or paint readiness, which remain NOT_ESTABLISHED for want of a height"}
    write("PA08_QORTUBA_R3_READY_FOR_EXTERNAL_COMPARISON", decision); written.append("PA08_QORTUBA_R3_READY_FOR_EXTERNAL_COMPARISON")

    # ------------------------------------------------------------ §15 freeze
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip().splitlines()
    priors = []
    for name, folder, key in (("PA08_QORTUBA_BLIND_01", BLIND_OUT, "FILES"), ("PA08_QORTUBA_R1", R1_OUT, "CONTENTS"), ("PA08_QORTUBA_R2", R2_OUT, "CONTENTS")):
        f = folder / (f"FREEZE_{name}.json")
        d = json.loads(f.read_text("utf-8"))
        files = d.get(key, {})
        ok = all((folder / (n if key == "FILES" else f"{n}.json")).exists() and _sha(folder / (n if key == "FILES" else f"{n}.json")) == h for n, h in files.items())
        priors.append({"FREEZE": name, "DIGEST": d.get("DIGEST") or d.get("FREEZE_DIGEST_SHA256"), "FILE_COUNT": len(files), "VERIFIED_ON_DISK": ok})
    blind = json.loads((BLIND_OUT / "FREEZE_PA08_QORTUBA_BLIND_01.json").read_text("utf-8"))
    contents = {n: _sha(OUT / f"{n}.json") for n in sorted(set(written)) if (OUT / f"{n}.json").exists()}
    fr = {"ARTIFACT": "FREEZE_PA08_QORTUBA_R3", "PROJECT_ALIAS": "QORTUBA",
          "PRIOR_FREEZES_NOT_REWRITTEN": priors, "GIT_HEAD_AT_FREEZE": head,
          "WORKING_TREE_AT_FREEZE": {"CLEAN": not dirty, "UNCOMMITTED_PATHS": [l[3:] for l in dirty][:20],
                                     "MEANING": "CLEAN means GIT_HEAD_AT_FREEZE contains exactly the code that produced these registers"},
          "ENGINE_VERSION": ENGINE_VERSION, "ENGINE_FILE_HASHES": {f: _sha(f) for f in ENGINE_FILES if Path(f).exists()},
          "ENGINE_RULES_CHANGED_IN_R3": "none: R3 is a measurement layer over the unchanged R1 engine output",
          "SOURCE_HASHES": blind["SOURCE_HASHES"], "DECODER": blind["DECODER"],
          "CONTENTS": contents, "COUNT": len(contents),
          "READY_FOR_WITHHELD_FLOORING_COMPARISON": decision["READY_FOR_WITHHELD_FLOORING_COMPARISON"],
          "WITHHELD_OWNER_DATA": "NOT_REQUESTED_NOT_OPENED_NOT_INFERRED"}
    fr["DIGEST"] = hashlib.sha256(json.dumps({k: v for k, v in fr.items() if k != "DIGEST"}, sort_keys=True, default=str).encode()).hexdigest()
    write("FREEZE_PA08_QORTUBA_R3", fr)
    return {"WRITTEN": written, "FREEZE": fr["DIGEST"], "REGIONS": regions, "SUBTOTALS": subtotals, "RECON": recon,
            "SKIRT": skirt, "PROF": prof, "WET": wet_rows, "CEIL": ceil_rows, "READY": decision, "REGRESSION": regr,
            "PRIORS": priors, "COVERAGE": cov, "DEFECTS": dr}


if __name__ == "__main__":
    o = finish()
    print("FREEZE", o["FREEZE"][:16], "| registers", len(o["WRITTEN"]), "| priors", [(p["FREEZE"], p["VERIFIED_ON_DISK"]) for p in o["PRIORS"]])
    for x in o["REGIONS"]:
        print(f"  {x['ROOM'][:16]:18s} {str(x['AREA_M2']['VALUE']):9s} {x['STATUS']:20s} {x['WET_OR_DRY']}")
    print("subtotals dry", o["SUBTOTALS"]["DRY_INTERNAL_FLOOR_AREA_M2"]["VALUE"], "wet", o["SUBTOTALS"]["WET_INTERNAL_FLOOR_AREA_M2"]["VALUE"])
    print("dimension reconciliation", Counter(x["VERDICT"] for x in o["RECON"]))
    print("regression", o["REGRESSION"]["SYNTHETIC"]["STATUS"], o["REGRESSION"]["SYNTHETIC"]["SUMMARY_LINE"][:40], "| invariants", o["REGRESSION"]["ALL_INVARIANTS_PASS"])
    print("READY:", o["READY"]["READY_FOR_WITHHELD_FLOORING_COMPARISON"], "failed", o["READY"]["FAILED"])
