"""T-757 (lane S, DELIVERY MODE): the 114 RANGED (held low .. high) STR.CONC lines of ARCH_TAKEOFF_V3.0.79 to points.

    python3 -I research/agents_t757/fill_t757.py            # writes research/agents_t757/out/FIX_ROWS.{json,md}
    python3 -I research/agents_t757/fill_t757.py --check    # self-test (synthetic villa) + rebuild must equal the files

Owner materiality rule (2026-11-13 14:00, DELIVERY_MODE s.3; Lead r2 text of T-757): a ranged line whose width
(high - low) is below 0.05 m3 takes its LOW bound and its width is logged in IGNORED_SMALL and added to the ONE existing
safety line NEW:STR.CONC.SAFETY (T-761), restated max(1.00, sum). Width >= 0.05 m3 -> a POINT by the fallback order
(drawing geometry / printed reading -> company default -> estimate), label + basis per line; a point must lie inside
the line's own [low, high] (both bounds are drawing-derived) and is never chosen because it is larger, smaller or
closer to the freelancer. No new rule file (Lead r2): the rule is applied, T-761 created the register and safety line.

Inputs (merged research files only, no private data): the V3.0.79 line index (T-314; its 114 ranged STR.CONC lines are
identical to V3.0.78), T-761 fix rows (its IGNORED_SMALL sum and safety line), the ST column schedule extract (CGT),
T-657 neck ledger, T-277 beam width conflicts, T-241 beam ledger, route G registers, T-669 / T-678 / T-707 height
datums, T-566 mark registration (10AE / 10E0), T-677 lintel members, T-233 / T-356 / T-445 / T-478 blinding readings.
"""
from __future__ import annotations

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
R = lambda p: os.path.join(ROOT, p)

INDEX = "research/agents_t314/out/LINE_INDEX_V3_0_79.json"
T761 = "research/agents_t761/out/FIX_ROWS.json"
SMALL = 0.05            # m3, owner materiality threshold
SAFETY_FLOOR = 1.00     # m3, owner: safety line = 1 m3 if the ignored sum < 1 m3, else the sum
ROOF_BUILDUP = 0.075 + 0.05 + 0.05   # company default roof build-up (screed avg + insulation + protection; membrane ~0), as T-761
LABELS = ("MEASURED", "DRAWING-READ", "DEFAULT", "ESTIMATE", "SAFETY")
TOL = 1e-6


# ------------------------------------------------------------------------------------------------ generic rule (any villa)
def apply_materiality(ranged, points, small=SMALL, floor=SAFETY_FLOOR, prior_ignored=0.0):
    """ranged: [{line_id, item_code, low, high}]; points: {line_id: (value, label, basis)} for widths >= small.
    Returns (rows, ignored_rows, safety). Raises on: a missing point (never silently low, never 0 by absence), a point
    outside its own bounds, a bad label, a high below the low. Width < small -> low, width logged."""
    rows, ignored = [], []
    for l in ranged:
        lo, hi = l["low"], l["high"]
        if lo is None or hi is None:
            raise ValueError(f"{l['line_id']}: not a bounded line (blank / one-sided lines are not this rule's)")
        if hi < lo - TOL:
            raise ValueError(f"{l['line_id']}: high below low")
        w = hi - lo
        if w < small - TOL:
            rows.append({**l, "width": round(w, 6), "after": round(lo, 6), "label": "DEFAULT",
                         "basis": f"width {w:.4f} m3 < {small} m3 (owner materiality 2026-11-13): low bound kept, width logged in IGNORED_SMALL and carried by STR.CONC.SAFETY",
                         "rule": "MATERIALITY_LOW"})
            ignored.append({"line_id": l["line_id"], "item_code": l["item_code"], "element_id": l.get("element_id"),
                            "low": lo, "high": hi, "width": round(w, 6), "cause": l.get("designer_item")})
            continue
        if l["line_id"] not in points:
            raise ValueError(f"{l['line_id']}: width {w:.4f} >= {small} needs a point by the fallback order")
        v, label, basis = points[l["line_id"]]
        if label not in LABELS:
            raise ValueError(f"{l['line_id']}: label {label}")
        if not (lo - TOL <= v <= hi + TOL):
            raise ValueError(f"{l['line_id']}: point {v} outside its bounds {lo} .. {hi}")
        rows.append({**l, "width": round(w, 6), "after": round(v, 6), "label": label, "basis": basis, "rule": "POINT"})
    isum = prior_ignored + sum(r["width"] for r in ignored)
    safety = floor if isum < floor else isum
    return rows, ignored, round(safety, 6), round(isum, 6)


