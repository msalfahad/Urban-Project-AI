"""T-166 hand ledger: Alsenan stair, swimming-pool and water-tank reinforcement by bar population (lane S, gate 3;
NO REPO CODE task: research arithmetic only, imports nothing from engine/, changes no released quantity).

    python3 -I research/agents_t166/t166_stair_pool_tank_steel.py --check      (synthetic NON-Alsenan fixture)
    python3 -I research/agents_t166/t166_stair_pool_tank_steel.py ledger [out dir]

Sources (Drive "Alsenan chalet project"; read in the git-excluded private folder, never committed):
  ST7757.pdf (sha256 74da1523...) p.3 ground-beam plan, p.4 / p.5 / p.6 roof-slab plans, p.7 DETAIL OF SWIMMING POOL
  (N.I.S.), p.8 notes 9 and 22, p.14 lift / parapet details, p.15 typical slab detail, p.16 TYPICAL STEEL LAYOUT-STAIR
  SECTION (N.I.S.) and TYPICAL DETAIL OF STAIR BEAM; ST7757 dxf.dxf (sha256 9f9d1179...) for the plan callouts.
Geometry (no new geometry is invented here):
  stairs: research/agents_t111/ledger_summary.json (checker-merged flight ledger: waist m3 per flight -> the sloped waist
          length L = m3 / (width x 0.16), Q-47 A), FLIGHTS.csv (risers, treads, widths);
  pool:   research/agents_t060/T-060_RESULT.md + agents_t063 (D shape, outer 3.50 x 1.75 + half circle r 1.75, walls
          0.20, inner r 1.55), owner Q-26 A (flat floor, inner depth 1.15 m, floor 0.40 m printed on p.7).
Rules: URBAN-REBAR-NET-AND-PROCUREMENT@v1 (kg = count x length x d^2/162, never kg/m3), owner Q-71 (OPEN: count from a
per-metre rate or a spacing; readings A / B / C side by side), Q-46 A, Q-47 A, Q-26 A, Q-50 A cond, Q-62 A cond,
UP-QTY-STATUS-001 (held is never 0). Note 22 (cover >= 2.5 cm, >= 7 cm against soil) is a minimum: no cover is
deducted, as in the slab ledger (T-152); lengths are at the concrete outline.

Count readings (Q-71 OPEN):
  A  N = ceil(rate x W) bars (one per equal strip);  B  N + 1 (a bar on both edges);  C  rate x W unrounded.
  On a CLOSED loop (pool wall perimeter) there are no edges: B = A by its own definition (flagged for the checker).
"""

import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = os.path.dirname(HERE)
EPS = 1e-9
DEV_K = (40, 70)      # p.8 note 9: development / lap not less than 40 d (compression) .. 70 d (tension)
STOCK_M = 12.0        # URBAN-REBAR-NET-AND-PROCUREMENT@v1 stock length (laps on longer closed hoops)
READINGS = ("A", "B", "C")


def kgm(d):
    return d * d / 162.0


def counts(rate, W, closed=False):
    """bars from a rate per metre across an extent W (m)."""
    if not (W > 0) or not (rate > 0):
        raise ValueError("extent and rate must be positive")
    n = int(math.ceil(rate * W - EPS))
    return {"A": n, "B": n if closed else n + 1, "C": rate * W}


def row(element, part, mark, page, d, direction, cnt, length, status, note="", dev_ends=2, closed_len=None):
    """one bar family. cnt = {A,B,C} or an exact int; length per bar (m) or None (HELD length)."""
    if isinstance(cnt, int):
        cnt = {"A": cnt, "B": cnt, "C": float(cnt)}
    r = {"element": element, "part": part, "mark": mark, "page": page, "d": d, "direction": direction,
         "n_A": cnt["A"], "n_B": cnt["B"], "n_C": round(cnt["C"], 4),
         "length_m": None if length is None else round(length, 4), "status": status, "note": note}
    for k in READINGS:
        r["m_" + k] = None if length is None else round(cnt[k] * length, 4)
        r["kg_" + k] = None if length is None else round(cnt[k] * length * kgm(d), 3)
    # HELD, never 0: development / laps (note 9), never part of a measured figure
    if closed_len is not None:          # closed hoop: laps = pieces of stock length
        laps = max(1, math.ceil(closed_len / STOCK_M - EPS))
        dev = [cnt["A"] * laps * k * d / 1000.0 * kgm(d) for k in DEV_K]
    else:
        dev = [cnt["A"] * dev_ends * k * d / 1000.0 * kgm(d) for k in DEV_K]
    r["dev_held_kg"] = "%.2f..%.2f" % tuple(dev) if dev_ends or closed_len else "-"
    r["_dev"] = dev if (dev_ends or closed_len) else [0.0, 0.0]
    return r


