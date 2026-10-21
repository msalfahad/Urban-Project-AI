"""T-149 hand ledger: Alsenan beam steel by bar population, per beam and span (lane S, gate 3; NO REPO CODE task).

A research script that only does the arithmetic of a hand table typed from the drawings; it imports nothing from
engine/ and changes no released quantity.

    python3 -I research/agents_t149/t149_beam_steel.py [--check] [--spans T149_SPANS_INPUT.csv]

Inputs (typed by hand from the issued structural PDF ST7757, read at 400 dpi this run; never copied client files):
  * SIMPLE: p.10 "Schedule of Simple Beams": B (cm), D (cm), BOTTOM BARS, TOP BARS, STIRRUPS/m, REMARKS (side bars
    "2ø12/30cm" ..., and a link-arrangement symbol: two nested links on B17, B19 .. B26, SB1, SB3; three on SB2).
  * CONT: p.11 "SCHEDULE OF CONTINUES BEAMS (2 SPAN)" and p.12 "(THREE SPAN)": per beam B x H, MIDDLE REINT., and the
    bar lines drawn per span (top corner bars, the bar over each interior support, bottom bars, STIR n ø d /m). The
    typical details at the head of p.11 / p.12 dimension the bar over an interior support as 0.22 Ln into each
    adjacent span measured from the support face (Ln = support axis to support axis, the dimension line between the
    dashed axes), and the first link 7.5 cm from the face.
  * p.8 general notes: 9 (Arabic: anchorage length of starter bars, "Development Length", not less than 70 d in tension
    zones and 40 d in compression zones), 21 (additional side bars 2 / 3 / 4 ø12 in beams deeper than 60 cm by beam
    width unless stated otherwise), 22 (cover not less than 2.5 cm in columns, slabs and beams).
  * p.15 "BEAM CARRYING PLANTED COL. DETAIL": 4 ø16 in the carrying beam, length not dimensioned.
  * T149_SPANS_INPUT.csv: written by t149_spans.py from the T-110 beam register (+ the T-145 CB5 span 2 row) and the
    structural DXF: clear length, span order, support widths, Ln.
Comparison only (never used in a hand value): frozen engine research S6 (research/alsenan_superstructure_beam_rebar_s6).

Rules: URBAN-REBAR-NET-AND-PROCUREMENT@v1 (kg = count x length x kg/m; net and procurement apart; laps only from the
structural notes; hooks / bends only from a detail with a length, else BLOCKED_DETAILING; never kg/m3),
URBAN-BEAM-TYPE-FROM-SCHEDULE-LENGTH-FROM-PLAN@v1 (bars from the schedule row, length from the plan),
URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1 (concrete only; bars are not split by it), owner Q-61 C (register holds),
owner Q-71 (OPEN: count from a per-metre notation -> readings A ceil, B A + 1, C fractional; HELD), UP-QTY-STATUS-001.
Writes T149_BEAMS.csv (one row per beam span and component) and T149_SUMMARY.json.
"""

import csv
import json
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
S6 = os.path.join(ROOT, "research/alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_OCCURRENCES.csv")

COVER = 0.025          # p.8 note 22, beams
DEV_K = (40, 70)       # p.8 note 9 (40 d compression .. 70 d tension); zone not printed -> range, HELD
STOCK_M = 12.0         # URBAN-REBAR-NET-AND-PROCUREMENT@v1 stock_length_m
K_SUP = 0.22           # p.11 / p.12 typical detail: bar over an interior support runs 0.22 Ln into each span
FIRST_LINK = 0.075     # p.11 / p.12 typical detail: first link 7.5 cm from the support face (continuous beams)


def kgm(d):
    """unit mass d^2 / 162 (the project method)."""
    return d * d / 162.0


