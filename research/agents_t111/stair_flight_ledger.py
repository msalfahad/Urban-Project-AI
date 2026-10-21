"""T-111: Alsenan stairs flight by flight, and the stair / landing / floor intersection ledger (owner Q-62 A cond).

NO REPO CODE: research output only; no engine, rule or tools file is changed, nothing is wired.

Inputs are the drawing readings below (counts, pitches, widths, levels, plan areas), each with its source. They were read
this run from the Drive copies (architectural DXF sha ab54dd55, structural DXF sha 9f9d1179, section A-A sheet 10,
section B-B sheet 11, GF / 1F plan sheets 3 / 4) by `read_stair_cad.py` and by eye on the sections; the frozen
structural study research/alsenan_stairs_s8_7c (by DXF handle) is the second source for the structural side. No
coordinate, name or file content of a client drawing is written: only lengths, areas, counts and levels.

Two methods side by side (owner instruction 2026-10-20: keep the owner's manual method and show the drawing-derived one):
  OWNER  = the owner-approved formulas exactly as STAIR_CONCRETE_V1 (T-056 / T-105) applies them: steps n x 1/2 r g w
           (Q-19, n = section risers, Q-46 A), waist w x hypot(goings x g, n x r) x t (Q-47 A), landing L x W x t with
           the printed / census sizes.
  DRAWN  = the same owner rules applied to the CAD geometry: straight goings as drawn up to the turn, landing depth from
           its riser line to the wall face, waist under the root line (inner corners) between the first and the last
           riser line; the last riser's wedge belongs to the plate or beam it sits in (Q-62 A).
Intersection ledger (Q-62 A cond): each flight end is modelled in its vertical profile (x along the flight, z up) with
the plate / beam it meets; the overlap area x the flight width is the 3-D intersection (the plate and the beam span the
full flight width). Assigned once: to the plate / beam; deducted from the stair only where both volumes are measured
lines and the geometry is not a drawn clash; otherwise shown with the reason (HELD).

Run: python3 -I research/agents_t111/stair_flight_ledger.py [--out DIR]   (stdlib + shapely; reads no drawing)
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

T16 = 0.16          # owner Q-47 A: 'T 16' printed inside the stair panels (GF / 1F roof slabs, round-stair panel)


# ---------------------------------------------------------------- profile geometry (x along the flight, z up)
def steps_poly(n, r, g, with_arrival=True):
    """Q-19 step wedges of a flight with n risers and n - 1 treads, foot riser at x = 0, z = 0. The n-th wedge (under
    the arrival tread, beyond the last riser line x = (n-1) g) is included when with_arrival."""
    tris = []
    for k in range(n if with_arrival else n - 1):
        tris.append(Polygon([(k * g, k * r), (k * g, (k + 1) * r), ((k + 1) * g, (k + 1) * r)]))
    return unary_union(tris)


def waist_poly(n, r, g, t):
    """waist strip under the root line z = (r / g) x, perpendicular thickness t, vertical cuts at the first and the
    last riser line (x = 0 .. (n-1) g)."""
    run = (n - 1) * g
    dz = t / math.cos(math.atan2(r, g))
    return Polygon([(0, 0), (run, run * r / g), (run, run * r / g - dz), (0, -dz)])


def plate(x0, x1, top, t):
    return box(min(x0, x1), top - t, max(x0, x1), top)


def wedge_area(r, g, t):
    """profile area of the last riser's wedge inside a plate of thickness t whose top is the arrival level."""
    full = 0.5 * r * g
    return full if t >= r else full - 0.5 * (r - t) * ((r - t) * g / r)


# ---------------------------------------------------------------- readings (counts, lengths, levels; with sources)
SEC = "section A-A (sheet 10)"
DXF = "architectural DXF"
S87C = "research/alsenan_stairs_s8_7c"

