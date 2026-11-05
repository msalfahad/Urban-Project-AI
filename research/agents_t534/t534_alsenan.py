"""T-534 on the training villa: Q-53's 39.49 m2 vs the T-511 census 35.4313 m2 reconciled flight by flight, the
drawing-derived stair marble / bed beside both, and FINISH V7 restated on each.

Reads only merged research and the candidate line index (no drawing, no workbook, no private file):
  A  Q-53 / T-086 scope   research/agents_t086/ALSENAN_FINISH_TABLE.csv (the ST-* rows; components from the T-086
                          builder: one tread per riser, printed width 1.20, full rise)
  B  candidate            research/agents_t507/out/LINE_INDEX_V3_0_57.json (ARCH_TAKEOFF_V3.0.57; V3.0.58 = T-507 adds
                          FIN.WP.ROOF lines only, arch_v3058 'nothing outside FIN.WP.ROOF / FIN.WP.ROOF_UPTURN moves'),
                          every FIN.MARBLE.TREAD / RISER / LANDING line bound to its drawn flight (T-412 / T-425 binding)
  C  drawing-derived      tread fronts and goings T-425 (MERGED, Checker re-measured), riser counts T-412 (section A-A,
                          Q-46 A; plans for D1 / E1 / round stair, Q-50 A cond), levels T-184, landings T-493 (MERGED)

  python3 -I research/agents_t534/t534_alsenan.py           # print the summary
  python3 -I research/agents_t534/t534_alsenan.py --write   # (re)write research/agents_t534/out/*
  python3 -I research/agents_t534/t534_alsenan.py --check   # recompute and compare with out/ (exit 1 on a difference)
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import stair_bed_reconcile as M  # noqa: E402
from engine.source import finish_materials_table as V1  # noqa: E402
from engine.source import finish_materials_table_v7 as V7  # noqa: E402

T086_CSV = ROOT / "research/agents_t086/ALSENAN_FINISH_TABLE.csv"
INDEX = ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
OUT = HERE / "out"
SCHEMA = "URBAN_T534_STAIR_BED_RECONCILE_V1"
STAIR_BED_CODES = ("FIN.MARBLE.TREAD", "FIN.MARBLE.RISER", "FIN.MARBLE.LANDING")
SURF = {"FIN.MARBLE.TREAD": M.TREAD, "FIN.MARBLE.RISER": M.RISER, "FIN.MARBLE.LANDING": M.LANDING}
TREAD_T = 0.03          # UP-STAIR-006 1.0.0 DEFAULT (owner 6E-A s.1): tread marble 30 mm -> visible riser (UP-STAIR-003)
RISER_BED_SOURCE = ("Q-45 answer B (owner 2026-10-19 21:40): item 1 asked 'marble stairs (treads, risers) __ cm'; "
                    "stairs 3 cm, 1:3 accepted; Q-53 C keeps 'treads, risers, landings' in the stair bed scope")

# storey rises (T-184 levels; section A-A counts, Q-46 A; round stair plan count, Q-50 A cond 'reconstructed, no
# section'): (rise m, source)
RISE = {"MS1": (4.50 / 27, "GF +1.00 -> 1F +5.50 = 4.50 / 27 risers (MS1-L 10 + MS1-T 5 + MS1-U 12, A-A)"),
        "MS2": (4.20 / 25, "1F +5.50 -> 2F +9.70 = 4.20 / 25 risers (MS2-L 12 + MS2-TR 1 + MS2-U 12, A-A)"),
        "D1": (0.70 / 4, "+0.30 -> +1.00 = 0.70 / 4 risers (GF plan)"),
        "E1": (0.85 / 5, "+0.15 -> +1.00 = 0.85 / 5 risers (GF plan)"),
        "RS": (4.50 / 28, "+1.00 -> +5.50 = 4.50 / 28 risers (12 + 11 + 5, Q-50 A cond, reconstructed, no section)")}

# ---------------------------------------------------------------- A: the Q-53 / T-086 figure ------------------------
# T-086 builder (research/agents_t086/alsenan_finish_table.py, stairs): steps = risers (one tread per riser), tread
# 0.30, printed width 1.20 (E1 2.80), full rise; landings printed 120 x 125 and 250 x 125. MS2-L's 13 risers are its
# 12 + the closing riser MS2-TR: re-keyed here (same m2), so that each key is one physical flight.
A_FLIGHTS = [  # key, csv id, treads, risers, rise key, width
    ("E1", "ST-E1", 5, 5, "E1", 2.80), ("D1", "ST-D1", 4, 4, "D1", 1.20),
    ("MS1-L", "ST-MS1-L", 10, 10, "MS1", 1.20), ("MS1-U", "ST-MS1-U", 12, 12, "MS1", 1.20),
    ("MS2-L", "ST-MS2-L", 12, 13, "MS2", 1.20), ("MS2-U", "ST-MS2-U", 12, 12, "MS2", 1.20)]
A_LANDINGS = [("MS1-LD", "ST-MS1-LD", 1.20, 1.25), ("MS2-LD", "ST-MS2-LD", 2.50, 1.25)]
A_HELD = ("ST-MS1-T", "ST-RS-C", "ST-RS-S", "ST-RS-A", "ST-RS-LD")


def scope_a():
    with open(T086_CSV, encoding="utf-8-sig") as fh:
        st = {r["id"]: r for r in csv.DictReader(fh) if r["id"].startswith("ST-")}
    parts = []
    for key, cid, nt, nr, rk, w in A_FLIGHTS:
        rise = RISE[rk][0]
        t, r = nt * 0.30 * w, nr * rise * w
        got = float(st[cid]["area_m2"])
        if abs(got - round(t + r, 4)) > 1e-4:
            raise M.ReconcileError(f"T-086 {cid}: printed {got} vs components {t + r:.6f}")
        parts.append(M.part(key, M.TREAD, t, M.CALCULATED, f"T-086 {cid}: {nt} treads x 0.30 x {w:g}",
                            components={"n": nt, "w": w, "d": 0.30}))
        if key == "MS2-L":      # 13 risers = MS2-L 12 + MS2-TR 1 (re-keyed, same m2)
            parts.append(M.part(key, M.RISER, 12 * rise * w, M.CALCULATED, f"T-086 {cid}: 12 of its 13 risers "
                                f"x {rise:.6f} x {w:g}", components={"n": 12, "w": w, "d": rise}))
            parts.append(M.part("MS2-TR", M.RISER, 1 * rise * w, M.CALCULATED, f"T-086 {cid}: its 13th riser "
                                f"(the closing riser) x {rise:.6f} x {w:g}", components={"n": 1, "w": w, "d": rise}))
        else:
            parts.append(M.part(key, M.RISER, r, M.CALCULATED, f"T-086 {cid}: {nr} risers x {rise:.6f} x {w:g}",
                                components={"n": nr, "w": w, "d": rise}))
    for key, cid, ln, wd in A_LANDINGS:
        got = float(st[cid]["area_m2"])
        if abs(got - ln * wd) > 1e-9:
            raise M.ReconcileError(f"T-086 {cid}: printed {got} vs {ln} x {wd}")
        parts.append(M.part(key, M.LANDING, ln * wd, M.CALCULATED, f"T-086 {cid}: printed {ln:g} x {wd:g}",
                            components={"n": 1, "w": wd, "d": ln}))
    for cid in A_HELD:
        status = st[cid]["status"]
        if status != "HELD":
            raise M.ReconcileError(f"T-086 {cid} is {status}, expected HELD")
    held = [{"key": cid, "reason": "HELD in T-086 (winders / round stair, Q-50 / Q-51 then open)"} for cid in A_HELD]
    return parts, held


# ---------------------------------------------------------------- B: the candidate (census 35.4313) ----------------
# every stair-bed line of V3.0.57 -> (drawn flight / landing key, note). Binding: T-412 CANDIDATE_BINDING (element ->
# drawn flight) as corrected by T-425 (1F F5 = MS1-T; 2F F1 = MS2-L again; GF F3 folded into GF F2) and T-493
# (the two landing bounds).
B_MAP = {
    "L-151d92470a81dd1c450b": ("MS1-L", "GF-R31F8AE flight 1 (T-425 9 treads)"),
    "L-ecc450d6cc865617f8f6": ("MS1-L", "riser HELD (count convention; A-A 10)"),
    "L-a4aeb32035d11684f1a2": ("D1", "GF-R31F8AE flight 2"),
    "L-8938aa3b25bf605e4b9d": ("D1", "riser HELD"),
    "L-e1eb8b9a7cb92508ccc9": ("MS1-U", "1F flight 3 (T-425 11 treads)"),
    "L-07e0855f961a839c1277": ("MS1-U", "riser HELD"),
    "L-65806b4d02d476603bc5": ("MS2-L", "1F flight 2"),
    "L-0f060e9951c28c4cf074": ("MS2-L", "riser HELD"),
    "L-79beb9688604887c59c5": ("MS2-L", "2F flight 1 = MS2-L seen again: EXCLUDED (T-425 double count)"),
    "L-7adf1ccd0c407b61221a": ("MS2-L", "2F flight 1 riser: EXCLUDED"),
    "L-07f00d5b0c4e1924aaf5": ("MS2-U", "2F flight 2 (10 treads; 11th going not drawn, HELD beside 0.345)"),
    "L-12f56cbfe750f8b30c41": ("MS2-U", "riser HELD"),
    "L-b4660de0ddd98ad0ffc2": ("MS1-T", "1F flight 5 = the winder turn seen through (T-425): HELD (S-9)"),
    "L-820baecf7f726b4d8f1e": ("MS1-T", "riser HELD"),
    "L-fa534ec5f9dc14947899": ("RS-C", "GF-RC99C2A flight 1, curved: HELD (Q-50 A cond)"),
    "L-913cda8eb6d73f6e28cc": ("RS-C", "riser HELD"),
    "L-6cf11c2d30387d0942b9": ("RS-C", "1F flight 1 = RS-C seen through the void: HELD bound (exposure)"),
    "L-1e36bc3c0893eeeb9c58": ("RS-C", "1F flight 1 riser HELD"),
    "L-89c84fdd4964dec8a323": ("RS-S", "GF-RC99C2A flight 2 (T-425 10 treads)"),
    "L-099fe9fcfa5667fb8b99": ("RS-S", "riser HELD"),
    "L-0ec429f1783f1f15e700": ("RS-S", "GF-RC99C2A flight 3: folded into flight 2, EXCLUDED"),
    "L-2efa4a4f4cc2aad9a2f2": ("RS-S", "flight 3 riser HELD (folded reading)"),
    "L-ea55ed317bc4de89aec1": ("RS-S", "1F flight 4 = RS-S seen from 1F: HELD bound (exposure, valued on GF)"),
    "L-24792292e996c57c52d9": ("RS-S", "1F flight 4 riser HELD"),
    "L-1dac5d9b574d7608d80d": ("RS-A", "GF-RC99C2A flight 4 (T-425 4 treads)"),
    "L-16e0c6682725260f28e7": ("RS-A", "riser HELD"),
    "L-5d338389185d72a6fb16": ("RS-A", "1F flight 6 = RS-A seen from 1F: HELD bound (exposure, valued on GF)"),
    "L-f24a09f1b4117814e4c8": ("RS-A", "1F flight 6 riser HELD"),
    "L-314c3ac6d45431b687c5": ("E1", "GF-COURT E1 treads (polygon; printed 4 x 0.30 x 2.80)"),
    "L-0afa7bd369ec489ebfc2": ("E1", "GF-COURT E1 risers"),
    "L-3dd82a576dce1beb4250": ("E1-LD", "GF-COURT E1 landing (polygon; printed 1.40 x 3.70)"),
    "L-8011889d84788553a6b1": ("1F-ARR", "1F arrival landing (Q-66 B; T-493 4.875 - 0.010 + 0.0575)"),
    "L-1983e89d8b619eade1db": ("GF-BOUND", "GF stair-room bound 0 .. 2.9225: holds no landing (T-493: treads, "
                                           "winders, divider, strip)"),
    "L-5d2be30dd8d2ffeacc42": ("2F-BOUND", "2F bound 0 .. 9.225: holds 2F-ARR 4.865 + MS2-LD 2.9325 (T-493)"),
}
# components of the released lines (drawn counts x width x depth); an area line beside them leaves a POLYGON residual
B_COMP = {"L-151d92470a81dd1c450b": (9, 1.15, 0.30), "L-a4aeb32035d11684f1a2": (3, 1.15, 0.30),
          "L-e1eb8b9a7cb92508ccc9": (11, 1.15, 0.30), "L-65806b4d02d476603bc5": (11, 1.15, 0.30),
          "L-07f00d5b0c4e1924aaf5": (10, 1.15, 0.30), "L-89c84fdd4964dec8a323": (10, 1.15, 0.30),
          "L-1dac5d9b574d7608d80d": (4, 1.15, 0.30), "L-314c3ac6d45431b687c5": (4, 2.80, 0.30),
          "L-0afa7bd369ec489ebfc2": (5, 2.80, RISE["E1"][0] - TREAD_T), "L-3dd82a576dce1beb4250": (1, 3.70, 1.40)}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def scope_b():
    d = json.loads(INDEX.read_text(encoding="utf-8"))
    if d.get("candidate_version") != "ARCH_TAKEOFF_V3.0.57":
        raise M.ReconcileError(f"STALE_CANDIDATE: {d.get('candidate_version')}")
    lines = [ln for ln in d["lines"] if ln["item_code"] in STAIR_BED_CODES]
    ids = {ln["line_id"] for ln in lines}
    if ids != set(B_MAP):
        raise M.ReconcileError(f"STALE_CANDIDATE: stair-bed lines unmapped {sorted(ids - set(B_MAP))} / "
                               f"absent {sorted(set(B_MAP) - ids)}")
    parts, held, table = [], [], []
    for ln in sorted(lines, key=lambda x: (B_MAP[x["line_id"]][0], x["item_code"], x["line_id"])):
        key, note = B_MAP[ln["line_id"]]
        s = SURF[ln["item_code"]]
        rec = {"line_id": ln["line_id"], "item_code": ln["item_code"], "element_id": ln["element_id"],
               "class": ln["class"], "net": ln["measured_net"], "held_low": ln["held_low"],
               "held_high": ln["held_high"], "key": key, "note": note}
        table.append(rec)
        if ln["class"] == "RELEASED":
            c = B_COMP.get(ln["line_id"])
            comp = None if c is None else {"n": c[0], "w": c[1], "d": c[2]}
            parts.append(M.part(key, s, ln["measured_net"], M.MEASURED, f"{ln['line_id']} RELEASED",
                                components=comp))
        else:
            held.append({"key": key, "surface": s, "line_id": ln["line_id"], "class": ln["class"],
                         "bound": [ln["held_low"], ln["held_high"]], "note": note})
            if ln["class"] == "HELD":       # a HELD line keeps the figure PARTIAL (never 0); EXCLUDED is not stair
                parts.append(M.part(f"{key}#{ln['line_id']}", s, None, M.HELD, f"{ln['line_id']} HELD",
                                    f"candidate line HELD: {note}", ln["held_high"]))
    return parts, held, table, d


# ---------------------------------------------------------------- C: drawing-derived (this task) -------------------
C_FLIGHTS = [
    dict(id="MS1-L", treads=9, risers=10, going=0.30, width=1.15, rise=RISE["MS1"][0],
         src="T-425 9 straight tread fronts (10th front 485 = first winder, in MS1-T); A-A 10 risers (T-412)"),
    dict(id="MS1-T", held="WINDER_TURN_HELD (owner S-9: never generate winders; A-A 5 risers vs plans 4 wedges, "
                          "C-ST-3 / Q-51 A cond)", beside_tread=1.495,
         src="T-412 / T-425: the candidate 1F F5 reading 1.495 m2 beside, not a measurement"),
    dict(id="MS1-U", treads=11, risers=12, going=0.30, width=1.15, rise=RISE["MS1"][0],
         src="T-425 11 fronts A92 .. ABE (ABE's going on ST p.4); A-A 12 risers"),
    dict(id="MS2-L", treads=11, risers=12, going=0.30, width=1.15, rise=RISE["MS2"][0],
         src="T-425 / T-412 12 fronts AC0 .. A97 (A97 = landing edge); A-A 12 risers"),
    dict(id="MS2-TR", treads=0, risers=0, risers_held=1, going=0.30, width=1.15, rise=RISE["MS2"][0],
         risers_held_reason="CLOSING_RISER_POSITION_HELD (A-A has it; plans: 12B4 / 12B5 at x 1.25 vs the 2F "
                            "diagonal pair, Q-ST-11; T-412 / T-493)",
         src="A-A closing riser between the split MS2-LD halves; length 1.15 (y 3.85 .. 5.00, T-493)"),
    dict(id="MS2-U", treads=10, risers=12, going=0.30, width=1.15, rise=RISE["MS2"][0], treads_held=1,
         treads_held_reason="TREAD_GOING_NOT_DRAWN (11th front 1386 drawn, its rear = the 2F floor edge on no sheet; "
                            "T-425)",
         src="T-425 11 fronts 135B .. 1386, 10 goings drawn; A-A 12 risers"),
    dict(id="D1", treads=3, risers=4, going=0.30, width=1.15, rise=RISE["D1"][0],
         src="T-425 / T-412 4 fronts 481 .. 490 (490 = GF hall floor edge); 4 risers (plan)"),
    dict(id="E1", treads=4, risers=5, going=0.30, width=2.80, rise=RISE["E1"][0],
         src="T-412 / T-490 5 fronts 36E .. 30A (30A = landing edge), printed 2.80; 5 risers (plan)"),
    dict(id="RS-C", held="CURVED_PART_HELD (Q-50 A cond: curved part HELD; RFI-S27)", beside_tread=4.094413,
         beside_riser=round(12 * 1.15 * (RISE["RS"][0] - TREAD_T), 6),
         src="T-412 12 radial fronts; candidate reading 4.094413 m2 beside"),
    dict(id="RS-S", treads=10, risers=11, going=0.30, width=1.15, rise=RISE["RS"][0],
         src="T-425 10 fronts B43 .. B4D (B4D = RS-LD edge, 1F reading); 11 risers (plan, Q-50 A cond)"),
    dict(id="RS-A", treads=4, risers=5, going=0.30, width=1.15, rise=RISE["RS"][0],
         src="T-425 4 fronts B59 .. B5C + floor edge D22; 5 risers (plan, Q-50 A cond)"),
]
C_LANDINGS = [
    dict(id="MS1-LD", length=1.25, width=1.15, src="T-493 F-3: own nosing x 1.25 to B16; A92 y 3.85 .. 5.00"),
    dict(id="1F-ARR", area_m2=4.9225, src="T-493: printed 4.875 - 0.010 + 0.0575 nosing band (= line L-8011889d)"),
    dict(id="MS2-LD", area_m2=2.9325, src="T-493 F-4: W 1.25 x 1.196 = 1.4950 + E 1.25 x 1.15 = 1.4375"),
    dict(id="2F-ARR", area_m2=4.8650, src="T-493 F-1: 2.50 x 1.90 + 1.15 x 0.10 (Q-70 A, condition met T-129)"),
    dict(id="RS-LD", area_m2=1.3525, src="T-493 F-2: 1.20 x 1.15 - column 3008 0.55 x 0.05"),
    dict(id="E1-LD", length=1.40, width=3.70, src="printed 1.40 x 3.70 (T-490 / T-493)"),
    dict(id="GF-HALL", area_m2=4.8050, material_held="FLOOR_OR_LANDING, no finish source (R-T490-1, RFI-B-A12)",
         src="T-418 / T-493 foot of MS1-L / top of D1 at +1.00"),
    dict(id="GF-LOBBY", area_m2=1.3225, material_held="FLOOR_OR_LANDING, no finish source (R-T490-1, RFI-B-A12)",
         src="T-418 / T-493 foot of D1 at +0.30"),
]


def scope_c():
    parts = []
    for f in C_FLIGHTS:
        parts += M.flight_parts(f, TREAD_T)
    for l in C_LANDINGS:
        parts.append(M.landing_part(l))
    return M.check_once(parts)


# ---------------------------------------------------------------- reconciliation causes ----------------------------
RISER_HELD_ON_B = ("candidate riser line HELD (STAIR_RISER_COUNT_CONVENTION / RISER_NOT_ESTABLISHED in "
                   "arch_measure); counts since settled by T-412 (A-A / plans), not integrated")
SCOPE_AB = {
    ("MS1-L", M.RISER): RISER_HELD_ON_B, ("MS1-U", M.RISER): RISER_HELD_ON_B, ("MS2-L", M.RISER): RISER_HELD_ON_B,
    ("MS2-TR", M.RISER): "candidate has no closing-riser line (inside MS2-L riser lines, HELD); position HELD",
    ("MS2-U", M.RISER): RISER_HELD_ON_B, ("D1", M.RISER): RISER_HELD_ON_B,
    ("MS1-LD", M.LANDING): "no candidate line (T-493 F-3: silent omission; the GF partition counts the +0.30 lobby "
                           "under it); T-502 queued",
    ("MS2-LD", M.LANDING): "only inside the HELD bound L-5d2be30d (T-493 F-4); T-502 queued",
    ("RS-S", M.TREAD): "T-086 held the round stair (Q-50 open then); Q-50 A cond: straight flights CALCULATED, "
                       "valued by T-425 / T-429",
    ("RS-A", M.TREAD): "as RS-S",
    ("E1-LD", M.LANDING): "T-086 carried no entrance landing (top E1 step counted as a 5th tread instead)",
    ("1F-ARR", M.LANDING): "Q-66 B (answered 16:23 after T-086): landing marble, own element; Q-66 text: stair "
                           "marble 39.49 + 4.875 = 44.365 m2",
}
POLY = {("E1", M.TREAD): "candidate polygon 3.3594 vs printed 4 x 0.30 x 2.80 = 3.3600 (T-425 s.3.2 AGREE)",
        ("E1-LD", M.LANDING): "candidate polygon 5.1794 vs printed 1.40 x 3.70 = 5.1800 (T-490 AGREE)"}
POLY_AC = dict(POLY)
POLY_AC[("MS2-LD", M.LANDING)] = ("T-086 printed 2.50 x 1.25 = 3.1250 vs T-493 drawn halves W 1.25 x 1.196 = 1.4950 + E "
                                  "1.25 x 1.15 = 1.4375: the landing ends at the arriving nosings A97 (y 3.80) / 135B "
                                  "(y 3.85), not 1.25 from the wall")
SCOPE_BC = {
    ("MS1-L", M.RISER): RISER_HELD_ON_B, ("MS1-U", M.RISER): RISER_HELD_ON_B, ("MS2-L", M.RISER): RISER_HELD_ON_B,
    ("MS2-U", M.RISER): RISER_HELD_ON_B, ("D1", M.RISER): RISER_HELD_ON_B, ("RS-S", M.RISER): RISER_HELD_ON_B,
    ("RS-A", M.RISER): RISER_HELD_ON_B,
    ("MS1-LD", M.LANDING): SCOPE_AB[("MS1-LD", M.LANDING)], ("MS2-LD", M.LANDING): SCOPE_AB[("MS2-LD", M.LANDING)],
    ("2F-ARR", M.LANDING): "only inside the HELD bound L-5d2be30d (T-493 F-1); T-502 queued",
    ("RS-LD", M.LANDING): "no candidate line (T-493 F-2; deducted from 1F porcelain as R04); T-502 queued",
}
SCOPE_AC = dict(SCOPE_BC)
SCOPE_AC.update({("MS2-TR", M.RISER): "T-086 counted the closing riser in MS2-L (13); drawing: position HELD",
                 ("RS-S", M.TREAD): SCOPE_AB[("RS-S", M.TREAD)], ("RS-A", M.TREAD): SCOPE_AB[("RS-A", M.TREAD)],
                 ("E1-LD", M.LANDING): SCOPE_AB[("E1-LD", M.LANDING)],
                 ("1F-ARR", M.LANDING): SCOPE_AB[("1F-ARR", M.LANDING)]})
SCOPE_AC.pop(("MS1-LD", M.LANDING))
SCOPE_AC.pop(("MS2-LD", M.LANDING))

CAUSE_MEANING = {
    M.TREAD: {"COUNT": "one tread per riser (T-086) vs the drawn tread fronts (the riser onto a landing / floor has "
                       "no tread; MS2-U 11th going not drawn)",
              "WIDTH": "printed stair width 1.20 vs the drawn front edge 1.150 (T-412 / T-425 ENGINE_RIGHT)",
              "DEPTH_OR_HEIGHT": "going"},
    M.RISER: {"COUNT": "riser count", "WIDTH": "printed 1.20 vs drawn 1.150",
              "DEPTH_OR_HEIGHT": "full rise (T-086) vs visible riser = rise - 0.030 tread marble (UP-STAIR-003 / 006)"},
    M.LANDING: {"COUNT": "-", "WIDTH": "printed landing width vs drawn polygon",
                "DEPTH_OR_HEIGHT": "printed landing depth vs drawn polygon (T-493 nosing / strip convention)"},
}


def v7_rows(parts, prefix):
    """FINISH V7 on determinate bed parts: one area element per part. V1 gives STAIR_FLIGHT and STAIR_LANDING the same
    bed (0.03) and mix (1:3) (asserted), so an area-given part uses the STAIR_LANDING row form."""
    ov = V1.OWNER_VALUES
    assert ov["bed_m"][V1.STAIR_FLIGHT] == ov["bed_m"][V1.STAIR_LANDING] == (0.03, 0.03)
    assert ov["mix"][V1.STAIR_FLIGHT] == ov["mix"][V1.STAIR_LANDING] == "1:3"
    els = [{"id": f"{prefix}:{p['key']}:{p['surface']}", "floor": "STAIR", "kind": V7.STAIR_LANDING,
            "area_m2": p["m2"]} for p in parts if p["status"] != M.HELD]
    t = V7.table(els)
    pr = t["project"]
    keys = ("area_m2", "mortar_m3_low", "cement_bags_low", "sand_m3_low")
    return {k: M._r(pr.get(k)) for k in keys} | {
        "cement_bags_procurement_allowance": M._r(sum(r["bed_purchasing_allowance"]["cement_bags_low"]
                                                      for r in t["rows"])),
        "sand_m3_procurement_allowance": M._r(sum(r["bed_purchasing_allowance"]["sand_m3_low"] for r in t["rows"])),
        "rule": t["rows"][0]["stair_rate"]["rule_id"] if t["rows"] else None, "rows": len(els)}


def build():
    a_parts, a_held = scope_a()
    b_parts, b_held, b_table, idx = scope_b()
    c_parts = scope_c()
    c_bed = M.bed_parts(c_parts, RISER_BED_SOURCE)
    c_bed_nosrc = M.bed_parts(c_parts, None)
    ab = M.reconcile(M.figure(a_parts), M.figure(b_parts), SCOPE_AB, POLY)
    bc = M.reconcile(M.figure(b_parts), M.figure(c_parts), SCOPE_BC, POLY)
    ac = M.reconcile(M.figure(a_parts), M.figure(c_parts), SCOPE_AC, POLY_AC)
    per_flight = {}
    for tag, parts in (("A_q53_t086", a_parts), ("B_candidate", b_parts), ("C_drawing", c_parts)):
        for p in parts:
            if p["status"] == M.HELD:
                continue
            k = p["key"].split("#")[0]
            per_flight.setdefault(k, {}).setdefault(tag, {s: 0.0 for s in M.SURFACES})[p["surface"]] += p["m2"]
    flights = []
    for k in sorted(per_flight):
        row = {"flight": k}
        for tag in ("A_q53_t086", "B_candidate", "C_drawing"):
            v = per_flight[k].get(tag)
            row[tag] = None if v is None else {s: M._r(x) for s, x in v.items()} | {"sum": M._r(sum(v.values()))}
        flights.append(row)
    out = {
        "schema": SCHEMA, "guard_class": "UNWIRED_RESEARCH", "released_quantities_changed": 0,
        "inputs": {"t086_csv": sha(T086_CSV), "line_index_v3_0_57": sha(INDEX),
                   "candidate": idx["candidate_version"],
                   "candidate_of_record_note": "V3.0.58 (T-507) adds FIN.WP.ROOF lines only: stair lines = V3.0.57"},
        "constants": {"tread_marble_t_m": TREAD_T, "tread_t_source": "UP-STAIR-006 1.0.0 DEFAULT",
                      "rises": {k: [M._r(v[0], 9), v[1]] for k, v in RISE.items()},
                      "riser_bed_source": RISER_BED_SOURCE},
        "A_q53_t086": {"totals": M.totals(a_parts), "held": a_held},
        "B_candidate": {"totals": M.totals(b_parts), "held_lines": b_held, "lines": b_table},
        "C_drawing": {"marble": M.totals(c_parts), "bed_with_q45_riser_source": M.totals(c_bed),
                      "bed_without_riser_source": M.totals(c_bed_nosrc), "parts": c_parts},
        "flight_table": flights,
        "reconcile": {"A_to_B": ab, "B_to_C": bc, "A_to_C": ac},
        "cause_meaning": CAUSE_MEANING,
        "v7": {"on_candidate_B": v7_rows(b_parts, "B"), "on_drawing_C_bed": v7_rows(c_bed, "C")},
    }
    return out


def write(o):
    OUT.mkdir(exist_ok=True)
    (OUT / "T534_STAIR_BED_RECONCILE.json").write_text(json.dumps(o, indent=1, sort_keys=True) + "\n",
                                                        encoding="utf-8")
    with open(OUT / "FLIGHT_TABLE_T534.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["flight", "scope", "tread_m2", "riser_m2", "landing_m2", "sum_m2"])
        for r in o["flight_table"]:
            for tag in ("A_q53_t086", "B_candidate", "C_drawing"):
                v = r[tag]
                w.writerow([r["flight"], tag] + (["", "", "", ""] if v is None else
                                                 [v["TREAD"], v["RISER"], v["LANDING"], v["sum"]]))
    with open(OUT / "RECONCILE_A_TO_B_T534.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["key", "surface", "a_m2", "b_m2", "diff_m2", "cause", "cause_m2", "note"])
        for r in o["reconcile"]["A_to_B"]["rows"]:
            for c in r["causes"] or [{"cause": "", "m2": 0.0, "note": ""}]:
                w.writerow([r["key"], r["surface"], r["a_m2"], r["b_m2"], r["diff_m2"], c["cause"], c["m2"],
                            c["note"] or ""])


def main(argv):
    o = build()
    if "--write" in argv:
        write(o)
    if "--check" in argv:
        old = json.loads((OUT / "T534_STAIR_BED_RECONCILE.json").read_text(encoding="utf-8"))
        new = json.loads(json.dumps(o, sort_keys=True))
        if old != new:
            print("T534 CHECK FAIL: out/ differs from the recomputation")
            return 1
        print("T534 CHECK PASS")
    s = o["reconcile"]["A_to_B"]
    print(f"A (Q-53 / T-086) {s['a_m2']} -> B (candidate) {s['b_m2']}: {s['diff_m2']} m2; by cause {s['by_cause']}")
    print(f"C marble {o['C_drawing']['marble']['print']}; bed {o['C_drawing']['bed_with_q45_riser_source']['print']}")
    print(f"V7 on B {o['v7']['on_candidate_B']}")
    print(f"V7 on C {o['v7']['on_drawing_C_bed']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
