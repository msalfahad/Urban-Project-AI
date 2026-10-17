"""PA04 workstream C - NORTH EAST and NORTH WEST facade openings and
facade-face geometry.  NW: the DWG carries an authored NW elevation
(dimension entities read by value / position, no text overrides) plus the
raster page 6; NE: raster page 7 only.  The primary reading here is merged
with the cold-challenge reading in challenges.py; finish eligibility is
kept separate from geometry.

    python3 -m research.qs_wall_treatment_01.pa04.facades
"""

from __future__ import annotations

import math

from engine import self_checks as SC
from engine.parapet_assembly import developed_length  # noqa: F401
from research.qs_wall_treatment_01.pa04 import common as C

BLOB = (-390000, -348000, -806500, -789000)


def _dims_in_blob():
    n = C.norm()
    out = []
    for d in n.dimensions:
        if BLOB[0] <= d.x1 <= BLOB[1] and BLOB[2] <= d.y1 <= BLOB[3]:
            out.append({"VALUE": d.display_value, "GEOMETRY_MM": round(d.geometry_mm, 1), "FROM": [round(d.x1, 1), round(d.y1, 1)], "TO": [round(d.x2, 1), round(d.y2, 1)],
                        "OVERRIDDEN": bool(d.user_text), "HANDLE": d.provenance.handle})
    return out


def _chain(dims, axis, at, tol=60):
    """Ordered dimension chain along one axis at a given coordinate."""
    key = 0 if axis == "x" else 1
    sel = [d for d in dims if abs(d["FROM"][1 - key] - at) < tol and abs(d["TO"][1 - key] - at) < tol]
    return sorted(sel, key=lambda d: min(d["FROM"][key], d["TO"][key]))


def _jamb_heights(xs, tol=40):
    out = []
    for p in C.prims():
        if p[0] == "SEGMENT" and p[2] in ("1", "W") and abs(p[3] - p[5]) < 1 and any(abs(p[3] - x) < tol for x in xs) and -806000 <= min(p[4], p[6]) and max(p[4], p[6]) <= -788000 and abs(p[4] - p[6]) > 300:
            out.append({"ID": p[1], "X": round(p[3], 1), "Y0": round(min(p[4], p[6]), 1), "Y1": round(max(p[4], p[6]), 1), "H_M": round(abs(p[4] - p[6]) / 1000, 3)})
    return out


def arch_area(width, rect_h, r=None):
    r = r if r is not None else width / 2
    return {"RECT_M2": round(width * rect_h, 4), "ARCH_M2": round(math.pi * r * r / 2, 4), "TOTAL_M2": round(width * rect_h + math.pi * r * r / 2, 4), "R_M": r, "SHAPE": "RECT+SEMICIRCLE", "BOUNDING_BOX_USED": False}