# p.10 Schedule of Simple Beams: mark -> (B cm, D cm, (n, d) bottom, (n, d) top, (rate, d) links, side remark, links)
SIMPLE = {
    "B1": (20, 40, (2, 14), (2, 12), (6, 8), None, 1),
    "B2": (20, 40, (3, 16), (2, 12), (6, 8), None, 1),
    "B3": (20, 40, (4, 16), (2, 12), (6, 8), None, 1),
    "B4": (20, 50, (4, 16), (2, 12), (6, 8), None, 1),
    "B5": (20, 50, (4, 18), (2, 12), (6, 8), None, 1),
    "B6": (25, 50, (5, 18), (2, 12), (6, 8), None, 1),
    "B7": (20, 75, (3, 16), (2, 12), (6, 8), (2, 12, 30), 1),
    "B8": (20, 75, (4, 16), (2, 12), (6, 8), (2, 12, 30), 1),
    "B9": (20, 75, (4, 18), (2, 12), (6, 8), (2, 12, 30), 1),
    "B10": (20, 75, (5, 18), (2, 12), (6, 8), (2, 12, 30), 1),
    "B11": (20, 75, (6, 18), (2, 12), (6, 8), (2, 12, 30), 1),
    "B12": (25, 75, (6, 18), (2, 14), (6, 8), (2, 12, 30), 1),
    "B13": (25, 75, (7, 18), (2, 14), (7, 8), (2, 12, 30), 1),
    "B14": (20, 75, (4, 18), (2, 12), (7, 8), (2, 12, 30), 1),
    "B15": (20, 120, (4, 16), (6, 18), (10, 8), (2, 12, 30), 1),
    "B16": (30, 75, (5, 18), (3, 14), (10, 10), (2, 16, 20), 1),
    "B17": (45, 75, (10, 18), (4, 14), (6, 8), (2, 12, 30), 2),
    "B18": (35, 75, (10, 18), (3, 14), (5, 8), (2, 12, 30), 1),
    "B19": (40, 75, (11, 18), (4, 14), (10, 10), (2, 14, 20), 2),
    "B20": (40, 75, (11, 18), (11, 18), (10, 8), (2, 12, 30), 2),
    "B21": (45, 75, (12, 18), (4, 14), (10, 10), (2, 12, 30), 2),
    "B22": (50, 75, (14, 18), (5, 14), (5, 8), (2, 12, 30), 2),
    "B23": (45, 75, (11, 18), (11, 18), (10, 8), (2, 12, 30), 2),
    "B24": (50, 75, (5, 16), (10, 18), (5, 8), (2, 12, 30), 2),
    "B25": (55, 75, (15, 18), (5, 14), (6, 8), (2, 12, 30), 2),
    "B26": (65, 85, (19, 18), (6, 14), (10, 10), (2, 16, 20), 2),
    "B27": (90, 85, (22, 20), (9, 16), (10, 10), (2, 16, 20), 1),
    "B28": (25, 75, (3, 16), (2, 14), (10, 10), (2, 12, 30), 1),
    "B29": (25, 75, (7, 18), (2, 14), (5, 8), (2, 12, 30), 1),
    "CA": (30, 50, (5, 18), (5, 18), (8, 8), None, 1),
}

# p.11 / p.12 continuous beams, typed per beam: B x H cm, middle (side) reinforcement, per span (top corner bars,
# bottom bars, links / m) and the bars over the supports. "sup" entries: (n, d, first support k, last support k):
# a bar over supports k .. m runs 0.22 Ln into the span before k, through every span between, 0.22 Ln into the span
# after m. "end_start": the bar starts at the outer end of span 1 (drawn hooked at the end support; CB8 5 ø18).
# top None = no corner bar drawn in that span (CB3 span 2, CB8 span 1).
CONT = {
    "CB1": dict(B=35, H=75, side=(2, 12, 30), spans=[((3, 14), (4, 18), (5, 8)), ((3, 14), (5, 18), (9, 10))],
                sup=[(8, 18, 1, 1)]),
    "CB2": dict(B=20, H=50, side=None, spans=[((2, 12), (3, 16), (6, 8)), ((2, 12), (3, 14), (6, 8))],
                sup=[(4, 16, 1, 1)]),
    "CB4": dict(B=20, H=50, side=None, spans=[((2, 12), (3, 14), (6, 8)), ((2, 12), (3, 16), (8, 8))],
                sup=[(4, 16, 1, 1)]),
    "CB5": dict(B=20, H=40, side=None, spans=[((2, 12), (3, 14), (7, 8)), ((2, 12), (4, 16), (7, 8))],
                sup=[(4, 16, 1, 1)]),
    "CB6": dict(B=20, H=75, side=(2, 12, 30), spans=[((2, 12), (3, 16), (5, 8)), ((2, 12), (4, 18), (6, 8))],
                sup=[(4, 18, 1, 1)]),
    "CB7": dict(B=20, H=75, side=(2, 12, 30), spans=[((2, 12), (3, 16), (7, 8)), ((2, 12), (3, 16), (7, 8))],
                sup=[(5, 18, 1, 1)]),
    "CB10": dict(B=25, H=50, side=None, spans=[((2, 12), (3, 16), (6, 8)), ((2, 12), (4, 18), (6, 8))],
                 sup=[(4, 18, 1, 1)]),
    "CB12": dict(B=25, H=75, side=(2, 12, 30), spans=[((2, 12), (5, 18), (9, 8)), ((2, 12), (3, 16), (7, 8))],
                 sup=[(6, 18, 1, 1)]),
    "CB13": dict(B=30, H=50, side=None, spans=[((3, 12), (4, 16), (7, 8)), ((3, 12), (4, 18), (7, 10))],
                 sup=[(5, 18, 1, 1)]),
    "CB3": dict(B=20, H=75, side=(2, 12, 30),
                spans=[((2, 12), (3, 16), (5, 8)), (None, (3, 16), (5, 8)), ((2, 12), (3, 16), (9, 8))],
                sup=[(3, 16, 1, 2)]),
    "CB8": dict(B=30, H=75, side=(2, 12, 30),
                spans=[(None, (3, 14), (5, 8)), ((3, 12), (7, 18), (8, 8)), ((3, 12), (4, 16), (5, 8))],
                sup=[(5, 18, 1, 1, "end_start"), (6, 18, 2, 2)]),
    "CB9": dict(B=20, H=50, side=None,
                spans=[((2, 12), (4, 16), (7, 8)), ((2, 12), (3, 14), (10, 8)), ((2, 12), (3, 14), (6, 8))],
                sup=[(4, 18, 1, 1), (3, 16, 2, 2)]),
    "CB11": dict(B=30, H=75, side=(2, 12, 30),
                 spans=[((2, 12), (6, 18), (10, 8)), ((2, 12), (4, 16), (6, 8)), ((2, 12), (4, 16), (5, 8))],
                 sup=[(8, 18, 1, 1), (4, 16, 2, 2)]),
}

