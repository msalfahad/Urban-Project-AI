"""ROOF-EDGE CAD SEARCH (directive §4): the SE roof edge in the authored
DWG roof-plan copy, measured deterministically, and its correspondence to
the frozen elevation traces - PROPOSED until proven.

    python3 -m research.qs_wall_treatment_01.roof_edge_cad
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from engine import cad_adapter as CA
from engine.parapet_assembly import developed_length
from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)
DECODE = "data/runs/cad_convert/P7757_ARCHITECTURAL.json"
# the DWG lays the plans out in a row 44 852.65 mm apart: GF, FF, ROOF (street at low x)
ROOF_WINDOW = {"x": (-256500, -213000), "y": (-812000, -783000)}
ELEV_WINDOW = {"x": (-389000, -348000), "y": (-812000, -783000)}
ELEV_GROUND_Y = -805246.0        # the 1440 chain's lower extension origin (+-0.00)


def _norm():
    d = json.loads(Path(DECODE).read_text("utf-8"))
    return CA.normalize(d, source_file="P7757_ARCHITECTURAL.dwg")


def _in(w, x, y):
    return w["x"][0] <= x <= w["x"][1] and w["y"][0] <= y <= w["y"][1]


def _vertical_runs(n, w, x_lo, x_hi, min_len=300):
    out = []
    for p in n.primitives:
        if p.kind != "SEGMENT" or abs(p.x1 - p.x2) > 1 or abs(p.y1 - p.y2) < min_len:
            continue
        if x_lo < p.x1 < x_hi and _in(w, p.x1, p.y1):
            out.append({"ID": p.object_id, "LAYER": p.provenance.layer, "X_MM": round(p.x1, 1),
                        "Y_FROM_MM": round(min(p.y1, p.y2), 1), "Y_TO_MM": round(max(p.y1, p.y2), 1),
                        "LENGTH_MM": round(abs(p.y2 - p.y1), 1), "KIND": "LINE",
                        "length_mm": abs(p.y2 - p.y1)})
    return sorted(out, key=lambda r: (r["X_MM"], r["Y_FROM_MM"]))


def _horizontal_runs(n, w, y_lo, y_hi, x_lo, x_hi, min_len=300):
    out = []
    for p in n.primitives:
        if p.kind != "SEGMENT" or abs(p.y1 - p.y2) > 1 or abs(p.x1 - p.x2) < min_len:
            continue
        if y_lo < p.y1 < y_hi and x_lo < min(p.x1, p.x2) < x_hi and _in(w, p.x1, p.y1):
            out.append({"ID": p.object_id, "LAYER": p.provenance.layer, "Y_MM": round(p.y1, 1),
                        "X_FROM_MM": round(min(p.x1, p.x2), 1), "X_TO_MM": round(max(p.x1, p.x2), 1),
                        "LENGTH_MM": round(abs(p.x2 - p.x1), 1), "KIND": "LINE",
                        "length_mm": abs(p.x2 - p.x1)})
    return sorted(out, key=lambda r: (r["Y_MM"], r["X_FROM_MM"]))


def _arcs(n, w, x_lo, x_hi):
    out = []
    for p in n.primitives:
        if p.kind == "ARC" and x_lo < p.cx < x_hi and _in(w, p.cx, p.cy):
            a0, a1 = getattr(p, "start_angle", None), getattr(p, "end_angle", None)
            sweep = (a1 - a0) % (2 * math.pi) if a0 is not None else None
            out.append({"ID": p.object_id, "LAYER": p.provenance.layer, "KIND": "ARC",
                        "CENTRE_MM": [round(p.cx, 1), round(p.cy, 1)], "RADIUS_MM": round(p.radius, 1),
                        "START_RAD": a0, "END_RAD": a1, "SWEEP_RAD": (round(sweep, 6) if sweep else None),
                        "radius_mm": p.radius, "sweep_rad": sweep or 0.0})
    return out


def run() -> dict:
    n = _norm()
    reg = json.loads(Path(P.TRACE_REGISTER).read_text("utf-8"))
    tr = {t["TRACE_ID"]: t for t in reg["TRACES"] if t["CASE_ID"] == "CASE-6-ROOF-PARAPET"}
    # ---- roof plan copy: domes locate the copy; the SE edge is the street-side vertical run
    domes = [{"ID": p.object_id, "LAYER": p.provenance.layer, "CENTRE_MM": [round(p.cx, 1), round(p.cy, 1)],
              "RADIUS_MM": round(p.radius, 1)} for p in n.primitives
             if p.kind == "CIRCLE" and p.radius > 2000 and _in(ROOF_WINDOW, p.cx, p.cy)]
    domes.sort(key=lambda d: d["CENTRE_MM"][0])
    se_dome = domes[0]
    x_search = (se_dome["CENTRE_MM"][0] - 3500, se_dome["CENTRE_MM"][0] - 2000)
    verts = _vertical_runs(n, ROOF_WINDOW, *x_search, min_len=2000)
    outer = min(verts, key=lambda v: v["X_MM"])          # street-most long line = outer face
    x_out = outer["X_MM"]
    lines = {v["ID"]: v for v in verts}
    at = lambda dx, tol=5: [v for v in verts if abs(v["X_MM"] - (x_out + dx)) <= tol]
    inner200 = at(200)
    line250 = at(250)
    line400 = at(400)
    corner_arcs = _arcs(n, ROOF_WINDOW, x_out - 100, x_out + 500)
    cross = _horizontal_runs(n, ROOF_WINDOW, outer["Y_FROM_MM"], outer["Y_TO_MM"], x_out - 10, x_out + 10, min_len=300)
    ne_inner = _horizontal_runs(n, ROOF_WINDOW, outer["Y_FROM_MM"] + 150, outer["Y_FROM_MM"] + 250, x_out - 10, x_out + 600, min_len=5000)
    sw_lines = _horizontal_runs(n, ROOF_WINDOW, outer["Y_TO_MM"] - 300, outer["Y_TO_MM"] + 5, x_out - 10, x_out + 600, min_len=2000)
    y_sw_outer = outer["Y_TO_MM"]
    y_ne_outer = outer["Y_FROM_MM"]
    kerb_zone = line250[0] if line250 else None
    # developed lengths (authored: lines by endpoints, arcs by r*sweep)
    outer_dev = developed_length([outer] + [a for a in corner_arcs if a["RADIUS_MM"] < 500])
    solid_portion = None
    lattice_portion = None
    if kerb_zone:
        y_split = kerb_zone["Y_FROM_MM"]                   # the 250-line ends here
        solid_portion = {"Y_FROM_MM": y_ne_outer, "Y_TO_MM": y_split,
                         "OUTER_FACE_LENGTH_M": round((y_split - y_ne_outer) / 1000, 4),
                         "ROOF_SIDE_FACE_LENGTH_M": round((y_split - (ne_inner[0]["Y_MM"] if ne_inner else y_ne_outer)) / 1000, 4),
                         "ROOF_SIDE_FROM": (ne_inner[0]["ID"] if ne_inner else None)}
        lattice_portion = {"Y_FROM_MM": y_split, "Y_TO_MM": y_sw_outer,
                           "OUTER_FACE_LENGTH_M": round((y_sw_outer - y_split) / 1000, 4),
                           "KERB_ZONE_LINE_LENGTH_M": round(kerb_zone["LENGTH_MM"] / 1000, 4),
                           "CORNER_ARC": [a for a in corner_arcs if a["RADIUS_MM"] < 500]}
    # frozen printed chain on the roof plan: 129 + 2 x R221 + 139 = 710 roof-side (SEG-02)
    chain_710 = None
    if line400:
        chain_710 = {"CAD_LINE_ID": line400[0]["ID"], "CAD_LENGTH_M": round(line400[0]["LENGTH_MM"] / 1000, 4),
                     "PRINTED_CHAIN_M": tr["SEG-02"]["LENGTH_M"],
                     "MATCH": abs(line400[0]["LENGTH_MM"] / 1000 - tr["SEG-02"]["LENGTH_M"]) < 0.005,
                     "WHAT_THE_LINE_IS": "third line 400 mm inside the outer face; the terrace floor "
                                         "hatch boundary the printed 129 tick lands on (frozen UNK-03)"}
    # ---- the DWG elevation (blob at x < -340 000): level chain and the parapet-zone levels
    elev_dims = []
    for d in n.dimensions:
        (x1, y1), (x2, y2) = d.extension_origins_mm if hasattr(d, "extension_origins_mm") else d.record()["extension_origins_mm"]
        if _in(ELEV_WINDOW, x1, y1):
            elev_dims.append({"ID": d.provenance.object_id, "DISPLAY": round(d.display_value, 3),
                              "MEASURED_MM": round(d.geometry_mm, 1), "FROM": [round(x1), round(y1)],
                              "TO": [round(x2), round(y2)],
                              "LEVEL_FROM": round((y1 - ELEV_GROUND_Y) / 1000, 3),
                              "LEVEL_TO": round((y2 - ELEV_GROUND_Y) / 1000, 3)})
    chain = [d for d in elev_dims if d["DISPLAY"] in (1440.0, 100.0, 870.0, 420.0, 50.0) and abs(d["FROM"][0] - d["TO"][0]) < 800]
    zone = []
    for p in n.primitives:
        if p.kind == "SEGMENT" and _in(ELEV_WINDOW, p.x1, p.y1) and -377500 < min(p.x1, p.x2) and max(p.x1, p.x2) < -366500:
            lv1, lv2 = (p.y1 - ELEV_GROUND_Y) / 1000, (p.y2 - ELEV_GROUND_Y) / 1000
            if 9.5 <= min(lv1, lv2) and max(lv1, lv2) <= 12.5 and abs(p.y1 - p.y2) < 1 and abs(p.x1 - p.x2) >= 1000:
                zone.append({"ID": p.object_id, "LAYER": p.provenance.layer, "LEVEL": round(lv1, 3),
                             "X_FROM": round(min(p.x1, p.x2)), "X_TO": round(max(p.x1, p.x2)),
                             "LENGTH_MM": round(abs(p.x2 - p.x1))})
    zone.sort(key=lambda z: (z["LEVEL"], z["X_FROM"]))
    levels = sorted({z["LEVEL"] for z in zone})
    out = {
        "PHASE_ID": P.PHASE_ID, "ARTIFACT": "ROOF_EDGE_PLAN_TO_ELEVATION_LINK_REGISTER",
        "SOURCE": {"DWG_DECODE": DECODE, "NORMALIZATION_HASH": n.normalization_hash(),
                   "DRAWING_UNIT": n.drawing_unit, "INSUNITS": n.insunits_code},
        "SOURCE_HIERARCHY_USED": ["DWG_AUTHORED_GEOMETRY", "PRINTED_DIMENSION (frozen A21)",
                                  "RASTER_INTERPRETATION (frozen A21)", "OWNER_INTERPRETATION"],
        "ROOF_PLAN_COPY": {"DOMES": domes, "SE_DOME_USED_AS_LOCATOR": se_dome,
                           "NOTE": "the roof plan is the third plan copy in the row; the SE (street) "
                                   "edge is the street-side vertical run beside the SE dome"},
        "SE_ROOF_EDGE_AUTHORED": {
            "OUTER_FACE": outer, "INNER_FACE_200": inner200, "LINE_250_KERB_ZONE": line250,
            "LINE_400_FLOOR_EDGE": line400, "CORNER_ARCS": corner_arcs, "CROSS_LINES": cross,
            "NE_INNER_RETURN": ne_inner, "SW_EDGE_LINES": sw_lines,
            "WALL_THICKNESS_MM": 200, "THICKNESS_SOURCE": "outer/inner authored lines 200 apart; frozen DIM-01 '20'",
            "CAD_GEOMETRY_STATUS": "ESTABLISHED_FROM_DWG",
        },
        "PLAN_RUN_LENGTH": {"OUTER_FACE_M": round(outer["LENGTH_MM"] / 1000, 4),
                            "OUTER_FACE_WITH_SW_CORNER_ARC": outer_dev,
                            "ROOF_SIDE_FLOOR_LINE_M": (round(line400[0]["LENGTH_MM"] / 1000, 4) if line400 else None),
                            "FACE_BASIS": "authored face lines, not centreline, not bbox"},
        "PORTIONS_PROPOSED": {
            "SOLID_PORTION_NE": solid_portion, "LATTICE_KERB_PORTION_SW": lattice_portion,
            "SPLIT_EVIDENCE": "the authored line 250 mm inside the outer face runs only from the SW corner "
                              "for the kerb-zone length and stops; the frozen raster trace UNK-01 is the same "
                              "line ('heavier line ... ends with a small hook at y~790'); the B-B cut "
                              "(SEC-01, plan y=750) lands inside it and shows the hatched kerb + lattice",
            "CORRESPONDENCE_STATUS": "PROPOSED_CORRESPONDENCE",
            "WHY_NOT_ESTABLISHED": "no printed dimension or section names the split; the elevation "
                                   "proportion (lattice 44% of the run) and the plan line (50%) agree "
                                   "only to about 0.45 m",
        },
        "PRINTED_710_CHAIN_CHECK": chain_710,
        "DWG_ELEVATION_SAME_FAMILY": {
            "WINDOW": ELEV_WINDOW, "GROUND_Y_MM": ELEV_GROUND_Y,
            "LEVEL_CHAIN": chain,
            "PARAPET_ZONE_HORIZONTALS": zone, "AUTHORED_LEVELS_M": levels,
            "ORIENTATION_VS_FROZEN_RASTER": "MIRRORED (DWG: solid portion left, lattice centre, tower right; "
                                            "raster SE elevation: tower left, lattice, solid portion right)",
            "REVISION_RELATION": "SAME_DESIGN_FAMILY_DIFFERENT_ANNOTATION: the DWG prints 110 (+9.70 to "
                                 "+10.80) where the frozen raster prints 680 to +11.10 with a 20 band; "
                                 "the DWG elevation corroborates the drawn base line ~+9.88 and is used "
                                 "for corroboration only, never as the frozen contract height",
            "CORROBORATIONS": {"BASE_LINE_LEVEL_M": [l for l in levels if 9.8 < l < 9.95],
                               "LATTICE_TOP_M": [l for l in levels if 10.5 < l < 10.7]},
        },
        "STATUS": "ESTABLISHED_FROM_DWG for plan lengths; PROPOSED_CORRESPONDENCE for the elevation split",
    }
    p = OUT / "ROOF_EDGE_PLAN_TO_ELEVATION_LINK_REGISTER.json"
    p.write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
    out["_SHA256"] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


if __name__ == "__main__":
    r = run()
    print(json.dumps({"OUTER": r["PLAN_RUN_LENGTH"], "PORTIONS": r["PORTIONS_PROPOSED"]["SOLID_PORTION_NE"],
                      "LATTICE": {k: v for k, v in (r["PORTIONS_PROPOSED"]["LATTICE_KERB_PORTION_SW"] or {}).items() if k != "CORNER_ARC"},
                      "710": r["PRINTED_710_CHAIN_CHECK"], "LEVELS": r["DWG_ELEVATION_SAME_FAMILY"]["AUTHORED_LEVELS_M"],
                      "SHA": r["_SHA256"]}, indent=1, default=str))
