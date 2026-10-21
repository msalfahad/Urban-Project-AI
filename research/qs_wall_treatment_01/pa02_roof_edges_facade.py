"""PA02.3 - the remaining roof edges (NE, NW/sea-view, SW, annex, tower),
the SE facade opening register (arches by rectangle + semicircle), the
external finish classification and the kerb profile.

Orchestrator visual reads of the native sheets are recorded as
RASTER_INTERPRETATION (PROVISIONAL) with the crop that shows them;
printed dimensions are cited where a witness line terminates on the
element.

    python3 -m research.qs_wall_treatment_01.pa02_roof_edges_facade
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from shapely.geometry import Polygon

from engine.opening_register import opening
from engine.quantity_state import totals_by_unit, weakest
from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)
SLAB, TOP, BAND = 9.70, 11.10, 0.20
PX_PER_M = 157.5   # native scan, 1:100 at ~400 dpi (checked on DIM-13 / DIM-21 / DIM-09)


def _traces(sheet):
    reg = json.loads(Path(P.TRACE_REGISTER).read_text("utf-8"))
    return {t["TRACE_ID"]: t for t in reg["TRACES"] if t["SHEET_ID"] == sheet}


def arch_area(width_m, rect_height_m, arch_kind="SEMICIRCLE", rise_m=None) -> dict:
    """rectangle + semicircle (or a circular segment of the given rise); never a bounding box."""
    if arch_kind == "SEMICIRCLE":
        r = width_m / 2.0
        top = math.pi * r * r / 2.0
        h_total = rect_height_m + r
    elif arch_kind == "SEGMENT":
        c, h = width_m, rise_m
        r = (c * c / 4.0 + h * h) / (2.0 * h)
        theta = 2 * math.asin(c / (2 * r))
        top = r * r / 2.0 * (theta - math.sin(theta))
        h_total = rect_height_m + h
    else:
        raise ValueError(arch_kind)
    return {"RECT_M2": round(width_m * rect_height_m, 4), "ARCH_M2": round(top, 4), "AREA_M2": round(width_m * rect_height_m + top, 4),
            "TOTAL_HEIGHT_M": round(h_total, 3), "SHAPE": f"RECT+{arch_kind}", "BOUNDING_BOX_USED": False}


def run() -> dict:
    tr = _traces("SOUTH_EAST_ELEVATION")
    link = json.loads((OUT / "ROOF_EDGE_PLAN_TO_ELEVATION_LINK_REGISTER.json").read_text("utf-8"))
    st = json.loads((OUT / "STRUCTURAL_SOURCE_CHECK.json").read_text("utf-8"))
    asm = json.loads((OUT / "PARAPET_ASSEMBLY_REGISTER.json").read_text("utf-8"))
    # ---- roof edges ---------------------------------------------------------------
    edges = []
    def edge(eid, **k):
        k["EDGE_ID"] = eid
        edges.append(k)
    sol = link["PORTIONS_PROPOSED"]["SOLID_PORTION_NE"]
    lat = link["PORTIONS_PROPOSED"]["LATTICE_KERB_PORTION_SW"]
    edge("SE", PLAN_RUN={"OUTER_M": 7.50, "SOLID_M": sol["OUTER_FACE_LENGTH_M"], "KERB_M": lat["KERB_ZONE_LINE_LENGTH_M"], "SOURCE": "DWG"},
         EXTERNAL_FACE={"SOLID": {"BOTTOM": SLAB, "TOP": TOP, "H": 1.40, "AREA_M2": round(1.40 * sol["OUTER_FACE_LENGTH_M"], 3)}, "KERB": "polygon PAR-11", "STATE": "PROVISIONAL"},
         ROOF_SIDE_FACE={"SOLID": {"DUAL_BASIS": "D1_LEVEL_IDENTITY.json"}, "KERB": "polygon PAR-11 + 0.18 x run", "STATE": "PROVISIONAL"},
         PARAPET_TYPE="SOLID_WALL (NE portion) + SOLID_KERB with X-LATTICE (SW portion)", BALUSTRADE_TYPE="OPEN_X_LATTICE",
         HEIGHT_BASIS="DIM-21 top +11.10; slab +9.70; base line +9.88 (identity open)", COPING="20 band over the solid portion (DIM-20); rail over the lattice",
         OPENINGS="none in the parapet", SOURCE="PARAPET_ASSEMBLY_REGISTER.json", STATUS="ESTABLISHED lengths / PROVISIONAL faces")
    ne_ext_ref = round(1.40 * 18.27, 3)
    edge("NE", PLAN_RUN={"OUTER_M": 18.27, "ROOF_SIDE_M": 18.87, "SOURCE": "DWG CAD-4735 / CAD-4741"},
         EXTERNAL_FACE={"BOTTOM": SLAB, "TOP": TOP, "H": 1.40, "GEOMETRIC_FACE_AREA_M2": ne_ext_ref, "PLASTER_QUANTITY_STATUS": "NOT_ESTABLISHED (neighbour-side finish eligibility unknown)",
                        "QUANTITY_STATE": "GEOMETRIC_REFERENCE_ONLY"},
         ROOF_SIDE_FACE={"BOTTOM": SLAB, "TOP": TOP, "H": 1.40, "AREA_M2": round(1.40 * 18.87, 3), "STATE": "PROVISIONAL"},
         PARAPET_TYPE="SOLID_WALL full length (A-A hatched cut PAR-07)", BALUSTRADE_TYPE="NONE",
         HEIGHT_BASIS="CORRECTED: the NE elevation wall top reads +11.10 by the chain scale (QA overlay NE_PARAPET_TOP.png: the +11.10 line sits on the drawn top edge); "
                      "A-A hatches 1.62 above the slab; the 1.40 face is carried, the 0.20 band on the NE is NOT_ESTABLISHED (the two readings differ by it); "
                      "the earlier 1.652 face height is SUPERSEDED",
         COPING={"H": BAND, "TOP_WIDTH": 0.20, "AREA_TOP_M2_IF_PRESENT": round(0.20 * 18.27, 3), "STATE": "NOT_ESTABLISHED (existence)"},
         OPENINGS="none", SOURCE="DWG lines + A-A + NE elevation (raster levels by chain scale)", STATUS="PROVISIONAL")
    edge("NW_SEA_VIEW", PLAN_RUN={"ELEMENT_M": round((803894 - 798106) / 1000, 3), "PROJECTION_M": 0.50, "SOURCE": "DWG roof copy lines x -220075 / -219975 (100 mm apart)"},
         EXTERNAL_FACE={"KERB": "curved solid kerb under the lattice: profile NOT_ESTABLISHED (B-B cut shows the lattice on the slab, kerb height ~0 at the cut)", "STATE": "NOT_ESTABLISHED"},
         ROOF_SIDE_FACE={"KERB": "same", "STATE": "NOT_ESTABLISHED"},
         PARAPET_TYPE="SOLID_KERB (curved, low) with X-LATTICE balustrade", BALUSTRADE_TYPE="OPEN_X_LATTICE (NW elevation p6 shows the X panels on a curved kerb; B-B shows a thin 1.30 element with a top cap)",
         HEIGHT_BASIS="NW elevation prints 100 (lattice) + 10 (cap) over the kerb; B-B prints 130 from the slab top to the cap top (DIM-07)",
         COPING="cap over the lattice (rail)", OPENINGS="n/a",
         SOURCE={"NW_ELEVATION": "page 6 native, crop visual read (RASTER_INTERPRETATION)", "B_B": "DIM-07 130, UNK-04/06", "DWG": "10 cm line pair"},
         STATUS="CLASSIFIED_PROVISIONAL: BALUSTRADE (zero plaster) on a low solid kerb; kerb area NOT_ESTABLISHED", 
         NW_THIN_ELEMENT_DECISION="RESOLVED_FROM_SOURCES: not a solid 1.30 m upstand; the 130 is the lattice-plus-cap height; owner question withdrawn")
    sw_h_base = 1.35
    edge("SW", PLAN_RUN={"OUTER_M": 4.325, "ROOF_SIDE_M": 4.125, "SOURCE": "DWG CAD-4805 / CAD-4793"},
         EXTERNAL_FACE={"STATE": "NOT_ESTABLISHED (the SW face faces the plan-top neighbour side; no elevation of it)"},
         ROOF_SIDE_FACE={"BOTTOM": SLAB, "TOP_CANDIDATE": round(9.88 + sw_h_base, 2), "H_CANDIDATE": round(sw_h_base + 0.18, 2),
                         "AREA_M2_CANDIDATE": round((sw_h_base + 0.18) * 4.125, 3), "STATE": "PROVISIONAL (end-on view)"},
         PARAPET_TYPE="SOLID_WALL (20 thick, DIM-05)", BALUSTRADE_TYPE="NONE seen",
         HEIGHT_BASIS="the SE elevation's end pier SEG-04 is the SW parapet seen end-on at the SW corner: 0.33 wide, rounded top ~1.35 above the base line "
                      "(frozen trace polygon); PROPOSED_CORRESPONDENCE; not the generic 0.90 concept",
         COPING="rounded top (no separate band seen)", OPENINGS="none", SOURCE="SE elevation SEG-04 polygon + DWG plan lines",
         STATUS="PROVISIONAL height from an end-on view; queue item SW-PARAPET-HEIGHT downgraded to confirmation")
    edge("ANNEX_4_30", PLAN_RUN={"SOURCE": "FF plan copy outline lines (x -205042..-194693, y -805094..-798594)", "BBOX_PERIMETER_M": round(2 * (10.35 + 6.50), 2),
                                 "STATUS": "GEOMETRIC_REFERENCE_ONLY (bbox of the outline lines; the parapet run is not traced line by line)"},
         EXTERNAL_FACE={"H": 0.50, "SOURCE": "SE elevation '50' above +4.30 (400 + 50 + 30 chain) and NE elevation", "STATE": "NOT_ESTABLISHED (run not traced)"},
         ROOF_SIDE_FACE={"H": 0.50, "STATE": "NOT_ESTABLISHED"}, PARAPET_TYPE="LOW SOLID PARAPET 0.50 with an X-LATTICE section at the SW corner (NE elevation)",
         BALUSTRADE_TYPE="OPEN_X_LATTICE (part)", HEIGHT_BASIS="printed 50 on the SE and NE elevations", COPING="not seen", OPENINGS="n/a",
         SOURCE="SE / NE elevations (raster), FF plan copy (DWG)", STATUS="NOT_STARTED beyond the height; run to be traced")
    tower = st["TOWER_ROOF_13_90_OUTLINE_p6"]
    edge("TOWER_13_90", PLAN_RUN={"RING_M": tower["DEVELOPED_PERIMETER_M"], "SOURCE": "ST7757 p6 exterior ring (vector)"},
         EXTERNAL_FACE={"H": 0.50, "AREA_M2": round(0.50 * tower["DEVELOPED_PERIMETER_M"], 3), "STATE": "PROVISIONAL"},
         ROOF_SIDE_FACE={"H": 0.50, "AREA_M2": asm and next(f["AREA"]["GROSS_AREA_M2"] for f in json.loads((OUT / "FACE_MEASUREMENT_REGISTER.json").read_text("utf-8"))["FACES"] if f["FACE_ID"] == "F-TOWER-RING-ROOFSIDE"), "STATE": "PROVISIONAL"},
         PARAPET_TYPE="SOLID ring 0.50 (A-A hatched)", BALUSTRADE_TYPE="NONE", HEIGHT_BASIS="DIM-10 OWNER_ESTABLISHED", COPING="not seen", OPENINGS="none",
         SOURCE="A-A + ST p6", STATUS="PROVISIONAL")
    # ---- SE facade openings (orchestrator visual read + printed dimensions) -------------
    ops = []
    NATIVE_BOX = {"SE-TW-W1": (1514, 2709, 1814, 2891), "SE-TW-W2": (2223, 2709, 2568, 2891), "SE-TW-W3": (2568, 2709, 2895, 2891),
                  "SE-TW-W4": (2895, 2709, 3150, 2891), "SE-TW-D1": (1260, 2300, 1560, 2470), "SE-MB-W1": (2275, 3375, 2574, 3714),
                  "SE-AN-D1": (1247, 3406, 1641, 3578)}   # native page-4 pixels (x = level axis, y = run axis), orchestrator read +-10 px
    def op(oid, host, typ, w, ws, h, hs, shape="RECT", arch=None, note=None, rd=0.20, rds="PROVISIONAL_DEFAULT", evidence=None):
        o = opening(opening_id=oid, host_face=host, opening_type=typ, width_m=w, width_source=ws, height_m=h, height_source=hs,
                    deduction_rule="FULL_OPENING_DEDUCTION", reveal_depth_m=rd, reveal_depth_source=rds)
        o["SHAPE"] = shape
        if arch:
            o["ARCH"] = arch
            o["AREA"] = arch["AREA_M2"]
            o["DEDUCTION_AMOUNT"] = arch["AREA_M2"]
            o["HEIGHT"] = arch["TOTAL_HEIGHT_M"]
        o["FLOOR"] = "SE facade"
        o["NOTE"] = note
        o["EVIDENCE"] = evidence
        o["ACTUAL_OR_DEFAULT"] = "ACTUAL_DRAWING" if ws != "PROVISIONAL_DEFAULT" and hs != "PROVISIONAL_DEFAULT" else "DEFAULT"
        o["NATIVE_BOX_PAGE4"] = NATIVE_BOX.get(oid)
        o["SOURCE_TIER"] = "RASTER_INTERPRETATION (orchestrator read of the native page 4 with the printed dimensions cited)"
        ops.append(o)
    # tower strip: widths printed 120; heights printed 200 / 230 / 200 / 170 (arched top)
    op("SE-TW-W1", "F-SE-TOWER-EXT", "WINDOW", 1.20, "PROVISIONAL", 2.00, "PROVISIONAL", note="tower strip, lowest window (printed 120 x 200; witness termination read on the native crop, not audited)", evidence="scratch se_tower_strip")
    op("SE-TW-W2", "F-SE-TOWER-EXT", "WINDOW", 1.20, "PROVISIONAL", 2.30, "PROVISIONAL", note="printed 120 x 230")
    op("SE-TW-W3", "F-SE-TOWER-EXT", "WINDOW", 1.20, "PROVISIONAL", 2.00, "PROVISIONAL", note="printed 120 x 200")
    op("SE-TW-W4", "F-SE-TOWER-EXT", "WINDOW", 1.20, "PROVISIONAL", 1.10, "PROVISIONAL", shape="RECT+SEMICIRCLE", arch=arch_area(1.20, 1.10),
       note="top window: printed 170 total = 110 rect + 60 semicircle (r = 0.60 = half the printed 120 width)")
    op("SE-TW-D1", "F-SE-TOWER-EXT", "DOOR", 1.08, "PROVISIONAL", 2.00, "PROVISIONAL", rd=0.20, note="tower base door at +0.15: native px 170 x 300 / 157.5 (raster read)")
    op("SE-MB-W1", "F-SE-FACADE-EXT", "WINDOW", 2.15, "PROVISIONAL", 1.90, "PROVISIONAL",
       note="grill window under the parapet: printed 215 x 190 with witness lines on the frame (native crop se_grill_window); side shutter panels excluded from the opening")
    op("SE-AN-D1", "F-SE-ANNEX-EXT", "DOOR", 1.00, "PROVISIONAL", 2.50, "OWNER_ESTABLISHED", note="annex entrance door: printed 250 high; width 155 px / 157.5 raster")
    # facade faces and net (GEOMETRIC_REFERENCE_ONLY until the finish system is known)
    faces = {
        "F-SE-TOWER-EXT": {"WIDTH_M": 4.41, "WIDTH_SOURCE": "printed 441 (tower width, SE elevation top chain) - PROVISIONAL (witness lines not audited)",
                           "BOTTOM": 0.15, "TOP": 14.40, "GROSS_M2": round(4.41 * (14.40 - 0.15), 3)},
        "F-SE-FACADE-EXT": {"WIDTH_M": 7.50, "WIDTH_SOURCE": "DWG outer face 7.50 (main block between the tower and the NE corner; printed 123 + 215 + 402 = 7.40 + corner)",
                            "BOTTOM": 4.30, "TOP": 9.70, "GROSS_M2": 40.5},
        "F-SE-ANNEX-EXT": {"WIDTH_M": None, "WIDTH_SOURCE": "NOT_ESTABLISHED (annex width not printed on the SE sheet; FF-copy outline not traced)",
                           "BOTTOM": 0.30, "TOP": 4.30, "GROSS_M2": None},
    }
    for fid, f in faces.items():
        ded = round(sum(o["AREA"] for o in ops if o["HOST_FACE"] == fid and o["AREA"]), 4)
        rev = round(sum(o["REVEAL_AREA"] for o in ops if o["HOST_FACE"] == fid and o["REVEAL_AREA"]), 4)
        f["OPENING_DEDUCTIONS_M2"] = ded
        f["REVEALS_M2"] = rev
        f["NET_M2"] = (round(f["GROSS_M2"] - ded, 3) if f["GROSS_M2"] else None)
        f["QUANTITY_STATE"] = "GEOMETRIC_REFERENCE_ONLY" if f["GROSS_M2"] else "NOT_ESTABLISHED"
        f["EXTERNAL_PLASTER_M2"] = None
        f["WHY"] = "external finish system UNKNOWN for this face (see EXTERNAL_FINISH_REGISTER)"
    finish = [
        {"ELEMENT": "annex entrance arch (rusticated quoin blocks)", "CLASS": "EXTERNAL_CLADDING_CONFIRMED", "EVIDENCE": "drawn as a stone-block pattern on the SE elevation (native crop se_annex_door)", "STATE": "PROVISIONAL"},
        {"ELEMENT": "grill window side panels (louvred)", "CLASS": "SURFACE_ELEMENT_NOT_PLASTER", "EVIDENCE": "hatched louvre panels either side of the 215 window", "STATE": "PROVISIONAL"},
        {"ELEMENT": "tower double-curve corner bands", "CLASS": "UNKNOWN_EXTERNAL_FINISH", "EVIDENCE": "thick concentric lines (72 / 72 / 5) - profile bands of unknown material", "STATE": "NOT_ESTABLISHED"},
        {"ELEMENT": "outer skin element on B-B (UNK-05, 10 cm, ~+8.6 to ~+10.5)", "CLASS": "UNKNOWN_EXTERNAL_FINISH", "EVIDENCE": "un-hatched outline on the section", "STATE": "NOT_ESTABLISHED"},
        {"ELEMENT": "plain facade faces (tower, main block, annex)", "CLASS": "UNKNOWN_EXTERNAL_FINISH", "EVIDENCE": "no hatch, no material note, no finish layer in the DWG (layers 0/1/2/3/4/5/D/W/ST/TEXT/TOI/ARNOTE/TE/LEVEL/S-COL.BON carry no finish), no detail sheet", "STATE": "NOT_ESTABLISHED"},
    ]
    # ---- kerb profile (SE) ---------------------------------------------------------------
    poly = Polygon(tr["PAR-11"]["ORIGINAL_PAGE_GEOMETRY"]["PIXEL_POLYGON"]["COORDINATES"])
    pts = list(poly.exterior.coords)
    # the polygon runs: base line (min x ~ constant) and top edge (varying); take the top edge as the vertices with x above the base line
    base_x = min(p[0] for p in pts)
    # top edge = ring segments that are neither on the base line nor vertical end returns
    dev_px, nseg = 0.0, 0
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        on_base = abs(x0 - base_x) < 2 and abs(x1 - base_x) < 2
        end_return = abs(y1 - y0) < 3
        if on_base or end_return:
            continue
        dev_px += math.hypot(x1 - x0, y1 - y0)
        nseg += 1
    dev = dev_px / PX_PER_M
    top_pts = [None] * (nseg + 1)
    kerb = {"KERB_PROFILE_ID": "KP-SE-01", "PLAN_RUN_LENGTH_M": lat["KERB_ZONE_LINE_LENGTH_M"],
            "ELEVATION_RASTER_WIDTH_M": round((max(p[1] for p in pts) - min(p[1] for p in pts)) / PX_PER_M, 3),
            "DEVELOPED_PROFILE_LENGTH_M": round(dev, 3), "TOP_EDGE_VERTICES": len(top_pts),
            "EXTERNAL_FACE_AREA_M2": round(poly.area / PX_PER_M / PX_PER_M, 4),
            "INTERNAL_FACE_AREA_M2": round(poly.area / PX_PER_M / PX_PER_M + 0.18 * lat["KERB_ZONE_LINE_LENGTH_M"], 4),
            "TOP_COPING_AREA_M2": round(0.20 * dev, 4),
            "CURVE_SOURCE": "frozen A21 trace polygon PAR-11 (raster, top edge as a polyline); the DWG holds no authored curve for the SE kerb (the DWG elevation blob is the NW elevation)",
            "STATUS": "PROVISIONAL (polyline approximation of the ogee: developed length is a lower bound of the true curve)",
            "PROJECTED_STRAIGHT_HEIGHT_NOT_USED": True}
    out = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "ROOF_EDGES_FACADE_FINISH_KERB", "ROOF_EDGE_REGISTER": edges,
           "SE_FACADE_OPENING_REGISTER": ops, "SE_FACADE_FACES": faces, "EXTERNAL_FINISH_REGISTER": finish,
           "EXTERNAL_FINISH_CONCLUSION": "no project-wide binary is supported: one element is confirmed cladding (the entrance arch), the plain faces are UNKNOWN_EXTERNAL_FINISH; "
                                         "external plaster quantities stay NOT_ESTABLISHED, geometric net faces are given as GEOMETRIC_REFERENCE_ONLY",
           "KERB_PROFILE_REGISTER": [kerb],
           "NOTE": "openings on the SE facade are orchestrator visual reads of the native page 4 with the printed dimensions cited; they are RASTER_INTERPRETATION (PROVISIONAL) "
                   "except the 215 x 190 window whose dimensions are printed on it"}
    p = OUT / "ROOF_EDGES_FACADE_FINISH_KERB.json"
    p.write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
    return {"EDGES": [(e["EDGE_ID"], e["STATUS"]) for e in edges], "OPENINGS": [(o["OPENING_ID"], o["WIDTH"], o["HEIGHT"], o["AREA"], o["STATUS"]) for o in ops],
            "FACES": {k: (v["GROSS_M2"], v["OPENING_DEDUCTIONS_M2"], v["NET_M2"], v["QUANTITY_STATE"]) for k, v in faces.items()},
            "KERB": {k: kerb[k] for k in ("DEVELOPED_PROFILE_LENGTH_M", "EXTERNAL_FACE_AREA_M2", "INTERNAL_FACE_AREA_M2", "TOP_COPING_AREA_M2")},
            "SHA": hashlib.sha256(p.read_bytes()).hexdigest()[:16]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