# Register holds (T-110 / T-145) and the hand candidates (from the register evidence; never one value chosen)
CANDIDATES = {
    "BM-GF-059": ["B24"], "BM-1F-032": ["B2"], "BM-2F-015": ["B8", "B3"], "BM-2F-016": ["B15", "B1", "B2", "B3"],
    "BM-2F-017": ["B1"], "BM-2F-018": ["B1"], "BM-GF-060": ["B7"], "BM-1F-039": ["B4"],
}
# "(With Stair)" printed beside the B3 label (DXF S-TEXT, 0.03 m above the mark): GF and 1F; the p.16 "TYPICAL DETAIL OF
# STAIR BEAM" prints exactly B3's bars (2 ø12 top, 4 ø16 bottom, 6 ø8/m) on a cranked profile without dimensions
STAIR_BEAMS = {"BM-GF-015": "GF", "BM-1F-001": "1F"}
NO_BARS = {  # drawn concrete with no bar printed anywhere -> unquantified (never 0)
    "upstand": "upstand on a beam: section prints the outline only, no bars (D-26 / T-043)",
    "strip": "projection band: no schedule row, no section with bars (owner Q-61 C(5)(6), designer D-05 / D-26)",
    "box": "projection band: no schedule row, no section with bars (owner Q-61 C(6), designer D-05 / D-26)",
}


def link_counts(rate, L, zone):
    a = math.ceil(rate * zone - 1e-9)
    return a, a + 1, rate * L


def link_paths(B, D, nl):
    """closed link on the core: perimeter at the cover; nested links (symbol) are not dimensioned:
    lower = one outer link + two legs per extra link; upper = nl outer links. Hooks not printed (unquantified)."""
    b, d = B / 100 - 2 * COVER, D / 100 - 2 * COVER
    per = 2 * (b + d)
    return per + 2 * (nl - 1) * d, nl * per


class Ledger:
    def __init__(self):
        self.rows = []

    def add(self, **kw):
        self.rows.append(kw)

    def bars(self, base, comp, n, d, length, state, note, ends=0, parent=None):
        kg = n * length * kgm(d)
        self.add(**base, parent=parent or state, component=comp, bars="%d ø%d" % (n, d), count=n, dia=d, length_m=round(length, 4),
                 kg=round(kg, 3), kg_hi="", state=state, note=note)
        if ends:
            lo, hi = (n * ends * k * d / 1000 * kgm(d) for k in DEV_K)
            self.add(**base, parent=state, component=comp + " ends (note 9, 40d..70d)", bars="%d ø%d x %d ends" % (n, d, ends),
                     count=n * ends, dia=d, length_m="", kg=round(lo, 3), kg_hi=round(hi, 3), state="HELD_RANGE",
                     note="development / lap at bar ends; p.8 note 9 prints 70 d tension / 40 d compression for "
                          "starter bars (Arabic 'اشاير'); zone not printed, applying it to beam bar ends is itself "
                          "unconfirmed -> range, HELD")
        return kg

    def links(self, base, rate, d, L, zone, B, D, nl, why, parent="RELEASED"):
        a, b, c = link_counts(rate, L, zone)
        lo_p, hi_p = link_paths(B, D, nl)
        u = kgm(d)
        self.add(**base, parent=parent, component="links %g ø%d/m (Q-71)" % (rate, d), bars="A %d / B %d / C %.3f" % (a, b, c),
                 count="", dia=d, length_m=round(lo_p, 4), kg=round(a * lo_p * u, 3), kg_hi=round(b * hi_p * u, 3),
                 state="HELD_RANGE", note="count rule = owner Q-71 (open); zone %s; path %.3f .. %.3f m (%d link%s, "
                 "hooks not printed); kg A %.3f / B %.3f / C %.3f at the lower path" % (
                     why, lo_p, hi_p, nl, "s" if nl > 1 else "", a * lo_p * u, b * lo_p * u, c * lo_p * u),
                 links_A=a, links_B=b, links_C=round(c, 3), kg_A=round(a * lo_p * u, 3), kg_B=round(b * lo_p * u, 3),
                 kg_C=round(c * lo_p * u, 3), kg_B_upper=round(b * hi_p * u, 3))

    def side(self, base, side, L, parent="RELEASED"):
        n, d, s = side
        self.add(**base, parent=parent, component="side bars %dø%d/%dcm" % side, bars="%d ø%d (minimum any reading gives)" % (n, d),
                 count=n, dia=d, length_m=round(L, 4), kg=round(n * L * kgm(d), 3), kg_hi="", state="HELD_RANGE",
                 note="schedule remark '%dø%d/%dcm' (p.8 note 21 'unless stated otherwise'): whether %d bars in all or "
                      "%d per face per %d cm of depth is not printed, and a count from a spacing is owner Q-71; the "
                      "kg shown is the 2-bar minimum only (HELD)" % (n, d, s, n, n, s))