@C.timed("C_facades")
def run():
    dims = _dims_in_blob()
    run_chain = _chain(dims, "x", -798589)          # horizontal chain at y -798589 (FF window sill zone)
    lv_chain = _chain(dims, "y", -376385)           # 100 / 870 / 420 / 50
    tower_chain = _chain(dims, "y", -364310)        # 115 / 70 / 430 / 20 / 305 / 45.4 / 199.5 / 320 / 20 / 214.9
    win_chain = _chain(dims, "y", -371936)          # 300 / 10.1 / 99.9 / 20 / 89.1 / 171.6
    big_chain = _chain(dims, "y", -366732)          # 83.9 / 216.1 / 230
    vals = [round(d["VALUE"], 1) for d in run_chain]
    total_run = round(sum(d["VALUE"] for d in run_chain) / 100, 3)
    # NW openings from the authored chains (primary reading; the cold challenge reads the raster independently)
    op = []
    def opening(oid, storey, typ, w, h, owner, shape="RECT", arch=None, conf="MEDIUM", note=None):
        area = arch_area(w, h)["TOTAL_M2"] if shape == "RECT+SEMICIRCLE" else round(w * h, 4)
        op.append({"OPENING_ID": oid, "FACADE": "NW", "STOREY": storey, "TYPE": typ, "SHAPE": shape, "WIDTH_M": w, "HEIGHT_M": h, "ARCH": arch_area(w, h) if shape == "RECT+SEMICIRCLE" else None,
                   "AREA_M2": area, "DIMENSION_OWNER": owner, "SOURCE": "DWG NW elevation dimension entities (authored)", "CONFIDENCE": conf, "NOTE": note, "BOUNDING_BOX_USED": False,
                   "FINISH_ELIGIBILITY": "SEPARATE (see FACADE_FACES)"})
    # three arched windows 155.2 wide on the FF of the main block; heights: chain at x -371936: 300 (sill zone?) / 10.1 / 99.9 / 20 / 89.1 / 171.6 -> the arched window's
    # rectangular part and arch are NOT separately owned by a printed figure here; the 171.6 is the arch-to-top segment: heights PROVISIONAL from the vertical chain at the window
    jambs = _jamb_heights([-369114, -370666, -371160, -372712])
    rect_h = round(min(j["H_M"] for j in jambs), 3) if jambs else 1.20
    for i, x in enumerate((-369114, -371160, -372712)):
        opening(f"NW-FF-W{i+1}", "FF", "WINDOW", 1.552, rect_h, f"width: printed 155.2 (run chain at y -798589); rectangular height {rect_h}: DWG jamb lines (layers 1 / W) from the +5.50 slab line -799746.4 to the springing -797585.5 (= the printed 216.1 chain figure); arch semicircle r 0.776 (half the width)",
                shape="RECT+SEMICIRCLE", conf="HIGH", note="arched French window to the slab (rect + semicircle); primary scaled 1.20 and challenger scaled ~3.45 total were both replaced by the DWG jamb geometry (CAD authority)")
        op[-1]["JAMB_ENTITIES"] = [j["ID"] for j in jambs]
    opening("NW-TW-ARCH", "FF (tower)", "ARCHED_OPENING", 2.691, 2.161, "width: printed 269.1 (run chain); rectangular height: printed 216.1 (chain at x -366732); arch: 83.9 above (chain) -> rise 0.839 < r 1.346: SEGMENTAL, not semicircular",
            shape="RECT+SEGMENT", conf="MEDIUM", note="the printed 83.9 rise is smaller than the half-width: a segmental arch; area = rect + circular segment")
    seg_r = (1.3455 ** 2 + 0.839 ** 2) / (2 * 0.839)
    theta = 2 * math.asin(1.3455 / seg_r)
    seg_area = round(0.5 * seg_r ** 2 * (theta - math.sin(theta)), 4)
    op[-1]["ARCH"] = {"KIND": "SEGMENT", "RISE_M": 0.839, "HALF_WIDTH_M": 1.3455, "R_M": round(seg_r, 4), "SEGMENT_M2": seg_area, "BOUNDING_BOX_USED": False}
    op[-1]["AREA_M2"] = round(2.691 * 2.161 + seg_area, 4)
    opening("NW-GF-GRILLE", "GF", "GRILLE / GLAZED SCREEN", 2.691, 4.30, "width: same tower bay 269.1 (PROVISIONAL alignment); height: printed 430 (tower chain 115 / 70 / 430)", conf="LOW",
            note="tall vertical-bar element under the tower arch on the DWG (a grille or screen); type PROVISIONAL")
    withdrawn = [{"OPENING_ID": "NW-GF-D1", "WHY": "the panelled door on the DWG NW elevation sits in the CUT ground storey (the sheet is a section-elevation: hatched +1.00 / +5.50 slabs); it is an interior door, not a facade opening (cold-challenge finding, confirmed by the hatch on page 6)", "STATUS": "WITHDRAWN_BEFORE_FREEZE"}]
    # facade faces (geometry only)
    h_ff = 4.20; h_gf = 4.50
    nw_faces = [{"FACE_ID": "F-NW-MAIN-FF", "STOREY": "FF", "WIDTH_M": round(sum(v for v in vals if v >= 10) / 100, 3), "HEIGHT_M": h_ff, "GROSS_GEOMETRIC_FACE_M2": None, "OPENING_IDS": ["NW-FF-W1", "NW-FF-W2", "NW-FF-W3"]},
                {"FACE_ID": "F-NW-TOWER-FF", "STOREY": "FF (tower bay)", "WIDTH_M": 2.691 + 0.298 + 0.75, "HEIGHT_M": h_ff, "GROSS_GEOMETRIC_FACE_M2": None, "OPENING_IDS": ["NW-TW-ARCH"]}]
    nw_faces.append({"FACE_ID": "F-NW-GF", "STOREY": "GF", "WIDTH_M": None, "HEIGHT_M": h_gf, "GROSS_GEOMETRIC_FACE_M2": None, "OPENING_IDS": [], "NOTE": "ground storey cut on page 6; openings not shown; NOT_ESTABLISHED"})
    for f in nw_faces:
        if f["WIDTH_M"] is None:
            f.update({"OPENING_AREA_M2": None, "NET_GEOMETRIC_FACE_M2": None, "FINISH_ELIGIBILITY_STATUS": "UNKNOWN", "QUANTITY_STATE": "NOT_ESTABLISHED"})
            continue
        f["GROSS_GEOMETRIC_FACE_M2"] = round(f["WIDTH_M"] * f["HEIGHT_M"], 3)
        f["OPENING_AREA_M2"] = round(sum(o["AREA_M2"] for o in op if o["OPENING_ID"] in f["OPENING_IDS"]), 3)
        f["NET_GEOMETRIC_FACE_M2"] = round(f["GROSS_GEOMETRIC_FACE_M2"] - f["OPENING_AREA_M2"], 3)
        f["FINISH_ELIGIBILITY_STATUS"] = "UNKNOWN_EXTERNAL_FINISH (owner item EXTERNAL-FINISH-SYSTEM)"
        f["QUANTITY_STATE"] = "GEOMETRIC_REFERENCE_ONLY"
        f["WIDTH_BASIS"] = "sum of the run-chain figures >= 10 cm at y -798589 (PROVISIONAL: the chain covers the main-block bays, tower bay partial)"
    ne = {"ELEVATION_SOURCE": "page 7 raster only (no DWG elevation for the NE side)", "PRIMARY_READ": [
            {"OPENING_ID": "NE-FF-W1", "STOREY": "FF", "TYPE": "WINDOW", "SHAPE": "RECT", "DIMENSION_OWNER": "none printed on page 7 - scaled only", "CONFIDENCE": "LOW", "NOTE": "small square window, left"},
            {"OPENING_ID": "NE-FF-W2", "STOREY": "FF", "TYPE": "WINDOW", "SHAPE": "RECT", "DIMENSION_OWNER": "none printed - scaled only", "CONFIDENCE": "LOW", "NOTE": "small square window, second from left"},
            {"OPENING_ID": "NE-FF-W3", "STOREY": "FF", "TYPE": "WINDOW", "SHAPE": "RECT", "DIMENSION_OWNER": "none printed - scaled only", "CONFIDENCE": "LOW", "NOTE": "larger square window, centre-left"}],
          "FACE": {"FACE_ID": "F-NE-MAIN", "WIDTH_M": 18.27, "WIDTH_BASIS": "NE parapet outer line CAD-4735 (roof copy)", "HEIGHT_M": None, "HEIGHT_BASIS": "the NE face rises from the neighbour-wall side; page 7 prints +5.50 only; ground level at the neighbour side NOT_ESTABLISHED",
                   "GROSS_GEOMETRIC_FACE_M2": None, "QUANTITY_STATE": "NOT_ESTABLISHED (height) / GEOMETRIC_REFERENCE_ONLY (width)"},
          "STATUS": "PRIMARY READ ONLY - merged with the cold challenge in challenges.py; no printed opening dimensions exist on page 7 so every NE opening stays PROVISIONAL / scaled"}
    lines = [{"ID": o["OPENING_ID"], "SOURCE": o["SOURCE"], "SOURCE_ENTITY_IDS": ["DWG NW elevation dims"], "PRINTED_VALUE": None} for o in op]
    checks = SC.run_all({"NW": op, "NE": ne}, lines)
    C.METRICS.setdefault("C_facades", {}).update({"AI_CALLS": 1, "AI_CALLS_NOTE": "one cold-challenge reader for both elevations", "DETERMINISTIC_OPS": len(dims)})
    C.write("FACADE_OPENINGS_NE_NW_PRIMARY.json", {"ARTIFACT": "FACADE_OPENINGS_NE_NW_PRIMARY", "WORKSTREAM": "C", "WITHDRAWN": withdrawn,
                                                     "SHEET_NATURE": "pages 6 and 7 are section-elevations: the ground storey is CUT (hatched slabs), so GF facade openings on the NE / NW faces are NOT shown; GF facade faces stay NOT_ESTABLISHED", "NW_DWG_DIMENSION_CHAINS": {"RUN_Y_-798589": vals, "RUN_TOTAL_M": total_run, "LEVELS_X_-376385": [d["VALUE"] for d in lv_chain],
                                                     "TOWER_X_-364310": [d["VALUE"] for d in tower_chain], "WINDOW_X_-371936": [d["VALUE"] for d in win_chain], "BIG_ARCH_X_-366732": [d["VALUE"] for d in big_chain]},
                                                     "NW_OPENINGS": op, "NW_FACADE_FACES": nw_faces, "NE": ne, "SELF_CHECKS": checks,
                                                     "FINISH_ELIGIBILITY": "GEOMETRIC_REFERENCE_ONLY for every face until EXTERNAL-FINISH-SYSTEM is answered"})
    return {"RUN": vals, "RUN_TOTAL": total_run, "NW_OPENINGS": [(o["OPENING_ID"], o["WIDTH_M"], o["HEIGHT_M"], o["AREA_M2"], o["CONFIDENCE"]) for o in op], "FACES": [(f["FACE_ID"], f["GROSS_GEOMETRIC_FACE_M2"], f["NET_GEOMETRIC_FACE_M2"]) for f in nw_faces], "CHECKS": checks["FAILED"]}


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=1, default=str))
