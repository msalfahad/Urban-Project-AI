"""PA04 §6 OPENING_REGISTER_V2 (all door / window / opening records
unified) and §7 PROFILE_STEEL_REGISTER_V2.  Actual source values override
defaults; defaults never overwrite actual values.  Door leaf widths are
read from the DWG door-swing arcs (radius = leaf width) on each plan copy.

    python3 -m research.qs_wall_treatment_01.pa04.openings_v2
"""

from __future__ import annotations

import math

from engine import self_checks as SC
from research.qs_wall_treatment_01.pa04 import common as C

OWNER_TEMP_DEFAULTS = {"DOOR": (1.00, 2.20), "WINDOW": (1.50, 1.50)}
FIELDS = ("OPENING_ID", "FLOOR", "HOST_FACE", "TYPE", "SHAPE", "WIDTH", "HEIGHT", "ARCH_RADIUS_OR_CURVE", "AREA", "SOURCE", "ACTUAL_OR_DEFAULT",
          "DOOR_OR_WINDOW_SCHEDULE_STATUS", "REVEAL_DEPTH", "REVEAL_AREA", "PROFILE_REQUIREMENT", "STATUS")


def _door_arcs(copy):
    dx = C.COPIES[copy]
    out = []
    for p in C.prims():
        if p[0] == "ARC" and p[2] == "D" and 600 <= p[9] <= 1300 and (-163000 + dx) <= p[7] <= (-126000 + dx) and -806500 <= p[8] <= -789000:
            sweep = (p[11] - p[10]) % (2 * math.pi)
            if 1.2 <= sweep <= 1.9:        # quarter-circle door swing
                out.append({"ID": p[1], "CX": round(p[7], 1), "CY": round(p[8], 1), "LEAF_W_M": round(p[9] / 1000, 3)})
    return out


def rec(**k):
    missing = [f for f in FIELDS if f not in k]
    if missing:
        raise SystemExit(f"opening missing {missing}")
    w, h = k["WIDTH"], k["HEIGHT"]
    if k["AREA"] is None and isinstance(w, (int, float)) and isinstance(h, (int, float)):
        k["AREA"] = round(w * h, 4)
    if k["ACTUAL_OR_DEFAULT"] == "ACTUAL":
        k["DEFAULT_MAY_OVERWRITE"] = False
    if k.get("REVEAL_AREA") is None and isinstance(w, (int, float)) and isinstance(h, (int, float)) and isinstance(k.get("REVEAL_DEPTH"), (int, float)):
        k["REVEAL_AREA"] = round((2 * h + w) * k["REVEAL_DEPTH"], 4)
        k["REVEAL_LENGTH"] = round(2 * h + w, 3)
    return k