# ------------------------------------------------------------------------------------------------ stairs
def flight_rows(fid, width, L, treads, riser, foot_top, head_top, status1, stair_status="", main=(8, 16), going=0.30):
    """one straight flight under the p.16 typical section, with the plan callout 8 ø 16/m.
    status1: status of the plan-printed main bars; the p.16-only families are HELD (TYPICAL_ONLY)."""
    out = []
    out.append(row(fid, "main bottom bars along the waist", "%dø%d/m (plan p.4 / p.5, p.16)" % main, "p.4/p.5 + p.16",
                   main[1], "along flight", counts(main[0], width), L, status1,
                   "length = sloped waist face to face (T-111 drawn waist / (w x 0.16)); continuation into the landing "
                   "or beam HELD (dev)" + stair_status))
    held = "HELD_TYPICAL_ONLY"
    tnote = ("p.16 TYPICAL STEEL LAYOUT-STAIR SECTION (N.I.S.) is the only source; no plan callout or note refers to "
             "it (frozen S8.7 holds the same families)")
    out.append(row(fid, "distribution under the main bars", "ø12/20cm (p.16)", "p.16", 12, "across flight",
                   counts(1 / 0.20, L), width, held, tnote))
    out.append(row(fid, "step bars (tread + riser shape)", "ø8/15 (p.16)", "p.16", 8, "across flight, per tread",
                   {k: v * treads for k, v in counts(1 / 0.15, width).items()}, going + riser, held,
                   tnote + "; %d treads; legs into the waist not dimensioned (dev)" % treads))
    out.append(row(fid, "nosing bar, one per tread", "1ø12 (p.16)", "p.16", 12, "across flight", treads, width, held,
                   tnote + "; exact count (no Q-71 reading)", dev_ends=0))
    for end, lab in (("head", head_top), ("foot", foot_top)):
        if lab is None:
            continue
        rate, d, txt = lab
        out.append(row(fid, "top bars at the %s" % end, txt, "p.16", d, "along flight", counts(rate, width), None,
                       "HELD_LENGTH", "count measured; bar length not dimensioned on the N.I.S. typical section"))
    return out


def strip_rows(sid, depth, length, overlap_len, s87_note, extra=""):
    """landing / turn strip with the horizontal plan callout 8 ø 16/m (bars across the stair, wall to wall)."""
    out = [row(sid, "landing strip bottom bars across the stair", "8ø16/m (plan p.4 / p.5, p.16)", "p.4/p.5 + p.16", 16,
               "across stair (E-W)", counts(8, depth), length, "MEASURED_NET_COUNT_HELD_Q71",
               "wall to wall 2.50 m (T-111: 1.20 + 0.10 well + 1.20); of each bar %.2f m lies over the frozen S8.7 "
               "plate %s (no double count when wired)%s" % (overlap_len, s87_note, extra)),
           row(sid, "landing strip top bars across the stair", "6ø12/m (p.16 landing)", "p.16", 12,
               "across stair (E-W)", counts(6, depth), length, "HELD_TYPICAL_ONLY",
               "p.16 typical landing only; no plan callout"),
           row(sid, "flight bars running through the strip", "8ø16/m (plan, vertical callouts)", "p.4/p.5", 16,
               "along flight (N-S)", counts(8, 1.20), None, "HELD_LENGTH",
               "extent of the flights' bars inside the strip not drawn (bar shape N.I.S.)")]
    return out