def simple_span(led, r, mark, state, cause, cand=None):
    B, D, bot, top, st, side, nl = SIMPLE[mark]
    L = float(r["clear_length_m"] or r["length_m"])
    Lreg = float(r["length_m"])
    base = dict(row_id=r["row_id"], member_id=r["member_id"], floor=r["floor"], mark=mark, kind="simple",
                span="", clear_length_m=round(L, 4), cause=cause, cand=cand or "")
    led.bars(base, "bottom", bot[0], bot[1], L, state, "schedule p.10 %s; clear span face to face" % mark, ends=2)
    led.bars(base, "top", top[0], top[1], L, state, "schedule p.10 %s; clear span face to face" % mark, ends=2)
    if Lreg - L > 0.0005:
        for comp, (n, d) in (("bottom", bot), ("top", top)):
            led.bars(base, comp + " over the end column inside the register span", n, d, Lreg - L, "HELD_RANGE",
                     "register length runs to the outer face of an end column (%.3f m); bars there are anchorage "
                     "into the support, already inside the note-9 range: kept apart, never added twice" % (Lreg - L),
                     parent=state)
    led.links(base, st[0], st[1], L, L, B, D, nl, "clear span (no first-link offset printed for simple beams)",
              parent=state)
    if side:
        led.side(base, side, L, parent=state)


def main(argv):
    spans_path = os.path.join(HERE, "T149_SPANS_INPUT.csv")
    if "--spans" in argv:
        spans_path = argv[argv.index("--spans") + 1]
    rows = list(csv.DictReader(open(spans_path, encoding="utf-8")))
    led = Ledger()
    cb_groups = defaultdict(dict)
    for r in rows:
        mark, st = r["mark"], r["status"]
        smark = r["schedule_mark"]
        typ = r["type"]
        if smark in CONT and r["span_index"]:
            cb_groups[(r["floor"], smark)][int(r["span_index"])] = r
            continue
        if "two marks" in typ:   # GF CB3 span 2 / "B3 (With Stair)": handled with CB3
            cb_groups[(r["floor"], "CB3")][2] = r
            continue
        base = dict(row_id=r["row_id"], member_id=r["member_id"], floor=r["floor"], mark=mark, kind="simple",
                    span="", clear_length_m=r.get("clear_length_m") or r["length_m"], cause="", cand="")
        if "upstand" in typ:
            led.add(**base, component="all bars", bars="not printed", count="", dia="", length_m=r["length_m"], kg="",
                    kg_hi="", state="UNQUANTIFIED", note=NO_BARS["upstand"])
            continue
        if st == "CALCULATED" and r["member_id"] in STAIR_BEAMS:
            simple_span(led, r, smark, "HELD_DEFINED", "'(With Stair)' beside the B3 label: p.16 TYPICAL DETAIL OF "
                        "STAIR BEAM draws the bars on a cranked profile with no dimensions; the plan length is only a "
                        "lower bound of each bar (BLOCKED_DETAILING)")
            continue
        if st == "CALCULATED" and smark in SIMPLE:
            if "ring beam" in typ:   # 1F west dome ring: arc pieces, centreline length = m3 / (B x D)
                B, D = SIMPLE[smark][0] / 100, SIMPLE[smark][1] / 100
                r = dict(r, length_m=str(round(float(r["m3_low"] if r.get("m3_low") else 0) / (B * D), 4)))
            cause = ""
            if "planted" in typ:
                cause = "p.15 planted-column extra 4 ø16 HELD (length not dimensioned)"
            simple_span(led, r, smark, "RELEASED", cause)
            if "planted" in typ:
                led.add(row_id=r["row_id"], member_id=r["member_id"], floor=r["floor"], mark=smark, kind="simple",
                        span="", clear_length_m="", cause=cause, cand="", component="planted-column extra (p.15)",
                        bars="4 ø16", count=4, dia=16, length_m="", kg="", kg_hi="", state="UNQUANTIFIED",
                        note="p.15 BEAM CARRYING PLANTED COL. DETAIL: 4 ø16 in the beam, length not dimensioned")
            continue
        if st == "CONFLICT" and smark in SIMPLE:
            simple_span(led, r, smark, "HELD_DEFINED", "register CONFLICT: " + "schedule width vs drawn width, "
                        "owner Q-61 C(1), designer D-27 (bar count and length do not depend on the width; the link "
                        "path does)")
            continue
        mid = r["member_id"]
        if mid in CANDIDATES:
            for c in CANDIDATES[mid]:
                rr = dict(r, clear_length_m=r.get("clear_length_m") or r["length_m"])
                try:
                    float(rr["clear_length_m"])
                except ValueError:   # ring drawn as arc pieces: centreline length = candidate m3 / (B x D)
                    B, D = SIMPLE[c][0] / 100, SIMPLE[c][1] / 100
                    rr["clear_length_m"] = rr["length_m"] = str(round(float(r["m3_low"]) / (B * D), 4))
                simple_span(led, rr, c, "HELD_CANDIDATE", "register HELD (%s): candidate %s of %s" % (
                    "designer D-28" if mid == "BM-1F-039" else "owner Q-61 C(4), designer D-04", c,
                    " / ".join(CANDIDATES[mid])), cand="%s|%s" % (mid, c))
            continue
        why = NO_BARS["box"] if "box" in typ else NO_BARS["strip"]
        led.add(**base, component="all bars", bars="not printed", count="", dia="", length_m=r["length_m"], kg="",
                kg_hi="", state="UNQUANTIFIED", note=why + "; register %s" % st)
    for (floor, cb), sp in sorted(cb_groups.items()):
        cont_member(led, floor, cb, sp)
    return led


