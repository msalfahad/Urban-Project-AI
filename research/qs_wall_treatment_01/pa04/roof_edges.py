"""PA04 workstream D - roof-edge geometry for SE / NE / NW / SW / ANNEX /
TOWER with the full field set.  Lengths from authored DWG lines and arcs
(developed length, never chord / bbox); heights from the frozen PA01-PA03
registers; the annex parapet run traced from the FF copy's annex-roof
region boundary.

    python3 -m research.qs_wall_treatment_01.pa04.roof_edges
"""

from __future__ import annotations

import math

import numpy as np

from engine import plan_regions as PR
from engine import self_checks as SC
from engine.parapet_assembly import developed_length
from research.qs_wall_treatment_01.pa04 import common as C

FIELDS = ("PLAN_RUN_LENGTH", "DEVELOPED_LENGTH", "EXTERNAL_FACE_HEIGHT", "INTERNAL_FACE_HEIGHT", "KERB", "COPING", "BALUSTRADE", "SOLID_UPSTAND", "CURVES", "OPENINGS", "SOURCE", "STATUS")


def _seg(pr, oid):
    for p in pr:
        if p[1] == oid:
            return p
    raise SystemExit(f"{oid} missing")


def _annex_run():
    """The annex roof (+4.30) region on the FF copy: its WALL-class boundary is the parapet / wall line around it."""
    dx = C.COPIES["FF"]
    box = (-163000 + dx, -806000, -126000 + dx, -789500)
    wall, door, meta = PR.rasterise(C.prims(), box, 50)
    seed = {"annex": (-199977.6, -802475.0)}        # inside the annex roof region (anchor from the FF region map, R2 54 m2)
    label, sl = PR.flood(wall, door, seed, meta, max_cells=3_000_000)
    lab = sl["annex"]
    faces = PR.merge_collinear(PR.boundary_faces(label, wall, door, lab, meta, min_run_cells=2))
    area = PR.region_area_m2(label, lab, 50)
    by, frag = {}, 0.0
    for f in faces:
        if f["LENGTH_M"] < 0.25:
            frag = round(frag + f["LENGTH_M"], 3)       # hatch-line stair-steps inside the roof region, not parapet run
            continue
        by[f["CLASS"]] = round(by.get(f["CLASS"], 0.0) + f["LENGTH_M"], 3)
    return {"REGION_AREA_M2": area, "BOUNDARY_LM_BY_CLASS": by, "FRAGMENTS_UNDER_0_25_M_LM": frag, "FACES": [f for f in faces if f["LENGTH_M"] >= 0.3]}