def stairs():
    j = json.load(open(os.path.join(RESEARCH, "agents_t111", "ledger_summary.json")))
    dr = {(x["id"], x["element"]): x for x in j["drawn_lines"]}
    ow = {(x["id"], x["element"]): x for x in j["owner_lines"]}

    def Lw(src, fid, w):
        return src[(fid, "WAIST")]["m3"] / (w * 0.16)

    T14 = (6, 14, "6ø14/m (p.16)")
    T_GB = None   # foot on a ground beam: 6ø16/m on p.16; GF foot condition not drawn -> handled as a note row
    F = [  # id, width, treads (drawn), riser, foot top, head top, status note
        ("MS1-L", 1.20, 9, 1 / 6.0, None, T14, " | foot at the GF hall (+1.00): p.16 draws 6ø16/m into a ground beam "
         "at a flight foot, the hall foot is not detailed: foot top bars HELD (6ø14 or 6ø16)"),
        ("MS1-U", 1.20, 11, 1 / 6.0, T14, T14, " | head 0.20 m inside B20 (designer clash, T-111)"),
        ("MS2-L", 1.20, 11, 0.168, T14, T14, ""),
        ("MS2-U", 1.20, 11, 0.168, T14, T14, " | head 0.20 m inside B23 (designer clash, T-111)"),
        ("RS-S", 1.20, 10, 4.5 / 28, None, T14, " | round stair, CALCULATED under Q-50 A cond (T-111); foot runs on "
         "from the HELD curved part"),
        ("RS-A", 1.25, 4, 4.5 / 28, T14, T14, " | round stair short flight, CALCULATED under Q-50 A cond"),
    ]
    rows = []
    for fid, w, t, r, foot, head, note in F:
        st = "MEASURED_NET_COUNT_HELD_Q71" if fid.startswith("MS") else "CALCULATED_COUNT_HELD_Q71"
        rows += flight_rows(fid, w, Lw(dr, fid, w), t, r, foot, head, st, note)
    # owner-basis lengths (STAIR_CONCRETE_V1 census) for the main bars, side by side (information)
    owner_basis = {fid: Lw(ow, fid, 1.20) for fid in ("MS1-L", "MS1-U", "MS2-L", "MS2-U")}
    rows += strip_rows("GF-STRIP (MS1-T turn + well + MS1-LD)", 1.20, 2.50, 1.20, "A1-L1 (1.20 x 1.20)",
                       " | the west 1.30 m crosses the winder turn, whose soffit is not drawn: plan length")
    rows += strip_rows("1F-STRIP (MS2-LD)", 1.20, 2.50, 0.0, "(none; A2-T1 is the 2F arrival strip)",
                       " | the strip has two levels +7.516 / +7.684 (closing riser, not detailed): plan length")
    # held rows (nothing dropped)
    rows.append(row("RS-LD corner landing", "bottom bars", "8ø16/m (flight callouts end on it)", "p.4", 16, "both?",
                    counts(8, 1.15), 1.25, "HELD_DIRECTION",
                    "no callout of its own; which flight's bars cross it, and in which direction, is not drawn; "
                    "candidate one direction shown"))
    rows.append(row("RS-C curved flight", "all families", "8ø16/m along the curve (plan p.4)", "p.4", 16, "curve",
                    counts(8, 1.15), None, "HELD", "owner Q-50: curved part HELD; helicoid soffit not drawn"))
    rows.append(row("MS1-T winders", "step / nosing bars", "ø8/15, 1ø12 (p.16)", "p.16", 8, "-", 0, None, "HELD",
                    "turn HELD (T-111: 4 plan / 5 section winders, soffit not drawn)", dev_ends=0))
    for fid, txt in (("E1 entrance flight", "court +0.15 -> GF +1.00, 2.80 wide"),
                     ("D1 hall -> lobby flight", "lobby +0.30 -> hall +1.00, 1.20 wide")):
        rows.append(row(fid, "all families", "none printed", "p.3 / p.4 / p.16 searched", 16, "-", 0, None, "HELD",
                        txt + ": on no slab plan, no callout; waist thickness not printed; designer item",
                        dev_ends=0))
    return rows, owner_basis