FLIGHTS = [
    # id, stair, from_to (finished levels), risers (section / plan), treads drawn, tread pitch, width, notes
    dict(id="MS1-L", stair="MAIN", run="GF-1F", kind="straight, foot at the GF hall", z0=1.00, z1=5.50, n_run=27,
         risers=10, treads_straight=9, g=0.30, w=1.20, t=T16,
         start="GF hall +1.00 (printed in the hall, DXF)", end="first tread of the turn (winder W1), NO landing",
         check=("DXF GF plan: 10 riser lines at 0.300 pitch, 2.700 m from the first riser to the turn line; the turn "
                "(NW quarter) begins at the 10th riser line. Section A-A: 10 risers before the dashed turn treads. "
                f"{S87C} B-27-S: lower run 2700 (by handle). OWNER census used 10 goings (3.00 m): one going is "
                "inside the turn"),
         struct="ST7757 p.4 GF roof slab stair panel 'T 16', '8 d16/m'; 'B3 (With Stair)' along the outer edge"),
    dict(id="MS1-T", stair="MAIN", run="GF-1F", kind="turn (winders)", z0=1.00, z1=5.50, n_run=27, risers=5,
         g=None, w=1.20, t=None,
         start="+2.667 (10 x 0.16667)", end="landing +3.50 (printed)",
         check=("section A-A: 5 rises in the turn (treads +2.667, +2.833, +3.0, +3.167, +3.333; landing +3.50). "
                "DXF GF and 1F plans: 4 wedges (3 radial lines from the well corner) in the NW quarter; drawn wedge "
                "areas 0.2944 / 0.3669 / 0.3674 / 0.2938 = 1.3225 m2 between the tread-end lines (1.15 x 1.15); the "
                "quarter from the 10th riser line to the north wall (DXF dimension 1200 on the 1F / 2F plans) and "
                "from the west wall to the central-wall face (DXF 1200) is 1.20 x 1.20 = 1.44 m2; the 0.10 m well "
                "strip to the drawn closing riser adds 0.12 m2"),
         struct="no winder detail; no soffit (warped slab) drawn under the turn"),
    dict(id="MS1-LD", stair="MAIN", run="GF-1F", kind="half landing NE quarter", z0=3.50, z1=3.50, n_run=27,
         risers=0, g=None, w=1.20, t=T16, length_owner=1.25, length_drawn=1.20,
         start="+3.50 (printed on A-A)", end="-",
         check=("DXF: riser line of the upper flight to the inner face of the north wall 1.200 m, central-wall face to "
                "the east wall face 1.200 m: 1.20 x 1.20 = 1.44 m2 (= S8.7c NE quarter 1200 x 1200 by handle). The "
                "printed '125' the census used is the outer-wall dimension chain (north wall outer face to the window "
                "jamb, 1.25 m; its DXF dimension is a text override), not the landing"),
         struct="T 16 panel tag (Q-47 A)"),
    dict(id="MS1-U", stair="MAIN", run="GF-1F", kind="straight, arrives at the 1F floor", z0=1.00, z1=5.50, n_run=27,
         risers=12, treads_straight=11, g=0.30, w=1.20, t=T16, head_beam=("B20", 0.40, 0.75, 0.20),
         start="landing +3.50", end="1F floor +5.50 (printed); the floor is the 12th tread",
         check=("section A-A (counted this run on the hatched cut flight): 12 risers, 11 treads, the 1F floor is the "
                "arrival tread; run 3.30 m. DXF plans draw 11 riser lines (3.00 m): the section's 12th riser falls on "
                "the 1F landing edge line (the first riser line of the next flight), 0.35 m beyond the plan's last "
                f"line (designer point D-13). {S87C}: that riser line is 0.20 m inside beam B20 (40 x 75) at the head"),
         struct="B20 40 x 75 at the head (S8.7c clash -200 mm), 1F slab beyond"),
    dict(id="MS2-L", stair="MAIN", run="1F-2F", kind="straight, foot at the 1F floor landing", z0=5.50, z1=9.70,
         n_run=25, risers=12, treads_straight=11, g=0.30, w=1.20, t=T16,
         start="1F floor +5.50 (printed '+5.50' at the 1.95 m floor landing)", end="flat NW quarter +7.516",
         check=("DXF 1F plan: 12 riser lines at 0.300, run printed '3300' (DXF dimension 3300 measured) = 11 goings. "
                "Section A-A: 12 risers to a flat quarter (no winder lines), one closing riser to the landing"),
         struct="ST7757 p.5 1F roof slab stair panel 'T 16', '8 d16/m'"),
    dict(id="MS2-TR", stair="MAIN", run="1F-2F", kind="closing riser quarter -> NE landing", z0=7.516, z1=7.684,
         n_run=25, risers=1, g=None, w=1.20, t=None, start="+7.516", end="+7.684",
         check=("section A-A: flat quarter then one closing riser; the 1F plan draws 4 winder wedges instead (Q-46 A: "
                "the section counts). Levels scaled, not printed"),
         struct="not detailed"),
    dict(id="MS2-LD", stair="MAIN", run="1F-2F", kind="half landing: NW quarter + well + NE quarter", z0=7.516,
         z1=7.684, n_run=25, risers=0, g=None, w=2.50, t=T16, length_owner=1.25, length_drawn=1.20,
         start="+7.516 / +7.684 (two levels, section)", end="-",
         check=("DXF 1F plan: 2.50 m wall to wall (printed '250', DXF 2500) by 1.20 m riser line to the north wall's "
                "inner face; the census '125' is the outer dimension chain as on GF"),
         struct="T 16 panel tag (Q-47 A)"),
    dict(id="MS2-U", stair="MAIN", run="1F-2F", kind="straight, arrives at the 2F floor", z0=5.50, z1=9.70, n_run=25,
         risers=12, treads_straight=11, g=0.30, w=1.20, t=T16, head_beam=("B23", 0.45, 0.75, 0.20),
         start="NE landing +7.684", end="2F floor +9.70 (printed); the floor is the 12th tread",
         check=("section A-A (counted this run): 12 risers, 11 treads. DXF 2F / 1F plans draw 11 riser lines; the "
                f"12th riser falls on the 2F lobby edge line ('195' edge, Q-70). {S87C}: 0.20 m inside B23 (45 x 75)"),
         struct="B23 45 x 75 at the head (clash, section only), 2F slab beyond"),
    dict(id="E1", stair="ENTRANCE", run="COURT-GF", kind="straight", z0=0.15, z1=1.00, n_run=5, risers=5,
         treads_straight=4, g=0.30, w=2.80, t=None,
         start="court +0.15 (printed 1.06 m from the foot)", end="GF floor +1.00 (printed); floor = 5th tread",
         check="DXF GF plan: 5 riser lines 2.800 m long (DXF dimension 2800) at 0.300; section B-B 5 risers",
         struct="not in a slab panel; waist on fill, no thickness printed"),
    dict(id="D1", stair="LOBBY", run="LOBBY-GF", kind="straight, under the main-stair landing", z0=0.30, z1=1.00,
         n_run=4, risers=4, treads_straight=3, g=0.30, w=1.20, t=None,
         start="lobby +0.30 (printed)", end="GF hall +1.00 (printed); hall floor = 4th tread",
         check="DXF GF plan: 4 solid riser lines at 0.300 under the dashed upper flight; section A-A: 4 risers",
         struct="no thickness printed"),
    dict(id="RS-C", stair="ROUND", run="GF-1F", kind="curved (12 tapered treads)", z0=1.00, z1=5.50, n_run=28,
         risers=12, g=None, w=1.15, t=None,
         start=("GF +1.00: printed on the same open floor 2.6 m from the foot, no step or wall line drawn between "
                "(DXF), section B-B draws the GF floor at one level; not printed at the foot itself"),
         end="riser 13 (first straight riser)",
         check=("DXF GF and 1F plans identical: 12 radial riser lines at 7.79 deg pitch about one centre, tread ends "
                "r 1.581 / 2.731 m (stringer arcs 1.531 / 2.781, walking line 2.156); treads 1-11 0.3371 m2 each, "
                "tread 12 (to the tangent point and the first straight riser) 0.3996 m2; 12 treads 4.1077 m2"),
         struct="T 16 in the round-stair panel (Q-47 A); helicoid soffit not drawn"),
    dict(id="RS-S", stair="ROUND", run="GF-1F", kind="straight", z0=1.00, z1=5.50, n_run=28, risers=11,
         treads_straight=10, g=0.30, w=1.20, t=T16,
         start="+2.929 (12 x 0.160714)", end="corner landing +4.696 (riser 23 lands on it)",
         check=("DXF: 11 riser lines at 0.300 (3.00 m first to last), width 1.200 (DXF dimension 1200 measured "
                "across the flight; tread lines 1.150); the 11th riser's tread is the corner landing"),
         struct=("beam CA 30 x 50 crosses the flight between risers 15 and 16 (level not stated, S8.7c R-10); "
                 "'B3 (With Stair)' along its edge")),
    dict(id="RS-LD", stair="ROUND", run="GF-1F", kind="corner landing", z0=4.696, z1=4.696, n_run=28, risers=0,
         g=None, w=1.25, t=T16, length_drawn=1.15,
         start="+4.696 (= 1.00 + 23 x 0.160714; not printed)", end="-",
         check=("DXF: 1.25 m wall to wall (DXF dimension 1250) by 1.15 m from riser 23 to riser 24; both edges are "
                "drawn riser lines, so the landing adds no rise; less a column corner 0.0275 m2 (S8.7c): 1.4100 m2"),
         struct="T 16 (round-stair panel)"),
    dict(id="RS-A", stair="ROUND", run="GF-1F", kind="straight, arrives at the 1F floor", z0=1.00, z1=5.50, n_run=28,
         risers=5, treads_straight=4, g=0.30, w=1.25, t=T16,
         start="corner landing +4.696", end="1F +5.50 (printed at the arrival); the floor is the 5th tread",
         check=("DXF 1F plan: 5 riser lines at 0.300, width 1.250 wall to wall (DXF dimension 1250); the GF plan "
                "draws 4 of them (beyond its cut)"),
         struct="arrival plate C-T1 (frozen S8.7 release)"),
]