def cont_member(led, floor, cb, sp):
    spec = CONT[cb]
    n = len(spec["spans"])
    held_member = None
    for k, r in sp.items():
        if r["status"] == "CONFLICT":
            held_member = "register CONFLICT: schedule width vs drawn width, owner Q-61 C(1), designer %s" % (
                "D-02" if cb == "CB10" else "D-27")
    L = {k: float(sp[k]["clear_length_m"] or sp[k]["length_m"]) for k in sp}
    Ln_lo = {k: float(sp[k]["Ln_lo"]) for k in sp if sp[k].get("Ln_lo")}
    Ln_hi = {k: float(sp[k]["Ln_hi"]) for k in sp if sp[k].get("Ln_hi")}
    w = {}   # interior support k between span k and k+1
    for k in range(1, n):
        if k in sp and sp[k].get("w_right_lo"):
            w[k] = float(sp[k]["w_right_lo"])
    span_hold = {k: None for k in range(1, n + 1)}
    if cb == "CB3":
        span_hold[2] = "GF CB3 span 2 carries two marks, CB3 and 'B3 (With Stair)' (owner Q-61 C(2), designer D-03)"
    cand_grp = None
    if cb == "CB3" and 2 in sp:
        cand_grp = sp[2]["member_id"]
        simple_span(led, sp[2], "B3", "HELD_CANDIDATE", span_hold[2] + ": candidate B3 of CB3 / B3",
                    cand="%s|B3" % cand_grp)
    for k in range(1, n + 1):
        r = sp.get(k)
        if r is None:
            continue
        top, bot, st = spec["spans"][k - 1]
        state = "RELEASED"
        cause = held_member or span_hold[k] or ""
        cand = ""
        if cause:
            state = "HELD_DEFINED"
        if span_hold[k] and cand_grp:
            state, cand = "HELD_CANDIDATE", "%s|CB3" % cand_grp
            cause += ": candidate CB3 of CB3 / B3"
        base = dict(row_id=r["row_id"], member_id=r["member_id"], floor=floor, mark=cb, kind="continuous",
                    span="%d/%d" % (k, n), clear_length_m=round(L[k], 4), cause=cause, cand=cand)
        led.bars(base, "bottom", bot[0], bot[1], L[k], state,
                 "p.11/p.12 %s span %d bottom; clear span face to face" % (cb, k), ends=2)
        Lreg = float(r["length_m"])
        if Lreg - L[k] > 0.0005:
            for comp, nd in (("bottom", bot), ("top corner", top)):
                if nd:
                    led.bars(base, comp + " over the end column inside the register span", nd[0], nd[1],
                             Lreg - L[k], "HELD_RANGE", "register length runs to the outer face of an end column "
                             "(%.3f m); anchorage into the support, inside the note-9 range: kept apart" % (Lreg - L[k]),
                             parent=state)
        if top:
            # zones taken by the support bars at this span's interior supports (0.22 Ln of THIS span each)
            zones = 0
            if k > 1:
                zones += 1
            if k < n:
                zones += 1
            ln = Ln_lo.get(k)
            if ln is None:
                state_t, note_t, length = "HELD_RANGE", "Ln not established at this span", 0.0
            else:
                length = L[k] - zones * K_SUP * ln
                state_t, note_t = state, ("p.11/p.12 %s span %d top corner bars: clear span less %d x 0.22 Ln "
                                          "(Ln %.4f) taken by the support bars; lap with them HELD" % (cb, k, zones, ln))
            led.bars(base, "top corner", top[0], top[1], length, state_t, note_t, ends=2)
            if Ln_hi.get(k) and Ln_hi[k] != ln:
                led.add(**base, component="top corner (Ln range)", bars="%d ø%d" % top, count=top[0], dia=top[1],
                        length_m="", kg=0.0, kg_hi=round(top[0] * zones * K_SUP * (Ln_hi[k] - ln) * kgm(top[1]), 3),
                        state="HELD_RANGE", note="Ln %.4f .. %.4f (end support not closed on the DXF)" % (ln, Ln_hi[k]))
        zone = L[k] - 2 * FIRST_LINK
        led.links(base, st[0], st[1], L[k], zone, spec["B"], spec["H"], 1, "clear span less 2 x 7.5 cm (detail)",
                  parent=state)
        if spec["side"]:
            led.side(base, spec["side"], L[k], parent=state)
    for s in spec["sup"]:
        nb, d, k1, k2 = s[:4]
        end_start = len(s) > 4
        r = sp.get(k1)
        parts, hold = [], held_member
        lo = hi = 0.0
        if end_start:
            parts.append("span 1 clear %.4f" % L[1])
            lo += L[1]
            hi += L[1]
        else:
            if k1 not in Ln_lo:
                hold = hold or "Ln of span %d not established" % k1
            lo += K_SUP * Ln_lo.get(k1, 0)
            hi += K_SUP * Ln_hi.get(k1, Ln_lo.get(k1, 0))
            parts.append("0.22 x Ln%d %.4f" % (k1, Ln_lo.get(k1, 0)))
        for k in range(k1, k2 + 1):
            lo += w.get(k, 0)
            hi += w.get(k, 0)
            parts.append("support %d %.4f" % (k, w.get(k, 0)))
            if k < k2:
                lo += L[k + 1]
                hi += L[k + 1]
                parts.append("span %d clear %.4f" % (k + 1, L[k + 1]))
                if span_hold.get(k + 1):
                    hold = hold or span_hold[k + 1]
        lo += K_SUP * Ln_lo.get(k2 + 1, 0)
        hi += K_SUP * Ln_hi.get(k2 + 1, Ln_lo.get(k2 + 1, 0))
        parts.append("0.22 x Ln%d %.4f" % (k2 + 1, Ln_lo.get(k2 + 1, 0)))
        cand = ""
        state = "HELD_DEFINED" if hold else "RELEASED"
        if cand_grp and any(span_hold.get(k + 1) for k in range(k1, k2)):
            state, cand, hold = "HELD_CANDIDATE", "%s|CB3" % cand_grp, hold + ": candidate CB3 of CB3 / B3"
        base = dict(row_id=r["row_id"], member_id=r["member_id"], floor=floor, mark=cb, kind="continuous",
                    span="support %d%s" % (k1, "" if k1 == k2 else "-%d" % k2), clear_length_m="",
                    cause=hold or "", cand=cand)
        led.bars(base, "top over support", nb, d, lo, state, "p.11/p.12 %s: %s = %.4f m" % (cb, " + ".join(parts), lo),
                 ends=1 if end_start else 0)
        if hi - lo > 0.0005:
            led.add(**base, component="top over support (Ln range)", bars="%d ø%d" % (nb, d), count=nb, dia=d,
                    length_m="", kg=0.0, kg_hi=round(nb * (hi - lo) * kgm(d), 3), state="HELD_RANGE",
                    note="Ln upper reading %.4f m (end support not closed on the DXF)" % hi)