def selftest():
    """Synthetic villa (not Alsenan): normal + adverse cases of the rule."""
    mk = lambda i, lo, hi: {"line_id": f"X-{i}", "item_code": "STR.CONC.BEAM", "low": lo, "high": hi}
    # normal: widths 0.03 + 0.04 -> low, logged; one wide line with a point inside; sum 0.07 < 1 -> safety 1.00
    rows, ign, s, isum = apply_materiality([mk(1, 0.20, 0.23), mk(2, 1.00, 1.04), mk(3, 0.40, 0.60)],
                                           {"X-3": (0.50, "DEFAULT", "synthetic")})
    assert [r["after"] for r in rows] == [0.20, 1.00, 0.50] and len(ign) == 2 and s == 1.0 and abs(isum - 0.07) < 1e-9
    # adverse 1: width exactly 0.05 is NOT ignored -> must have a point
    try:
        apply_materiality([mk(4, 0.10, 0.15)], {})
        raise AssertionError("width 0.05 must need a point")
    except ValueError:
        pass
    # adverse 2: a point outside its own bounds is refused (no picking beyond the drawing)
    try:
        apply_materiality([mk(5, 0.10, 0.30)], {"X-5": (0.31, "DEFAULT", "x")})
        raise AssertionError("out-of-bounds point accepted")
    except ValueError:
        pass
    # adverse 3: a blank / one-sided line is not silently made 0 or low
    try:
        apply_materiality([mk(6, 0.10, None)], {})
        raise AssertionError("one-sided line accepted")
    except ValueError:
        pass
    # adverse 4: the ignored sum above 1 m3 -> safety = the sum (prior register 0.98 + 0.04 + 0.03)
    _, _, s, isum = apply_materiality([mk(7, 0.0, 0.04), mk(8, 2.0, 2.03)], {}, prior_ignored=0.98)
    assert abs(s - 1.05) < 1e-9 and abs(isum - 1.05) < 1e-9
    # adverse 5: units: a point in litres (x1000) is refused by the bound check
    try:
        apply_materiality([mk(9, 0.30, 0.40)], {"X-9": (350.0, "DEFAULT", "litres")})
        raise AssertionError("unit error accepted")
    except ValueError:
        pass
    return "selftest PASS (6 cases)"


# ------------------------------------------------------------------------------------------------ Alsenan points
def schedule():
    d = json.load(open(R("research/alsenan_control_plane_01/evidence/ST7757_SCHEDULE_EXTRACT.json")))
    s = {}
    for r in d["blocks"]["CGT"]:
        a = r["attributes"]
        sec = lambda w, h: round(int(a[w]) * int(a[h]) / 10000.0, 6) if a[w] and a[h] else None
        s[a["COL-T"]] = {"FOU": sec("FOU.W", "FOU.H"), "GF": sec("GR.W", "GR.H"), "1F": sec("1ST.W", "1ST.H"), "2F": sec("2ND.W", "2ND.H"),
                         "txt": {k: f"{a[k + '.W']}x{a[k + '.H']}" for k in ("FOU", "GR", "1ST", "2ND")}}
    return s