def riser_of(f):
    return (f["z1"] - f["z0"]) / f["n_run"]


def owner_lines():
    """the owner-method lines exactly as STAIR_CONCRETE_V1 computes them for the Alsenan census (T-056 / T-105)."""
    r1, r2 = 4.50 / 27, 4.20 / 25
    L = []
    def add(i, el, q, st, calc):
        L.append(dict(id=i, element=el, m3=q, status=st, calc=calc))
    add("MS1-L", "STEPS", 10 * 0.5 * r1 * 0.30 * 1.20, "MEASURED", "10 x 1/2 x 0.166667 x 0.30 x 1.20")
    add("MS1-L", "WAIST", 1.20 * math.hypot(10 * 0.30, 10 * r1) * T16, "MEASURED", "1.20 x hypot(10 x 0.30, 10 r) x 0.16")
    add("MS1-T", "TURNING_STEPS", None, "HELD", "Q-51 conditional; candidate 1/2 r 1.44 = 0.120")
    add("MS1-LD", "LANDING", 1.25 * 1.20 * T16, "MEASURED", "1.25 x 1.20 x 0.16")
    add("MS1-U", "STEPS", 12 * 0.5 * r1 * 0.30 * 1.20, "MEASURED", "12 x 1/2 x 0.166667 x 0.30 x 1.20")
    add("MS1-U", "WAIST", 1.20 * math.hypot(11 * 0.30, 12 * r1) * T16, "MEASURED", "1.20 x hypot(11 x 0.30, 12 r) x 0.16")
    add("MS2-L", "STEPS", 12 * 0.5 * r2 * 0.30 * 1.20, "MEASURED", "12 x 1/2 x 0.168 x 0.30 x 1.20")
    add("MS2-L", "WAIST", 1.20 * math.hypot(11 * 0.30, 12 * r2) * T16, "MEASURED", "1.20 x hypot(11 x 0.30, 12 r) x 0.16")
    add("MS2-TR", "TURN_RISER", None, "HELD", "landing levels not printed")
    add("MS2-LD", "LANDING", 2.50 * 1.25 * T16, "MEASURED", "2.50 x 1.25 x 0.16")
    add("MS2-U", "STEPS", 12 * 0.5 * r2 * 0.30 * 1.20, "MEASURED", "12 x 1/2 x 0.168 x 0.30 x 1.20")
    add("MS2-U", "WAIST", 1.20 * math.hypot(11 * 0.30, 12 * r2) * T16, "MEASURED", "1.20 x hypot(11 x 0.30, 12 r) x 0.16")
    add("E1", "STEPS", 5 * 0.5 * 0.17 * 0.30 * 2.80, "MEASURED", "5 x 1/2 x 0.17 x 0.30 x 2.80")
    add("E1", "WAIST", None, "HELD", "not in a slab panel, no thickness printed")
    add("D1", "STEPS", 4 * 0.5 * 0.175 * 0.30 * 1.20, "MEASURED", "4 x 1/2 x 0.175 x 0.30 x 1.20")
    add("D1", "WAIST", None, "HELD", "no thickness printed")
    for i in ("RS-C", "RS-S", "RS-LD", "RS-A"):
        add(i, "ALL", None, "HELD", "T-056: Q-50 / Q-51 open at the time")
    return L