# ------------------------------------------------------------------------------------------------ pool
def d_shape(straight=3.50, depth_rect=1.75, r=1.75, n=720):
    """outer D: straight wall on x = 0 (y -r..r), rectangle to x = depth_rect, half circle centre (depth_rect, 0)."""
    pts = [(0.0, -r), (depth_rect, -r)]
    for i in range(1, n):
        a = -math.pi / 2 + math.pi * i / n
        pts.append((depth_rect + r * math.cos(a), r * math.sin(a)))
    pts += [(depth_rect, r), (0.0, r)]
    return pts


def chord_sum(poly, axis, rate):
    """bar lines of one direction across a polygon: A midpoints of N strips, B N+1 lines edge to edge."""
    from shapely.geometry import LineString, Polygon
    P = Polygon(poly)
    x0, y0, x1, y1 = P.bounds
    lo, hi = (y0, y1) if axis == "x" else (x0, x1)
    H = hi - lo
    n = int(math.ceil(rate * H - EPS))
    pos = {"A": [lo + (k + 0.5) * H / n for k in range(n)], "B": [lo + k * H / n for k in range(n + 1)]}
    out = {}
    for k, ps in pos.items():
        tot = 0.0
        for c in ps:
            ln = LineString([(x0 - 1, c), (x1 + 1, c)]) if axis == "x" else LineString([(c, y0 - 1), (c, y1 + 1)])
            tot += P.intersection(ln).length
        out[k] = (len(ps), tot)
    out["C"] = (rate * H, rate * P.area)
    return out


def pool():
    r_o, r_i, t, straight = 1.75, 1.55, 0.20, 3.50
    P_out = straight + 2 * 1.75 + math.pi * r_o          # 12.4978 (outer face)
    P_in = (straight - 2 * t) + 2 * 1.55 + math.pi * r_i   # 11.0695 (inner face)
    P_cl = (straight - t) + 2 * 1.65 + math.pi * 1.65     # 11.7836 (centre line)
    H = 1.15 + 0.40                                        # wall bars: floor bottom to rim (outline)
    poly = d_shape()
    readings = {  # the p.7 detail prints two zones; the owner ruled the floor flat at 1.15 (Q-26 A)
        # floor: 'long' = the bar lines drawn along the section (labels on the lines), 'trans' = the dot rows (X leader
        # to the top and bottom dots: 6ø14/m deep, 6ø12/m shallow; re-read at 400 dpi this run)
        "R1 deep-end population": dict(vo=(7, 14), vi=(7, 12), h=(12,), long=(7, 14), trans=(6, 14), rim="3ø16",
                                       corner="3ø16"),
        "R2 shallow-end population": dict(vo=(6, 12), vi=(6, 12), h=(10,), long=(6, 12), trans=(6, 12), rim=None,
                                          corner="4ø16"),
    }
    rows = []
    for rd, z in readings.items():
        st = "HELD_DESIGNER (%s)" % rd
        e = "POOL " + rd
        rows.append(row(e, "wall vertical, outer face", "%dø%d/m (p.7)" % z["vo"], "p.7", z["vo"][1], "vertical",
                        counts(z["vo"][0], P_out, closed=True), H, st,
                        "outer perimeter %.4f m (closed loop: B = A); bar 0.40 + 1.15 m, L-leg into the floor HELD"
                        % P_out, dev_ends=1))
        rows.append(row(e, "wall vertical, inner face", "%dø%d/m (p.7)" % z["vi"], "p.7", z["vi"][1], "vertical",
                        counts(z["vi"][0], P_in, closed=True), H, st, "inner perimeter %.4f m%s" % (
                            P_in, "; shallow wall: one U bar over the top, both legs 6ø12/m" if z["vo"] == z["vi"] else ""),
                        dev_ends=1))
        for face, P in (("outer", P_out), ("inner", P_in)):
            rows.append(row(e, "wall horizontal hoops, %s face" % face, "ø%d/20cm (p.7)" % z["h"][0], "p.7",
                            z["h"][0], "horizontal", counts(5, H), P, st, "hoop = %s perimeter %.4f m; laps HELD"
                            % (face, P), dev_ends=0, closed_len=P))
        for lay in ("bottom", "top"):
            for ax, fam in (("x", "long"), ("y", "trans")):
                rate, dia = z[fam]
                cs = chord_sum(poly, ax, rate)
                cnt = {k: cs[k][0] for k in READINGS}
                tot = {k: cs[k][1] for k in READINGS}
                rr = row(e, "floor %s, %s bars" % (lay, "section-line" if fam == "long" else "dot-row"),
                         "%dø%d/m (p.7)" % z[fam], "p.7", dia, ax, cnt, 1.0, st,
                         "outer D 10.936 m2, chords face to face (bars run under the walls, p.7); the plan direction of "
                         "the section is not marked, but the D's chord sums are equal in x and y, so the kg does not "
                         "depend on it")
                for k in READINGS:      # replace count x 1.0 by the chord sums
                    rr["m_" + k] = round(tot[k], 4)
                    rr["kg_" + k] = round(tot[k] * kgm(dia), 3)
                rr["length_m"] = "chords"
                rows.append(rr)
        for what, lab in (("rim bars at the wall top", z["rim"]), ("corner bars floor / wall", z["corner"])):
            if lab is None:
                rows.append(row(e, what, "none printed in this zone", "p.7", 16, "-", 0, None, "NOT_PRINTED",
                                "the shallow wall top carries no group label", dev_ends=0))
                continue
            n = int(lab[0])
            rows.append(row(e, what, lab + " (p.7)", "p.7", 16, "along the wall", n, P_cl, st,
                            "centre-line perimeter %.4f m; exact count; laps HELD" % P_cl, dev_ends=0, closed_len=P_cl))
    return rows, dict(P_out=P_out, P_in=P_in, P_cl=P_cl, H=H)


