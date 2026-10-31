"""T-398 Alsenan: stairs, domes and the pool pump room of the T-385 r2 UNRESOLVED components (SD-STAIR, SD-DOME,
PL-PUMP) reconciled piece by piece against the freelancer (research only; development villa, not an accuracy claim).

    python3 -I research/agents_t398/t398_alsenan.py --freelancer <private>/concrete_rebar.xlsx [--out <private dir>]

Engine side (tracked, no private data): the 22 STAIR / DOME / POOL lines of the committed V3.0.21 concrete file
(research/agents_t332/CANDIDATE_V3021_CONCRETE_LINES.json), asserted equal (ids, states, valued m3) to the V3.0.29
binding of record (research/agents_t387/BINDING_T387.csv); pieces from the merged T-258 r2 ledger
(research/agents_t258/LEDGER_T258.csv), every line = the sum of its closable pieces (asserted). Drawn figures re-read
from 'ST7757 dxf.dxf' (9f9d1179) this run, by handle (see DRAWN below and T-398_STAIR_DOME_PUMP.md).
Freelancer side: his rows read from the private workbook copy at run time only; the per-row table goes to --out (must
be outside the repository); the tracked summary carries engine figures and cause terms in m3 only.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t398_rules as R  # noqa: E402

LINES = ROOT / "research" / "agents_t332" / "CANDIDATE_V3021_CONCRETE_LINES.json"
BINDING = ROOT / "research" / "agents_t387" / "BINDING_T387.csv"
LEDGER = ROOT / "research" / "agents_t258" / "LEDGER_T258.csv"

# ---- drawn / printed figures (own read of 'ST7757 dxf.dxf' this run; m)
DRAWN = {
    # ST p.5 MS2-L riser lines 646 (y 45.198) .. 632 (y 48.498): run 3.300; riser lines 1.150 long, lane 1.20
    # (R-STAIR-LANE-1, T-258 r2); 12 risers r = 4.20 / 25 (section A-A); 'T 16'.  MS2-U 62F .. 644 the same run.
    # ST p.4 MS1-U 25B (y 48.448) .. 459 (y 45.148): run 3.300; r = 4.50 / 27.
    "run": 3.30, "lane": 1.20, "going": 0.30, "waist": 0.16, "r_ms1": 4.50 / 27, "r_ms2": 4.20 / 25,
    # candidate lengths a 'flight length' of his could be (R-T398-3): run; sloped run (sec x 3.30 at r 0.168);
    # stair hall B23 inner face 5E1 (y 45.348) -> north edge 5C0 (y 49.648) 4.30; outer face 5E4 (44.898) 4.75;
    # run + half landing (632 -> 5C0 1.15) 4.45; run + arrival landing (T-234 GF-077 1.55 + B20 0.40) 5.25
    "flight_length_candidates": (3.30, 3.782186, 4.30, 4.75, 4.45, 5.25),
    # landing plates (T-258 r2 / Checker): MS1-LD 1.20 x 1.20; MS2-LD-W 1.30 x 1.15 = 1.495; MS2-LD-E 1.20 x 1.20;
    # RS-LD 1.3525; MS1-T-SLAB 1.30 x 1.15 = 1.495 (held)
    "landing_area_candidates": (1.44, 1.495, 2.935, 1.3525),
    # ST p.7 DETAIL OF DOME: chord DIM 1A38 '442', rise 1A6D '190', shell 19B1 '10'
    "dome": (4.42, 1.90, 0.10),
    # ST-02 developed lengths (own read p.4): straight RS-S 11 tread lines 2BA .. 2C4 (3.000), RS-LD 1.150 (2C4 -> 289),
    # RS-A 1.200 (2C8 .. 315); curved part 13 radial tread lines 2DF .. 2EA (1.150 long) between S-OPENING arcs 2DE
    # r 1.531 and 2DD r 2.781 about (63.879, 40.778): arc lengths 2.493 / 4.035 m
    "st02_straight": 3.00 + 1.15 + 1.20, "st02_curve_inner": 2.493, "st02_curve_outer": 4.035,
    "st02_curve_centre": 4.1077 / 1.25,           # CAD tread area 4.1077 m2 (T-258) / drawn tread width 1.25
}

# freelancer rows (sheet index, row) -> component binding by his own printed unit (count x unit, R-T398-6)
HIS = {"ENTRANCE": (6, 11), "STAIR2": (6, 12), "DOME": (6, 13), "FLIGHTS": (6, 20), "LANDINGS": (6, 21),
       "PUMP_WALLS": (7, 13), "PUMP_FLOOR": (7, 15)}
HIS_TOTALS = {6: [(6, 16), (6, 23)], 7: [(7, 16)]}
SUMMARY_ROWS = {"STAIR_DOME": 22, "POOL": 23}


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def read_his(path):
    import openpyxl  # private step only
    wb = openpyxl.load_workbook(path, data_only=True)
    out = {}
    for k, (si, r) in HIS.items():
        ws = wb.worksheets[si]
        b, c, d, e, f = (ws.cell(r, x).value for x in (2, 3, 4, 5, 6))
        net = ws.cell(r, 7 if si == 6 else 9).value
        if not all(_num(x) for x in (b, c, d, e, f, net)):
            raise SystemExit(f"his row {si}:{r} lacks a printed dimension, unit or count")
        if abs(b * c * d - e) > 1e-6 or abs(e * f - net) > 1e-6:
            raise SystemExit(f"his row {si}:{r}: unit or net not equal to his own dimensions x count")
        out[k] = {"w": float(b), "L": float(c), "t": float(d), "unit": float(e), "count": int(f), "net": float(net)}
    tot = {si: sum(float(wb.worksheets[s].cell(r, 7 if s == 6 else 9).value) for s, r in rows)
           for si, rows in HIS_TOTALS.items()}
    fam = {k: float(wb.worksheets[0].cell(r, 5).value) for k, r in SUMMARY_ROWS.items()}
    return out, tot, fam


def engine():
    doc = json.loads(LINES.read_text(encoding="utf-8"))
    lines = {l["line_id"]: l for l in doc["lines"] if l["item_code"].split(".")[-1] in ("STAIR", "DOME", "POOL")}
    bind = {r["line_id"]: r for r in csv.DictReader(BINDING.open(encoding="utf-8"))}
    for lid, l in lines.items():
        b = bind[lid]
        v = l["measured_net"]
        if (v is None) != (b["valued_m3"] == "") or (v is not None and abs(v - float(b["valued_m3"])) > 1e-6):
            raise SystemExit(f"{lid}: V3.0.21 file and V3.0.29 binding differ")
    led = {r["id"]: r for r in csv.DictReader(LEDGER.open(encoding="utf-8"))}
    return lines, led


def val(led, pid):
    return float(led[pid]["value_m3"])


def build(his, his_tot, his_fam):
    lines, led = engine()
    lv = {k: (v["measured_net"] if v["measured_net"] is not None else None) for k, v in lines.items()}
    # every closable line = the sum of its ledger pieces (pieces bound to their line once)
    PIECES_OF = {"L-e37d81a8be8e0aa0010c": ["ST01-MS1-LD", "ST01-MS1-U"], "L-67e4b0485135f84acc46": ["ST01-MS2-L"],
                 "L-bb0e57b1948175a3d5b8": ["ST01-MS2-U"], "L-2416e65f053a14199cfc": ["ST01-MS2-LD-W", "ST01-MS2-LD-E"],
                 "L-056402f98a6dbbcde0a0": ["ST02-RS-S", "ST02-RS-LD", "ST02-RS-A"],
                 "L-85f64587588af8537b4b": ["ST01b-D1-STEPS"],
                 "L-8ea34765d16b54898140": ["DOME-A-SHELL"], "L-fffa895ed96b9d6a682c": ["DOME-B-SHELL"]}
    for lid, ps in PIECES_OF.items():
        if abs(sum(val(led, p) for p in ps) - lv[lid]) > 2e-6:
            raise SystemExit(f"{lid}: line {lv[lid]} != pieces {ps}")
    line_of = {p: lid for lid, ps in PIECES_OF.items() for p in ps}

    def V(pid):                                            # a valued piece (value from its line's ledger piece)
        return {"id": pid, "line": line_of[pid], "state": "VALUED", "m3": val(led, pid)}

    def H(pid, line, lo=None, hi=None):
        return {"id": pid, "line": line, "state": "HELD", "low": lo, "high": hi}

    def X(pid, line):
        return {"id": pid, "line": line, "state": "EXCLUDED"}

    # ---- R-T398-1 ownership census of every stair / dome piece (one solid, one owner)
    owners = [{"id": r["id"], "owners": [r["owner_line"]]} for r in led.values()
              if r["owner_line"] and r["cls"] != "BESIDE"]
    own = R.ownership(owners)
    elsewhere = {k: v for k, v in own.items() if v != "STAIR" and v != "DOME"}

    # ---- flights ST-01 (his FLIGHTS row: count 4 x unit; 3 units against the three valued flights)
    F = his["FLIGHTS"]
    fl = [("ST01-MS1-U", DRAWN["r_ms1"], 12, ["ST01-MS1-U-HEAD"], 0.030000),
          ("ST01-MS2-L", DRAWN["r_ms2"], 12, ["ST01-MS2-L-FOOT"], 0.030171),
          ("ST01-MS2-U", DRAWN["r_ms2"], 12, ["ST01-MS2-U-HEAD"], 0.030240)]
    agg = {}
    hand = {}
    for pid, r, n, owned, wedge in fl:
        g = R.flight(n, r, DRAWN["going"], DRAWN["lane"], DRAWN["run"], DRAWN["waist"])
        ded = [val(led, o) for o in owned] + [wedge]
        hand[pid] = {"steps": g["steps_m3"], "waist": g["waist_m3"], "owned_elsewhere": R.r6(sum(ded)),
                     "net": R.r6(g["gross_m3"] - sum(ded)), "ledger": val(led, pid)}
        if abs(hand[pid]["net"] - val(led, pid)) > 2e-6:
            raise SystemExit(f"{pid}: hand {hand[pid]['net']} != ledger {val(led, pid)}")
        for t in R.plate_terms(g["gross_m3"], ded, DRAWN["run"], DRAWN["lane"], F["L"], F["w"], F["t"],
                               DRAWN["flight_length_candidates"]):
            a = agg.setdefault(t["term"], {"term": t["term"], "m3": 0.0, "traced": t["traced"]})
            a["m3"] = R.r6(a["m3"] + t["m3"])
            a["traced"] = a["traced"] and t["traced"]
    near_len = min(DRAWN["flight_length_candidates"], key=lambda x: abs(x - F["L"]))
    Lc = his["LANDINGS"]
    land_terms = {}
    for pid, area in (("MS1-LD", 1.44), ("MS2-LD", 2.935)):
        for t in R.landing_terms(area, DRAWN["waist"], Lc["w"] * Lc["L"], Lc["t"], DRAWN["landing_area_candidates"]):
            a = land_terms.setdefault(t["term"], {"term": t["term"], "m3": 0.0, "traced": t["traced"]})
            a["m3"] = R.r6(a["m3"] + t["m3"])
            a["traced"] = a["traced"] and t["traced"]
    D = his["DOME"]
    cap = R.cap_shell(*DRAWN["dome"])
    if abs(cap["V_m3"] - val(led, "DOME-A-SHELL")) > 2e-6:
        raise SystemExit("dome shell hand figure differs from the line")
    dome_drawn_areas = (cap["outer_area_m2"], cap["equiv_area_m2"])
    dome_terms = {}
    for _ in range(2):
        for t in R.shell_terms(cap["V_m3"], DRAWN["dome"][2], D["w"] * D["L"], D["t"], dome_drawn_areas):
            a = dome_terms.setdefault(t["term"], {"term": t["term"], "m3": 0.0, "traced": t["traced"]})
            a["m3"] = R.r6(a["m3"] + t["m3"])

    E, S2 = his["ENTRANCE"], his["STAIR2"]
    st02_len_c = DRAWN["st02_straight"] + DRAWN["st02_curve_centre"]
    st02_len_o = DRAWN["st02_straight"] + DRAWN["st02_curve_outer"]
    comps = [
        {"id": "SD-ST01-FLIGHTS", "element": "ST-01 straight flights MS1-U, MS2-L, MS2-U (waist T 16 + steps, net)",
         "pieces": [V("ST01-MS1-U"), V("ST01-MS2-L"), V("ST01-MS2-U")], "his_m3": 3 * F["unit"],
         "his_unit": "flights row: 3 of his 4 counted flights", "verdict": "ENGINE_RIGHT",
         "terms": list(agg.values()),
         "cause": "drawn flight = 12 step triangles + waist T 16 / cos on the drawn 3.300 run x lane 1.20, heads / foot "
                  "inside B20 / B23 owned by the beams (billed full depth: P-C:BEAMS:GF:BAND0043.2 0.990, "
                  "P-C:BEAMS:1F:BAND0031.2 1.11375) and the Q-62 A wedges owned by the landing / slab; his one-plate "
                  f"thickness on the drawn run is THICKNESS_BASIS; his flight length matches no drawn length (nearest "
                  f"drawn {near_len:.3f} m: run + arrival landing) -> LENGTH UNTRACED",
         "evidence": "ST p.4 25B .. 459, p.5 646 .. 632 / 62F .. 644, 5E1 / 5E4 / 5C0; T-258 r2; T-189; Q-19, Q-47 A, Q-62 A"},
        {"id": "SD-ST01-MS1L", "element": "ST-01 MS1-L straight + winder treads MS1-T (GF -> +3.50)",
         "pieces": [H("ST01-MS1-L", "L-7863355dfcb68a681d2d", 0.863029, 1.054813),
                    H("ST01-MS1-T", "L-7863355dfcb68a681d2d", 0.12, 0.13)],
         "his_m3": F["unit"], "his_unit": "flights row: 1 of his 4 counted flights", "verdict": "HELD",
         "cause": "C-ST-4 riser-count CONFLICT (structural 12 + 3 winders vs architectural 10 + section) and the "
                  "winder soffit not drawn (C-ST-3): held range, never a midpoint, never 0",
         "evidence": "RFI-A04, RFI-S24; T-258 r2"},
        {"id": "SD-ST01-LANDINGS", "element": "ST-01 half landings MS1-LD (+3.50) and MS2-LD (+7.516 / +7.684, two plates)",
         "pieces": [V("ST01-MS1-LD"), V("ST01-MS2-LD-W"), V("ST01-MS2-LD-E")], "his_m3": 2 * Lc["unit"],
         "his_unit": "landings row: 2 of his 3 counted landings", "verdict": "ENGINE_RIGHT",
         "terms": list(land_terms.values()),
         "cause": "printed plate thickness T 16 against his landing thickness printed nowhere (THICKNESS_BASIS); "
                  "drawn plates 1.44 and 2.935 m2 (MS2-LD spans both lanes 5E3 -> 5D4 2.50 m) against his one "
                  "landing area that no drawn plate reproduces (AREA UNTRACED)",
         "evidence": "ST p.4 / p.5; Checker 2026-10-22 17:18 and T-187 Gate B"},
        {"id": "SD-ST01-TURNS", "element": "ST-01 slab under the winder turn MS1-T-SLAB + turn riser MS2-TR",
         "pieces": [H("ST01-MS1-T-SLAB", "L-7863355dfcb68a681d2d", 0.2304, 0.2496),
                    H("ST01-MS2-TR", "L-659243ed9fc2831c3ae8")],
         "his_m3": Lc["unit"], "his_unit": "landings row: 1 of his 3 counted landings", "verdict": "HELD",
         "cause": "turn soffit and the two-plate junction are not drawn (C-ST-3): held",
         "evidence": "RFI-S24, RFI-S25"},
        {"id": "SD-D1-STEPS", "element": "stair-hall flight D1 steps (+0.30 -> +1.00, 4 risers)",
         "pieces": [V("ST01b-D1-STEPS")], "his_m3": 0.0, "his_unit": "no row of his", "verdict": "ENGINE_RIGHT",
         "cause": "drawn element he omits: 4 riser lines 1C4 .. 1C7 (1.150) on ST p.3 and ARCH GF 482 .. 48A, "
                  "4 triangles 0.126 less the arrival part inside ground-slab panel GS-08 0.025714",
         "evidence": "T-258 r2 ST01b-D1-STEPS"},
        {"id": "SD-D1-WAIST", "element": "stair-hall flight D1 waist / support",
         "pieces": [H("ST01b-D1-WAIST", "L-821032bc04a0b0d02133")], "his_m3": 0.0, "his_unit": "no row of his",
         "verdict": "HELD", "cause": "no thickness or support printed: waist or steps on fill (RFI-S26)",
         "evidence": "RFI-S26"},
        {"id": "SD-ST03-E1", "element": "entrance flight ST-03 E1 (+0.15 -> +1.00, 5 risers x 2.80)",
         "pieces": [H("ST03-E1", "L-061e18cf35a4b6b33d68")], "his_m3": E["net"], "his_unit": "entrance row",
         "verdict": "HELD",
         "cause": "waist thickness not printed (S-9 / RFI-S26): line held; steps 0.355017 DRAWING-CONFIRMED named, "
                  f"not booked. His width {'= the drawn 2.80 riser length' if abs(E['L'] - 2.80) < 0.01 or abs(E['w'] - 2.80) < 0.01 else 'not the drawn 2.80'}; "
                  "his other plan dimension is not the drawn 1.200 run",
         "evidence": "ST p.3 18A .. 179; ARCH GF dim 2800; section B-B"},
        {"id": "SD-ST02", "element": "round stair ST-02: straight RS-S + corner landing RS-LD + RS-A (valued) and "
                                     "the curved part RS-C, its soffit, CA junction, 2CC pair (held)",
         "pieces": [V("ST02-RS-S"), V("ST02-RS-LD"), V("ST02-RS-A"), H("ST02-HELD", "L-b6b0354b7842f0ed6e41")],
         "his_m3": S2["net"], "his_unit": "stair 2 row (one lump)", "verdict": "UNRESOLVED",
         "cause": "his one row covers valued and held parts and is not split by part: no closure without "
                  "re-attributing his lump. Diagnostic: his length exceeds the whole drawn developed length "
                  f"(straight {DRAWN['st02_straight']:.3f} + curved centreline {DRAWN['st02_curve_centre']:.3f} = "
                  f"{st02_len_c:.3f} m; along the outer edge {st02_len_o:.3f} m) - no drawn length of ST-02 supports it",
         "evidence": "ST p.4 2BA .. 2C4, 2C4 / 289, 2C8 .. 315, 2DF .. 2EA, arcs 2DD / 2DE; RFI-S27, RFI-A03"},
        {"id": "SD-DOMES-AB", "element": "dome shells DOME-A (west) and DOME-B (east), 442 / 190 / 10 above the springing",
         "pieces": [V("DOME-A-SHELL"), V("DOME-B-SHELL")], "his_m3": 2 * D["unit"],
         "his_unit": "dome row: 2 of his 3 counted domes", "verdict": "ENGINE_RIGHT", "terms": list(dome_terms.values()),
         "cause": "spherical cap shell from the printed chord / rise / thickness (equivalent area "
                  f"{cap['equiv_area_m2']:.4f} m2, outer {cap['outer_area_m2']:.4f}); his developed area matches no "
                  "area of the drawn cap (AREA UNTRACED); thickness 0.10 the same (THICKNESS_BASIS 0); rings in "
                  "the beam family (DOME-1F-W 0.7552 valued, DOME-1F-E held), drums held (RFI-A05): none inside the shell",
         "evidence": "ST p.7 DIM 1A38 / 1A6D / 19B1; T-185; Q-18, Q-61 C(3)"},
        {"id": "SD-DOME-3", "element": "tower dome over the 2F maid room", "pieces": [H("DOME-3-SHELL", "L-d5401fa8986900c66c37")],
         "his_m3": D["unit"], "his_unit": "dome row: 1 of his 3 counted domes", "verdict": "HELD",
         "cause": "Q-27 A: it exists; ST p.6 prints a flat +13.90 slab with no opening or ring, no structural detail",
         "evidence": "RFI-S28; T-185"},
        {"id": "SD-NA", "element": "superseded / retired route-G stair and dome lines",
         "pieces": [X("NA-" + k[-4:], k) for k in ("L-004e8e9fd032cb0aeb72", "L-33769fb181e11dca13cc",
                                                   "L-14f885e95132fa0cedec")],
         "his_m3": 0.0, "his_unit": "no row", "verdict": "AGREE",
         "cause": "NOT_APPLICABLE_WITH_EVIDENCE lines (replaced by the verified shells; the 1F 'stair' was the dome ribs)",
         "evidence": "T-185, T-193"},
    ]
    stair_his = sum(his[k]["net"] for k in ("ENTRANCE", "STAIR2", "DOME", "FLIGHTS", "LANDINGS"))
    if abs(stair_his - his_fam["STAIR_DOME"]) > 1e-6:
        raise SystemExit("his stair rows differ from his summary row")
    srows, sfam = R.family("CONC.STAIR_DOME", comps, his_fam["STAIR_DOME"])
    if abs(his_tot[6] - his_fam["STAIR_DOME"]) > 1e-6:
        raise SystemExit("his stair sheet totals differ from his summary row")

    pump = [
        {"id": "PL-PUMP-ROOM", "element": "pool pump / plant room walls and floor",
         "pieces": [], "held_named_item": "PUMP-ROOM (drawn on no sheet)",
         "his_m3": his["PUMP_WALLS"]["net"] + his["PUMP_FLOOR"]["net"], "his_unit": "pump walls + room floor rows",
         "verdict": "HELD",
         "cause": "R-T398-7: no pump / plant room on any sheet: structural DXF (text, layers, ST p.7 pool detail) and "
                  "architectural DXF searched (pump, plant, machine, equipment, filter, Arabic equivalents): none; "
                  "a pool needs plant somewhere, so it is not a verified absence: engine HELD named item, no value, "
                  "never valued from his row; designer fact row proposed",
         "evidence": "own search this run; S8.2 source search; T-385 PL-PUMP"},
        {"id": "PL-POOL-NA", "element": "superseded pool scope lines (route convention)",
         "pieces": [X("NA-6dca", "L-6dcad5ae573eec5aac19"), X("NA-8ca2", "L-8ca24b308e52eb6a7cf0")],
         "his_m3": 0.0, "his_unit": "no row", "verdict": "AGREE",
         "cause": "NOT_APPLICABLE_WITH_EVIDENCE lines replaced by the verified POOL-1 base / walls (carried by PL-BASE / PL-WALLS)",
         "evidence": "T-183 r2"},
    ]
    prows, pfam = R.family("CONC.POOL (pump part)", pump, pump[0]["his_m3"])
    return srows, sfam, prows, pfam, hand, cap, own, elsewhere


def _csv(rows):
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    return b.getvalue()


ENGINE_KEYS = ("id", "element", "engine_valued_m3", "held_pieces", "held_low_m3", "held_high_m3", "held_unbounded",
               "contribution_m3", "named_m3", "held_named_m3", "unexplained_m3", "untraced_term_m3", "terms", "verdict")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    his, tot, fam = read_his(argv[argv.index("--freelancer") + 1])
    srows, sfam, prows, pfam, hand, cap, own, elsewhere = build(his, tot, fam)
    summ = {"schema": "T398_SUMMARY_V1", "candidate_lines": "V3.0.21 file = V3.0.29 binding (asserted)",
            "stair_dome_family": {k: v for k, v in sfam.items() if k != "freelancer_m3"},
            "pump_part": {k: v for k, v in pfam.items() if k != "freelancer_m3"},
            "components": [{k: r[k] for k in ENGINE_KEYS} for r in srows + prows],
            "flight_hand_figures": hand, "dome_cap": cap,
            "owned_elsewhere_pieces": elsewhere, "ownership_pieces": len(own)}
    out = {"summary_t398.json": json.dumps(summ, ensure_ascii=False, indent=1, sort_keys=True) + "\n"}
    if "--out" in argv:
        d = Path(argv[argv.index("--out") + 1]).resolve()
        if ROOT in d.parents or d == ROOT:
            raise SystemExit("--out must be outside the repository (the table prints freelancer values)")
        d.mkdir(parents=True, exist_ok=True)
        (d / "RECON_T398.csv").write_text(_csv(srows + prows), encoding="utf-8")
        (d / "summary_t398.json").write_text(out["summary_t398.json"], encoding="utf-8")
    if "--write" in argv:
        (HERE / "summary_t398.json").write_text(out["summary_t398.json"], encoding="utf-8")
    return out


if __name__ == "__main__":
    print(main()["summary_t398.json"])