def summarise(led):
    tot = defaultdict(float)
    tot_hi = defaultdict(float)
    per_floor = defaultdict(lambda: defaultdict(float))
    links = defaultdict(float)
    unq = []
    over12 = []
    cand = defaultdict(lambda: defaultdict(float))
    for r in led.rows:
        st = r["state"]
        kg = r["kg"] if r["kg"] != "" else 0.0
        if st in ("RELEASED", "HELD_DEFINED"):
            tot[st] += kg
            per_floor[r["floor"]][st] += kg
            if isinstance(r["length_m"], float) and r["length_m"] > STOCK_M:
                over12.append(r["row_id"])
        elif st == "HELD_CANDIDATE":
            grp, c = r["cand"].split("|")
            cand[(r["floor"], grp)][c] += kg
        elif st == "HELD_RANGE" and r.get("cand"):
            continue   # candidate alternatives: their links / ends stay in the CSV, never added across candidates
        elif st == "HELD_RANGE":
            sfx = "" if r.get("parent", "RELEASED") == "RELEASED" else " [members held]"
            if r["component"].startswith("links"):
                for k in ("kg_A", "kg_B", "kg_C", "kg_B_upper"):
                    links[k + sfx] += r[k]
                    per_floor[r["floor"]]["links_" + k + sfx] += r[k]
            else:
                key = r["component"].split(" (")[0] if "ends" not in r["component"] else "ends (note 9)"
                if "side bars" in key:
                    key = "side bars (2-bar minimum)"
                if "end column" in key:
                    key = "bars over end columns inside the register span"
                if "Ln range" in r["component"]:
                    key = "Ln upper reading"
                key += sfx
                tot["range_lo:" + key] += kg
                tot_hi["range_hi:" + key] += (r["kg_hi"] if r["kg_hi"] != "" else kg)
        elif st == "UNQUANTIFIED":
            unq.append("%s %s %s %s" % (r["floor"], r["member_id"], r["mark"], r["component"]))
    cands = {}
    for (f, grp), d in sorted(cand.items()):
        lo, hi = min(d.values()), max(d.values())
        cands["%s %s" % (f, grp)] = {k: round(v, 2) for k, v in d.items()}
        per_floor[f]["HELD_CANDIDATE_lo"] += lo
        per_floor[f]["HELD_CANDIDATE_hi"] += hi
        tot["HELD_CANDIDATE_lo"] += lo
        tot["HELD_CANDIDATE_hi"] += hi
    return dict(candidates=cands, totals={k: round(v, 2) for k, v in tot.items()}, totals_hi={k: round(v, 2) for k, v in tot_hi.items()},
                per_floor={f: {k: round(v, 2) for k, v in d.items()} for f, d in per_floor.items()},
                links={k: round(v, 2) for k, v in links.items()}, unquantified=unq, bars_over_12m=over12)