@C.timed("openings_profiles_v2")
def run():
    tw = C.read("TRADES_WET_OPENINGS_FLOORS_COVERAGE.json", C.OUT)
    se = C.read("SE_OPENING_DIMENSION_OWNERSHIP_AUDIT.json", C.OUT)
    nw = C.read("pa04/FACADE_OPENINGS_NE_NW_PRIMARY.json", C.OUT)
    old = tw["PROJECT_OPENING_REGISTER"]
    R = []
    # 1. carried PA02 project openings (GF traces + defaults), unchanged values
    se_ids = {o["OPENING_ID"] for o in se["OPENINGS"]}
    for o in old:
        if o["OPENING_ID"] in se_ids:
            continue            # superseded by the PA03 ownership audit record below
        R.append(rec(OPENING_ID=o["OPENING_ID"], FLOOR=o.get("FLOOR"), HOST_FACE=o.get("HOST_FACE") or o.get("HOST_ZONE"), TYPE=o["TYPE"], SHAPE=o.get("SHAPE", "RECT"), WIDTH=o.get("WIDTH"), HEIGHT=o.get("HEIGHT"),
                     ARCH_RADIUS_OR_CURVE=None, AREA=o.get("AREA"), SOURCE=o.get("SOURCE"), ACTUAL_OR_DEFAULT={"ACTUAL": "ACTUAL", "ACTUAL_DRAWING": "ACTUAL"}.get(o.get("ACTUAL_OR_DEFAULT"), o.get("ACTUAL_OR_DEFAULT") or "TEMP_DEFAULT"),
                     DOOR_OR_WINDOW_SCHEDULE_STATUS="SOURCE_NOT_PROVIDED (no door / window schedule in the set)", REVEAL_DEPTH=o.get("REVEAL_DEPTH"), REVEAL_AREA=o.get("REVEAL_AREA"),
                     PROFILE_REQUIREMENT="jambs + head (door) / jambs + head + sill (window)", STATUS=o.get("STATUS"), CARRIED_FROM="PA02 PROJECT_OPENING_REGISTER"))
    # 2. SE facade openings with the PA03 ownership audit
    for o in se["OPENINGS"]:
        arch = o["ARCH_GEOMETRY"]
        R.append(rec(OPENING_ID=o["OPENING_ID"], FLOOR="SE facade", HOST_FACE=o["HOST_FACE"], TYPE="WINDOW" if "W" in o["OPENING_ID"].split("-")[-1] else "DOOR", SHAPE="RECT+SEMICIRCLE" if arch else "RECT",
                     WIDTH=o["CLEAR_WIDTH"], HEIGHT=o["TOTAL_HEIGHT"], ARCH_RADIUS_OR_CURVE=arch, AREA=o["TOTAL_AREA"], SOURCE="native page 4 printed dimensions (ownership audit PA03): " + ", ".join(o["SOURCE_DIMENSIONS"]),
                     ACTUAL_OR_DEFAULT="ACTUAL", DOOR_OR_WINDOW_SCHEDULE_STATUS="SOURCE_NOT_PROVIDED", REVEAL_DEPTH=0.20, REVEAL_AREA=None, PROFILE_REQUIREMENT="external reveal profile (finish unknown)",
                     STATUS=o["STATUS"], CARRIED_FROM="PA03 SE_OPENING_DIMENSION_OWNERSHIP_AUDIT"))
    # 3. NW facade openings (DWG authored dims, primary; cold challenge merged in challenges.py)
    for o in nw["NW_OPENINGS"]:
        R.append(rec(OPENING_ID=o["OPENING_ID"], FLOOR=o["STOREY"], HOST_FACE="F-NW-" + ("TOWER" if "TW" in o["OPENING_ID"] or "GRILLE" in o["OPENING_ID"] else "MAIN"), TYPE=o["TYPE"], SHAPE=o["SHAPE"], WIDTH=o["WIDTH_M"], HEIGHT=o["HEIGHT_M"],
                     ARCH_RADIUS_OR_CURVE=o["ARCH"], AREA=o["AREA_M2"], SOURCE=o["SOURCE"] + " - " + o["DIMENSION_OWNER"], ACTUAL_OR_DEFAULT="ACTUAL" if o["CONFIDENCE"] != "LOW" else "ACTUAL (scaled part PROVISIONAL)",
                     DOOR_OR_WINDOW_SCHEDULE_STATUS="SOURCE_NOT_PROVIDED", REVEAL_DEPTH=0.20, REVEAL_AREA=None, PROFILE_REQUIREMENT="external reveal profile (finish unknown)", STATUS=f"PROVISIONAL ({o['CONFIDENCE']})", CARRIED_FROM="PA04 facades"))
    # 4. door leaves from the DWG swing arcs on every copy (ACTUAL widths; heights TEMP_DEFAULT 2.20 only as provisional)
    for copy in ("GF", "FF", "ROOF"):
        for i, a in enumerate(_door_arcs(copy)):
            R.append(rec(OPENING_ID=f"DR-{copy}-{i+1:02d}", FLOOR=copy, HOST_FACE="host wall at the hinge (region face register)", TYPE="DOOR", SHAPE="RECT", WIDTH=a["LEAF_W_M"], HEIGHT=OWNER_TEMP_DEFAULTS["DOOR"][1],
                         ARCH_RADIUS_OR_CURVE=None, AREA=None, SOURCE=f"DWG door-swing arc {a['ID']} (radius = leaf width) at ({a['CX']}, {a['CY']})", ACTUAL_OR_DEFAULT="WIDTH ACTUAL / HEIGHT TEMP_DEFAULT",
                         DOOR_OR_WINDOW_SCHEDULE_STATUS="SOURCE_NOT_PROVIDED", REVEAL_DEPTH=0.20, REVEAL_AREA=None, PROFILE_REQUIREMENT="door jambs + head", STATUS="PROVISIONAL (height default 2.20 by owner temporary rule)",
                         CARRIED_FROM="PA04 DWG door arcs", HEIGHT_DEFAULT_PERMITTED="owner temporary default for provisional calculations only"))
    # 5. NE openings (raster only) as placeholders until the cold challenge merges
    for o in nw["NE"]["PRIMARY_READ"]:
        R.append(rec(OPENING_ID=o["OPENING_ID"], FLOOR=o["STOREY"], HOST_FACE="F-NE-MAIN", TYPE=o["TYPE"], SHAPE=o["SHAPE"], WIDTH=None, HEIGHT=None, ARCH_RADIUS_OR_CURVE=None, AREA=None,
                     SOURCE="page 7 raster, no printed dimension", ACTUAL_OR_DEFAULT="NOT_ESTABLISHED", DOOR_OR_WINDOW_SCHEDULE_STATUS="SOURCE_NOT_PROVIDED", REVEAL_DEPTH=None, REVEAL_AREA=None,
                     PROFILE_REQUIREMENT="external reveal profile (finish unknown)", STATUS="NOT_ESTABLISHED", CARRIED_FROM="PA04 facades (NE primary read)"))
    ids = [r["OPENING_ID"] for r in R]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    lines = [{"ID": r["OPENING_ID"], "UNIT": "m2", "VALUE": r["AREA"], "QUANTITY_STATE": "SOURCE_ESTABLISHED_QUANTITY" if r["ACTUAL_OR_DEFAULT"] == "ACTUAL" and r["AREA"] else ("NOT_ESTABLISHED" if r["AREA"] is None else "PROVISIONAL_QUANTITY"),
              "SOURCE": r["SOURCE"], "SOURCE_ENTITY_IDS": [r["SOURCE"]]} for r in R]
    checks = SC.run_all({"OPENINGS": R}, lines)
    # ---- profiles v2 ---------------------------------------------------------------------------
    P = []
    def prof(pid, host, lm, source, trade, status, note=None):
        P.append({"PROFILE_ID": pid, "HOST": host, "LENGTH_LM": lm, "UNIT": "lm", "SOURCE": source, "TRADE": trade, "STATUS": status, "NOTE": note})
    for r in R:
        w, h = r["WIDTH"], r["HEIGHT"]
        if not (isinstance(w, (int, float)) and isinstance(h, (int, float))):
            prof(f"PF-{r['OPENING_ID']}-JAMBS", r["OPENING_ID"], None, r["SOURCE"], "PLASTER_EDGE_PROFILE", "NOT_ESTABLISHED", "opening size not established")
            continue
        st = "PROVISIONAL_QUANTITY" if "DEFAULT" in r["ACTUAL_OR_DEFAULT"] or "PROVISIONAL" in str(r["STATUS"]) else "SOURCE_ESTABLISHED_QUANTITY"
        if r["TYPE"] == "DOOR":
            prof(f"PF-{r['OPENING_ID']}-JAMBS", r["OPENING_ID"], round(2 * h, 3), r["SOURCE"], "PLASTER_EDGE_PROFILE", st)
            prof(f"PF-{r['OPENING_ID']}-HEAD", r["OPENING_ID"], round(w, 3), r["SOURCE"], "PLASTER_EDGE_PROFILE", st)
        else:
            arch = r["ARCH_RADIUS_OR_CURVE"]
            head = round(math.pi * arch["R_M"], 3) if isinstance(arch, dict) and arch.get("R_M") and arch.get("SHAPE", "").endswith("SEMICIRCLE") else w
            prof(f"PF-{r['OPENING_ID']}-JAMBS", r["OPENING_ID"], round(2 * (h - (arch["R_M"] if isinstance(arch, dict) and arch.get("R_M") else 0)), 3), r["SOURCE"], "PLASTER_EDGE_PROFILE", st)
            prof(f"PF-{r['OPENING_ID']}-HEAD", r["OPENING_ID"], head, r["SOURCE"], "PLASTER_EDGE_PROFILE", st, "curved head measured along the arc" if head != w else None)
            prof(f"PF-{r['OPENING_ID']}-SILL", r["OPENING_ID"], round(w, 3), r["SOURCE"], "PLASTER_EDGE_PROFILE", st, "sill profile where applicable (trade rule not yet decided)")
    stx = C.read("pa04/STRUCTURAL_EXPOSURE_REGISTER.json", C.OUT)
    d2 = stx["D2_COLUMN"]
    prof("PF-COL-LOOP-059-CORNERS", "LOOP-059 exposed room-side corners (2)", round(2 * d2["COLUMN_EXPOSED_HEIGHT_M"]["VALUE"], 3), "COLUMN_VERTICAL_EXPOSURE + STRUCTURAL_EXPOSURE (CB7 soffit)", "PLASTER_EDGE_PROFILE", "PROVISIONAL_QUANTITY",
         "two vertical external corners of the N face; height PROVISIONAL")
    prof("PF-EXT-CORNERS", "external wall corners (all floors)", None, "not yet traced from the region registers", "PLASTER_EDGE_PROFILE", "NOT_STARTED")
    prof("PF-OTHER-EXPOSED-EDGES", "other exposed plaster edges (beam soffits, void slab edges)", None, "STRUCTURAL_EXPOSURE_REGISTER candidates", "PLASTER_EDGE_PROFILE", "NOT_STARTED")
    tot = {}
    for p in P:
        if p["LENGTH_LM"]:
            tot[p["STATUS"]] = round(tot.get(p["STATUS"], 0.0) + p["LENGTH_LM"], 3)
    C.METRICS.setdefault("openings_profiles_v2", {}).update({"AI_CALLS": 0, "DETERMINISTIC_OPS": len(R) + len(P)})
    C.write("OPENING_REGISTER_V2.json", {"ARTIFACT": "OPENING_REGISTER_V2", "OPENINGS": R, "COUNT": len(R), "DUPLICATE_IDS": dup, "OWNER_TEMP_DEFAULTS": OWNER_TEMP_DEFAULTS,
                                         "RULES": ["actual source overrides defaults", "defaults never overwrite actual values", "temporary defaults only where explicitly permitted for provisional calculations"], "SELF_CHECKS": checks})
    C.write("PROFILE_STEEL_REGISTER_V2.json", {"ARTIFACT": "PROFILE_STEEL_REGISTER_V2", "LINES": P, "TOTAL_LM_BY_STATE": tot, "UNIT_RULE": "lm only; never mixed with m2"})
    return {"OPENINGS": len(R), "BY_ORIGIN": {k: sum(1 for r in R if r["CARRIED_FROM"] == k) for k in {r["CARRIED_FROM"] for r in R}}, "PROFILE_LM": tot, "CHECKS": checks["FAILED"], "DUP": dup}


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=1, default=str))