def drawn_lines():
    """the same owner rules on the CAD geometry (DRAWN method), status after the Q-50 / Q-51 / Q-62 conditions."""
    r1, r2, r3 = 4.50 / 27, 4.20 / 25, 4.50 / 28
    L = []
    def add(i, el, q, st, calc, why=""):
        L.append(dict(id=i, element=el, m3=q, status=st, calc=calc, reason=why))
    def waist(n, r, g, w, t):
        return waist_poly(n, r, g, t).area * w
    # main stair GF -> 1F
    add("MS1-L", "STEPS", 9 * 0.5 * r1 * 0.30 * 1.20, "MEASURED", "9 x 1/2 x 0.166667 x 0.30 x 1.20",
        "the 10th riser's wedge sits on winder W1 (in the turn line)")
    add("MS1-L", "WAIST", 1.20 * math.hypot(9 * 0.30, 9 * r1) * T16, "MEASURED", "1.20 x hypot(2.70, 1.50) x 0.16",
        "drawn straight run 2.70 m up to the turn line")
    add("MS1-T", "TURNING_STEPS", None, "HELD", "candidate 1/2 x 0.166667 x 1.44 = 0.1200 (NW quarter, wall to "
        "central-wall face, riser 10 to the north wall: the same 1.20 basis as the flights) .. x 1.56 = 0.1300 (with "
        "the 0.10 x 1.20 well strip up to the drawn closing riser); tread-line basis 1.3225 m2 -> 0.1102",
        "Q-51 cond: area condition MET on the wall-to-wall basis (1.20 x 1.20 dimensioned on the 1F / 2F plans, the "
        "GF 5000 = 1100 + 2700 + 1200; no landing or void inside the quarter; the sum 1/2 r x total area does not "
        "depend on 4 (plan) or 5 (section) turn treads); NOT MET: the well strip is unassigned (turn or landing) and "
        "no soffit is drawn for the wedge-over-uniform-waist model")
    add("MS1-T", "TURN_SOFFIT_SLAB", None, "HELD", "candidate plan 1.44 .. 1.56 m2 x 0.16 = 0.2304 .. 0.2496 "
        "(horizontal projection, less than the warped slab)",
        "NEW LINE: the slab under the winders is in no line of the owner census (silent omission); soffit not drawn")
    add("MS1-LD", "LANDING", 1.20 * 1.20 * T16, "MEASURED", "1.20 x 1.20 x 0.16", "landing depth from the CAD")
    add("MS1-U", "STEPS", 12 * 0.5 * r1 * 0.30 * 1.20, "MEASURED", "12 x 1/2 x 0.166667 x 0.30 x 1.20 (incl. the "
        "arrival wedge, deducted in the ledger)", "")
    add("MS1-U", "WAIST", waist(12, r1, 0.30, 1.20, T16), "MEASURED", "root-line strip 11 x 0.30 run, 0.16 thick",
        "")
    add("MS2-L", "STEPS", 12 * 0.5 * r2 * 0.30 * 1.20, "MEASURED", "12 x 1/2 x 0.168 x 0.30 x 1.20 (incl. the "
        "arrival wedge on the flat quarter, deducted in the ledger)", "")
    add("MS2-L", "WAIST", waist(12, r2, 0.30, 1.20, T16), "MEASURED", "root-line strip 11 x 0.30 run, 0.16 thick", "")
    add("MS2-TR", "TURN_RISER", None, "HELD", "-", "levels +7.516 / +7.684 scaled from the section, not printed")
    add("MS2-LD", "LANDING", 2.50 * 1.20 * T16, "MEASURED", "2.50 x 1.20 x 0.16", "landing depth from the CAD")
    add("MS2-U", "STEPS", 12 * 0.5 * r2 * 0.30 * 1.20, "MEASURED", "12 x 1/2 x 0.168 x 0.30 x 1.20", "")
    add("MS2-U", "WAIST", waist(12, r2, 0.30, 1.20, T16), "MEASURED", "root-line strip 11 x 0.30 run, 0.16 thick", "")
    # entrance and lobby: unchanged (CAD confirms counts, pitch, widths)
    add("E1", "STEPS", 5 * 0.5 * 0.17 * 0.30 * 2.80, "MEASURED", "5 x 1/2 x 0.17 x 0.30 x 2.80", "CAD confirms")
    add("E1", "WAIST", None, "HELD", "-", "not in a slab panel, no thickness printed")
    add("D1", "STEPS", 4 * 0.5 * 0.175 * 0.30 * 1.20, "MEASURED", "4 x 1/2 x 0.175 x 0.30 x 1.20", "CAD confirms")
    add("D1", "WAIST", None, "HELD", "-", "no thickness printed")
    # round stair (Q-50 A cond: straight flights CALCULATED once verified, curved parts HELD)
    curved_area = 11 * 0.5 * math.radians(7.79) * (2.731 ** 2 - 1.581 ** 2) + \
        0.5 * math.radians(270 - 261.67) * (2.731 ** 2 - 1.581 ** 2) + 0.034 * 1.15
    add("RS-C", "CURVED_STEPS", None, "HELD", f"candidate 1/2 x 0.160714 x {curved_area:.4f} = "
        f"{0.5 * r3 * curved_area:.4f}", "Q-50 / Q-51: curved parts HELD; helicoid soffit not drawn")
    add("RS-C", "CURVED_SOFFIT", None, "HELD", "-", "helicoid waist not drawn (Q-51 step 5)")
    add("RS-S", "STEPS", 11 * 0.5 * r3 * 0.30 * 1.20, "CALCULATED", "11 x 1/2 x 0.160714 x 0.30 x 1.20",
        "Q-50 A cond: straight flight geometrically verified (count, pitch, width, both levels)")
    add("RS-S", "WAIST", 1.20 * math.hypot(10 * 0.30, 10 * r3) * T16, "CALCULATED",
        "1.20 x hypot(3.00, 1.607) x 0.16 (riser 13 to riser 23)",
        "T 16 in the round-stair panel (Q-47 A); the CA beam junction stays HELD in the ledger")
    add("RS-LD", "LANDING", (1.25 * 1.15 - 0.0275) * T16, "CALCULATED", "(1.25 x 1.15 - 0.0275 column) x 0.16",
        "level +4.696 reconstructed (equal risers), not printed: 'reconstructed, no section'")
    add("RS-A", "STEPS", 5 * 0.5 * r3 * 0.30 * 1.25, "CALCULATED", "5 x 1/2 x 0.160714 x 0.30 x 1.25",
        "Q-50 A cond: verified (5 risers on the 1F plan, floor = last tread, '+5.50' printed at the arrival)")
    add("RS-A", "WAIST", 1.25 * math.hypot(4 * 0.30, 4 * r3) * T16, "CALCULATED", "1.25 x hypot(1.20, 0.643) x 0.16",
        "T 16 (round-stair panel)")
    return L


