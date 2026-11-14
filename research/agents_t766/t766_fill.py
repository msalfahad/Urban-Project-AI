"""T-766 F-07 STAIR FINISHES to figures (DELIVERY MODE fix-row set; worker 2, 2026-11-14).

Reads the candidate line index ARCH_TAKEOFF_V3.0.81 (agents/task-T-770, sha16 3976b262611bc3bd) and writes
out/FIX_ROWS.json + out/FIX_ROWS.md: one row per non-released, non-excluded line of FIN.STAIR.FLIGHT / STEP_LM /
SOFFIT / SKIRTING.SLOPED / SKIRTING.ZIGZAG and FIN.MARBLE.RISER / TREAD / LANDING, plus two ADD rows (B7-04 landings
with no line, T-502). Nothing else is touched. Lift surround marble (FIN.MARBLE.LIFT_SURROUND) is left to T-768.

Inputs (merged files on the working branch, read as data): T-738 entries (drawn points not yet released), T-501 stair
skirting table (piece plan / risers / zigzag / sloped, Checker-merged), T-415 RS-C geometry (radii, 7.790996 deg step,
K 5.064265 m2), T-493 landing census (Checker 4 / 4 AGREE), T-718 winder / curved bounds.

Choices (each labelled on its row):
  skirting form (ORR-007 still with the owner): the ZIGZAG line carries the strip, the SLOPED alternative is EXCLUDED
    (never additive with it; T-508 design: the unchosen form becomes NOT_APPLICABLE). Evidence for zigzag: the
    freelancer measures stair skirting per step (his marble sheet), and the stepped strip is the strip that follows the
    visible tread / riser tops. Revert by swapping the two lines of each piece if the owner answers 'sloped'.
  winder corner MS1-T: the total rise across the turn is fixed by the printed levels (+2.667 -> +3.500 = 0.833333), so
    zigzag W + N = plan W + plan N + 0.833333 whatever the riser count (5 on A-A vs 4 wedges); split by plan length.
  winder turn 1F flight 5: 5 fronts = entry edge 1.150 + drawn fan at 22.5 / 45 (BE6 1.626346) / 67.5 deg + exit edge
    1.150 (ESTIMATE: the 22.5 / 67.5 lines assumed symmetric to BE6); walking line = quarter arc r 0.575 (lane centre).
  curved flight RS-C: walking line r 2.1555 (lane centre, T-415), drawn step 7.790996 deg; finish lane r 1.5805 ..
    2.7305 (the drawn 1.150 riser lines); junction tread 12 scaled by its drawn plan ratio 0.415515 / 0.366379.
  soffits: ST-01 = measured rows 20.423364 + winder / junction plan 1.500 x the stair's own secant hypot(0.30, 0.166667)
    / 0.30; ST-02 = measured rows 4.460946 + RS-C helical underside = K 5.064265 (T-415, integral of sec over the drawn
    lane; the waist thickness changes the volume, not the soffit area).
  openings beside a flight (MS1-U.E2 GF hidden opening 33C / 33D): head at the 2.20 default (+3.20) lies below the
    flight (+4.08 .. +4.62): the wall face at the strip is solid -> full piece.
  MS1-U.E3b: 12 risers (section A-A + ST p.4 edge 459 + printed FFL arithmetic (5.50 - 3.50) / 0.166667 = 12; 11 risers
    would give 0.1818 > the 0.175 equal-riser ceiling) -> DRAWING-READ.
  RS-S.S0 / RS-C.OUT: no wall or column face on the stretch (both layers read, T-410 / T-501): an open side carries no
    skirting (R-T508-1, B7-09 owns the edge) -> NOT_APPLICABLE on both forms.

  python3 -I research/agents_t766/t766_fill.py <LINE_INDEX_V3_0_81.json> [--check]
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "FIX_ROWS.json")
OUT_MD = os.path.join(HERE, "out", "FIX_ROWS.md")
INDEX_SHA16 = "3976b262611bc3bd"
FAMILIES = ("FIN.STAIR.FLIGHT", "FIN.STAIR.STEP_LM", "FIN.STAIR.SOFFIT", "FIN.STAIR.SKIRTING.SLOPED",
            "FIN.STAIR.SKIRTING.ZIGZAG", "FIN.MARBLE.RISER", "FIN.MARBLE.TREAD", "FIN.MARBLE.LANDING")
LABELS = ("MEASURED", "DRAWING-READ", "DEFAULT", "ESTIMATE", "SAFETY")
r6 = lambda x: round(x + 0.0, 6)

# ---- geometry constants (sources in the docstring) ---------------------------------------------------------------
R_MS1 = 4.50 / 27            # MS1 / ST-01 lower rise (Q-46 A)
R_RS = 4.50 / 28             # ST-02 rise (Q-50 A cond)
MARBLE_T = 0.030             # riser face = rise - tread marble (UP-STAIR-006, as the released riser lines)
STEP_DEG = 7.790996
R_IN, R_OUT, R_WALK = 1.5805, 2.7305, 2.1555
T_STRUCT, T_JUNCTION = 0.366379, 0.415515
CURTAIL_PLAN = 0.090129
RS_FRONTS, RS_FRONT_CURTAILS = 13.80, 0.949440 + 0.672000
RS_FACES, RS_FACE_CURTAILS = 13.798023, 0.840283 + 0.562992
TURN = 1.150
BE6 = 1.626346
K_RSC = 5.064265

dth = math.radians(STEP_DEG)
going_rs = R_WALK * dth
fin_tread = 0.5 * dth * (R_OUT ** 2 - R_IN ** 2)
turn_fronts = TURN + TURN / math.cos(math.radians(22.5)) + BE6 + TURN / math.cos(math.radians(22.5)) + TURN
turn_walk = math.pi / 2 * (TURN / 2)
turn_rise = 3.5 - 8 / 3          # +2.666667 -> +3.500

FIG = {}
# FLIGHT (lm along the pitch line)
FIG["L-a08d67ca292ab16ef9c3"] = (11 * math.hypot(0.300, 4.20 / 25), "DRAWING-READ", "1F MS2-L: 11 goings x hypot(0.300, 4.20/25) (T-738 drawn point, released here)")
FIG["L-54eb280b9f7bf5eda65f"] = (11 * math.hypot(0.300, R_MS1), "DRAWING-READ", "1F MS1-U: 11 goings x hypot(0.300, 4.50/27) (T-738 drawn point)")
FIG["L-48bb13e2f1c94d852a03"] = (11 * math.hypot(0.300, 4.20 / 25), "DRAWING-READ", "2F MS2-U: 11 goings x hypot(0.300, 4.20/25) (T-738 drawn point)")
FIG["L-a1a0ab49818d4b9621b5"] = (9 * math.hypot(0.300, R_MS1), "DRAWING-READ", "GF MS1-L: 9 goings x hypot(0.300, 4.50/27) (T-738 drawn point)")
FIG["L-cccf54f717124cd750b3"] = (3 * math.hypot(0.300, 0.70 / 4), "DRAWING-READ", "GF D1: 3 goings x hypot(0.300, 0.70/4) (T-738 drawn point)")
FIG["L-509c6af3d162ae145108"] = (10 * math.hypot(0.300, R_RS), "DRAWING-READ", "GF RS-S: 10 goings x hypot(0.300, 4.50/28) (T-738 drawn point; riser Q-50 A cond)")
FIG["L-406aae9a9854e015c45e"] = (4 * math.hypot(0.300, R_RS), "DRAWING-READ", "GF RS-A: 4 goings x hypot(0.300, 4.50/28) (T-738 drawn point)")
FIG["L-c6724654ee4ccdb0c508"] = (math.hypot(turn_walk, turn_rise), "ESTIMATE",
                                 f"1F MS1-T winder turn: walking line quarter arc r 0.575 (lane centre of the 1.150 turn) = {turn_walk:.4f} plan, rise +2.667 -> +3.500 = 0.8333 printed: hypot")
FIG["L-30009d8eb01996ec6399"] = (11 * math.hypot(going_rs, R_RS) + math.hypot(going_rs * T_JUNCTION / T_STRUCT, R_RS), "ESTIMATE",
                                 f"GF RS-C curved: walking line r 2.1555 x drawn step 7.790996 deg = going {going_rs:.4f}; 11 x hypot(going, 4.50/28) + junction tread going x 0.415515/0.366379 (drawn plan ratio)")
# STEP_LM (front edges)
FIG["L-e085c168dee5fb19a7fb"] = (turn_fronts, "ESTIMATE", "1F MS1-T turn: entry 1.150 + fan 22.5 deg 1.2448 + BE6 1.626346 (drawn) + 67.5 deg 1.2448 + exit 1.150 (inside the drawn 5.75 .. 8.1317 bound)")
FIG["L-95b9555dd144951b071e"] = (RS_FRONTS + RS_FRONT_CURTAILS, "DRAWING-READ", "GF RS-C: 12 drawn front edges 13.800 (T-718) + drawn curtail front arcs 258 0.949440 / 25A 0.672000")
# RISER (m2)
pts = {"L-0f060e9951c28c4cf074": (12, 4.20 / 25, "1F MS2-L 12 risers"), "L-07e0855f961a839c1277": (12, R_MS1, "1F MS1-U 12 risers"),
       "L-12f56cbfe750f8b30c41": (12, 4.20 / 25, "2F MS2-U 12 risers"), "L-ecc450d6cc865617f8f6": (10, R_MS1, "GF MS1-L 10 risers"),
       "L-8938aa3b25bf605e4b9d": (4, 0.70 / 4, "GF D1 4 risers"), "L-099fe9fcfa5667fb8b99": (11, R_RS, "GF RS-S 11 risers"),
       "L-16e0c6682725260f28e7": (5, R_RS, "GF RS-A 5 risers")}
for lid, (n, r, t) in pts.items():
    FIG[lid] = (n * 1.150 * (r - MARBLE_T), "DRAWING-READ", f"{t} x 1.150 x ({r:.6f} - 0.030) (T-738 drawn point)")
FIG["L-d014870b8dcae736608d"] = (1.150 * (7.684 - 7.516 - MARBLE_T), "DRAWING-READ", "2F MS2-TR closing riser 1.150 x (0.168 printed levels - 0.030) (T-738 ADD point)")
FIG["L-820baecf7f726b4d8f1e"] = (turn_fronts * (R_MS1 - MARBLE_T), "ESTIMATE", "1F MS1-T turn: 5 fronts 6.4159 (as STEP_LM) x (4.50/27 - 0.030)")
FIG["L-913cda8eb6d73f6e28cc"] = ((RS_FACES + RS_FACE_CURTAILS) * (R_RS - MARBLE_T), "DRAWING-READ", "GF RS-C: 12 drawn riser faces 13.798023 + drawn curtail face arcs 259 0.840283 / 25B 0.562992, x (4.50/28 - 0.030)")
# TREAD (m2)
FIG["L-b4660de0ddd98ad0ffc2"] = (TURN * TURN, "DRAWING-READ", "1F MS1-T: the 5 winder treads tile the drawn 1.150 x 1.150 turn (T-738 / T-493)")
FIG["L-fa534ec5f9dc14947899"] = (11 * fin_tread + T_JUNCTION * (TURN / 1.250) + CURTAIL_PLAN, "ESTIMATE",
                                 f"GF RS-C: finish lane r 1.5805 .. 2.7305: 11 x {fin_tread:.6f} + junction 0.415515 x 1.15/1.25 + curtail 0.090129 beyond the lane (T-415)")
# LANDING (m2)
FIG["L-5d2be30dd8d2ffeacc42"] = (2.9325 + 4.865, "MEASURED", "ST-01 MS2-LD 2.9325 (+7.516) + 2F arrival 4.865 (+9.70), T-493 census, Checker own re-measure 4 / 4 AGREE; inside the held 0 .. 9.225")
# SOFFIT (m2)
FIG["L-1fcec3328ccd0ea243d4"] = (20.423364 + 1.500 * math.hypot(0.300, R_MS1) / 0.300, "ESTIMATE",
                                 "ST-01: measured rows 20.423364 (T-281 / T-718) + winder / junction plan 1.500 x secant hypot(0.30, 4.50/27)/0.30 = 1.1439")
FIG["L-c77e3887f7e348b1461d"] = (4.460946 + K_RSC, "ESTIMATE", "ST-02: measured RS-S / RS-LD / RS-A rows 4.460946 + RS-C helical underside K 5.064265 (T-415, drawn lane)")

# ---- skirting pieces: (zigzag, label, basis); None = NOT_APPLICABLE ------------------------------------------------
w_share = 1.20 / (1.20 + 1.15)
SK = {
    "MS1-L.W1": (0.733334, "ESTIMATE", "T-501 piece plan 0.40 + 2 risers"),
    "MS1-L.W1C": (0.766667, "ESTIMATE", "T-501 piece plan 0.50 + 1 riser + return 0.10"),
    "MS1-L.W1B": (1.250001, "ESTIMATE", "T-501 piece plan 0.75 + 3 risers"),
    "MS1-U.E1": (1.616668, "ESTIMATE", "T-501 piece plan 0.95 + 4 risers"),
    "MS1-U.E2": (1.400001, "ESTIMATE", "T-501 piece plan 0.90 + 3 risers; GF opening 33C / 33D head 2.20 default (+3.20) below the flight (+4.08): face solid"),
    "MS1-U.E3a": (1.816668, "ESTIMATE", "T-501 piece plan 1.15 + 4 risers"),
    "MS1-U.E3b": (0.466667, "DRAWING-READ", "12th riser: section A-A + ST p.4 edge 459 + FFL (5.50-3.50)/0.166667 = 12 (11 -> 0.182 > 0.175); plan 0.30 + 1 riser"),
    "MS1-T.W": (1.20 + turn_rise * w_share, "ESTIMATE", "winder: plan 1.20 + share of the printed rise 0.8333 by plan length (total fixed by the levels)"),
    "MS1-T.N": (1.15 + turn_rise * (1 - w_share), "ESTIMATE", "winder: plan 1.15 + share of the printed rise 0.8333 by plan length"),
    "MS2-L.W1": (1.672, "ESTIMATE", "T-501 piece plan 1.00 + 4 risers"),
    "MS2-L.W1C": (0.768, "ESTIMATE", "T-501 piece plan 0.50 + 1 riser + return 0.10"),
    "MS2-L.W1B": (1.254, "ESTIMATE", "T-501 piece plan 0.75 + 3 risers"),
    "MS2-TR.N": (0.168, "DRAWING-READ", "closing riser: one rise 7.516 -> 7.684 printed, on the north wall wherever it meets it"),
    "MS2-U.E": (5.316, "ESTIMATE", "T-501 piece plan 3.30 + 12 risers"),
    "D1.E": (1.6, "ESTIMATE", "T-501 piece plan 0.90 + 4 risers"),
    "RS-S.S1": (1.332143, "ESTIMATE", "T-501 piece plan 0.80 + 3 risers + return 0.05"),
    "RS-S.S2": (3.125, "ESTIMATE", "T-501 piece plan 2.00 + 7 risers"),
    "E1.S": (2.05, "ESTIMATE", "T-501 piece plan 1.20 + 5 risers"),
    "RS-S.S0": None,
    "RS-C.OUT": None,
}
FORM_NOTE = "ZIGZAG form carries the strip (ORR-007 open; freelancer measures per step)"


def build(index_path):
    raw = open(index_path, "rb").read()
    if hashlib.sha256(raw).hexdigest()[:16] != INDEX_SHA16:
        raise SystemExit("index is not V3.0.81 3976b262611bc3bd")
    lines = json.loads(raw)["lines"]
    rows, seen = [], set()
    for l in lines:
        ic = l["item_code"]
        if ic not in FAMILIES or l["class"] in ("RELEASED", "EXCLUDED"):
            continue
        lid = l["line_id"]
        before = {"class": l["class"], "net": l["measured_net"], "low": l["held_low"], "high": l["held_high"]}
        base = dict(line_id=lid, item_code=ic, unit=l["unit"], element_id=l["element_id"], before=before, set="STAIR")
        if ic.startswith("FIN.STAIR.SKIRTING"):
            piece = l["element_id"].split(":", 1)[1]
            if piece not in SK:
                raise SystemExit(f"{lid}: skirting piece {piece} has no figure")
            v = SK[piece]
            if v is None:
                base.update(after={"class": "EXCLUDED", "net": None, "reason": "NOT_APPLICABLE_WITH_EVIDENCE"}, label="NOT_APPLICABLE",
                            basis=f"{piece}: no wall or column face on the stretch (T-410 / T-501 both layers read); open side carries no skirting (R-T508-1, B7-09 owns the edge)")
            elif ic.endswith("SLOPED"):
                base.update(after={"class": "EXCLUDED", "net": None, "reason": "FORM_ALTERNATIVE_ORR-007"}, label="NOT_APPLICABLE",
                            basis=f"{piece}: {FORM_NOTE}; this sloped alternative is never additive with the zigzag line; swap if the owner answers sloped")
            else:
                val, lab, why = v
                base.update(after={"class": "RELEASED", "net": r6(val)}, label=lab, basis=f"{piece} zigzag {val:.4f} lm: {why}; {FORM_NOTE}")
        else:
            if lid not in FIG:
                raise SystemExit(f"{lid} {ic}: no figure")
            val, lab, why = FIG[lid]
            if not val or val <= 0:
                raise SystemExit(f"{lid}: figure missing -> never 0")
            lo, hi = before["low"], before["high"]
            if lo is not None and val < lo - 1e-6 or hi is not None and val > hi + 1e-3:
                raise SystemExit(f"{lid}: {val} outside the held bound {lo} .. {hi}")
            base.update(after={"class": "RELEASED", "net": r6(val)}, label=lab, basis=why)
        if base["label"] not in LABELS + ("NOT_APPLICABLE",):
            raise SystemExit(lid)
        seen.add(lid)
        rows.append(base)
    unused = set(FIG) - seen
    if unused:
        raise SystemExit(f"figures for lines not in the index: {sorted(unused)}")
    adds = [
        dict(line_id=None, action="ADD", item_code="FIN.MARBLE.LANDING", unit="m2", element_id="STAIR-LANDING:ST01-MS1-LD",
             before=None, after={"class": "RELEASED", "net": 1.4375}, label="MEASURED", set="STAIR",
             basis="ST-01 MS1-LD +3.50: 1.25 x 1.15 (T-493 census, Checker 4 / 4 AGREE); no line today (silent omission F-3, T-502)"),
        dict(line_id=None, action="ADD", item_code="FIN.MARBLE.LANDING", unit="m2", element_id="STAIR-LANDING:ST02-RS-LD",
             before=None, after={"class": "RELEASED", "net": 1.3525}, label="MEASURED", set="STAIR",
             basis="ST-02 RS-LD +4.696 (T-493, Checker AGREE); already deducted from 1F porcelain (R04 1.352454): no double count (T-502)"),
    ]
    rows.sort(key=lambda r: (r["item_code"], r["element_id"]))
    return rows + adds


def summarise(rows, lines):
    def tot(code, cls=("RELEASED",)):
        s = sum(l["measured_net"] or 0 for l in lines if l["item_code"] == code and l["class"] == "RELEASED")
        s += sum(r["after"]["net"] for r in rows if r["item_code"] == code and r["after"]["class"] == "RELEASED")
        return round(s, 2)
    return {c: tot(c) for c in FAMILIES}


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    rows = build(argv[1])
    lines = json.load(open(argv[1]))["lines"]
    blank_before = sum(1 for r in rows if r["line_id"])
    doc = dict(task="T-766", candidate_version="ARCH_TAKEOFF_V3.0.81", base="agents/task-T-770 (V3.0.81)", index_sha16=INDEX_SHA16,
               rows=len(rows), blank_or_ranged_before=blank_before, left_after=0, overlap_with_MAIN_FILL_ALL=0,
               totals_after=summarise(rows, lines),
               freelancer={"ST-01 steps": "63 x 1.2 m2 = 75.6", "ST-01 landing": 6.2, "ST-01 skirting lm": 23.1,
                           "ST-02 steps": "28 x 1.2 m2 = 33.6", "ST-02 landing": 1.44, "ST-02 skirting lm": 2.4,
                           "E1 steps": "5 x 2.8 = 14", "E1 landing": 5.1, "E1 skirting lm": 4.37, "stair soffit paint m2": 39.99},
               rows_detail=rows)
    text = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if "--check" in argv:
        if open(OUT).read() != text:
            raise SystemExit("FIX_ROWS.json differs from a rebuild")
        print(f"T-766 --check OK {len(rows)} rows")
        return
    open(OUT, "w").write(text)
    md = ["# T-766 stair finishes fix rows (V3.0.81)", "", "| line | item | unit | before | after | label | basis |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        b = r["before"]
        bef = "-" if b is None else (f"{b['net']}" if b["net"] is not None else (f"{b['low']} .. {b['high']}" if b["low"] is not None else "blank"))
        a = r["after"]
        aft = f"{a['net']}" if a["net"] is not None else a["reason"]
        md.append(f"| {r['line_id'] or 'ADD ' + r['element_id']} | {r['item_code']} | {r['unit']} | {bef} | {aft} | {r['label']} | {r['basis']} |")
    md += ["", "Totals after (released + these rows): " + json.dumps(doc["totals_after"])]
    open(OUT_MD, "w").write("\n".join(md) + "\n")
    print(f"T-766 wrote {len(rows)} rows; totals {doc['totals_after']}")


if __name__ == "__main__":
    main(sys.argv)
