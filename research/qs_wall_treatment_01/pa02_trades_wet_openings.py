"""PA02.4 - wall-treatment trade matrix over every face, wet rooms from the
E1.4 layer (lengths only), the project opening register, profile steel,
floor-by-floor output and the coverage matrix.

    python3 -m research.qs_wall_treatment_01.pa02_trades_wet_openings
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine import wall_treatment_matrix as WTM
from engine.opening_register import opening
from engine.quantity_state import totals_by_unit, weakest
from research.qs_wall_treatment_01 import protocol as P
from research.qs_wall_treatment_01.owner_parameters import p7757_registry

OUT = Path(P.OUT_DIR)
E14_CHAIN = "data/runs/7757/e1_4/E1_4_PHYSICAL_BOUNDARY_CHAIN_REGISTER.json"
E14_DOORS = "data/runs/7757/e1_4/E1_4_DOOR_ENTITY_REGISTER.json"
WET = ("BATH", "W.C", "KITCHEN", "PANTRY", "WASH", "LAUNDRY", "IRONING", "SHOWER")
FLOORS = ("GROUND", "FIRST", "SECOND_ROOF", "ANNEX")


def _v(reg, k):
    v = reg[k]
    return v["VALUE"] if isinstance(v, dict) else v


def run() -> dict:
    tr = json.loads((OUT / "PLASTER_QUANTITY_TRACE.json").read_text("utf-8"))
    stair = json.loads((OUT / "DOUBLE_HEIGHT_AND_STAIR_REGISTERS.json").read_text("utf-8"))
    cols = json.loads((OUT / "COLUMN_FACE_REGISTER.json").read_text("utf-8"))["COLUMNS"]
    ref = json.loads((OUT / "ROOF_EDGES_FACADE_FINISH_KERB.json").read_text("utf-8"))
    v4o = json.loads((OUT / "OPENING_REGISTER_v4.json").read_text("utf-8"))["OPENINGS"]
    d1 = json.loads((OUT / "D1_LEVEL_IDENTITY.json").read_text("utf-8"))
    reg = p7757_registry()
    h_norm = _v(reg, "NORMAL_INTERNAL_PLASTER_HEIGHT")
    # ---- trade matrix over faces --------------------------------------------------------
    matrix = []
    kind_by_cat = {"NORMAL_INTERNAL_WALL": "NORMAL_WALL_FACE", "SOLID_PARAPET": "PARAPET_FACE", "ROOF_SIDE_PARAPET": "PARAPET_FACE",
                   "COLUMN_BONDING": "EXPOSED_COLUMN_FACE", "EXTERNAL_FACADE": "EXTERNAL_FACE"}
    for l in tr["LINES"]:
        if l.get("UNIT") != "m2":
            continue
        kind = kind_by_cat.get(l["CATEGORY"], "NORMAL_WALL_FACE")
        matrix.append(dict(WTM.treatment_lines(face_id=l["LINE_ID"], physical_area_m2=l.get("VALUE"), area_state=l["QUANTITY_STATE"], face_kind=kind,
                                               finish_status=None), FLOOR=l["FLOOR"], CATEGORY=l["CATEGORY"]))
    for f in stair["STAIR_WELL_FACE_REGISTER"]["WALL_FACES"]:
        matrix.append(dict(WTM.treatment_lines(face_id=f["FACE_ID"], physical_area_m2=f["GROSS_AREA_M2"], area_state=f["QUANTITY_STATE"], face_kind="STAIR_WALL_FACE"),
                           FLOOR={"GF": "GROUND", "FF": "FIRST", "ROOF": "SECOND_ROOF"}[f["STOREY"]], CATEGORY="STAIR_WALL"))
    for fid, f in ref["SE_FACADE_FACES"].items():
        matrix.append(dict(WTM.treatment_lines(face_id=fid, physical_area_m2=f["NET_M2"], area_state="NOT_ESTABLISHED", face_kind="EXTERNAL_FACE", finish_status="UNKNOWN_EXTERNAL_FINISH"),
                           FLOOR="EXTERNAL", CATEGORY="EXTERNAL_FACADE", GEOMETRIC_REFERENCE_NET_M2=f["NET_M2"]))
    # column: bonding then plaster on ONE area (LOOP-059 GF)
    c = next(x for x in cols if x["COLUMN_ID"].startswith("LOOP-059"))
    col_area = round(c["EXPOSED_PLASTERABLE_GIRTH_LM"] * h_norm, 4)
    matrix.append(dict(WTM.treatment_lines(face_id="LOOP-059 exposed faces", physical_area_m2=col_area, area_state=weakest([c["GIRTH_STATE"], "OWNER_PROJECT_INPUT"]), face_kind="EXPOSED_COLUMN_FACE"),
                       FLOOR="GROUND", CATEGORY="COLUMN_BONDING", NOTE="already in the plaster trace as D2:COLUMN:LOOP-059; listed here for the sequence, not added"))
    # ---- wet rooms from the E1.4 chain layer (GF) -----------------------------------------
    ch = json.loads(Path(E14_CHAIN).read_text("utf-8"))
    wet = []
    for cnd in ch["CANDIDATES"]:
        ident = cnd["IDENTITY_AS_DRAWN"]
        if not any(w in ident.upper() for w in WET):
            continue
        chain = cnd["CHAIN"]
        mat = round(chain["material_length_mm"] / 1000, 3)
        open_len = round(chain["length_with_no_material_mm"] / 1000, 3)
        closed = chain["CLOSED_BY_DRAWN_MATERIAL"]
        n_el = len(chain["CHAIN"])
        suspicious = mat > 20 or n_el > 40
        wet.append({"ROOM_ID": cnd["CANDIDATE_ID"], "IDENTITY_AS_DRAWN": ident, "FLOOR": "GROUND", "SEED_MM": cnd.get("SEED_MM"),
                    "ESTABLISHED_WALL_LENGTH_LM": mat, "OPEN_EDGE_LENGTH_LM": open_len, "CLOSED_BY_DRAWN_MATERIAL": closed, "CHAIN_ELEMENTS": n_el,
                    "LENGTH_STATE": "PROVISIONAL" if not suspicious else "NOT_ESTABLISHED",
                    "WHY": ("E1.4 physical boundary chain (separate evidence layer): material faces only; open edges contribute zero"
                            if not suspicious else "chain length or element count implausible for one room (merged region): not carried"),
                    "TREATMENT": "TILE_WALL_PREPARATION", "TREATMENT_HEIGHT_M": None, "TREATMENT_HEIGHT_STATE": "NOT_ESTABLISHED (wet-room treatment height not established; 3.20 not applied)",
                    "AREA_M2": None, "AREA_STATE": "NOT_ESTABLISHED", "UNIT_FOR_LENGTH": "lm"})
    wet_lm = round(sum(w["ESTABLISHED_WALL_LENGTH_LM"] for w in wet if w["LENGTH_STATE"] == "PROVISIONAL"), 3)
    # ---- project opening register --------------------------------------------------------
    ops = []
    for o in v4o:
        o = dict(o)
        o.update({"FLOOR": "GROUND", "HOST_ZONE": "SALOON", "SHAPE": "RECT", "ACTUAL_OR_DEFAULT": ("DEFAULT" if o["WIDTH_SOURCE"] == "PROVISIONAL_DEFAULT" or o["HEIGHT_SOURCE"] == "PROVISIONAL_DEFAULT" else "ACTUAL"),
                  "PROFILE_LM": {"JAMB": (round(2 * o["HEIGHT"], 3) if o["HEIGHT"] else None), "HEAD": o["WIDTH"], "SILL": (o["WIDTH"] if o["TYPE"] == "WINDOW" else None)}})
        ops.append(o)
    for o in ref["SE_FACADE_OPENING_REGISTER"]:
        o = dict(o)
        o.update({"FLOOR": "EXTERNAL_SE", "HOST_ZONE": o["HOST_FACE"],
                  "PROFILE_LM": {"JAMB": round(2 * (o["HEIGHT"] if o["SHAPE"] == "RECT" else o["ARCH"]["TOTAL_HEIGHT_M"]), 3), "HEAD": o["WIDTH"], "SILL": (o["WIDTH"] if o["TYPE"] == "WINDOW" else None)}})
        ops.append(o)
    doors = json.loads(Path(E14_DOORS).read_text("utf-8"))
    m = {a["door_id"]: a for a in doors["HOST_WALL_MATCH_ATTEMPTS"]}
    seen = set()
    for dd in doors["DOORS"]:
        if dd["length_mm"] < 600:
            continue
        key = (round(dd["length_mm"]), round(dd["at_mm"][0] / 100), round(dd["at_mm"][1] / 100))
        if key in seen:
            continue
        seen.add(key)
        a = m.get(dd["door_id"], {})
        w = round(dd["length_mm"] / 1000, 3)
        o = opening(opening_id=f"E14:{dd['door_id']}", host_face=("MATCHED_HOST" if a.get("MATCHED") else None), opening_type="DOOR", width_m=w,
                    width_source="PROVISIONAL", height_m=_v(reg, "DOOR_HEIGHT"), height_source="PROVISIONAL_DEFAULT", deduction_rule="FULL_OPENING_DEDUCTION",
                    reveal_depth_m=None, reveal_depth_source="NOT_ESTABLISHED")
        o.update({"FLOOR": "GROUND", "HOST_ZONE": "GF (E1.4 door leaf at %s)" % [round(v) for v in dd["at_mm"]], "SHAPE": "RECT", "ACTUAL_OR_DEFAULT": "WIDTH_ACTUAL_LEAF / HEIGHT_DEFAULT",
                  "E14_HOST_MATCH": a.get("MATCHED"), "E14_REJECTION": a.get("REJECTED_BECAUSE"),
                  "NOTE": "width = authored door-leaf line length (E1.4 door entity); leaf length approximates the clear opening width; PROVISIONAL",
                  "PROFILE_LM": {"JAMB": round(2 * _v(reg, "DOOR_HEIGHT"), 3), "HEAD": w, "SILL": None}})
        ops.append(o)
    # ---- profile steel -----------------------------------------------------------------------
    prof = {"DOOR_JAMB_PROFILE": 0.0, "DOOR_HEAD_PROFILE": 0.0, "WINDOW_JAMB_PROFILE": 0.0, "WINDOW_HEAD_PROFILE": 0.0, "WINDOW_SILL_PROFILE": 0.0,
            "EXTERNAL_CORNER_PROFILE": 0.0, "COLUMN_CORNER_PROFILE": 0.0, "OTHER_EDGE_PROFILE": 0.0}
    prof_state = {k: [] for k in prof}
    for o in ops:
        if not o.get("WIDTH") or not o.get("HEIGHT"):
            continue
        st = o["STATUS"]
        pl = o["PROFILE_LM"]
        if o["TYPE"] == "DOOR":
            prof["DOOR_JAMB_PROFILE"] += pl["JAMB"]; prof["DOOR_HEAD_PROFILE"] += pl["HEAD"]; prof_state["DOOR_JAMB_PROFILE"].append(st); prof_state["DOOR_HEAD_PROFILE"].append(st)
        elif o["TYPE"] == "WINDOW":
            prof["WINDOW_JAMB_PROFILE"] += pl["JAMB"]; prof["WINDOW_HEAD_PROFILE"] += pl["HEAD"]; prof["WINDOW_SILL_PROFILE"] += pl["SILL"] or 0
            for k in ("WINDOW_JAMB_PROFILE", "WINDOW_HEAD_PROFILE", "WINDOW_SILL_PROFILE"):
                prof_state[k].append(st)
    prof["COLUMN_CORNER_PROFILE"] = round(4 * h_norm, 3)
    prof_state["COLUMN_CORNER_PROFILE"].append(weakest([c["GIRTH_STATE"], "OWNER_PROJECT_INPUT"]))
    prof_lines = [{"PROFILE": k, "UNIT": "lm", "VALUE": (round(v, 3) if v else None),
                   "QUANTITY_STATE": (weakest(prof_state[k]) if prof_state[k] else "NOT_ESTABLISHED"),
                   "NOTE": ("external corners: parapet / facade corner lengths not compiled" if k == "EXTERNAL_CORNER_PROFILE" else
                            "LOOP-059: 4 corners x 3.20 (owner height)" if k == "COLUMN_CORNER_PROFILE" else None)} for k, v in prof.items()]
    # ---- floor-by-floor ----------------------------------------------------------------------
    def cat_total(lines, cat, floor=None):
        sel = [l for l in lines if l["CATEGORY"] == cat and (floor is None or l["FLOOR"] == floor)]
        return totals_by_unit(sel)
    fbf = {}
    L = tr["LINES"]
    stair_faces = stair["STAIR_WELL_FACE_REGISTER"]["WALL_FACES"]
    for fl, key in (("GROUND", "GROUND"), ("FIRST", "FIRST"), ("SECOND_ROOF", "ROOF"), ("ANNEX", "ANNEX")):
        st_lines = [{"UNIT": "m2", "VALUE": f["GROSS_AREA_M2"], "QUANTITY_STATE": f["QUANTITY_STATE"]} for f in stair_faces
                    if {"GF": "GROUND", "FF": "FIRST", "ROOF": "SECOND_ROOF"}[f["STOREY"]] == fl]
        fbf[fl] = {
            "NORMAL_INTERNAL_PLASTER_M2": cat_total(L, "NORMAL_INTERNAL_WALL", key),
            "TILE_PREP_M2": {"m2": {}, "NOTE": (f"wet-room wall length {wet_lm} lm PROVISIONAL (GF, E1.4 layer); area NOT_ESTABLISHED" if fl == "GROUND" else "not started")},
            "COLUMN_BONDING_M2": cat_total(L, "COLUMN_BONDING", key),
            "STAIR_WALL_M2": totals_by_unit(st_lines),
            "STAIR_UNDERSIDE_M2": {"m2": {}, "NOTE": "NOT_ESTABLISHED"},
            "EXTERNAL_GEOMETRIC_FACE_M2": ({"GEOMETRIC_REFERENCE_ONLY": round(sum(v["NET_M2"] for v in ref["SE_FACADE_FACES"].values() if v["NET_M2"]), 3)} if fl == "GROUND" else {}),
            "EXTERNAL_PLASTER_M2": {"m2": {}, "NOTE": "NOT_ESTABLISHED (finish system unknown)"},
            "PARAPET_EXTERNAL_M2": cat_total(L, "SOLID_PARAPET", key),
            "PARAPET_INTERNAL_M2": cat_total(L, "ROOF_SIDE_PARAPET", key),
            "REVEALS_M2": {"m2": {"PROVISIONAL_QUANTITY": round(sum(o["REVEAL_AREA"] for o in ops if o.get("REVEAL_AREA") and o.get("FLOOR") == fl), 3)}} if fl == "GROUND" else {},
            "PROFILE_LM": {"NOTE": "see PROFILE_STEEL_REGISTER (not split by floor yet)"},
            "UNRESOLVED_COMPONENTS": [u for u in tr["UNRESOLVED_SCOPE"] if fl == "GROUND" or u.get("CATEGORY") in ("SOLID_PARAPET", "ROOF_SIDE_PARAPET")][:12],
            "NOT_A_TOTAL": True,
        }
    # ---- coverage matrix ---------------------------------------------------------------------
    cov = []
    def row(floor, zone, trade, expected, est, prov, unres, notstarted):
        status = "NOT_STARTED" if notstarted and not (est or prov) else "PARTIAL" if (est or prov) else "UNRESOLVED"
        cov.append({"FLOOR": floor, "ZONE": zone, "TRADE": trade, "EXPECTED_COMPONENTS": expected, "ESTABLISHED_COMPONENTS": est,
                    "PROVISIONAL_COMPONENTS": prov, "UNRESOLVED_COMPONENTS": unres, "NOT_STARTED_COMPONENTS": notstarted, "COVERAGE_STATUS": status})
    row("GROUND", "SALOON", "NORMAL_INTERNAL_PLASTER", "all wall faces of the SALOON", ["SEG-02 5.15", "SEG-03 2.00"], ["SEG-05", "SEG-01 block portions"], ["SEG-04", "SEG-06"], ["faces not traced"])
    row("GROUND", "SALOON/RECEPTION edge", "COLUMN_BONDING", "LOOP-059 + piers", [], ["LOOP-059 1.80 lm", "COL-01 0.30", "COL-02 0.20"], ["girth 1.80 vs 1.70"], [])
    row("GROUND", "RECEPTION", "NORMAL_INTERNAL_PLASTER", "perimeter walls (normal height; the void is a stair well)", [], [], [], ["perimeter faces not traced"])
    row("GROUND", "wet rooms (E1.4 layer)", "TILE_WALL_PREPARATION", f"{len(wet)} rooms", [], [f"{wet_lm} lm wall length"], ["treatment height"], ["FF wet rooms"])
    row("GROUND+FIRST+ROOF", "block stair", "STAIR_WALL_PLASTER", "4 faces x 3 storeys", [], [f"{sum(stair['STAIR_WALL_GROSS_SUBTOTAL_BY_STOREY_M2'].values()):.1f} m2 gross"], ["spine wall role", "landing interruptions", "underside"], [])
    row("FIRST", "all rooms", "NORMAL_INTERNAL_PLASTER", "FF walls", [], [], [], ["not traced"])
    row("EXTERNAL", "SE facade", "EXTERNAL_PLASTER", "tower, main block, annex faces", [], [], ["finish system"], ["annex width"])
    row("EXTERNAL", "NE / NW facades", "EXTERNAL_PLASTER", "faces and openings", [], [], [], ["not traced"])
    row("ROOF", "SE / NE / tower edges", "PARAPET_PLASTER", "faces", [], ["SE solid", "kerb", "NE roof-side", "tower ring"], ["NE external eligibility", "SW height (end-on)", "NW kerb"], ["annex parapet run"])
    row("ROOF", "roof rooms (maid)", "NORMAL_INTERNAL_PLASTER", "maid block rooms", [], [], [], ["not traced"])
    out = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "TRADES_WET_OPENINGS_FLOORS_COVERAGE",
           "WALL_TREATMENT_MATRIX": matrix, "WET_ROOM_REGISTER": {"ROOMS": wet, "GF_WALL_LENGTH_LM_PROVISIONAL": wet_lm, "AREA_M2": None,
                                                                  "RULE": "physical host walls only; open edges zero; TILE_WALL_PREPARATION separate from plaster; 3.20 not applied"},
           "PROJECT_OPENING_REGISTER": ops, "PROFILE_STEEL_REGISTER": prof_lines, "FLOOR_BY_FLOOR": fbf, "COVERAGE_MATRIX": cov,
           "A_SUBTOTAL_IS_NOT_A_PROJECT_TOTAL": True}
    p = OUT / "TRADES_WET_OPENINGS_FLOORS_COVERAGE.json"
    p.write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
    return {"MATRIX": len(matrix), "WET": [(w["IDENTITY_AS_DRAWN"], w["ESTABLISHED_WALL_LENGTH_LM"], w["LENGTH_STATE"]) for w in wet], "WET_LM": wet_lm,
            "OPENINGS": len(ops), "PROFILES": [(x["PROFILE"], x["VALUE"], x["QUANTITY_STATE"]) for x in prof_lines],
            "FLOORS": {k: {kk: vv for kk, vv in v.items() if kk in ("NORMAL_INTERNAL_PLASTER_M2", "COLUMN_BONDING_M2", "STAIR_WALL_M2", "PARAPET_EXTERNAL_M2", "PARAPET_INTERNAL_M2", "REVEALS_M2")} for k, v in fbf.items()},
            "COVERAGE": [(c["ZONE"], c["TRADE"], c["COVERAGE_STATUS"]) for c in cov], "SHA": hashlib.sha256(p.read_bytes()).hexdigest()[:16]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