# ---------------------------------------------------------------- intersection ledger (Q-62 A cond)
def head_case(n, r, g, w, plate_t, beam=None):
    """flight end at a floor: profile with the floor plate (and the head beam band). Returns (wedge m3 in the
    partner, flight-in-beam m3 beyond the wedge, wedge left below the plate m3)."""
    run = (n - 1) * g
    H = n * r
    stp = steps_poly(n, r, g, with_arrival=True)
    wst = waist_poly(n, r, g, T16)
    flight = unary_union([stp, wst])
    wedge = Polygon([(run, run * r / g), (run, H), (run + g, H)])
    if beam is None:
        partner = plate(run, run + 3.0, H, plate_t)
        clash = 0.0
    else:
        _, bw, bd, inside = beam                     # riser line 'inside' metres inside the beam from its stair face
        b = box(run - inside, H - bd, run - inside + bw, H)
        partner = unary_union([b, plate(run - inside + bw, run + 3.0, H, plate_t)])
        clash = flight.difference(wedge).intersection(partner).area * w
    in_partner = wedge.intersection(partner).area * w
    return in_partner, clash, wedge.area * w - in_partner


def ledger():
    r1, r2, r3 = 4.50 / 27, 4.20 / 25, 4.50 / 28
    rows = []
    def add(i, end, partner, m3, assigned, action, why, check=None):
        rows.append(dict(flight=i, end=end, partner=partner, overlap_m3=round(m3, 6), assigned_to=assigned,
                         action=action, reason=why, hand_check=check))
    w_in, clash, left = head_case(12, r1, 0.30, 1.20, T16, beam=("B20", 0.40, 0.75, 0.20))
    add("MS1-U", "head, 1F floor +5.50", "beam B20 40 x 75 + 1F slab", w_in, "B20 / 1F slab", "DEDUCT from stair steps",
        "Q-62 A: the 12th riser's wedge (tread = the floor) is inside B20 and the slab", f"1/2 x {r1:.6f} x 0.30 x 1.20")
    add("MS1-U", "head, 1F floor +5.50", "beam B20 (drawn clash)", clash, "B20", "HELD (designer RFI B20 / Q-46)",
        "the section's 12-riser flight puts its last 0.20 m of tread 11 and waist inside B20: a drawn clash, not a "
        "measurement convention", "0.20 x (r/g x 0.10 + t / cos a) x 1.20")
    w_in2, clash2, _ = head_case(12, r2, 0.30, 1.20, T16, beam=("B23", 0.45, 0.75, 0.20))
    add("MS2-U", "head, 2F floor +9.70", "beam B23 45 x 75 + 2F slab", w_in2, "B23 / 2F slab", "DEDUCT from stair steps",
        "as MS1-U", f"1/2 x {r2:.6f} x 0.30 x 1.20")
    add("MS2-U", "head, 2F floor +9.70", "beam B23 (drawn clash)", clash2, "B23", "HELD (designer RFI B23 / Q-46)",
        "as MS1-U", "0.20 x (r/g x 0.10 + t / cos a) x 1.20")
    q = wedge_area(r2, 0.30, T16) * 1.20
    add("MS2-L", "top, flat quarter +7.516", "landing MS2-LD (T 16)", q, "landing MS2-LD", "DEDUCT from stair steps",
        "NEW: both are measured lines of the owner census (5.011); STAIR_CONCRETE_V1 checks arrival wedges only when "
        "the next part is a LANDING, and here a TURN_RISER part sits between", "1/2 r g w less the 0.008 m sliver below "
        "the 0.16 plate")
    add("MS1-L", "top, winder W1", "turn (HELD)", 0.0, "-", "none now",
        "the 10th riser's wedge is in the turn's plan area; DRAWN counts 9 straight wedges, so nothing overlaps")
    q = wedge_area(r1, 0.30, T16) * 1.20
    add("MS1-T", "top, landing +3.50", "landing MS1-LD (T 16)", q, "landing MS1-LD", "none now (turn HELD)",
        "the turn's closing riser wedge will overlap the landing when the turn is released", "1/2 r g w")
    add("MS1-U / MS2-U / MS2-L / MS1-L", "foot", "landing / floor below", 0.0, "-", "none",
        "the flight starts at the plate edge: the volumes touch along the riser line, no 3-D overlap (the soffit knee "
        "under each plate edge is in neither line: see knee check)")
    add("E1", "top, GF floor +1.00", "GF floor at the threshold", 0.5 * 0.17 * 0.30 * 2.80, "-",
        "HELD (shown, not deducted)", "the GF floor at the porch is on fill with no printed thickness and no measured "
        "concrete line: no counted partner volume to assign it to", "1/2 x 0.17 x 0.30 x 2.80")
    add("D1", "top, GF hall +1.00", "GF hall floor", 0.5 * 0.175 * 0.30 * 1.20, "-", "HELD (shown, not deducted)",
        "as E1", "1/2 x 0.175 x 0.30 x 1.20")
    add("RS-S", "top, corner landing +4.696", "corner landing RS-LD (T 16)", wedge_area(r3, 0.30, T16) * 1.20,
        "landing RS-LD", "DEDUCT from stair steps", "both CALCULATED in this ledger", "1/2 r g w less the sliver")
    add("RS-A", "head, 1F +5.50", "arrival plate C-T1 (frozen S8.7, T 16)", wedge_area(r3, 0.30, T16) * 1.25,
        "arrival plate", "DEDUCT when both lines are wired (lane I)", "the arrival plate is a released S8.7 line",
        "1/2 r g w")
    add("RS-S", "beam CA across the flight", "beam CA 30 x 50", 0.0, "CA", "HELD (level not stated, S8.7c R-10)",
        "intersection unknown until the CA level is stated (0 .. about 0.09 m3)")
    return rows


