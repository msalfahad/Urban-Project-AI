"""PA04 workstream E - stair geometry v3 for the MAIN CURVED STAIR and the
BLOCK / SERVICE STAIR from the DWG plan copies, the level chains and A-A.
Components are separate objects: TREAD, RISER, LANDING, SOFFIT, STAIR WALL,
OPEN WELL, CENTRAL 10 cm ELEMENT, RAILING, SLAB EDGE, BEAM, COLUMN.  Stair
plaster is face by face only; no perimeter x height.

    python3 -m research.qs_wall_treatment_01.pa04.stairs_v3
"""

from __future__ import annotations

import math

from engine import self_checks as SC
from engine import source_review as SR
from engine.parapet_assembly import developed_length
from research.qs_wall_treatment_01.pa04 import common as C


def _arcs_at(pr, cx, cy, tol=5):
    return sorted([p for p in pr if p[0] == "ARC" and abs(p[7] - cx) < tol and abs(p[8] - cy) < tol], key=lambda p: p[9])


def _radials(pr, cx, cy, rmin, rmax, tol_deg=1.5):
    """Tread nosing lines of the curved flight: segments whose extension passes through the centre."""
    out = []
    for p in pr:
        if p[0] != "SEGMENT" or p[2] not in ("5", "2"):
            continue
        d1 = math.hypot(p[3] - cx, p[4] - cy); d2 = math.hypot(p[5] - cx, p[6] - cy)
        if not (rmin - 60 <= min(d1, d2) <= rmax + 60 and rmin - 60 <= max(d1, d2) <= rmax + 60):
            continue
        a1 = math.atan2(p[4] - cy, p[3] - cx); a2 = math.atan2(p[6] - cy, p[5] - cx)
        if abs(math.degrees(a1 - a2)) < tol_deg:
            out.append((p[1], p[2], round(math.degrees(a1), 2), round(min(d1, d2)), round(max(d1, d2))))
    return sorted(out, key=lambda t: t[2])