def points_for(lines):
    sch = schedule()
    P = {}

    def put(lid, v, label, basis):
        assert lid not in P, lid
        P[lid] = (v, label, basis)

    # ---- COLUMNS: company default 'schedule governs a column' (owner 2026-11-13); heights from printed datums
    H_GF, H_1F = 4.50, 4.20                      # T-214 slab tops +0.95 / +5.45 / +9.65 (route G release register)
    H_2F = 13.90 - ROOF_BUILDUP - 9.65           # SECTION A-A roof finished +13.90 (printed) - 0.175 default - 2F base +9.65
    H_ANNEX = 4.30 - ROOF_BUILDUP - 0.25         # annex roof finished +4.30 (printed, T-321 / T-678) - 0.175 - base +0.25
    pos_drawn = {  # T-566 mark CONFLICT positions: the mark is in doubt, so the schedule cannot govern; drawn outline does
        "C8@256160,53630": ("10E0", 0.20, "drawn 0.25 x 0.80 (GFRS 380 / FFRS 69A); marks C8 (FP, CAP) vs C7 (GBP) in CONFLICT, every printed size fits C7 (T-566)"),
        "C3@241094,51256": ("10AE", 0.08, "drawn 0.20 x 0.40 (GFRS 350); marks C3 vs C in CONFLICT, outline fits neither GR band (T-566)"),
    }
    for lid, l in lines.items():
        if l["item_code"] != "STR.CONC.COLUMN":
            continue
        e = l["element_id"]
        if e == "HL:PLANTED_COLUMN:PC-2F:CONCRETE":
            h = H_2F - 0.75
            put(lid, 0.10 * h, "DEFAULT", f"PC-2F planted on the 0.75 support: section = its printed size text 'P.C 20x50' 0.10 m2 (company default: the printed size governs a column; drawn 0.20 x 0.40 = 0.08, D-66) x h {h:.3f} = roof slab top (+13.90 finished - 0.175 roof build-up default) - 9.65 - 0.75 = {0.10 * h:.4f} m3; D-39 / D-66 answer replaces it")
            continue
        body, storey = e.split(":")[-1].split("|")
        mark = body.split("@")[0]
        annex = storey == "GF" and "D-39" in (l.get("designer_item") or "")
        h = H_ANNEX if annex else {"GF": H_GF, "1F": H_1F, "2F": H_2F}[storey]
        hs = {True: f"annex h {H_ANNEX:.3f} = +4.30 printed finished - 0.175 roof build-up default - base +0.25"}.get(annex) or {
            "GF": "GF h 4.50 (slab tops +0.95 .. +5.45)", "1F": "1F h 4.20 (+5.45 .. +9.65)",
            "2F": f"2F h {H_2F:.3f} = +13.90 printed finished - 0.175 roof build-up default - base +9.65"}[storey]
        if body in pos_drawn:
            p, a, why = pos_drawn[body]
            put(lid, a * h, "DRAWING-READ" if not annex else "DEFAULT", f"{p} {storey}: {why}: {a:.3f} m2 x {hs} = {a * h:.4f} m3; designer mark answer replaces it")
            continue
        a = sch[mark][storey]
        key = {"GF": "GR", "1F": "1ST", "2F": "2ND"}[storey]
        put(lid, a * h, "DEFAULT", f"{mark} {storey}: schedule CGT {key} {sch[mark]['txt'][key]} = {a:.3f} m2 (company default: schedule governs a column; D-66 drawn outline differs where named) x {hs} = {a * h:.4f} m3")

    # ---- NECKS: T-657 ledger; founding at the printed minimum (ST p.9 n.1, 1.50 below EG) = the only printed level
    for n in json.load(open(R("research/agents_t657/out/T657_NECK_LEDGER.json")))["necks"]:
        lid = n["line_id"]
        if lid not in lines or n.get("m3_high") is None:
            continue
        mark = n["mark"]
        cands = [float(c) for c in n["section_candidates_m2"]]
        h = float(n["h_low_m"])
        if n["position"] == "10E0":
            a, src = 0.24, "drawn 30 x 80 = C7 FOU (mark C8 / C7 CONFLICT at 10E0, T-566; same reading as its GF / 1F column)"
        elif len(cands) > 1:
            a, src = sch[mark]["FOU"], f"schedule FOU {sch[mark]['txt']['FOU']} (company default: schedule governs; drawn {min(cands):.3f} differs)"
        else:
            a = cands[0]
            src = f"section {a:.3f} m2" + (f" (= schedule FOU {sch[mark]['txt']['FOU']})" if mark in sch and abs((sch[mark]['FOU'] or 0) - a) < TOL else " (drawn; no schedule row for this mark)")
        put(lid, a * h, "DRAWING-READ", f"neck {mark} {n['position']}: {src} x h {h:.3f} = top +0.95 + founding at the printed minimum 1.50 below EG (ST p.9 n.1, the only printed level) - 0.17 stack - footing H (T-657) = {a * h:.4f} m3; deeper formation (second GB row, ST p.13) would be a design change")

    # ---- BEAMS
    conf = {r["run"]: r for r in csv.DictReader(open(R("research/agents_t277/CONFLICTS_T277.csv")))}
    for lid, l in lines.items():
        if l["item_code"] != "STR.CONC.BEAM":
            continue
        run = l["element_id"].split(":")[-1]
        if run in conf:   # D-27 / D-02 width: drawn vs schedule
            c = conf[run]
            drawn_low = float(c["drawn_m"]) < float(c["schedule_m"])
            v = l["held_low"] if drawn_low else l["held_high"]
            put(lid, v, "DRAWING-READ", f"{c['mark']} {c['storey']}: drawn width {c['drawn_m']} (DXF edges {c['edges']}; geometry first, DELIVERY_MODE s.3) x L {c['L_m']} x D {c['D_m']} less junctions (T-277 ledger) = {v:.4f} m3; schedule {c['schedule_m']} gives {(l['held_high'] if drawn_low else l['held_low']):.4f}; owner Q-61: never the schedule only because printed; {c['designer']} answer replaces it")
    beam_adj = {  # D-04 unlabelled / D-03 two marks: company default 'same mark / adjacent span / 0.60' -> adjacent span on the same line
        "U-C:BEAMS:1F:BAND0005.1": (0.16, 0.40, "B2 20x40 inherited along line (route G, SH04 faces 1478 / 1507)"),
        "U-C:BEAMS:2F:BAND0006.1": (0.62, 1.20, "B15 20x120 adjacent span on the same line (route G, SH02 faces 918 / 919; B15 stand = D-44)"),
        "U-C:BEAMS:2F:BAND0008.1": (0.28, 0.40, "B1 20x40 adjacent span on the same line (route G, SH02 faces 921 / 924)"),
        "U-C:BEAMS:2F:BAND0011.1": (0.28, 0.40, "B1 20x40 adjacent span on the same line (route G, SH02 faces 926 / 929)"),
        "HL:BEAM_LEDGER:2F:BM-2F-015#BAND0001.3": (0.226, 0.75, "B8 20x75 = BAND0001.2, the adjacent span on the same 2F perimeter line (T-559: .1 B3 / .2 B8 / .3 unlabelled 1.13 m x 0.20)"),
        "HL:BEAM_LEDGER:GF:BM-GF-057#BAND0019.2": (0.53, 0.75, "CB3 20x75 = BAND0019.1 and BAND0019.3 on both sides (T-241 / T-110 schedule); marks 'CB3 and B3 (with stair)' D-03, one beam counted once (Q-61 (2))"),
    }
    for lid, l in lines.items():
        e = l["element_id"]
        if e in beam_adj:
            a, d, why = beam_adj[e]
            put(lid, a * d, "DEFAULT", f"plan {a:.3f} m2 x depth {d:.2f}: company default beam depth = adjacent span: {why} = {a * d:.4f} m3; {l.get('designer_item')} answer replaces it")

    # ---- GROUND BEAMS D-34: ST p.13 typical class by CLEAR span (the convention of merged T-761 / route G)
    gb = {"P-C:GROUND_BEAMS:GROUND:BAND0007": 2.40, "P-C:GROUND_BEAMS:GROUND:BAND0025.1": 2.325, "P-C:GROUND_BEAMS:GROUND:BAND0039": 2.07}
    for lid, l in lines.items():
        if l["element_id"] in gb:
            span = gb[l["element_id"]]
            put(lid, l["held_low"], "DEFAULT", f"clear span {span:.2f} < 2.50 -> ST p.13 typical 30x30 (class by clear span, as T-761 / route G): drawn plan {l['held_low'] / 0.30:.4f} m2 x 0.30 = {l['held_low']:.4f} m3; c/c reading gives 30x40 {l['held_high']:.4f}; D-34 answer replaces it")

    # ---- LINTELS: printed bearing 'MIN 40 cm' (ST p.13 lintel note) governs over the 0.15 company default
    lin = {"LINTEL:A-1F-01": (0.15, 0.20, 1.00), "LINTEL:P-1F-01": (0.15, 0.20, 1.30), "LINTEL:W07": (0.20, 0.20, 0.60),
           "LINTEL:W23": (0.20, 0.20, 0.60), "LINTEL:W24": (0.20, 0.20, 1.55)}
    for lid, l in lines.items():
        if l["element_id"] in lin:
            b, d, w = lin[l["element_id"]]
            v = b * d * (w + 0.80)
            put(lid, v, "DRAWING-READ", f"{l['element_id'][7:]}: {b:.2f} x {d:.2f} (T-677 member) x (opening {w:.2f} + 2 x 0.40 printed 'MIN 40 cm' bearing) = {v:.4f} m3; the 0.15 company default applies only where nothing is printed (T-761 lines: F-V761-1 / T-777)")

    # ---- FOUNDATION family
    E = {l["element_id"]: lid for lid, l in lines.items()}
    put(E["P-C:FTG:SH10:T652:10A5"], 3.25 * 1.40 * 0.50, "DEFAULT", "F10 + F one drawn outline 1B1B 3.25 x 1.40 x 0.50 = 2.2750 m3: owner Q-31 answer C 'you can also choose the bigger area' = the drawn outline, PROVISIONAL and flagged (reading A schedule F10 1.96 + F 0.216 = 2.176)")
    v = (3.25 + 0.20) * (1.40 + 0.20) * 0.10
    put(E["U-C:PLAIN_CONCRETE:FOUNDATION:BLINDING_FOOTING:FTG:SH10:T652:10A5"], v, "DEFAULT", f"F10 + F blinding follows its footing reading (Q-31 bigger area): (3.25 + 2 x 0.10) x (1.40 + 2 x 0.10) x 0.10 printed '10 | L x W | 10' (ST p.13) = {v:.4f} m3")
    put(E["HL:STRAP_CONCRETE:SB1:IN_FOOTING:F10_F"], 0.0, "DEFAULT", "SB1 end inside the F10 + F outline: under the Q-31 drawn-outline reading that volume is the footing's own concrete (counted once, T-233 / T-658): 0.0000 m3 here; reading A would give up to 0.385")
    put(E["HL:STRAP_CONCRETE:SB3:IN_FOOTING:F3"], lines[E["HL:STRAP_CONCRETE:SB3:IN_FOOTING:F3"]]["held_low"], "DRAWING-READ", "SB3 0.50 x 0.40 inside the F3 outline above the F3 top = 0.0295 m3; whatever the strap soffit (D-15), the part below the F3 top is F3's own concrete (one solid, counted once)")
    put(E["U-C:PLAIN_CONCRETE:FOUNDATION:BLINDING_GROUND_BEAM"], 9.422514, "DRAWING-READ", "ground-beam blinding reading R 9.4225 m3 (own layer under each drawn beam: every GB soffit >= 0.28 m above every footing top, T-230 / T-233 finding 2); reading L 4.9494 needs a beam at footing level that no plan draws; the second GB row (formation below ~-1.67) is a design change, not drawn")
    put(E["U-C:PLAIN_CONCRETE:FOUNDATION:BLINDING_STRAP"], 0.912684, "ESTIMATE", "strap blinding not printed (D-15; ST p.13 prints no strap section): straps own strip 0.912684 m3 at the printed 10 cm plain concrete every other foundation member stands on (footings, ground beams, pool, boundary A-A) (T-356); D-15 replaces it")
    put(E["P-C:PLAIN_CONCRETE:FOUNDATION:BLINDING_LIFT_RAFT_FF"], 2.256, "DRAWING-READ", "FF lift-raft blinding at the project's printed projection 0.10 (every dimensioned blinding detail: ST p.13 '10 | L x W | 10', p.14 A-A '10', pool wrap 0.10) = 2.2560 m3; the scaled 0.15 reading (2.352) is a scale measurement, not a print (RFI S08 / S23)")
    put(E["P-C:PLAIN_CONCRETE:FOUNDATION:BLINDING_BEYOND_PLOT_LINE"], 0.0, "DEFAULT", "projection past the plot line not built: blinding clipped at the plot line, as the merged T-761 pool blinding (T-667); 0.0000 m3 (D-14 answer could add up to 0.189)")
    put(E["P-C:SCOPE:BOUNDARY_WALL:FOUNDATION:CC-9fd936ab60:BEAM"], (91.94 - 21.45) * 0.20 * 0.60, "DEFAULT", "boundary band = B.W beam 0.20 x 0.60 not counted again inside footings: (91.94 - 21.45) x 0.20 x 0.60 = 8.4588 m3 (owner Q-28 answer A, PROVISIONAL); T-776 restates it per run type (under-building vs fence runs)")
    return P