@C.timed("D_roof_edges")
def run():
    pr = C.prims()
    ref = C.read("ROOF_EDGES_FACADE_FINISH_KERB.json", C.OUT)
    asm = C.read("PARAPET_ASSEMBLY_REGISTER.json", C.OUT)
    ne_el = C.read("NE_ELEVATION_FINISH_ELIGIBILITY_REGISTER.json", C.OUT)["FACES"][0]
    d1 = C.read("D1_LEVEL_IDENTITY.json", C.OUT)
    edges = []
    def edge(eid, **f):
        missing = [k for k in FIELDS if k not in f]
        if missing:
            raise SystemExit(f"{eid} missing {missing}")
        edges.append(dict({"EDGE_ID": eid}, **f))
    # SE (frozen PA01/PA03 geometry)
    se_outer = _seg(pr, "CAD-4804"); se_len = round(C.seg_len(se_outer) / 1000, 3)
    kerb_arc = [p for p in pr if p[1] == "CAD-6565"][0]
    edge("SE", PLAN_RUN_LENGTH={"OUTER_M": se_len, "ROOF_SIDE_M": 7.100, "SOLID_PORTION_M": [3.683, 3.483], "KERB_LATTICE_PORTION_M": 3.767, "SOURCE": "CAD-4804 / CAD-4809 / CAD-4808 (PA01)"},
         DEVELOPED_LENGTH={"CORNER_ARC": developed_length([{"ID": "CAD-6565", "KIND": "ARC", "radius_mm": kerb_arc[9], "sweep_rad": (kerb_arc[11] - kerb_arc[10]) % (2 * math.pi)}]), "KERB_PROFILE_DEVELOPED_M": 3.473},
         EXTERNAL_FACE_HEIGHT={"SOLID": {"VISIBLE_FINISH_BASIS": 1.22, "EXECUTED_BASIS": 1.40, "TOP": 11.10, "STATE": "DUAL (D1 open)"}, "KERB": "profile developed 1.109 m2 ext (KP-SE-01)"},
         INTERNAL_FACE_HEIGHT={"SOLID": {"VISIBLE_FINISH_BASIS": 1.22, "EXECUTED_BASIS": 1.40}, "KERB_ROOFSIDE_M2": 1.787},
         KERB={"EXISTS": True, "PROFILE": "ogee, 6-vertex polyline lower bound (KP-SE-01)", "LENGTH_M": 3.767}, COPING={"EXISTS": True, "WIDTH_M": 0.20, "OVER": "solid portion only (F-SE-CAP-*)"},
         BALUSTRADE={"EXISTS": True, "KIND": "X-lattice over the kerb", "PLASTER": 0.0}, SOLID_UPSTAND={"EXISTS": True, "LENGTH_M": 3.683}, CURVES=["corner arc r 0.231 (CAD-6565)", "kerb ogee profile"],
         OPENINGS=[], SOURCE="DWG roof copy + SE elevation audit + PA01 assembly register", STATUS="ESTABLISHED lengths; heights dual basis (D1); split PROPOSED")
    ne_out = _seg(pr, "CAD-4735"); ne_in = _seg(pr, "CAD-4741")
    edge("NE", PLAN_RUN_LENGTH={"OUTER_M": round(C.seg_len(ne_out) / 1000, 3), "ROOF_SIDE_M": round(C.seg_len(ne_in) / 1000, 3), "SOURCE": "CAD-4735 / CAD-4741"},
         DEVELOPED_LENGTH={"STRAIGHT": True, "M": round(C.seg_len(ne_in) / 1000, 3)},
         EXTERNAL_FACE_HEIGHT={"VALUE": 1.40, "TOP_STATUS": ne_el["SOLID_FACE_TOP_STATUS"]["STATUS"], "STATE": "GEOMETRIC_REFERENCE_ONLY (finish unknown)"},
         INTERNAL_FACE_HEIGHT={"VALUE": 1.40, "BAND": ne_el["BAND_EXISTS_STATUS"]["STATUS"], "STATE": "PROVISIONAL"},
         KERB={"EXISTS": False}, COPING={"EXISTS": ne_el["BAND_EXISTS_STATUS"]["STATUS"], "HEIGHT": ne_el["BAND_HEIGHT_STATUS"], "ROLE": ne_el["BAND_TRADE_ROLE"]["STATUS"]},
         BALUSTRADE={"EXISTS": False}, SOLID_UPSTAND={"EXISTS": True, "LENGTH_M": round(C.seg_len(ne_in) / 1000, 3)}, CURVES=[], OPENINGS=[],
         SOURCE="DWG roof copy; A-A; NE elevation page 7", STATUS="lengths ESTABLISHED; face top PROVISIONAL; band NOT_ESTABLISHED")
    nw = next((e for e in ref["ROOF_EDGE_REGISTER"] if "NW" in str(e.get("EDGE_ID", e.get("EDGE", "")))), {})
    edge("NW_SEA_VIEW", PLAN_RUN_LENGTH={"M": round(abs(-798106 + 803894) / 1000, 3), "SOURCE": "lines x -220075 / -219975 (layers 2 / 5) y -803894..-798106"},
         DEVELOPED_LENGTH={"STRAIGHT": True, "M": 5.788, "NOTE": "the kerb curve is in the profile, not the plan"},
         EXTERNAL_FACE_HEIGHT={"LATTICE_M": 1.30, "KERB_M": 0.10, "SOURCE": "page 6 printed 100 + 10; B-B 130", "STATE": "PROVISIONAL"},
         INTERNAL_FACE_HEIGHT={"KERB_M": 0.10, "STATE": "PROVISIONAL"}, KERB={"EXISTS": True, "CURVED": True, "PROFILE": "NOT_ESTABLISHED"},
         COPING={"EXISTS": "cap on the lattice (B-B)", "PLASTER": 0.0}, BALUSTRADE={"EXISTS": True, "KIND": "open X-lattice", "PLASTER": 0.0, "BALUSTRADE_PLASTERABLE_SOLID_FACE_M2": 0.0},
         SOLID_UPSTAND={"EXISTS": False}, CURVES=["kerb profile (elevation)"], OPENINGS=[], SOURCE="DWG roof copy + page 6 + B-B", STATUS="lattice CONFIRMED (PA03); kerb profile NOT_ESTABLISHED")
    edge("SW", PLAN_RUN_LENGTH={"OUTER_M": 4.325, "ROOF_SIDE_M": 4.125, "SOURCE": "CAD-4776 / 4793 / 4805 (PA02)"}, DEVELOPED_LENGTH={"STRAIGHT": True, "M": 4.125},
         EXTERNAL_FACE_HEIGHT={"VALUE": "~1.53 above the slab (SEG-04 end-on, PROPOSED)", "STATE": "PROVISIONAL (owner item SW-PARAPET-HEIGHT-CONFIRM)"},
         INTERNAL_FACE_HEIGHT={"VALUE": "~1.53 (same basis)", "STATE": "PROVISIONAL"}, KERB={"EXISTS": "UNKNOWN"}, COPING={"EXISTS": "UNKNOWN (rounded top on SEG-04)"}, BALUSTRADE={"EXISTS": False},
         SOLID_UPSTAND={"EXISTS": True, "LENGTH_M": 4.125}, CURVES=["rounded top (SEG-04)"], OPENINGS=[], SOURCE="DWG roof copy; SE elevation end-on", STATUS="every geometric component finished except the height (owner confirmation)")
    ann = _annex_run()
    edge("ANNEX_4_30", PLAN_RUN_LENGTH={"WALL_BOUNDED_M": ann["BOUNDARY_LM_BY_CLASS"].get("WALL", 0.0), "OPEN_M": ann["BOUNDARY_LM_BY_CLASS"].get("OPEN", 0.0), "REGION_AREA_M2": ann["REGION_AREA_M2"],
                                        "SOURCE": "FF copy annex-roof region boundary (flood fill), faces >= 0.3 m listed", "FACES": ann["FACES"]},
         DEVELOPED_LENGTH={"M": ann["BOUNDARY_LM_BY_CLASS"].get("WALL", 0.0), "NOTE": "axis-aligned runs; the curved corner is stair-stepped on the 50 mm grid (PROVISIONAL developed length)"},
         EXTERNAL_FACE_HEIGHT={"VALUE": None, "STATE": "NOT_ESTABLISHED (no elevation cut of the annex parapet read)"}, INTERNAL_FACE_HEIGHT={"VALUE": None, "STATE": "NOT_ESTABLISHED"},
         KERB={"EXISTS": "UNKNOWN"}, COPING={"EXISTS": "UNKNOWN"}, BALUSTRADE={"EXISTS": "UNKNOWN"}, SOLID_UPSTAND={"EXISTS": "UNKNOWN (the boundary lines are the FF walls of the main block on three sides and the annex outer wall on the others)"},
         CURVES=["curved corner (FF copy)"], OPENINGS=[], SOURCE="DWG FF copy", STATUS="plan run ESTABLISHED (wall-bounded lm); heights NOT_ESTABLISHED")
    ring = 29.794
    edge("TOWER_13_90", PLAN_RUN_LENGTH={"EXTERIOR_RING_M": ring, "SOURCE": "ST7757 p6 +13.90 slab outline (PA01)"}, DEVELOPED_LENGTH={"M": ring, "NOTE": "polygon ring from the structural outline (curves as drawn)"},
         EXTERNAL_FACE_HEIGHT={"VALUE": 0.50, "BASIS": "+13.90 -> +14.40 (DWG NW elevation chain 420 + 50)", "STATE": "PROVISIONAL"}, INTERNAL_FACE_HEIGHT={"VALUE": 0.50, "STATE": "PROVISIONAL"},
         KERB={"EXISTS": False}, COPING={"EXISTS": "UNKNOWN"}, BALUSTRADE={"EXISTS": False}, SOLID_UPSTAND={"EXISTS": True, "LENGTH_M": ring}, CURVES=["ring corners per the structural outline"], OPENINGS=[],
         SOURCE="ST7757 p6 + DWG NW elevation", STATUS="ring PROVISIONAL / PROPOSED_CORRESPONDENCE; height PROVISIONAL")
    lines = [{"ID": e["EDGE_ID"], "SOURCE": e["SOURCE"], "SOURCE_ENTITY_IDS": [e["SOURCE"]]} for e in edges]
    checks = SC.run_all({"EDGES": edges}, lines)
    C.METRICS.setdefault("D_roof_edges", {}).update({"AI_CALLS": 0, "DETERMINISTIC_OPS": len(edges)})
    C.write("ROOF_EDGE_REGISTER_V2.json", {"ARTIFACT": "ROOF_EDGE_REGISTER_V2", "WORKSTREAM": "D", "EDGES": edges, "SYMMETRY_USED": False, "SELF_CHECKS": checks})
    return {"EDGES": [(e["EDGE_ID"], e["STATUS"]) for e in edges], "ANNEX": ann["BOUNDARY_LM_BY_CLASS"], "CHECKS": checks["FAILED"]}


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=1, default=str))
