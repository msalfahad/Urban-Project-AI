"""T-584 development-villa build (research, unwired): STEPS. (1) the step at every external door / gate (F-T577-2),
(2) the entrance stair E1 step lm (F-T577-1), (3) stair-flight steps as count x length (F-T577-3), each closed against
the freelancer one unit at a time (lm, m2, nr), on the candidate of record ARCH_TAKEOFF_V3.0.58 (= the V3.0.57 lines
for every code read here, T-577 s.0).

    .work/venv/bin/python -I research/agents_t584/t584_alsenan.py [--check]

Reads only repository files (sha256-pinned): T584_DRAWN.json (this task's own read of the architectural DXF by handle,
t584_extract.py), the V3.0.57 line index (T-507), the T-325 sill / threshold ledger, the T-412 flight table, and his
rows as numbers (FREELANCER_RAW_ROWS.json through the merged T-577 reader: cells by sheet hash and column label hash;
no workbook text is written). Writes out/T584_STEPS.json; --check rebuilds it byte-identical. Signs: ours - his."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (HERE, ROOT / "research" / "agents_t577"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import t584_rules as R  # noqa: E402
import t577_alsenan as T577  # noqa: E402  (merged reader of his cells, read only)

DRAWN = "research/agents_t584/T584_DRAWN.json"
LINE_INDEX = "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
LEDGER = "research/agents_t325/SILL_THRESHOLD_LEDGER_T325.csv"
FLIGHTS = "research/agents_t412/FLIGHT_TABLE_T412.csv"
RAW = "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json"
PINS = {DRAWN: "1abe50a74e13f42e", LINE_INDEX: "fed5141ea31bfdd9", LEDGER: "ef6f2cb0c0d7619e", FLIGHTS: "20703ee293f0b39c",
        RAW: "752c9f4e0c4546d0"}
OUT = HERE / "out" / "T584_STEPS.json"
D = R.D
Z = Decimal(0)
PLAN_LOW_GF = "+-0.00"      # the lowest printed level of the GF plan (datum blocks LEL A86 / A89): a bound only


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def pins():
    for p, h in PINS.items():
        if h is not None and _sha(p) != h:
            raise R.RuleError(f"input {p} changed ({_sha(p)} != {h}): restate the inputs")


def S(x):
    return None if x is None else str(x)


# ---- (1) steps at external doors / gate --------------------------------------------------------------------------------
# side of the opening frame that is OUTSIDE (from the merged rulings: T-260 sides, T-325 external flag, T-175 gate)
DOORS = {   # oid: (threshold line owning the strip, T-325 class of the strip, his door-step reading)
    "D-GF-01": ("L-b3933a51bd95e9bc542b", "EXT"),
    "D-GF-03": ("L-74cd61b430eec9933d15", "EXT"),
    "D-GF-05": ("L-c8b5c7f742b22388339e", "WET (T-325); outside door to the side passage (T-268 ruled, open mouth)"),
    "D-GF-06": ("L-9fa69ef1a11ef9987967", "EXT"),
    "D-GF-07": ("L-ad41b065d825c0190b7d", "EXT"),
    "D-GF-09": ("L-8111095f6db78f0e674b", "EXT"),
    "D-2F-01": ("L-3e5c6b7af8dd06b2836c", "EXT"),
    "D-GF-15": ("L-56acf34557c315f65bb1", "GATE (fence, T-175 / T-327: width / host not established)"),
}
# Levels: the printed level nearest the opening's face mid point on each side with no wall line (layer 1) crossed.
# Two openings need a merged ruling for the outside level as well: D-GF-06 and D-GF-07 open onto the E1 entrance
# landing +1.00 (T-260 OUTDOOR_STAIR_LANDING; T-412 / T-184: E1 rises +0.15 -> +1.00, top edge 30A = landing edge);
# from D-GF-06 the nearest unobstructed figure is the court +0.15 seen down the open E1 flight, which is not the level
# at the door: the landing level governs there (it is the surface the door sill meets).
LANDING_RULING = {"D-GF-06": ("+1.00", "T-260 OUTDOOR_STAIR_LANDING (landing +1.00, step lines 30A / 30C / 30D start "
                                       "0.059 past the jamb); T-412 E1 +0.15 -> +1.00")}


def door_steps(drawn, L, led):
    led_w = {r["opening"]: r for r in led if r["component"] == "THRESHOLD"}
    out = {}
    for oid, (lid, cls) in DOORS.items():
        o = drawn["openings"][oid]
        if lid not in L or L[lid]["item_code"] != ("FIN.MARBLE.THRESHOLD" if oid == "D-GF-05" else "ARCH.THRESHOLD"):
            raise R.RuleError(f"{oid}: owning threshold line {lid} not as stated")
        face = [e for e in o["edges_on_face"]]
        solid = [e for e in face if e["layer"] == "5" and abs(e["offset_from_face_y0_m"]) < 0.011]
        comp = [e for e in face if e["layer"] == "2" and abs(abs(e["offset_from_face_y0_m"]) - 0.05) < 0.011]
        through = o["face_lines_through_opening"]
        beyond = [e for e in o["lines_beyond_face"]]
        # a parallel line beyond the face is a step only if it is not the opposite wall / window of a passage
        beyond_steps = [e for e in beyond if e["handle"] not in NOT_A_STEP]
        lv = {}
        for side in ("neg", "pos"):
            xs = [z for z in o[f"levels_side_{side}"] if z["walls_crossed"] == 0]
            lv[side] = xs[0] if xs else None
        if oid in LANDING_RULING:
            out_side = "neg"
            lv[out_side] = {"handle": "ruling", "level": LANDING_RULING[oid][0], "distance_m": None,
                            "walls_crossed": 0, "source": LANDING_RULING[oid][1]}
        if solid and comp or (through and comp):
            if len(comp) != 1 or (solid and len(solid) != 1):
                raise R.RuleError(f"{oid}: more than one front edge pair on the face")
            edge = comp[0]["length_m"] if through else solid[0]["length_m"]
            if solid and D(solid[0]["length_m"]) != D(comp[0]["length_m"]):
                raise R.RuleError(f"{oid}: front edge and companion differ")
            # the companion lies on the UPHILL side (T-412 convention): the printed levels must agree with it
            up = "pos" if comp[0]["offset_from_face_y0_m"] > 0 else "neg"
            dn = "neg" if up == "pos" else "pos"
            if lv[up] is None:
                raise R.RuleError(f"{oid}: no level printed on the uphill side")
            if lv[dn] is not None and R.level(lv[dn]["level"]) >= R.level(lv[up]["level"]):
                raise R.RuleError(f"{oid}: the companion side is not the higher printed level")
            p = R.step_at_opening(oid, edge, True, bool(beyond_steps), lv[up]["level"],
                                  None if lv[dn] is None else lv[dn]["level"], plan_low=PLAN_LOW_GF)
            ev = {"front": (through[0]["handle"] + " (face line through the opening)") if through else solid[0]["handle"],
                  "companion": comp[0]["handle"], "high": lv[up], "low": lv[dn]}
        else:
            if face or through or beyond_steps:
                raise R.RuleError(f"{oid}: a single unpaired line at the opening: not read")
            p = R.step_at_opening(oid, None, False, False, lv["neg"]["level"], lv["pos"]["level"])
            ev = {"levels": [lv["neg"], lv["pos"]]}
        w = led_w.get(oid, {}).get("width_m") or None
        out[oid] = {"line": lid, "strip_class": cls, "strip_width_m_T325": w, "block": o["block"],
                    "block_span_m": o["block_span_m"], "piece": p, "evidence": ev,
                    "beyond_named": [{"handle": e["handle"], "why": NOT_A_STEP[e["handle"]]} for e in beyond
                                     if e["handle"] in NOT_A_STEP]}
    return out


NOT_A_STEP = {"3CB": "D-GF-05: the inner line of the window in the passage's opposite wall 1.20 away (glazing lines "
                     "3CC .. 3CF behind it on layer W, wall ends 3D1 / 3D5 on layer 1), not a step front"}


# ---- (2) / (3) flight steps -------------------------------------------------------------------------------------------
# candidate FIN.STAIR.STEP_LM lines (V3.0.57) bound to drawn flights by the merged T-418 / T-429 binding
STEP_LINES = {   # line: (stair, flight, drawn treads (T-429), disposition)
    "L-d4d764ae7bb07b474b6f": ("ST-01", "MS1-L", 9, "OWN"),
    "L-f20f8544a42807c0cfcf": ("ST-01", "D1", 3, "OWN"),
    "L-0aa47300a16de572c967": ("ST-01", "MS1-U", 11, "OWN"),
    "L-23651ecfef77992ec8d4": ("ST-01", "MS2-L", 11, "OWN"),
    "L-60fc97c4306696c74c38": ("ST-01", "MS2-U", 11, "OWN"),
    "L-e085c168dee5fb19a7fb": ("ST-01", "MS1-T", 5, "HELD"),
    "L-1e88ac0d4ba0b4e8a950": ("ST-01", "MS2-L", 0, "SECOND_READING"),
    "L-59354cfe423b026db61a": ("ST-02", "RS-S", 10, "OWN"),
    "L-f145a2d130cba9450a24": ("ST-02", "RS-A", 4, "OWN"),
    "L-95b9555dd144951b071e": ("ST-02", "RS-C", 12, "HELD"),
    "L-3a3aabb15b187e33e3da": ("ST-02", "RS-C", 0, "SECOND_READING"),
    "L-c955f6b3a3abca48d562": ("ST-02", "RS-S", 0, "SECOND_READING"),
    "L-57202d2823270429cd80": ("ST-02", "RS-A", 0, "SECOND_READING"),
    "L-fef9ec154deaec502498": ("ST-02", "RS-S", 0, "SECOND_READING"),
}
HELD_BESIDE = {"MS1-T": ((D("4.14365"), None), "T-429 / T-434: three drawn winder fronts 4.14365 beside, candidate "
                         "reading 4.7815; governing count 5 winders (section A-A, Q-46 A), subdivision not drawn (C-ST-3)"),
               "RS-C": ((D("13.7964"), D("13.85")), "T-429 beside 13.7964; T-412 drawn radial fronts 13.85 (Q-50 A cond, "
                        "RFI-S27)")}
WIDTH = D("1.150")      # every drawn front edge of ST-01 / ST-02 (T-412 s.2)
E1_WIDTH = D("2.800")


def flight_table(L, flights):
    used = set()
    st = {}
    for lid, (stair, fl, treads, disp) in STEP_LINES.items():
        x = L[lid]
        if x["item_code"] != "FIN.STAIR.STEP_LM" or x["unit"] != "lm":
            raise R.RuleError(f"{lid}: not a step lm line")
        used.add(lid)
        g = st.setdefault(stair, {"own": [], "held": [], "second": []})
        if disp == "OWN":
            if x["class"] != "RELEASED":
                raise R.RuleError(f"{lid}: owned flight line not released")
            lm, nr = R.flight_steps(treads, WIDTH)
            if lm != D(x["measured_net"]):
                raise R.RuleError(f"{lid}: {treads} x {WIDTH} = {lm} != line {x['measured_net']}")
            g["own"].append({"line": lid, "flight": fl, "treads": nr, "lm": lm, "status": "DRAWING-CONFIRMED"})
        elif disp == "HELD":
            if x["class"] != "HELD":
                raise R.RuleError(f"{lid}: not HELD")
            g["held"].append({"line": lid, "flight": fl, "treads": treads, "bound": HELD_BESIDE[fl][0],
                              "why": HELD_BESIDE[fl][1]})
        else:
            if x["class"] == "RELEASED":
                raise R.RuleError(f"{lid}: a second reading released (double count)")
            g["second"].append({"line": lid, "flight": fl, "class": x["class"],
                                "why": "the same drawn flight read again (seen through the void / folded); owned by "
                                       "the flight's own line (T-129 / T-429), never a step of its own"})
    rest = [x["line_id"] for x in L.values() if x["item_code"] == "FIN.STAIR.STEP_LM" and x["line_id"] not in used]
    if rest:
        raise R.RuleError(f"step lines outside this table: {rest}")
    # T-412 census: treads and arrival edges per stair
    cen = {}
    for r in flights:
        c = cen.setdefault(r["stair"], {"treads": 0, "arrival": 0, "risers": 0})
        c["treads"] += int(r["treads"])
        c["arrival"] += int(r["landing_edges"]) + int(r["floor_edges"])
        c["risers"] += int(r["risers"])
    for stair, g in st.items():
        own = sum(p["treads"] for p in g["own"])
        held = sum(p["treads"] for p in g["held"])
        if own + held != cen[stair]["treads"]:
            raise R.RuleError(f"{stair}: candidate {own} + held {held} != census treads {cen[stair]['treads']}")
    # E1: no step line; the drawn fronts (own read + T-412) give the omission
    return st, cen


def e1_fronts(drawn):
    fr = drawn["E1_fronts"]
    if len(fr) != 5 or any(D(f["length_m"]) != E1_WIDTH for f in fr) or D(drawn["E1_width_dimension_A06_m"]) != E1_WIDTH:
        raise R.RuleError("E1 fronts not 5 x 2.800 with dimension A06 2800")
    treads, arrival = 4, 1          # 36E 36C 36A 30B front treads; 30A is the landing (platform) edge (T-412)
    lm, nr = R.flight_steps(treads, E1_WIDTH)
    return {"treads": nr, "arrival": arrival, "lm": lm, "fronts": [f["handle"] for f in fr],
            "status": "DRAWING-CONFIRMED", "levels": "+0.15 -> +1.00 (T-184 ST-03; T-412)"}


# ---- his cells -------------------------------------------------------------------------------------------------------
def his(cells):
    def row(r):
        g = lambda c: cells.get(f"MRB.{c}{r}")    # noqa: E731
        return {c: (None if g(c) is None else T577._q(g(c))) for c in "BCDFGH"}
    if [T577.col_unit(cells, c) for c in "BCDFGH"] != ["nr", "lm", "m2", "height", "lm", "m2"]:
        raise R.RuleError("marble sheet column labels not as expected")
    out = {}
    for key, r in (("ST-03", 16), ("ST-01", 23), ("ST-02", 30)) + tuple((f"DOOR{r}", r) for r in range(36, 42)):
        x = row(r)
        if T577.R.classify_cell("m2", x["B"], x["C"], x["D"], x["F"], x["H"]) != "LENGTH_IN_AREA_COLUMN":
            raise R.RuleError(f"his row {r}: not a length in the area column")
        out[key] = {"nr": int(x["B"]), "piece_m": x["C"], "lm": T577.R.length_of_row(x["B"], "nr", x["C"], "lm"),
                    "m2_cell": x["H"], "cells": {"nr": f"MRB.B{r}", "lm": f"MRB.B{r}xC{r}", "m2": f"MRB.H{r}"}}
    return out


# ---- reconciliation ----------------------------------------------------------------------------------------------------
C = R.cause


def stair_groups(st, cen, e1, H):
    G = {"lm": [], "m2": [], "nr": []}
    for stair in ("ST-01", "ST-02"):
        g, h = st[stair], H[stair]
        own_t = sum(p["treads"] for p in g["own"])
        own_lm = sum((p["lm"] for p in g["own"]), Z)
        held_t = sum(p["treads"] for p in g["held"])
        lo = sum((p["bound"][0] for p in g["held"]), Z)
        hi = None if any(p["bound"][1] is None for p in g["held"]) else sum((p["bound"][1] for p in g["held"]), Z)
        _, arr, rem = R.piece_per_riser_split(h["nr"], own_t, held_t, cen[stair]["arrival"])
        pw = h["piece_m"]
        cl = [C(f"width: {own_t} drawn treads x (drawn front edge {WIDTH} - his {pw})", own_t * (WIDTH - pw),
                "ENGINE_RIGHT", "MEASURE", "T-412 s.2 (every drawn marble front edge 1.150; 0.050 is the band)"),
              C(f"{held_t} treads in HELD flight lines ({', '.join(p['flight'] for p in g['held'])}): his share "
                f"{held_t} x {pw}; ours blank with the bound beside", -held_t * pw, "HELD", "HELD",
                "; ".join(p["why"] for p in g["held"]), bound=(lo, hi)),
              C(f"{arr} arrival edges (landing / floor): his piece per riser, our step per tread (UP-STAIR-008, "
                "R-T412-1; the edge is a B7-05 nosing)", -arr * pw, "RULE_DIFFERENCE", "MEASURE",
                "T-412 flight table landing_edges + floor_edges")]
        if rem:
            cl.append(C(f"{rem} pieces beyond every reading of his count (risers {cen[stair]['risers']}, treads "
                        f"{cen[stair]['treads']}): no breakdown in his row", -rem * pw, "UNRESOLVED", "MEASURE",
                        "T-412 s.5; T-578 F-T578-3"))
        G["lm"].append(R.close(stair, "lm", own_lm, h["lm"], cl))
        cn = [C("treads in HELD flight lines", -held_t, "HELD", "HELD", "as lm", bound=(D(held_t - 1 if stair == "ST-01"
                                                                                           else held_t), D(held_t))),
              C("arrival edges counted as pieces by him", -arr, "RULE_DIFFERENCE", "MEASURE", "as lm")]
        if rem:
            cn.append(C("pieces beyond every reading of his count", -rem, "UNRESOLVED", "MEASURE", "as lm"))
        G["nr"].append(R.close(stair, "nr", own_t, h["nr"], cn))
    h = H["ST-03"]
    G["lm"].append(R.close("ST-03", "lm", Z, h["lm"], [
        C(f"E1 has no FIN.STAIR.STEP_LM line: {e1['treads']} drawn treads x {E1_WIDTH} = {e1['lm']} (fronts "
          f"{' '.join(e1['fronts'][:4])}; dimension A06 2800) - fix row FR-T584-1", -e1["lm"], "ENGINE_OMISSION",
          "MEASURE", "own read by handle + T-412 (36E 36C 36A 30B, 30A platform edge)"),
        C("his 5th piece = the platform edge 30A (landing / arrival edge, not a step)", -e1["arrival"] * h["piece_m"],
          "RULE_DIFFERENCE", "MEASURE", "T-412 / T-534")]))
    G["nr"].append(R.close("ST-03", "nr", 0, h["nr"], [
        C("E1 treads with no step line (FR-T584-1)", -e1["treads"], "ENGINE_OMISSION", "MEASURE", "as lm"),
        C("his platform-edge piece", -e1["arrival"], "RULE_DIFFERENCE", "MEASURE", "as lm")]))
    tot_m2 = sum((H[s]["m2_cell"] for s in ("ST-01", "ST-02", "ST-03")), Z)
    G["m2"].append(R.close("STAIR_STEPS", "m2", Z, tot_m2, [
        C("his H16 / H23 / H30 are count x length in an area column (no width cell): never compared as m2 (R-T577-1 "
          "(c)); the tread / riser m2 lines are B7-02 / B7-03, not the step", -tot_m2, "RULE_DIFFERENCE", "UNIT",
          "his B x C = H, D / F blank")]))
    return G


def door_groups(steps, H):
    G = {"lm": [], "m2": [], "nr": []}
    rows = [H[f"DOOR{r}"] for r in range(36, 42)]
    his_lm = sum((x["lm"] for x in rows), Z)
    his_nr = sum(x["nr"] for x in rows)
    his_m2 = sum((x["m2_cell"] for x in rows), Z)
    house = {k: v for k, v in steps.items() if k != "D-GF-15"}
    st = {k: v["piece"] for k, v in house.items() if v["piece"]["kind"] != "NO_STEP"}
    none = sorted(k for k, v in house.items() if v["piece"]["kind"] == "NO_STEP")
    our_lm = sum((p["lm"] for p in st.values()), Z)
    our_nr = sum(p["nr"] for p in st.values())
    our_m2 = sum((p["m2"] for p in st.values() if p["m2"] is not None), Z)
    held = {k: p for k, p in st.items() if p["status"] == "HELD"}
    h1 = (f"his {len(rows)} door-step pieces carry no door id (matching his rows to doors by figure is refused, "
          f"R-T577-1); drawn: {len(st)} steps ({', '.join(sorted(st))}) and no step at {', '.join(none)} (same level "
          "printed both sides, no edge drawn). Reading H1 (one piece per T-325 external door) would put 3 of his "
          "pieces where nothing is drawn and none at D-GF-05; not established, so UNRESOLVED")
    G["lm"].append(R.close("DOOR_STEPS", "lm", our_lm, his_lm, [
        C(h1, our_lm - his_lm, "UNRESOLVED", "MEASURE", "own DXF read (T584_DRAWN.json); his B36..B41 x C36..C41")]))
    G["nr"].append(R.close("DOOR_STEPS", "nr", our_nr, his_nr, [
        C(h1, our_nr - his_nr, "UNRESOLVED", "MEASURE", "as lm")]))
    hb = (sum((p["bound"]["m2"][0] for p in held.values()), Z), sum((p["bound"]["m2"][1] for p in held.values()), Z))
    G["m2"].append(R.close("DOOR_STEPS", "m2", our_m2, his_m2, [
        C("his H36..H41 are count x length in an area column: never compared as m2", -his_m2, "RULE_DIFFERENCE", "UNIT",
          "his B x C = H"),
        C("our riser faces (edge x printed level difference) have no area counterpart in his rows", our_m2,
          "ENGINE_RIGHT", "SCOPE", "own DXF read"),
        C(f"riser HELD where the outside level is not printed ({', '.join(sorted(held))})", 0, "HELD", "HELD",
          "plan lowest printed level +-0.00 (datum LEL) bounds the drop", bound=hb)]))
    g = steps["D-GF-15"]["piece"]
    G["lm"].append(R.close("GATE_STEP", "lm", g["lm"], Z, [
        C("the fence gate step (court +0.15 / outside datum +-0.00, edge on the fence line): whether his rows hold it "
          "is not established (no id)", g["lm"], "UNRESOLVED", "SCOPE", "own DXF read")]))
    G["nr"].append(R.close("GATE_STEP", "nr", g["nr"], 0, [
        C("as lm", g["nr"], "UNRESOLVED", "SCOPE", "own DXF read")]))
    G["m2"].append(R.close("GATE_STEP", "m2", g["m2"], Z, [
        C("riser face of the gate step; no counterpart", g["m2"], "UNRESOLVED", "SCOPE", "own DXF read")]))
    return G


def fix_rows(steps, e1):
    fr = [{"id": "FR-T584-1", "family": "B7-06 FIN.STAIR.STEP_LM", "element": "GF-COURT#E1 steps",
           "proposal": f"NEW line {e1['lm']} lm / {e1['treads']} nr, DRAWING-CONFIRMED ({e1['treads']} fronts x 2.800, "
                       "A06 2800), material marble (OWNER_RULE_OUTDOOR_FLOORS: outside stairs marble), bound to "
                       "L-314c3ac6d45431b687c5 (tread) / L-0afa7bd369ec489ebfc2 (riser); 30A stays the landing edge "
                       "(L-3dd82a576dce1beb4250, B7-05)",
           "state": "HELD until wired (manifest row, lane I)"}]
    for oid in ("D-GF-01", "D-GF-03", "D-GF-05", "D-GF-09", "D-GF-15"):
        s = steps[oid]
        p = s["piece"]
        rise = (f"riser {p['riser_m']} x {p['lm']} = {p['m2']} m2" if p["m2"] is not None else
                f"riser HELD 0 .. {p['bound']['riser_m'][1]} (outside level not printed), m2 0 .. {p['bound']['m2'][1]}")
        fr.append({"id": f"FR-T584-2:{oid}", "family": "external threshold (ARCH.THRESHOLD / B6 threshold line)",
                   "element": f"{oid} THRESHOLD_STEP", "line": s["line"],
                   "proposal": f"two measures beside the strip on its own line: nosing {p['lm']} lm (drawn edge "
                               f"{s['evidence']['front']} / {s['evidence']['companion']}), {rise}; no new step line; "
                               "material by the strip's specification (HELD)",
                   "state": "HELD until wired"})
    fr.append({"id": "FR-T584-3", "family": "element register", "element": "external door step vs threshold strip",
               "proposal": "R-T584-1 (b): edge on the wall face = ONE element (the threshold stone with its nosing and "
                           "riser, owned by the threshold line); edge beyond the face = EXT_STEP (outside stair, B7, "
                           "marble); same level both sides and no edge = NOT_APPLICABLE",
               "state": "proposal for the Lead (ELEMENT_REGISTER ruling)"})
    return fr


def build():
    pins()
    drawn = json.loads((ROOT / DRAWN).read_text())
    L = {x["line_id"]: x for x in json.loads((ROOT / LINE_INDEX).read_text())["lines"]}
    led = list(csv.DictReader((ROOT / LEDGER).open(encoding="utf-8")))
    flights = list(csv.DictReader((ROOT / FLIGHTS).open(encoding="utf-8")))
    steps = door_steps(drawn, L, led)
    R.owners_once({k: [v["line"]] for k, v in steps.items()})
    st, cen = flight_table(L, flights)
    e1 = e1_fronts(drawn)
    H = his(T577.his_cells())
    groups = {"stairs": stair_groups(st, cen, e1, H), "doors": door_groups(steps, H)}

    def gout(g):
        return {"id": g["id"], "ours": S(g["ours"]), "his": S(g["his"]), "gap": S(g["gap"]), "pct": S(g["pct"]),
                "causes": [{"label": c["label"], "verdict": c["verdict"], "kind": c["kind"], "amount": S(c["amount"]),
                            **({"bound": [S(c["bound"][0]), S(c["bound"][1])]} if "bound" in c else {}),
                            "source": c["source"]} for c in g["causes"]]}

    def pout(p):
        return {k: (S(v) if isinstance(v, Decimal) else
                    ({kk: [S(vv[0]), S(vv[1])] for kk, vv in v.items()} if isinstance(v, dict) else v))
                for k, v in p.items()}
    return {
        "schema": "T584_STEPS_V1", "rule": "R-T584-1", "candidate": "ARCH_TAKEOFF_V3.0.58", "sign": "ours - his",
        "pins": {k: (v or _sha(k)) for k, v in PINS.items()},
        "openings": {k: {**{kk: vv for kk, vv in v.items() if kk != "piece"}, "piece": pout(v["piece"])}
                     for k, v in steps.items()},
        "e1": {**e1, "lm": S(e1["lm"])},
        "flights": {s: {"own": [{**p, "lm": S(p["lm"])} for p in g["own"]],
                        "held": [{**p, "bound": [S(p["bound"][0]), S(p["bound"][1])]} for p in g["held"]],
                        "second_readings": g["second"], "census": cen[s]} for s, g in st.items()},
        "tables": {k: {u: [gout(g) for g in v[u]] for u in ("lm", "m2", "nr")} for k, v in groups.items()},
        "fix_rows": fix_rows(steps, e1),
        "released": "NOTHING RELEASED; no candidate, engine, rule or registry file changed (research ledger)",
    }


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    out = dump(build())
    if "--check" in argv:
        if OUT.read_text(encoding="utf-8") != out:
            raise SystemExit("T584 output differs from a rebuild")
        print("T584 check: byte-identical")
        return
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(out, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


# T-653: this builder's functions run in the same local 40-digit context as its rules (before T-653 they ran
# at 40 only because importing the rules changed the process-global context).
R.in_prec40(globals())


if __name__ == "__main__":
    main(sys.argv[1:])