def knees():
    """soffit knee under a plate edge: the concrete between the vertical end cut of the waist and the point where the
    waist soffit meets the plate soffit (in neither the flight line nor the plate line). Check only."""
    out = []
    for i, r in (("MS1-U foot (landing +3.50)", 4.50 / 27), ("MS2-L foot (1F floor)", 4.20 / 25),
                 ("MS2-U foot (landing +7.684)", 4.20 / 25), ("RS-A foot (corner landing)", 4.50 / 28)):
        a = math.atan2(r, 0.30)
        dz = T16 / math.cos(a)
        # soffit z = (r/g) x - dz for x <= 0; plate soffit z = -T16; triangle between x = 0 and the meeting point
        xm = (dz - T16) / (r / 0.30)
        out.append(dict(junction=i, knee_profile_m2=round(0.5 * xm * (dz - T16), 6),
                        knee_m3_at_width=round(0.5 * xm * (dz - T16) * (1.25 if i.startswith("RS") else 1.20), 6)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    own, drw, led, kn = owner_lines(), drawn_lines(), ledger(), knees()

    def tot(lines, ids, st=("MEASURED", "CALCULATED")):
        return sum(x["m3"] for x in lines if x["id"] in ids and x["status"] in st and x["m3"] is not None)
    main_ids = {"MS1-L", "MS1-T", "MS1-LD", "MS1-U", "MS2-L", "MS2-TR", "MS2-LD", "MS2-U"}
    ded_main = sum(x["overlap_m3"] for x in led if x["flight"] in ("MS1-U", "MS2-U", "MS2-L")
                   and x["action"].startswith("DEDUCT"))
    held_main = sum(x["overlap_m3"] for x in led if x["flight"] in ("MS1-U", "MS2-U") and x["action"].startswith("HELD"))
    ded_round = sum(x["overlap_m3"] for x in led if x["flight"].startswith("RS") and x["action"].startswith("DEDUCT"))
    summ = {
        "main_owner_lines_m3": round(tot(own, main_ids), 4),
        "main_drawn_lines_m3": round(tot(drw, main_ids), 4),
        "main_ledger_deducted_m3": round(ded_main, 4),
        "main_ledger_held_clash_m3": round(held_main, 4),
        "main_owner_after_ledger_m3": round(tot(own, main_ids) - ded_main, 4),
        "main_drawn_after_ledger_m3": round(tot(drw, main_ids) - ded_main, 4),
        "entrance_m3": round(tot(drw, {"E1"}), 4), "lobby_m3": round(tot(drw, {"D1"}), 4),
        "round_steps_straight_and_arrival_m3": round(sum(x["m3"] for x in drw if x["id"] in ("RS-S", "RS-A")
                                                        and x["element"] == "STEPS"), 6),
        "round_calculated_m3": round(tot(drw, {"RS-S", "RS-LD", "RS-A"}), 4),
        "round_ledger_deducted_m3": round(ded_round, 4),
        "freelancer_m3": {"main": 8.131, "entrance": 1.411, "round": 5.510},
    }
    for k, v in summ.items():
        print(f"{k:42s} {v}")
    print("\nOWNER vs DRAWN, main stair lines:")
    for o in own:
        if o["id"] in main_ids:
            d = [x for x in drw if x["id"] == o["id"] and x["element"] == o["element"]]
            dv = d[0]["m3"] if d else None
            print(f"  {o['id']:7s} {o['element']:14s} owner {o['m3'] if o['m3'] is None else round(o['m3'], 4)!s:>8s}"
                  f"  drawn {dv if dv is None else round(dv, 4)!s:>8s}")
    print("\nledger:")
    for x in led:
        print(f"  {x['flight']:28s} {x['end']:28s} {x['overlap_m3']:9.6f}  {x['action']}")
    print("\nknees:", kn)
    if a.out:
        o = Path(a.out)
        o.mkdir(parents=True, exist_ok=True)
        with open(o / "FLIGHTS.csv", "w", newline="", encoding="utf-8") as fh:
            wr = csv.writer(fh)
            wr.writerow(["flight", "stair", "run", "kind", "levels", "risers", "riser_m", "treads_straight",
                         "going_m", "width_m", "thickness_m", "start", "end", "drawing_check", "structural_ref",
                         "owner_m3", "owner_status", "drawn_m3", "drawn_status", "drawn_reason"])
            for f in FLIGHTS:
                ol = [x for x in own if x["id"] == f["id"]]
                dl = [x for x in drw if x["id"] == f["id"]]
                fmt = lambda ls: " + ".join(f"{x['element']} {'HELD' if x['m3'] is None else format(x['m3'], '.4f')}"  # noqa: E731
                                            for x in ls)
                wr.writerow([f["id"], f["stair"], f["run"], f["kind"], f"{f['z0']:+.3f} -> {f['z1']:+.3f}",
                             f["risers"], round(riser_of(f), 6), f.get("treads_straight", ""), f.get("g") or "",
                             f["w"], f.get("t") or "", f["start"], f["end"], f["check"], f["struct"], fmt(ol),
                             "/".join(sorted({x["status"] for x in ol})), fmt(dl),
                             "/".join(sorted({x["status"] for x in dl})),
                             " | ".join(x.get("reason", "") for x in dl if x.get("reason"))])
        with open(o / "INTERSECTIONS.csv", "w", newline="", encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, fieldnames=list(led[0].keys()))
            wr.writeheader()
            wr.writerows(led)
        (o / "ledger_summary.json").write_text(json.dumps({"summary": summ, "knees": kn,
                                                           "owner_lines": own, "drawn_lines": drw}, indent=1))


if __name__ == "__main__":
    main()
