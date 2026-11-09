"""T-568 development-villa run (research, unwired): doors and windows by type, count (nr) and opening area (m2) on the
candidate ARCH_TAKEOFF_V3.0.58, against the freelancer (R-T568-1), and the +6.30 m2 opening counts T-559 left
UNRESOLVED taken to their physical cause.

    .work/venv/bin/python -I research/agents_t568/t568_alsenan.py [--alu <xlsx>] [--masonry <xlsx>] [--write]

Inputs (merged repository files): research/agents_t507/out/LINE_INDEX_V3_0_57.json (the V3.0.58 door / window lines:
V3.0.58 = V3.0.57 + 5 pool-court lines, T-530; every ARCH.WINDOW / DOOR.* line is the V3.0.57 line), the opening
records behind them (T-150 r2 register, T-201 heads, T-207 W11 / W12, T-238 W15 / W16 / W17, T-232 held door widths,
T-268 / T-260 door rulings), restated in OPENINGS below and asserted against the candidate's line sums.
Private (never tracked): the freelancer's aluminium and masonry workbooks (Drive "Alsenan chalet project"), decoded into
.work/private; read here row by row (count, width, height, printed m2 checked). Without them only the engine side and
the closure of the candidate lines run (the run says so).
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t568_rules as R  # noqa: E402

LINE_INDEX = ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
OUT = HERE / "out" / "T568_TYPE_TABLE.json"
PRIV = ROOT.parent / "private"                 # .work/private when run from a worktree
ALU_DEFAULT, MAS_DEFAULT = PRIV / "alum.xlsx", PRIV / "masonry.xlsx"

ALU, PVC, MAIN, WIN, LIFT = ("DOOR.EXTERNAL.ALUMINIUM", "DOOR.INTERNAL.PVC", "DOOR.MAIN_ENTRANCE", "WINDOW.ALUMINIUM",
                             "LIFT.LANDING_OPENING")

# ---- the candidate's openings: id, storey, class, width m, area m2 (None = HELD), basis, bounds, source -------------
def _o(i, st, cls, w, a, basis, src, bounds=None, count_held=False):
    return {"id": i, "storey": st, "cls": cls, "w_m": w, "area_m2": a, "basis": basis, "bounds": bounds,
            "count_held": count_held, "source": src}


OPENINGS = [
    # aluminium external doors (T-150 r2; classes / widths ruled T-260 -> V3.0.13; head Q-55 C 2.20)
    _o("D-GF-01", "GF", ALU, "1.00", "2.200", "Q55C", "T-150 / T-260 (court)"),
    _o("D-GF-03", "GF", ALU, "0.90", "1.980", "Q55C", "T-150 (driver room to court; census 900)"),
    _o("D-GF-05", "GF", ALU, "1.00", "2.200", "Q55C", "T-260 ruling (kitchen to the open side passage, Q-67 A)"),
    _o("D-GF-06", "GF", ALU, "1.00", "2.200", "Q55C", "T-260 ruling (pantry to the +1.00 entrance landing)"),
    _o("D-GF-09", "GF", ALU, "0.90", "1.980", "Q55C", "T-260 (0.90 between masonry ends; 1.00 is the D120 frame)"),
    _o("D-2F-01", "2F", ALU, "1.00", "2.200", "Q55C", "T-150 (roof access)"),
    # main entrance: printed 2.00 x 2.50; HELD single vs double leaf (T-161 F07c, designer D-53)
    _o("D-GF-07", "GF", MAIN, "2.00", None, "HELD", "T-150 / T-232", bounds=["5.000", "5.000"]),
    # internal doors (PVC by owner rule UP-DOOR-CLS-001 / 003), head Q-55 C
    _o("D-GF-02", "GF", PVC, None, None, "HELD", "T-232 width 0.69 .. 0.80", bounds=["1.518", "1.760"]),
    _o("D-GF-04", "GF", PVC, "0.80", "1.760", "Q55C", "T-150"),
    _o("D-GF-08", "GF", PVC, "1.00", "2.200", "Q55C", "T-150 (20 cm wall GF-W08)"),
    _o("D-GF-10", "GF", PVC, None, None, "HELD", "T-232 width 0.69 .. 0.797", bounds=["1.518", "1.760"]),
    _o("D-GF-11", "GF", PVC, "0.80", "1.760", "Q55C", "T-150"),
    _o("D-GF-12", "GF", PVC, "0.80", "1.760", "Q55C", "T-150"),
    _o("D-GF-13", "GF", PVC, "1.00", "2.200", "Q55C", "T-150"),
    _o("D-GF-14", "GF", PVC, None, None, "HELD", "T-232 loose arc, width 0.69 .. 0.80", bounds=["1.518", "1.760"]),
    _o("D-1F-01", "1F", PVC, "0.80", "1.760", "Q55C", "T-150"),
    _o("D-1F-02", "1F", PVC, "1.00", "2.200", "Q55C", "T-150 (D115 from the landing)"),
    _o("D-1F-03", "1F", PVC, None, None, "HELD", "T-232 width 0.89 .. 1.00", bounds=["1.958", "2.200"]),
    _o("D-1F-04", "1F", PVC, None, None, "HELD", "T-232 width 0.69 .. 0.80", bounds=["1.518", "1.760"]),
    _o("D-1F-05", "1F", PVC, "0.90", "1.980", "Q55C", "T-150 (laundry, 20 cm wall 1F-W07)"),
    _o("D-1F-06", "1F", PVC, "0.80", "1.760", "Q55C", "T-150"),
    _o("D-1F-07", "1F", PVC, "0.80", "1.760", "Q55C", "T-150"),
    _o("D-1F-08", "1F", PVC, "0.90", "1.980", "Q55C", "T-150"),
    _o("D-1F-09", "1F", PVC, "0.90", "1.980", "Q55C", "T-150"),
    _o("D-1F-10", "1F", PVC, "0.80", "1.760", "Q55C", "T-150"),
    _o("D-2F-02", "2F", PVC, "0.90", "1.980", "Q55C", "T-150 (maid room, 20 cm wall 2F-W05)"),
    _o("D-2F-03", "2F", PVC, "0.80", "1.760", "Q55C", "T-150"),
    # lift landing openings: EXCLUDED.LIFT_CANDIDATE in the candidate (the lift supplier's item, UP-ELEV-SCHED-001)
    _o("L-GF-01", "GF", LIFT, "1.00", None, "HELD", "T-150 (excluded: lift supply)", bounds=None),
    _o("L-1F-01", "1F", LIFT, "1.00", None, "HELD", "T-150 (excluded: lift supply)", bounds=None),
    _o("L-2F-01", "2F", LIFT, "1.00", None, "HELD", "T-150 (excluded: lift supply)", bounds=None),
    # aluminium windows (T-201 heads, T-207 W11 / W12, T-238 Q-32 A on the opening line; W17 Q-76 A not yet wired)
    _o("W01", "GF", WIN, "1.20", "2.400", "DRAWING_CONFIRMED", "T-201"),
    _o("W02", "GF", WIN, "6.33", None, "HELD", "T-207: count 1 (drawings) vs 2 (render), D-53",
       bounds=["13.926", None], count_held=True),
    _o("W03", "GF", WIN, "6.57", "28.251", "PRINTED", "T-201 (curved pool glazing, printed 6.57 x 4.30)"),
    _o("W04", "GF", WIN, "0.60", "0.480", "DRAWING_CONFIRMED", "T-201"),
    _o("W05", "GF", WIN, "0.60", "0.480", "DRAWING_CONFIRMED", "T-201"),
    _o("W06", "GF", WIN, "0.60", "0.480", "DRAWING_CONFIRMED", "T-201"),
    _o("W07", "GF", WIN, "0.60", "0.480", "DRAWING_CONFIRMED", "T-201"),
    _o("W08", "GF", WIN, "1.50", "2.250", "DRAWING_CONFIRMED", "T-201"),
    _o("W09", "GF", WIN, "1.50", "2.250", "DRAWING_CONFIRMED", "T-201"),
    _o("W10", "GF", WIN, "1.00", "1.500", "DRAWING_CONFIRMED", "T-201"),
    _o("W11", "GF", WIN, "1.95", "4.290", "DRAWING_CONFIRMED", "T-207 (opening between the louvred leaves)"),
    _o("W12", "GF", WIN, "1.95", "4.290", "DRAWING_CONFIRMED", "T-207"),
    _o("W13", "1F", WIN, "1.20", "2.760", "PRINTED", "T-150 / T-201"),
    _o("W14", "1F", WIN, "2.45", "3.920", "PRINTED", "T-150 / T-201"),
    _o("W15", "1F", WIN, "1.55", "4.650", "Q32A", "T-238 (crown of the opening 3.00; 3.10 is the band)"),
    _o("W16", "1F", WIN, "1.55", "4.650", "Q32A", "T-238 (twin of W15)"),
    _o("W17", "1F", WIN, "3.29", None, "HELD", "T-238; candidate HELD 9.870 .. 11.515 (Q-76 A answered 9.870)",
       bounds=["9.870", "11.515"]),
    _o("W18", "1F", WIN, "0.50", "1.080", "PRINTED", "T-150 (sheet04 chain '50'; NW chain 84 / 216)"),
    _o("W19", "1F", WIN, "0.60", "0.480", "DRAWING_CONFIRMED", "T-201"),
    _o("W20", "1F", WIN, "0.60", "0.480", "DRAWING_CONFIRMED", "T-201"),
    _o("W21", "1F", WIN, "0.60", "0.480", "DRAWING_CONFIRMED", "T-201"),
    _o("W22", "1F", WIN, "0.60", "0.480", "DRAWING_CONFIRMED", "T-201"),
    _o("W23", "1F", WIN, "0.60", "0.480", "DRAWING_CONFIRMED", "T-201"),
    _o("W24", "1F", WIN, "1.55", "2.325", "DRAWING_CONFIRMED", "T-201"),
    _o("W25", "1F", WIN, "1.00", "1.500", "DRAWING_CONFIRMED", "T-201"),
    _o("W26", "2F", WIN, "1.20", "2.040", "Q32A", "T-238 (170 chain ends on the opening apex)"),
    _o("W27", "2F", WIN, "1.00", "1.500", "DRAWING_CONFIRMED", "T-201"),
    _o("W28", "2F", WIN, "0.60", "0.480", "DRAWING_CONFIRMED", "T-201"),
    _o("W29", "2F", WIN, "1.20", "1.800", "DRAWING_CONFIRMED", "T-201"),
]
# census openings that are no door / window supply item (named, never 0 in their own trades)
NOT_SUPPLY = {"A-GF-01": "arch, no leaf", "A-1F-01": "arch, no leaf", "SX-01": "filling HELD (T-161 F09)",
              "SX-03": "passage, no leaf", "P-GF-01 .. P-GF-05, P-1F-01": "passages, no leaf",
              "D-GF-15": "site gate (no Urban door class)", "U-01": "census UNRESOLVED (no host wall)"}

# the candidate's lines (item code, floor, unit, part) -> (measured_net, held_low, held_high) and the ids behind them
CANDIDATE_GROUPS = {
    (ALU, "GF", "pcs"): ["D-GF-01", "D-GF-03", "D-GF-05", "D-GF-06", "D-GF-09"],
    (ALU, "2F", "pcs"): ["D-2F-01"],
    (WIN, "GF", "pcs"): ["W01", "W03", "W04", "W05", "W06", "W07", "W08", "W09", "W10", "W11", "W12"],
    (WIN, "1F", "pcs"): ["W13", "W14", "W15", "W16", "W17", "W18", "W19", "W20", "W21", "W22", "W23", "W24", "W25"],
    (WIN, "2F", "pcs"): ["W26", "W27", "W28", "W29"],
}

# drawn door leaves read independently this run (P7757.dxf model space INSERTs, handle -> opening), and the
# S8.6 census (research/alsenan_lintels_s8_6/01_OPENING_CENSUS.csv) that ties each handle to its jambs
DRAWN_LEAVES = {
    "GF external": {"D120:15E": "D-GF-01", "d220:1B5": "D-GF-03", "D120:192": "D-GF-05", "D120:33E": "D-GF-06",
                    "D120:3FF": "D-GF-09"},
    "1F internal": {"D315:C2B": "D-1F-01", "D115:C31": "D-1F-02", "D115:C32": "D-1F-03", "D315:C2E": "D-1F-04",
                    "d220:C1A": "D-1F-05", "D315:11B4": "D-1F-06", "D315:BEE": "D-1F-07", "D215:C18": "D-1F-08",
                    "D215:BEF": "D-1F-09", "D315:C12": "D-1F-10"},
}


def check_candidate(lines: list[dict], ops: dict) -> list[dict]:
    """every door / window line of the candidate equals the sum of OPENINGS (pcs and m2, settled and held)."""
    got = {}
    for ln in lines:
        ic = WIN if ln["item_code"] == "ARCH.WINDOW" else ln["item_code"]
        if ic not in (ALU, PVC, MAIN, WIN) or not ln["element_id"].startswith("OPENINGS:") or ln["class"] == "EXCLUDED":
            continue
        _, _, floor, part = ln["element_id"].split(":")
        got[(ic, floor, ln["unit"], part)] = (ln["measured_net"], ln["held_low"], ln["held_high"])
    want = {}
    for o in ops.values():
        if o["cls"] == LIFT:
            continue
        settled = o["basis"] != "HELD"
        m2_part = ("SETTLED_ASSUMED_OWNER_APPROVED" if o["basis"] == "Q55C" else "SETTLED_DRAWING_CONFIRMED") \
            if settled else ("HELD" if o["bounds"] and o["bounds"][1] else "HELD_NO_FIGURE")
        pcs_part = "SETTLED_DRAWING_CONFIRMED" if (settled or o["cls"] == WIN) and not o["count_held"] else "HELD"
        k = (o["cls"], o["storey"], "m2", m2_part)
        a = want.setdefault(k, [Decimal(0), Decimal(0), Decimal(0)])
        if settled:
            a[0] += R.D(o["area_m2"])
        elif m2_part == "HELD":
            a[1] += R.D(o["bounds"][0]); a[2] += R.D(o["bounds"][1])
        k = (o["cls"], o["storey"], "pcs", pcs_part)
        a = want.setdefault(k, [Decimal(0), Decimal(0), Decimal(0)])
        if pcs_part.startswith("SETTLED"):
            a[0] += 1
        else:
            a[1] += 1; a[2] += 2 if o["count_held"] else 1
    out = []
    for k, (net, lo, hi) in sorted(want.items()):
        g = got.get(k)
        if g is None:
            raise R.RuleError(f"candidate has no line {k}")
        if k[3].startswith("SETTLED"):
            ok = R.D(g[0]) == net
        elif k[3] == "HELD":
            ok = R.D(g[1]) == lo and R.D(g[2]) == hi
        else:
            ok = g == (None, None, None)
        if not ok:
            raise R.RuleError(f"candidate line {k} = {g}, OPENINGS give {(net, lo, hi)}")
        out.append({"line": "|".join(k), "candidate": g, "openings": [str(net), str(lo), str(hi)]})
    extra = set(got) - set(want)
    if extra:
        raise R.RuleError(f"candidate door / window lines not explained by OPENINGS: {sorted(extra)}")
    return out


# ---- the freelancer's rows (private workbooks) -------------------------------------------------------------------
FLOOR_WORDS = (("الأرض", "GF"), ("الأول", "1F"), ("السطح", "2F"))


def _floor(s: str):
    for w, f in FLOOR_WORDS:
        if w in s:
            return f
    return None


def read_alu(path: Path) -> list[dict]:
    import openpyxl
    ws = openpyxl.load_workbook(path, data_only=True, read_only=True)["الكميات"]
    rows, floor = [], None
    for i, r in enumerate(ws.iter_rows(values_only=True), 1):
        v = [x for x in r if x is not None]
        if not v:
            continue
        if isinstance(v[0], str) and _floor(v[0]) and len(v) == 1:
            floor = _floor(v[0]); continue
        nums = [x for x in v if isinstance(x, (int, float))]
        lab = v[0] if isinstance(v[0], str) else ""
        if len(nums) == 4 and floor:
            n, w, h, m2 = nums
            cls = ALU if "باب" in lab else WIN
            rows.append({"row": f"ALU:{i}", "storey": floor, "cls": cls, "n": n, "w_m": R.D(w), "h_m": R.D(h),
                         "m2": (R.D(n) * R.D(w) * R.D(h)), "printed_m2": m2})
    for r in rows:                                        # his printed m2 (float) agrees with n x w x h
        if abs(R.D(r.pop("printed_m2")) - r["m2"]) > Decimal("1e-9"):
            raise R.RuleError(f"his {r['row']}: printed m2 differs from n x w x h")
    return rows


def read_masonry_doors(path: Path) -> list[dict]:
    """his internal 15 cm / 20 cm opening deductions (doors; the external sections repeat the aluminium rows and the
    main entrance); the 20 cm section prints no floor (storey None)."""
    import openpyxl
    ws = openpyxl.load_workbook(path, data_only=True, read_only=True)["الكميات"]
    rows, section, in_open, floor = [], None, False, None
    for i, r in enumerate(ws.iter_rows(values_only=True), 1):
        v = [x for x in r if x is not None]
        if not v:
            continue
        s = " ".join(str(x) for x in v)
        if "15 سم داخلي" in s:
            section, in_open, floor = "INT15", False, None; continue
        if "20سم داخلي" in s or "20 سم داخلي" in s:
            section, in_open, floor = "INT20", False, None; continue
        if "مبانى" in s or "مباني" in s:
            if section and "داخلي" not in s:
                section = None
            if section is None:
                section = "EXT"
        if "خصم" in s and "فتح" in s and "اجمالي" not in s and "الإجمالي" not in s:
            in_open = True; continue
        if "اجمالي" in s or "الإجمالي" in s:
            in_open = False; continue
        if isinstance(v[0], str) and _floor(v[0]):
            floor = _floor(v[0]); continue
        nums = [x for x in v if isinstance(x, (int, float))]
        if in_open and section in ("INT15", "INT20") and len(nums) == 4:
            n, w, h, m2 = nums
            rows.append({"row": f"MAS:{i}", "storey": floor if section == "INT15" else None, "section": section,
                         "n": n, "w_m": R.D(w), "h_m": R.D(h), "m2": R.D(n) * R.D(w) * R.D(h), "printed": m2})
    for r in rows:
        if abs(R.D(r.pop("printed")) - r["m2"]) > Decimal("1e-9"):
            raise R.RuleError(f"his {r['row']}: printed m2 differs from n x w x h")
    return rows


# ---- pairings (his rows carry no id: stated, consistent matches; R-T568-1 (d)) ------------------------------------
def alu_pairs(rows):
    """T-181 scope ties (Checker-merged), restated by row order within each storey and class."""
    by = {}
    for r in rows:
        by.setdefault((r["storey"], r["cls"]), []).append(r["row"])
    g = lambda st, cls, k: by[(st, cls)][k]                                   # noqa: E731
    P = [("D-GF-01", g("GF", ALU, 0), "his 4 x 1.00 GF external doors"), ("D-GF-06", g("GF", ALU, 0), ""),
         ("D-GF-03", g("GF", ALU, 0), ""), ("D-GF-09", g("GF", ALU, 0), ""),
         ("D-2F-01", g("2F", ALU, 0), "roof door")]
    gf = by[("GF", WIN)]
    P += [(w, gf[0], "GF bath 0.60 x 0.80") for w in ("W04", "W05", "W06", "W07")]
    P += [("W03", gf[1], ""), ("W02", gf[2], "count HELD (render 2)"), ("W10", gf[3], ""), ("W08", gf[4], ""),
          ("W01", gf[5], ""), ("W11", gf[6], ""), ("W12", gf[6], ""), ("W09", gf[7], "")]
    f1 = by[("1F", WIN)]
    P += [("W25", f1[0], ""), ("W18", f1[1], "his sixth 0.60 x 0.80 = W18 (T-181 tie)")]
    P += [(w, f1[1], "1F bath") for w in ("W19", "W20", "W21", "W22", "W23")]
    P += [("W17", f1[2], "Q-76 A"), ("W15", f1[3], ""), ("W16", f1[3], ""), ("W24", f1[4], ""), ("W14", f1[5], ""),
          ("W13", f1[6], "")]
    f2 = by[("2F", WIN)]
    P += [("W27", f2[0], ""), ("W26", f2[1], ""), ("W28", f2[2], ""), ("W29", f2[3], "")]
    return P


def alu_pairs_alt(rows):
    """the T-559 pairing: D-GF-05 paired, D-GF-03 his omission (consistent too)."""
    P = alu_pairs(rows)
    return [("D-GF-05" if p[0] == "D-GF-03" else p[0], p[1], p[2]) for p in P]


def mas_pairs(rows):
    by = {}
    for r in rows:
        by.setdefault((r["section"], r["storey"], str(r["w_m"])), []).append(r["row"])
    g = lambda *k: by[k][0]                                                   # noqa: E731
    P = [(d, g("INT15", "GF", "0.8"), "") for d in ("D-GF-02", "D-GF-04", "D-GF-10", "D-GF-11", "D-GF-12", "D-GF-14")]
    P += [("D-GF-13", g("INT15", "GF", "1"), ""), ("D-GF-08", g("INT20", None, "1.1"), "lobby door in GF-W08")]
    P += [(d, g("INT15", "1F", "0.8"), "") for d in ("D-1F-01", "D-1F-04", "D-1F-06", "D-1F-07")]
    P += [(d, g("INT15", "1F", "0.9"), "") for d in ("D-1F-05", "D-1F-08", "D-1F-09")]
    P += [("D-1F-03", g("INT15", "1F", "0.9"), "his fourth 0.90 vs a drawn 1.00 (D-1F-02 or D-1F-03)")]
    P += [("D-2F-03", g("INT15", "2F", "0.8"), ""), ("D-2F-02", g("INT15", "2F", "0.9"), "")]
    P += [(lid, g("INT20", None, "1"), "lift landing") for lid in ("L-GF-01", "L-1F-01", "L-2F-01")]
    return P


VERDICTS = {
    # unpaired drawn leaves: each read independently this run (DRAWN_LEAVES) -> the count is the drawing's
    "D-GF-05": {"count": "ENGINE_RIGHT"}, "D-GF-03": {"count": "ENGINE_RIGHT"},
    "D-1F-02": {"count": "ENGINE_RIGHT"}, "D-1F-10": {"count": "ENGINE_RIGHT"},
    # widths between masonry ends on both faces (T-260 VERIFIED; census 900): his 1.00 is the D120 / d220 frame
    "D-GF-09": {"width": "ENGINE_RIGHT"},
    # D-GF-03: wall-face ends 0.900 apart on both faces (P7757.dxf layer 1, read this run); his 1.00 = the frame
    "D-GF-03": {"count": "ENGINE_RIGHT", "width": "ENGINE_RIGHT"},
    # W18: printed width '50' (sheet04 chain), his 0.60 is the W.C. window size
    "W18": {"width": "ENGINE_RIGHT"},
    # D-GF-08: drawn 1.000 between the masonry ends (read this run); his 1.10 = 1.00 + 0.10, the Q-04 wall-opening
    # minimum; UP-DOOR-OPEN-003 keeps owner minimums apart from the measured width -> a rule reading, not a measure
    "D-GF-08": {"width": "RULE_DIFFERENCE"},
}
# wall-face (layer 1) end-to-end gaps read this run at each insert, metres (one face unless stated)
JAMB_READS = {"D-GF-01": "1.000 (both faces)", "D-GF-03": "0.900 (both faces)", "D-GF-09": "0.900 (both faces)",
              "D-GF-05": "1.000", "D-GF-06": "1.000", "D-GF-08": "1.000", "D-1F-02": "1.000", "D-1F-03": "1.000",
              "D-1F-10": "0.800"}


def _units_for(rows, cls_of):
    out = []
    for r in rows:
        out.append({"row": r["row"], "storey": r["storey"], "cls": cls_of(r), "n": r["n"], "w_m": r["w_m"],
                    "h_m": r["h_m"], "m2": r["m2"]})
    return R.his_units(out)


def build(alu_path: Path | None, mas_path: Path | None) -> dict:
    ops = R.openings_once(OPENINGS)
    lines = json.loads(LINE_INDEX.read_text(encoding="utf-8"))["lines"]
    doc = {"task": "T-568", "candidate": "ARCH_TAKEOFF_V3.0.58 (door / window lines = V3.0.57)",
           "candidate_closure": check_candidate(lines, ops), "not_supply_items": NOT_SUPPLY,
           "drawn_leaves": DRAWN_LEAVES, "jamb_reads": JAMB_READS}
    if not (alu_path and alu_path.exists() and mas_path and mas_path.exists()):
        doc["comparison"] = "NOT RUN: the freelancer workbooks are private (.work/private)"
        return doc
    alu = read_alu(alu_path)
    supply_ops = {k: v for k, v in ops.items() if v["cls"] in (ALU, WIN)}
    U = _units_for(alu, lambda r: r["cls"])
    t_a = R.type_table(openings=supply_ops, units=U, pairs=alu_pairs(alu), verdicts=VERDICTS)
    t_b = R.type_table(openings=supply_ops, units=_units_for(alu, lambda r: r["cls"]), pairs=alu_pairs_alt(alu),
                       verdicts=VERDICTS)
    doc["supply_aluminium"] = t_a
    doc["pairing_move_ALU_T559_vs_T181"] = R.pairing_move(t_a, t_b, ALU)
    # internal doors / lift landings / main entrance: his only door rows are masonry deductions (no supply row)
    mas = read_masonry_doors(mas_path)
    mops = {k: v for k, v in ops.items() if v["cls"] in (PVC, LIFT)}
    MU = _units_for(mas, lambda r: LIFT if (r["section"] == "INT20" and r["w_m"] == 1) else PVC)
    doc["masonry_deduction_doors"] = R.type_table(openings=mops, units=MU, pairs=mas_pairs(mas), verdicts=VERDICTS)
    # windows like for like (the openings settled on our side and paired), and with Q-76 A applied to W17
    rows = t_a[WIN]["rows"]
    held = sum((R.D(r["delta"]) for r in rows if r["cause"] == "HELD" and r["unit"] == "m2"), Decimal(0))
    ours = R.D(t_a[WIN]["m2"]["ours_settled"])
    his = R.D(t_a[WIN]["m2"]["his"])
    lfl_his = his + held                                   # his m2 on the openings settled on both sides
    w17_his = Decimal("9.45")
    doc["windows_like_for_like"] = {
        "settled_both_sides": {"nr": 27, "ours": str(ours), "his": str(lfl_his), "diff": str(ours - lfl_his),
                               "pct": str(((ours - lfl_his) / lfl_his * 100).quantize(Decimal("0.01")))},
        "with_Q76A_W17": {"nr": 28, "ours": str(ours + Decimal("9.870")), "his": str(lfl_his + w17_his),
                          "diff": str(ours + Decimal("9.870") - lfl_his - w17_his),
                          "pct": str(((ours + Decimal("9.870") - lfl_his - w17_his) / (lfl_his + w17_his) * 100)
                                     .quantize(Decimal("0.01")))}}
    return doc


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    alu = Path(argv[argv.index("--alu") + 1]) if "--alu" in argv else ALU_DEFAULT
    mas = Path(argv[argv.index("--masonry") + 1]) if "--masonry" in argv else MAS_DEFAULT
    doc = build(alu, mas)
    if "--write" in argv:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    for k in ("supply_aluminium", "masonry_deduction_doors"):
        for cls, t in (doc.get(k) or {}).items():
            print(k, cls, "nr", t["nr"]["ours_settled"], "vs", t["nr"]["his"], t["nr"]["by_cause"], "| m2",
                  t["m2"]["ours_settled"], "vs", t["m2"]["his"], t["m2"]["by_cause"])
    print(json.dumps(doc.get("windows_like_for_like"), indent=1))
    print(json.dumps(doc.get("pairing_move_ALU_T559_vs_T181"), indent=1))
    return doc


if __name__ == "__main__":
    main()