def build():
    idx = json.load(open(R(INDEX)))
    lines = {l["line_id"]: l for l in idx["lines"]}
    t761 = json.load(open(R(T761)))
    sweep = {r["line_id"]: r for r in t761["ranged_kept_named"]}
    ranged = {lid: {**l, "designer_item": (sweep.get(lid) or {}).get("designer_item")} for lid, l in lines.items()
              if l["item_code"].startswith("STR.CONC") and l["class"] == "HELD" and l["held_low"] is not None}
    assert len(ranged) == 114 and set(ranged) == set(sweep), "ranged set differs from T-761's named set"
    P = points_for(ranged)
    flat = [{"line_id": lid, "item_code": l["item_code"], "element_id": l["element_id"], "low": l["held_low"], "high": l["held_high"],
             "designer_item": l["designer_item"]} for lid, l in sorted(ranged.items(), key=lambda kv: (kv[1]["item_code"], kv[1]["element_id"]))]
    narrow = {f["line_id"] for f in flat if f["high"] - f["low"] < SMALL - TOL}
    extra = sorted(set(P) & narrow)
    for lid in extra:   # the materiality rule decides narrow lines; a family point computed for them is dropped (listed)
        del P[lid]
    prior = t761["ignored_small"]["sum_m3"]
    rows, ignored, safety, isum = apply_materiality(flat, P, prior_ignored=prior)

    # summaries (m3): per item, before (low .. high) and after; candidate concrete totals
    by = {}
    for r in rows:
        b = by.setdefault(r["item_code"], {"lines": 0, "low": 0.0, "high": 0.0, "after": 0.0, "points": 0, "low_by_rule": 0})
        b["lines"] += 1; b["low"] += r["low"]; b["high"] += r["high"]; b["after"] += r["after"]
        b["points" if r["rule"] == "POINT" else "low_by_rule"] += 1
    by_label = {}
    for r in rows:
        by_label[r["label"]] = by_label.get(r["label"], 0.0) + r["after"]
    released = {}
    for l in idx["lines"]:
        if l["item_code"].startswith("STR.CONC") and l["class"] == "RELEASED":
            released[l["item_code"]] = released.get(l["item_code"], 0.0) + l["measured_net"]
    t761_add = {k: v["m3"] for k, v in t761["released_m3_by_item"].items()}
    items = sorted(set(released) | set(t761_add) | set(by))
    totals = {k: {"released_index": round(released.get(k, 0.0), 4), "t761_fill": round(t761_add.get(k, 0.0), 4),
                  "t757_ranged_low": round(by.get(k, {}).get("low", 0.0), 4), "t757_ranged_high": round(by.get(k, {}).get("high", 0.0), 4),
                  "t757_points": round(by.get(k, {}).get("after", 0.0), 4)} for k in items}
    for k, v in totals.items():
        v["before_low"] = round(v["released_index"] + v["t761_fill"] + v["t757_ranged_low"], 4)
        v["before_high"] = round(v["released_index"] + v["t761_fill"] + v["t757_ranged_high"], 4)
        v["after"] = round(v["released_index"] + v["t761_fill"] + v["t757_points"], 4)
    g = lambda f: round(sum(v[f] for v in totals.values()), 4)
    out = {"schema": "T757_FIX_ROWS_V1", "task": "T-757", "candidate_version": idx.get("candidate_version"), "index": INDEX,
           "rule": {"materiality_m3": SMALL, "safety_floor_m3": SAFETY_FLOOR, "source": "owner 2026-11-13 14:00 (DELIVERY_MODE s.3), Lead T-757 r2: no new rule file"},
           "defaults_used": {"roof_buildup_m": ROOF_BUILDUP, "h_GF": 4.50, "h_1F": 4.20, "h_2F_roof": round(13.90 - ROOF_BUILDUP - 9.65, 4), "h_annex": round(4.30 - ROOF_BUILDUP - 0.25, 4),
                             "column_section": "schedule CGT governs (owner company default); drawn outline only at the two mark-CONFLICT positions 10AE / 10E0"},
           "counts": {"ranged_before": len(rows), "ranged_after": 0, "points": sum(1 for r in rows if r["rule"] == "POINT"),
                      "low_by_materiality": len(ignored), "family_points_dropped_as_narrow": extra},
           "ranged_by_item": {k: {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()} for k, v in sorted(by.items())},
           "after_by_label": {k: round(v, 4) for k, v in sorted(by_label.items())},
           "concrete_totals_m3": {"by_item": totals, "before_low": g("before_low"), "before_high": g("before_high"), "after_without_safety": g("after"),
                                  "safety_before": t761["safety_line"]["after"]["net"], "safety_after": safety, "after_with_safety": round(g("after") + safety, 4),
                                  "note": "released lines of the V3.0.79 index + T-761 blank-line fill (merged, unwired) + the 114 ranged lines (this row); MAIN_FILL and other fix-row sets carry no STR.CONC line"},
           "beam_vs_freelancer": {"engine_beam_m3": totals["STR.CONC.BEAM"]["after"], "freelancer_beam_m3": 66.09,
                                  "diff_m3": round(totals["STR.CONC.BEAM"]["after"] - 66.09, 4),
                                  "diff_pct": round((totals["STR.CONC.BEAM"]["after"] - 66.09) / 66.09 * 100, 2),
                                  "label": "UNRESOLVED (T-777 splits it by cause)"},
           "ignored_small": {"t761_lines": t761["ignored_small"]["lines"], "t761_sum_m3": prior, "t757_lines": len(ignored),
                             "t757_width_sum_m3": round(isum - prior, 6), "total_m3": isum, "rows": ignored},
           "safety_line": {"line_id": "NEW:STR.CONC.SAFETY", "item_code": "STR.CONC.SAFETY", "unit": "m3", "label": "SAFETY",
                           "before": t761["safety_line"]["after"]["net"], "after": safety,
                           "basis": f"ONE safety line restated (replaces T-761's {t761['safety_line']['after']['net']:.2f}, never a second line): ignored known pieces T-761 {prior:.4f} m3 on {t761['ignored_small']['lines']} lines + T-757 unresolved widths {isum - prior:.4f} m3 on {len(ignored)} ranged lines = {isum:.4f} m3 -> max(1.00, sum) = {safety:.4f} m3"},
           "rows": [{"line_id": r["line_id"], "item_code": r["item_code"], "element_id": r["element_id"], "unit": "m3",
                     "before": {"class": "HELD", "low": r["low"], "high": r["high"]}, "after": {"class": "RELEASED", "net": r["after"]},
                     "width": r["width"], "label": r["label"], "basis": r["basis"], "designer_item": r["designer_item"], "rule": r["rule"]} for r in rows]}
    md = [f"# T-757 FIX ROWS on {out['candidate_version']}: ranged STR.CONC lines to points (lane S, DELIVERY MODE)", "",
          f"Ranged STR.CONC lines: {len(rows)} -> 0 ({out['counts']['points']} points by the fallback order, {len(ignored)} at the low bound under the owner "
          f"materiality rule, widths logged). Safety line restated {out['safety_line']['before']:.2f} -> {safety:.4f} m3.", "",
          "| item | lines | before low .. high | after | points | low by rule |", "|---|---|---|---|---|---|"]
    md += [f"| {k[9:]} | {v['lines']} | {v['low']:.3f} .. {v['high']:.3f} | {v['after']:.3f} | {v['points']} | {v['low_by_rule']} |" for k, v in out["ranged_by_item"].items()]
    md += ["", "After by label: " + ", ".join(f"{k} {v:.3f} m3" for k, v in out["after_by_label"].items()), "",
           "## Concrete totals (m3): released index + T-761 fill + this row", "", "| item | before low .. high | after |", "|---|---|---|"]
    md += [f"| {k[9:]} | {v['before_low']:.3f} .. {v['before_high']:.3f} | {v['after']:.3f} |" for k, v in totals.items()]
    c = out["concrete_totals_m3"]
    md += [f"| **all (without safety)** | {c['before_low']:.3f} .. {c['before_high']:.3f} | {c['after_without_safety']:.3f} |",
           f"| SAFETY | {c['safety_before']:.2f} | {c['safety_after']:.4f} |", "",
           f"Beam vs freelancer: engine {out['beam_vs_freelancer']['engine_beam_m3']:.3f} m3 vs 66.09 m3 = {out['beam_vs_freelancer']['diff_m3']:+.3f} m3 "
           f"({out['beam_vs_freelancer']['diff_pct']:+.2f} %), UNRESOLVED (T-777).", "",
           "## Rows", "", "| line | item | element | low .. high | after | label | basis |", "|---|---|---|---|---|---|---|"]
    md += [f"| {r['line_id']} | {r['item_code'][9:]} | {r['element_id']} | {r['before']['low']} .. {r['before']['high']} | {r['after']['net']:.4f} | {r['label']} | {r['basis']} |" for r in out["rows"]]
    md += ["", "## IGNORED_SMALL additions (width of the unresolved part, m3)", "", "| line | item | element | low .. high | width | cause |", "|---|---|---|---|---|---|"]
    md += [f"| {g_['line_id']} | {g_['item_code'][9:]} | {g_['element_id']} | {g_['low']} .. {g_['high']} | {g_['width']:.4f} | {g_['cause']} |" for g_ in ignored]
    md += ["", f"SAFETY: {out['safety_line']['basis']}"]
    return out, "\n".join(md) + "\n"


def main(argv):
    od = os.path.join(HERE, "out")
    out, md = build()
    js = json.dumps(out, indent=1, ensure_ascii=False) + "\n"
    if "--check" in argv:
        print(selftest())
        ok = open(os.path.join(od, "FIX_ROWS.json")).read() == js and open(os.path.join(od, "FIX_ROWS.md")).read() == md
        print("rebuild byte-identical:", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    os.makedirs(od, exist_ok=True)
    open(os.path.join(od, "FIX_ROWS.json"), "w").write(js)
    open(os.path.join(od, "FIX_ROWS.md"), "w").write(md)
    print(json.dumps(out["counts"]), json.dumps(out["concrete_totals_m3"]["before_low"]), out["concrete_totals_m3"]["after_without_safety"],
          "safety", out["safety_line"]["after"], json.dumps(out["beam_vs_freelancer"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