def s6_compare(led):
    """frozen S6 lower-bound kg per floor (comparison only)."""
    if not os.path.exists(S6):
        return {}
    fl = {"GF_ROOF": "GF", "1F_ROOF": "1F", "2F_ROOF": "2F"}
    out = defaultdict(float)
    for r in csv.DictReader(open(S6, encoding="utf-8")):
        out[fl.get(r["floor"], r["floor"])] += float(r["known_kg"] or 0)
    return {k: round(v, 2) for k, v in out.items()}


def write(led, summ):
    fields = ["row_id", "member_id", "floor", "mark", "kind", "span", "cand", "clear_length_m", "component", "bars", "count",
              "dia", "length_m", "kg", "kg_hi", "state", "parent", "cause", "note", "links_A", "links_B", "links_C", "kg_A",
              "kg_B", "kg_C", "kg_B_upper"]
    with open(os.path.join(HERE, "T149_BEAMS.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in led.rows:
            w.writerow({k: r.get(k, "") for k in fields})
    json.dump(summ, open(os.path.join(HERE, "T149_SUMMARY.json"), "w"), indent=1, ensure_ascii=False)


def check():
    """non-Alsenan hand fixture + re-add checks (asserted)."""
    import tempfile
    # Beam "K7", 2-span continuous, 25 x 60, spans clear 4.00 / 5.00 m, supports 0.30 (end), 0.40 (middle), 0.30 (end)
    # Ln1 = 4.00 + 0.15 + 0.20 = 4.35; Ln2 = 5.00 + 0.20 + 0.15 = 5.35
    # bottom 3 ø16 / 4 ø16, top corner 2 ø12 each span, over the support 5 ø16, links 6 ø8 / m
    CONT["K7"] = dict(B=25, H=60, side=None, spans=[((2, 12), (3, 16), (6, 8)), ((2, 12), (4, 16), (6, 8))],
                      sup=[(5, 16, 1, 1)])
    SIMPLE["K1"] = (25, 50, (4, 16), (2, 12), (5, 8), (2, 12, 30), 1)
    tmp = tempfile.mkdtemp()
    p = os.path.join(tmp, "spans.csv")
    hdr = ["row_id", "member_id", "floor", "mark", "schedule_mark", "type", "status", "width_m", "depth_m", "length_m",
           "span_index", "n_spans", "axis", "span_start", "span_end", "w_left_lo", "w_left_hi", "w_right_lo",
           "w_right_hi", "Ln_lo", "Ln_hi", "clear_length_m", "geometry_left", "geometry_right", "framing_beams", "m3_low"]
    data = [
        dict(row_id="X1", member_id="K7-1", floor="L1", mark="K7", schedule_mark="K7", type="beam span",
             status="CALCULATED", length_m="4.0", clear_length_m="4.0", span_index="1", n_spans="2", w_left_lo="0.3",
             w_left_hi="0.3", w_right_lo="0.4", w_right_hi="0.4", Ln_lo="4.35", Ln_hi="4.35"),
        dict(row_id="X2", member_id="K7-2", floor="L1", mark="K7", schedule_mark="K7", type="beam span",
             status="CALCULATED", length_m="5.0", clear_length_m="5.0", span_index="2", n_spans="2", w_left_lo="0.4",
             w_left_hi="0.4", w_right_lo="0.3", w_right_hi="0.3", Ln_lo="5.35", Ln_hi="5.35"),
        # simple beam, mirrored / rotated plans give the same clear length; register runs over a 0.30 end column
        dict(row_id="X3", member_id="K1-a", floor="L1", mark="K1", schedule_mark="K1", type="beam span",
             status="CALCULATED", length_m="3.30", clear_length_m="3.00"),
        # width conflict -> held defined, same kg
        dict(row_id="X4", member_id="K1-b", floor="L1", mark="K1", schedule_mark="K1", type="beam span",
             status="CONFLICT", length_m="3.00", clear_length_m="3.00"),
        # no schedule row -> unquantified, never 0
        dict(row_id="X5", member_id="K0", floor="L1", mark="(none)", schedule_mark="", type="0.20 strip",
             status="HELD", length_m="2.00", clear_length_m="2.00"),
    ]
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr)
        w.writeheader()
        for d in data:
            w.writerow({k: d.get(k, "") for k in hdr})
    led = main(["--spans", p])
    get = lambda rid, comp: [r for r in led.rows if r["row_id"] == rid and r["component"] == comp]
    u16, u12, u8 = kgm(16), kgm(12), kgm(8)
    # hand values
    assert abs(get("X1", "bottom")[0]["kg"] - 3 * 4.00 * u16) < 1e-3          # 18.963
    assert abs(get("X2", "bottom")[0]["kg"] - 4 * 5.00 * u16) < 1e-3          # 31.605
    tc1 = 4.00 - 0.22 * 4.35                                                     # 3.043
    tc2 = 5.00 - 0.22 * 5.35                                                     # 3.823
    assert abs(get("X1", "top corner")[0]["length_m"] - round(tc1, 4)) < 1e-4
    assert abs(get("X2", "top corner")[0]["kg"] - 2 * tc2 * u12) < 1e-3
    sup = 0.22 * 4.35 + 0.40 + 0.22 * 5.35                                       # 2.534
    s = get("X1", "top over support")[0]
    assert abs(s["length_m"] - round(sup, 4)) < 1e-4 and abs(s["kg"] - 5 * sup * u16) < 1e-3
    lk = get("X1", "links 6 ø8/m (Q-71)")[0]                                   # zone 4.00 - 0.15 = 3.85 -> 23.1
    assert (lk["links_A"], lk["links_B"], lk["links_C"]) == (24, 25, 24.0)
    path = 2 * ((0.25 - 0.05) + (0.60 - 0.05))                                   # 1.50
    assert abs(lk["length_m"] - path) < 1e-9 and abs(lk["kg_A"] - 24 * path * u8) < 1e-3
    ends = get("X1", "bottom ends (note 9, 40d..70d)")[0]                       # 3 bars x 2 ends
    assert abs(ends["kg"] - 6 * 0.64 * u16) < 1e-3 and abs(ends["kg_hi"] - 6 * 1.12 * u16) < 1e-3
    # simple beam over an end column: released on the clear 3.00 m, the 0.30 m part kept apart
    assert abs(get("X3", "bottom")[0]["kg"] - 4 * 3.00 * u16) < 1e-3
    oc = get("X3", "bottom over the end column inside the register span")[0]
    assert oc["state"] == "HELD_RANGE" and abs(oc["kg"] - 4 * 0.30 * u16) < 1e-3
    k1 = get("X3", "links 5 ø8/m (Q-71)")[0]                                     # zone 3.00: 15 / 16 / 15.0
    assert (k1["links_A"], k1["links_B"], k1["links_C"]) == (15, 16, 15.0)
    assert get("X4", "bottom")[0]["state"] == "HELD_DEFINED"
    assert get("X4", "bottom")[0]["kg"] == get("X3", "bottom")[0]["kg"]
    x5 = get("X5", "all bars")[0]
    assert x5["state"] == "UNQUANTIFIED" and x5["kg"] == ""                       # missing never becomes 0
    # exact multiple: 6 / m over 3.00 m = 18 links, no float overshoot
    assert link_counts(6, 3.0, 3.0)[0] == 18
    # mm typed once (unit guard): 4000 mm read as metres would make the corner bar absurd
    assert 0 < tc1 < 4.0
    del CONT["K7"], SIMPLE["K1"]
    # re-add on the project ledger: rows -> floor totals -> project totals
    led = main([])
    summ = summarise(led)
    rel = sum(r["kg"] for r in led.rows if r["state"] == "RELEASED")
    assert abs(rel - summ["totals"]["RELEASED"]) < 0.01
    assert abs(sum(f.get("RELEASED", 0) for f in summ["per_floor"].values()) - rel) < 0.03
    assert all(r["kg"] == "" for r in led.rows if r["state"] == "UNQUANTIFIED")
    assert not any(r["state"] == "RELEASED" and r["kg"] <= 0 for r in led.rows)
    print("fixture PASS; project re-add PASS (released %.2f kg)" % rel)


if __name__ == "__main__":
    if "--check" in sys.argv:
        check()
    led = main(sys.argv)
    summ = summarise(led)
    summ["frozen_S6_lower_bound_kg_per_floor"] = s6_compare(led)
    write(led, summ)
    print(json.dumps({k: summ[k] for k in ("totals", "totals_hi", "links", "bars_over_12m")}, indent=1))
    print(json.dumps(summ["per_floor"], indent=1))
    print("unquantified", len(summ["unquantified"]))