@C.timed("E_stairs_v3")
def run():
    pr = C.prims()
    st2 = C.read("STAIR_COMPONENT_REGISTER_V2.json", C.OUT)
    void = C.read("VOID_GEOMETRY_RECONCILIATION.json", C.OUT)["OBJECTS_PRESERVED"]
    stx = C.read("pa04/STRUCTURAL_EXPOSURE_REGISTER.json", C.OUT) if (C.OUT / "pa04/STRUCTURAL_EXPOSURE_REGISTER.json").exists() else None
    # ---------------- main curved stair (GF copy centre) ----------------
    cx, cy = -138454.2, -800863.5
    arcs = _arcs_at(pr, cx, cy)
    r_in, r_out = arcs[0][9], arcs[-1][9]
    rad = _radials(pr, cx, cy, r_in, r_out)
    # distinct nosing angles on layer 5 (layer 2 = the 50 mm offset copies)
    nos = sorted({t[2] for t in rad if t[1] == "5"})
    sweep_in = (arcs[0][11] - arcs[0][10]) % (2 * math.pi)
    curved_treads = max(len(nos) - 1, 0)
    straight = void["STRAIGHT_FLIGHT_STRIP"]
    east_run = next(c for c in st2["STAIRS"][0]["COMPONENTS"] if c["COMPONENT"] == "SHORT_RUN_EAST_STRIP")
    treads_total = curved_treads + straight["TREADS"] + east_run["TREADS"]
    rise = C.LEVELS["FF_SLAB"] - C.LEVELS["GF_FFL"]
    risers = treads_total + 1
    riser_h = round(rise / risers, 4) if risers else None
    # flight footprint areas (plan) and soffit (inclined) estimates
    sector = round(0.5 * sweep_in * ((r_out / 1000) ** 2 - (r_in / 1000) ** 2), 3)
    straight_plan = round(straight["WIDTH_M"] * straight["DEPTH_M"], 3)
    east_plan = round(east_run["TREADS"] * 0.30 * east_run["STRIP_WIDTH_M"], 3)
    def soffit(plan_area, treads, going=0.30):
        if riser_h is None or treads == 0:
            return None
        return round(plan_area * math.hypot(going, riser_h) / going, 3)
    main = {"STAIR_ID": "MAIN-CURVED", "RISE_M": rise, "RISE_SOURCE": "levels +1.00 / +5.50 (established)",
            "COMPONENTS": {
                "TREAD": {"CURVED_FLIGHT": {"NOSING_LINES_LAYER_5": len(nos), "TREADS": curved_treads, "R_IN_MM": round(r_in, 1), "R_OUT_MM": round(r_out, 1), "SWEEP_RAD": round(sweep_in, 4),
                                            "GOING_AT_WALKING_LINE_M": round((r_in + 600) / 1000 * sweep_in / curved_treads, 3) if curved_treads else None, "PLAN_AREA_M2": sector,
                                            "SOURCE": "arcs " + ", ".join(a[1] for a in arcs) + " + radial nosing lines", "STATUS": "ESTABLISHED_FROM_DWG (count), walking line 0.60 from the inner string PROVISIONAL"},
                          "STRAIGHT_FLIGHT_NE": {"TREADS": straight["TREADS"], "GOING_M": 0.30, "WIDTH_M": straight["DEPTH_M"], "PLAN_AREA_M2": straight_plan, "SOURCE": straight["BASIS"], "STATUS": "ESTABLISHED_FROM_DWG"},
                          "EAST_RUN": {"TREADS": east_run["TREADS"], "GOING_M": 0.30, "WIDTH_M": east_run["STRIP_WIDTH_M"], "PLAN_AREA_M2": east_plan, "STATUS": east_run["STATUS"]},
                          "TOTAL_TREADS": treads_total},
                "RISER": {"COUNT": risers, "HEIGHT_M": riser_h, "BASIS": "rise 4.50 / (treads + 1) - assumes every tread is a step and no intermediate landing; PROVISIONAL", "STATUS": "PROVISIONAL"},
                "LANDING": {"COUNT": "0 identified inside the opening (the FF gallery is the arrival); a quarter-landing between the straight flight and the east run is NOT drawn as a landing", "STATUS": "PROVISIONAL"},
                "SOFFIT": {"CURVED_M2": soffit(sector, curved_treads, (r_in + 600) / 1000 * sweep_in / max(curved_treads, 1)), "STRAIGHT_M2": soffit(straight_plan, straight["TREADS"]), "EAST_RUN_M2": soffit(east_plan, east_run["TREADS"]),
                           "BASIS": "plan footprint x slope factor from the riser height (no stair detail in the set)", "STATUS": "PROVISIONAL", "QUANTITY_STATE": "PROVISIONAL_QUANTITY"},
                "STAIR_WALL": {"FACES": ["RVF-S-B (NE wall behind the straight flight, candidate double height, NOT_ESTABLISHED)", "RVF-W-FF (FF wall over the curved flight, bottom NOT_ESTABLISHED)"], "PERIMETER_X_HEIGHT_USED": False},
                "OPEN_WELL": {"SLAB_OPENING_M2": void["SLAB_OPENING"]["AREA_M2"], "OPEN_TO_FF_CEILING_M2_PROVISIONAL": round(void["SLAB_OPENING"]["AREA_M2"] - sector, 3)},
                "CENTRAL_10CM_ELEMENT": None,
                "RAILING": {"ENTITIES": st2["STAIRS"][0]["COMPONENTS"][3]["ENTITIES"], "OUTER_STRING_DEVELOPED": st2["STAIRS"][0]["COMPONENTS"][0]["OUTER_STRING_DEVELOPED"], "PLASTER": 0.0},
                "SLAB_EDGE": {"NORTH_M": 5.87, "EAST_M": 2.85, "BEAMS": "CB6 (north) 20 x 75, CB5 (east strip) 20 x 40 - see STRUCTURAL_EXPOSURE_REGISTER", "STATUS": "PROVISIONAL"},
                "BEAM": {"FLIGHT_BEAM": "B27 90 x 85 inclined across the B5 panel (structural p4; LOW confidence correspondence)"},
                "COLUMN": {"ON_THE_NE_WALL_LINE": ["800 x 250 loop at x -138220..-137420", "LOOP-059 600 x 250 (D2)"]}}}
    # ---------------- block / service stair (ROOF copy cell holds the authored dims) ----------------
    blk = st2["STAIRS"][1]
    el = blk["MID_ELEMENT"]
    st_lines = [p for p in pr if p[0] == "SEGMENT" and p[2] == "ST" and -236000 < p[3] < -229000 and -799000 < p[4] < -791000]
    treads_per_flight = round(3.30 / 0.30)
    flights = 2
    storeys = {"GF": (0.30, 5.50), "FF": (5.50, 9.70), "ROOF": (9.70, 13.90)}
    blk_comp = {}
    for s, (b, t) in storeys.items():
        r = round(t - b, 2)
        n_r = 2 * (treads_per_flight + 1)
        blk_comp[s] = {"RISE_M": r, "FLIGHTS": flights, "TREADS_PER_FLIGHT": treads_per_flight, "RISERS": n_r, "RISER_HEIGHT_M": round(r / n_r, 4),
                       "FLIGHT_PLAN_M2": round(2 * 3.30 * 1.20, 3), "LANDINGS_M2": round(1.20 * 2.50 + 1.95 * 2.50, 3),
                       "SOFFIT_M2_PROVISIONAL": round(2 * 3.30 * 1.20 * math.hypot(0.30, r / n_r) / 0.30, 3), "BASIS": "DWG dims 120 / 330 / 195 and 120 + 10 + 120; two flights per storey (A-A); going 0.30 assumed from 330 / 11", "STATUS": "PROVISIONAL"}
    element = SR.stair_element(element_id=el["ELEMENT_ID"], printed_thickness_cm=10, length_m=el["LENGTH_M"], role="UNRESOLVED", role_evidence=el["ROLE_EVIDENCE"], excluded_roles=el["EXCLUDED_ROLES"])
    element["GEOMETRY_ESTABLISHED"] = {"THICKNESS_M": 0.10, "LENGTH_M": el["LENGTH_M"], "HEIGHT_M": None, "SOURCE": "DWG lines " + ", ".join(l["ID"] for l in el["DWG_LINES"])}
    element["STRUCTURAL_EVIDENCE"] = "ST7757 p4 / p5 stair cell B3 (With Stair): no spine wall or beam drawn between the flights (visual read, PROVISIONAL)"
    element["PLASTER_ELIGIBILITY"] = "UNKNOWN (geometry established; semantic role not forced)"
    block = {"STAIR_ID": "BLOCK-SERVICE", "WELL": blk["WELL_PRINTED"], "PER_STOREY": blk_comp, "CENTRAL_10CM_ELEMENT": element,
             "STAIR_WALL": {"FACES": [{"FACE_ID": f["FACE_ID"], "LENGTH_M": f["LENGTH_M"], "HEIGHT_M": f["HEIGHT_M"], "REFERENCE_GROSS_M2": f["REFERENCE_GROSS_M2"], "EXPOSURE": f["EXPOSURE"], "OPENINGS": f["OPENINGS"],
                                       "LANDING_INTERRUPTION": f["SLAB_LANDING_INTERRUPTION"], "FLIGHT_OCCLUSION": f["STAIR_FLIGHT_OCCLUSION"], "QUANTITY_STATE": "GEOMETRIC_REFERENCE_ONLY",
                                       "NET_PLASTER_M2": None, "WHY_NO_NET": "landing and flight geometry per face not yet subtracted; no stair detail in the set"} for f in blk["FACES"]],
                            "PERIMETER_X_HEIGHT_USED": False},
             "OPEN_WELL": {"WIDTH_M": 0.10, "NOTE": "the 10 cm element occupies the gap between the flights; no open well beyond it"},
             "RAILING": {"NOTE": "handrails on both flights (A-A)", "PLASTER": 0.0}, "ST_LAYER_LINES": len(st_lines)}
    lines = [{"ID": "MAIN-CURVED", "SOURCE": "DWG GF/FF copies + levels", "SOURCE_ENTITY_IDS": [a[1] for a in arcs]},
             {"ID": "BLOCK-SERVICE", "SOURCE": "DWG ROOF copy dims + A-A", "SOURCE_ENTITY_IDS": [l["ID"] for l in el["DWG_LINES"]]}]
    checks = SC.run_all({"MAIN": main, "BLOCK": block}, lines)
    C.METRICS.setdefault("E_stairs_v3", {}).update({"AI_CALLS": 0, "DETERMINISTIC_OPS": 2 + len(storeys)})
    C.write("STAIR_GEOMETRY_V3.json", {"ARTIFACT": "STAIR_GEOMETRY_V3", "WORKSTREAM": "E", "STAIRS": [main, block], "RULES": ["face-by-face plaster only", "no generic stairwell perimeter x height", "the 10 cm element's role is not forced"],
                                       "SELF_CHECKS": checks})
    return {"MAIN_TREADS": treads_total, "RISER_H": riser_h, "CURVED_TREADS": curved_treads, "SOFFIT": main["COMPONENTS"]["SOFFIT"], "BLOCK_GF": blk_comp["GF"], "CHECKS": checks["FAILED"]}


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=1, default=str))