# ------------------------------------------------------------------------------------------------ tank
def tank():
    return [row("WATER TANK walls / base", "all families", "none printed", "p.6 / p.7 / p.14 / p.15 / p.16 searched",
                12, "-", 0, None, "HELD",
                "p.6 prints only 'WATER TANK PLACE' over two T 18 (T&B) roof panels; no tank wall, base, opening or "
                "member is drawn, noted or scheduled in either discipline (frozen S8.4 agrees); designer item. The "
                "(T&B) panels are in the slab ledger T-152 (2F-011, 2F-013): not repeated here", dev_ends=0)]


# ------------------------------------------------------------------------------------------------ ledger
FIELDS = ["element", "part", "mark", "page", "d", "direction", "n_A", "n_B", "n_C", "length_m", "m_A", "m_B", "m_C",
          "kg_A", "kg_B", "kg_C", "status", "dev_held_kg", "note"]


def ssum(rows, pred, k):
    return sum(r["kg_" + k] for r in rows if pred(r) and r["kg_" + k] is not None)


def ledger(outdir=None):
    outdir = outdir or HERE
    srows, owner_basis = stairs()
    prows, pg = pool()
    trows = tank()
    allr = srows + prows + trows
    with open(os.path.join(outdir, "T166_STEEL.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in allr:
            w.writerow(r)
    S = {}
    is_main = lambda r: r["status"].startswith(("MEASURED", "CALCULATED"))
    S["stairs_plan_printed_count_held_Q71"] = {k: round(ssum(srows, is_main, k), 2) for k in READINGS}
    S["stairs_main_stair_only"] = {k: round(ssum(srows, lambda r: is_main(r) and not r["element"].startswith("RS"), k), 2)
                                   for k in READINGS}
    S["stairs_round_stair_calculated"] = {k: round(ssum(srows, lambda r: is_main(r) and r["element"].startswith("RS"),
                                                        k), 2) for k in READINGS}
    S["stairs_typical_only_HELD"] = {k: round(ssum(srows, lambda r: r["status"] == "HELD_TYPICAL_ONLY", k), 2)
                                     for k in READINGS}
    S["stairs_corner_landing_HELD_candidate"] = {k: round(ssum(srows, lambda r: r["status"] == "HELD_DIRECTION", k), 2)
                                                 for k in READINGS}
    S["stairs_dev_HELD_kg"] = [round(sum(r["_dev"][i] for r in srows if is_main(r)), 2) for i in (0, 1)]
    S["stairs_dev_HELD_typical_kg"] = [round(sum(r["_dev"][i] for r in srows if r["status"] == "HELD_TYPICAL_ONLY"), 2)
                                       for i in (0, 1)]
    S["s87_overlap_GF_strip_EW_kg"] = {k: round(r["n_" + k] * 1.20 * kgm(16), 3) for r in srows
                                       if r["element"].startswith("GF-STRIP") and r["d"] == 16 and r["length_m"]
                                       for k in READINGS}
    for rd in ("R1", "R2"):
        sel = lambda r, rd=rd: r["element"].startswith("POOL " + rd)
        S["pool_%s_HELD" % rd] = {k: round(ssum(prows, sel, k), 2) for k in READINGS}
        S["pool_%s_dev_HELD_kg" % rd] = [round(sum(r["_dev"][i] for r in prows if sel(r)), 2) for i in (0, 1)]
    S["pool_geometry"] = {k: round(v, 4) for k, v in pg.items()}
    S["main_bars_owner_basis_lengths_m"] = {k: round(v, 4) for k, v in owner_basis.items()}
    S["main_bars_owner_basis_kg"] = {k: round(sum(counts(8, 1.20)[k] * v * kgm(16) for v in owner_basis.values()), 2)
                                     for k in READINGS}
    S["freelancer"] = {"stairs_plus_dome_t": 3.9, "stairs_plus_dome_m3": 21.8328, "pool_t": 1.5, "pool_m3": 12.348,
                       "tank": "no row (tank T&B inside his slabs lump)"}
    S["rows"] = len(allr)
    json.dump(S, open(os.path.join(outdir, "T166_SUMMARY.json"), "w"), indent=1, sort_keys=True)
    return S


# ------------------------------------------------------------------------------------------------ fixture
def check():
    bad = []

    def eq(name, got, want, tol=1e-3):
        ok = abs(got - want) <= tol
        print(("PASS " if ok else "FAIL ") + name + ": %s (want %s)" % (round(got, 4), want))
        if not ok:
            bad.append(name)

    # F1 straight flight, NOT Alsenan: 2.00 wide, 10 risers 0.175, 9 treads 0.28, waist 0.15 (sloped L by hand)
    L = math.hypot(9 * 0.28, 10 * 0.175)          # 3.0681
    rows = flight_rows("FX", 2.00, L, 9, 0.175, (5, 12, "5ø12/m"), (5, 12, "5ø12/m"), "MEASURED_NET_COUNT_HELD_Q71",
                       main=(10, 12), going=0.28)
    m = rows[0]
    eq("F1 main 10ø12/m over 2.00: A 20 bars", m["n_A"], 20, 0)
    eq("F1 main B 21 bars", m["n_B"], 21, 0)
    eq("F1 main A kg 20 x 3.0681 x 0.8889 = 54.544", m["kg_A"], 20 * L * 144 / 162)
    rows = flight_rows("FX", 2.00, L, 9, 0.175, None, None, "X", going=0.28)
    eq("F1 main 8ø16/m: A ceil(16.0) = 16 (exact multiple, not 17)", rows[0]["n_A"], 16, 0)
    eq("F1 distribution ø12/20: A ceil(3.0681/0.2)=16", rows[1]["n_A"], 16, 0)
    eq("F1 step bars ø8/15 over 2.00: ceil(13.33)=14 x 9 treads = 126", rows[2]["n_A"], 126, 0)
    eq("F1 step bar length 0.28 + 0.175 = 0.455", rows[2]["length_m"], 0.455)
    eq("F1 nosing 9 x 2.00 m x 0.8889 = 16.0 kg", rows[3]["kg_A"], 16.0)
    # landing strip 1.50 deep x 3.10 wide
    s = strip_rows("LX", 1.50, 3.10, 0.0, "-")
    eq("L1 strip bottom 8ø16/m over 1.50: A 12, B 13", s[0]["n_A"] * 100 + s[0]["n_B"], 1213, 0)
    eq("L1 strip bottom A kg 12 x 3.10 x 1.5802 = 58.785", s[0]["kg_A"], 12 * 3.10 * 256 / 162)
    assert s[2]["kg_A"] is None and s[2]["status"].startswith("HELD"), "held length must stay None, never 0"
    print("PASS L1 strip flight-bar continuation stays HELD (None, not 0)")
    # mirror / rotation: a D-shape floor and a rectangle mirrored and rotated give the same chord sums
    rect = [(0, 0), (3.0, 0), (3.0, 2.0), (0, 2.0)]
    cs = chord_sum(rect, "x", 5)                  # bars in x across y = 2.0: A 10 x 3.0 = 30.0, B 11 x 3.0 = 33.0
    eq("R1 rectangle 5/m x 2.0: A 10 bars x 3.0 = 30.0 m", cs["A"][1], 30.0)
    eq("R1 rectangle B 11 bars x 3.0 = 33.0 m", cs["B"][1], 33.0)
    eq("R1 rectangle C 5 x 6.0 m2 = 30.0 m", cs["C"][1], 30.0)
    rot = [(-y, x) for x, y in rect]              # 90 degrees: the same bars now run in y
    eq("R1 rotated 90 deg, bars in y: A 30.0 m", chord_sum(rot, "y", 5)["A"][1], 30.0)
    mir = [(-x, y) for x, y in rect][::-1]        # mirror
    eq("R1 mirrored: A 30.0 m", chord_sum(mir, "x", 5)["A"][1], 30.0)
    mm = [(x * 1000, y * 1000) for x, y in rect]  # millimetres -> metres
    eq("R1 mm input / 1000: A 30.0 m", chord_sum([(x / 1000, y / 1000) for x, y in mm], "x", 5)["A"][1], 30.0)
    D = d_shape(2.0, 1.0, 1.0)                    # small D: area 2.0 + pi/2 = 3.5708
    eq("D2 small D area by C: 4/m x 3.5708 = 14.283 m", chord_sum(D, "x", 4)["C"][1], 4 * (2.0 + math.pi / 2), 2e-3)
    # T1 rectangular tank wall NOT Alsenan: 2.40 x 2.00 plan, 1.80 high, 6ø12/m vertical on a closed loop with a
    # 0.60 x 0.60 opening: loop 8.80 m -> A ceil(52.8)=53 = B (closed), bars cut by the opening ceil(6 x 0.60)=4
    P = 2 * (2.40 + 2.00)
    c = counts(6, P, closed=True)
    eq("T1 closed loop 6/m x 8.80: A 53", c["A"], 53, 0)
    eq("T1 closed loop: B = A = 53", c["B"], 53, 0)
    cut = counts(6, 0.60)["A"]
    eq("T1 vertical metres (53 x 1.80 - 4 x 0.60) = 93.0", c["A"] * 1.80 - cut * 0.60, 93.0)
    h = row("T1", "hoops", "ø10/20", "-", 10, "h", counts(5, 1.80), P, "X", dev_ends=0, closed_len=P)
    eq("T1 hoops ø10/20 over 1.80: A 9 x 8.80 = 79.2 m", h["m_A"], 79.2)
    eq("T1 hoop under 12 m stock: 1 lap each, 40d..70d -> dev low 9 x 0.40 x 0.6173 = 2.222", h["_dev"][0],
       9 * 0.40 * 100 / 162)
    # missing reading stays HELD
    t = tank()[0]
    assert t["kg_A"] is None and t["status"] == "HELD", "a missing reading must stay HELD, never 0"
    print("PASS M1 tank with no printed reinforcement: HELD, kg None (not 0)")
    for bad_in in ((8, 0.0), (0, 1.2), (8, -1.0)):
        try:
            counts(*bad_in)
            bad.append("invalid %s accepted" % (bad_in,))
            print("FAIL invalid input accepted", bad_in)
        except ValueError:
            print("PASS invalid input refused", bad_in)
    print("ALL PASS" if not bad else "FAILED: %s" % bad)
    return not bad


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        sys.exit(0 if check() else 1)
    if len(sys.argv) > 1 and sys.argv[1] == "ledger":
        print(json.dumps(ledger(sys.argv[2] if len(sys.argv) > 2 else None), indent=1, sort_keys=True))
        sys.exit(0)
    print(__doc__)
