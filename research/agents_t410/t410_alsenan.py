"""T-410 development-villa side table (Alsenan is one sample; the method is stair_skirting_sides.py, every villa).

Build (needs the PRIVATE architectural DXF, P7757_DXF_COMPRESSED.zip on Drive, decoded into .work/private only):
    python3 -I research/agents_t410/t410_alsenan.py --dxf <P7757.dxf> --write
reads every position it uses BY ENTITY HANDLE, asserts the layer / orientation / extent it relies on, converts it to
run positions (metres along each flight, no coordinates) and writes ALSENAN_SIDES_T410.json, SIDE_TABLE_T410.csv and
summary.json beside this file. Check (no private input):
    python3 -I research/agents_t410/t410_alsenan.py --check
recomputes the table from the committed ALSENAN_SIDES_T410.json and prints REPRODUCED when it matches the CSV.
r2 (Checker gate e on r1): every side is also read on the COLUMN layer S-COL.BON (rule R-T410-4 in
stair_skirting_sides.py): column_census() scans every closed S-COL.BON outline beside every side line (by the side's
own handles), classes it PROUD / FLUSH / CROSSES / BEHIND, writes COLUMN_CENSUS_T410.csv (run positions and
projections only) and the faces into ALSENAN_SIDES_T410.json, so --check re-runs check_faces without private input.
The proud columns were cross-read on the structural plan (ST7757 dxf.dxf, T-108 translations): same outline, same size.
Riser counts / sizes are the merged T-184 inventory (Q-46 A) and the ST-02 / ST-03 / D1 drawn lines; railing run ids
are T-164 / T-393 (merged). No drawing content, client name or freelancer row text is written.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stair_skirting_sides as K  # noqa: E402

MM = 0.001
SIDES_JSON = HERE / "ALSENAN_SIDES_T410.json"
TABLE_CSV = HERE / "SIDE_TABLE_T410.csv"
SUMMARY = HERE / "summary.json"
STAIR_INPUT = HERE.parent / "agents_t184" / "ALSENAN_STAIR_INPUT.json"
COLUMN_CSV = HERE / "COLUMN_CENSUS_T410.csv"
COLS = ["sid", "element", "side", "class", "face", "plan_lm", "risers_in", "returns_lm", "zigzag_lm", "sloped_lm",
        "level_rise_m", "qty_lm", "status", "form", "railing_run", "cause", "evidence", "binds"]
CCOLS = ["element", "side", "plan", "column", "relation", "s0", "s1", "proud_m", "carrier", "returns_confirmed_lm",
         "returns_held_lm", "st_plan"]
# proud columns cross-read on ST7757 dxf.dxf (sha 9f9d1179) through the T-108 translations (GF 202.33 / 841.64 m,
# 1F 208.46 / 841.64 m): the ST outline handle, same size, within 3 mm
ST_CROSS = {"2FBD": "ST 36B 0.250 x 0.500 (GF)", "3005": "ST 691 0.250 x 0.500 (1F)", "2F78": "stacked on 3005 (2F)",
            "2FD2": "ST 380 0.800 x 0.250 (GF)", "2FC6": "ST 374 0.600 x 0.250 (GF)"}


# ------------------------------------------------------------------ DXF reading (private input, build mode only)

class Dxf:
    def __init__(self, path):
        import ezdxf
        self.db = ezdxf.readfile(path).entitydb

    def line(self, h, layer=None):
        e = self.db[h]
        assert e.dxftype() == "LINE", (h, e.dxftype())
        if layer is not None:
            assert e.dxf.layer == layer, (h, e.dxf.layer, layer)
        return (e.dxf.start[0], e.dxf.start[1]), (e.dxf.end[0], e.dxf.end[1])

    def y(self, h, layer=None):  # a horizontal line's y
        a, b = self.line(h, layer)
        assert abs(a[1] - b[1]) < 1, h
        return a[1]

    def x(self, h, layer=None):  # a vertical line's x
        a, b = self.line(h, layer)
        assert abs(a[0] - b[0]) < 1, h
        return a[0]

    def yspan(self, h, layer=None):
        a, b = self.line(h, layer)
        assert abs(a[0] - b[0]) < 1, h
        return min(a[1], b[1]), max(a[1], b[1])

    def xspan(self, h, layer=None):
        a, b = self.line(h, layer)
        assert abs(a[1] - b[1]) < 1, h
        return min(a[0], b[0]), max(a[0], b[0])

    def box(self, h, layer="S-COL.BON"):  # a closed outline's extent
        e = self.db[h]
        assert e.dxftype() == "LWPOLYLINE" and e.closed and e.dxf.layer == layer, (h, e.dxftype())
        xs, ys = zip(*[(p[0], p[1]) for p in e.get_points()])
        return min(xs), min(ys), max(xs), max(ys)

    def outlines(self, layer):
        for e in self.db.values():
            if e.dxftype() == "LWPOLYLINE" and e.closed and e.dxf.get("layer") == layer:
                yield e.dxf.handle

    def arc(self, h):
        e = self.db[h]
        assert e.dxftype() == "ARC", h
        return (e.dxf.center[0], e.dxf.center[1]), e.dxf.radius


def _flights():
    data = json.loads(STAIR_INPUT.read_text())
    st = next(s for s in data["stairs"] if s["stair_id"] == "ST-01")
    out = {f["id"]: {"risers": f["risers"], "riser": f["riser"], "goings": f["goings"], "going": f["going"],
                     "src": f"T-184 ALSENAN_STAIR_INPUT ({f['src']})"} for f in st["flights"]}
    out["D1"] = {"risers": 4, "riser": 0.175, "goings": 3, "going": 0.30,
                 "src": "GF plan 4 solid riser lines 481 / 484 / 48F / 490 (0.90 m); levels +0.30 -> +1.00 (T-184 ST-01b)"}
    out["E1"] = {"risers": 5, "riser": 0.17, "goings": 4, "going": 0.30,
                 "src": "GF plan 5 riser lines 30A / 30B / 36A / 36C / 36E (1.20 m); +0.15 -> +1.00 (T-184 ST-03)"}
    out["RS-S"] = {"risers": 11, "riser": 4.5 / 28, "goings": 10, "going": 0.30,
                   "src": "1F plan 11 riser lines B43 .. B4D (3.00 m); 28 risers over 4.50 m (T-184 ST-02)"}
    return out


def build(dxf_path):
    d = Dxf(dxf_path)
    fl = _flights()
    S = []

    def add(**kw):
        kw.setdefault("binds", ())
        S.append(kw)

    # ---------------- ST-01 MS1-L: GF west lane, ascending north, wall = west face x -145040 (layer 1)
    y0 = d.y("DC", "5")                 # first riser (+1.00)
    y_last = d.y("485", "2")            # tenth riser line, start of the winder corner
    assert abs((y_last - y0) * MM - fl["MS1-L"]["goings"] * fl["MS1-L"]["going"]) < 1e-6
    xw = d.x("298", "1")
    lo, hi = d.yspan("298", "1")        # solid face below the window
    wlo, whi = d.yspan("354", "W")       # GF window in the west face
    assert abs(xw - d.x("354", "W")) < 1 and abs(hi - wlo) < 1 and lo <= y0 and whi >= y_last
    s_split = (hi - y0) * MM
    run = (y_last - y0) * MM
    cx0, cy0, cx1, cy1 = d.box("2FBD")     # GF column in the west face, 0.050 proud (R-T410-4)
    assert abs(cx1 - xw - 50) < 1 and y0 < cy0 < cy1 < hi
    c0, c1 = (cy0 - y0) * MM, (cy1 - y0) * MM
    add(sid="MS1-L.W1", element="MS1-L", side="west (shaft wall)", cls=K.WALL, s0=0.0, s1=c0,
        evidence="GF wall face 298 (layer 1) beside riser lines DC .. ; 1F plan same face AF1", binds=("ST01-MS1-L-W-a",))
    add(sid="MS1-L.W1C", element="MS1-L", side="west (shaft wall)", cls=K.WALL, s0=c0, s1=c1, face="column",
        returns_lm=0.100, evidence="GF column 2FBD (S-COL.BON) 0.050 proud of 298, both ends on the wall face: 2 "
        "returns x 0.050; ST plan 36B", binds=("ST01-MS1-L-W-col",))
    add(sid="MS1-L.W1B", element="MS1-L", side="west (shaft wall)", cls=K.WALL, s0=c1, s1=s_split,
        evidence="GF wall face 298 (layer 1)", binds=("ST01-MS1-L-W-a2",))
    add(sid="MS1-L.W2", element="MS1-L", side="west (shaft wall)", cls=K.HELD, s0=s_split, s1=run,
        cause="GF window 354-356 (layer W) in the west face over this stretch; its sill / head against the flight "
              "(treads +2.00 .. +2.67) not printed", evidence="GF plan 354 / 353 / 352", binds=("ST01-MS1-L-W-b",))
    add(sid="MS1-L.E", element="MS1-L", side="east (well)", cls=K.OPEN, s0=0.0, s1=run, railing_run="RL-07 MS1-L",
        evidence="well band 157 / 151 (layer 5)")

    # ---------------- MS1-U: east lane, from MS1-LD (+3.50, north) descending in plan to 1F (+5.50, south)
    y0 = d.y("A92", "5")                # first riser at the landing edge (1F plan)
    f = fl["MS1-U"]
    run = f["goings"] * f["going"]
    xe_gf = d.x("21B", "1")
    a_lo, a_hi = d.yspan("21B", "1")
    b_lo, b_hi = d.yspan("21C", "1")
    h_lo, h_hi = d.yspan("33C", "2")
    assert abs(xe_gf - d.x("33C", "2")) < 1 and abs(a_lo - h_hi) < 1 and abs(h_lo - b_hi) < 1
    lo16, hi16 = d.yspan("B16", "1")
    assert lo16 <= y0 - run / MM and hi16 >= y0
    s_a = (y0 - a_lo) * MM              # wall above the hidden opening ends
    s_b = (y0 - b_hi) * MM              # wall resumes
    add(sid="MS1-U.E1", element="MS1-U", side="east (lift wall)", cls=K.WALL, s0=0.0, s1=s_a,
        evidence="GF face 21B (layer 1); 1F face B16 continuous", binds=("ST01-MS1-U-E-a",))
    add(sid="MS1-U.E2", element="MS1-U", side="east (lift wall)", cls=K.HELD, s0=s_a, s1=s_b,
        cause="GF plan draws an opening ABOVE the cut in this face (hidden 33C / 33D, 0.90 m); its height against "
              "the flight (+4.0 .. +4.5) not printed", evidence="GF plan 33C / 33D (layer 2)", binds=("ST01-MS1-U-E-b",))
    add(sid="MS1-U.E3", element="MS1-U", side="east (lift wall)", cls=K.WALL, s0=s_b, s1=run,
        evidence="GF face 21C (layer 1); 1F face B16", binds=("ST01-MS1-U-E-c",))
    add(sid="MS1-U.W", element="MS1-U", side="west (well)", cls=K.OPEN, s0=0.0, s1=run, railing_run="RL-07 MS1-U",
        evidence="well band A8F / A90 (1F)")

    # ---------------- MS2-L: 1F west lane, ascending north, wall = west face x -189893
    y0, y_last = d.y("AC0", "5"), d.y("A97", "5")
    f = fl["MS2-L"]
    run = (y_last - y0) * MM
    assert abs(run - f["goings"] * f["going"]) < 1e-6
    lo, hi = d.yspan("AF1", "1")
    wlo, whi = d.yspan("C5C", "W")
    lo2, hi2 = d.yspan("12B7", "1")
    wlo2, _ = d.yspan("12D1", "W")
    assert abs(hi - wlo) < 1 and lo <= y0 and abs(hi2 - hi) < 1 and abs(wlo2 - wlo) < 1 and whi >= y_last
    s_split = (hi - y0) * MM
    cx0, cy0, cx1, cy1 = d.box("3005")     # 1F column in the west face, 0.050 proud; 2F 2F78 stacked on it
    bx0, by0, bx1, by1 = d.box("2F78")
    assert abs(cx1 - d.x("AF1", "1") - 50) < 1 and abs(by0 - cy0) < 1 and abs(by1 - cy1) < 1 and y0 < cy0 < cy1 < hi
    assert abs(bx1 - d.x("12B7", "1") - 50) < 1
    c0, c1 = (cy0 - y0) * MM, (cy1 - y0) * MM
    add(sid="MS2-L.W1", element="MS2-L", side="west (shaft wall)", cls=K.WALL, s0=0.0, s1=c0,
        evidence="1F face AF1 (layer 1); 2F face 12B7", binds=("ST01-MS2-L-W-a",))
    add(sid="MS2-L.W1C", element="MS2-L", side="west (shaft wall)", cls=K.WALL, s0=c0, s1=c1, face="column",
        returns_lm=0.100, evidence="1F column 3005 / 2F column 2F78 (S-COL.BON) 0.050 proud of AF1 / 12B7, both ends "
        "on the wall face: 2 returns x 0.050; ST plan 691", binds=("ST01-MS2-L-W-col",))
    add(sid="MS2-L.W1B", element="MS2-L", side="west (shaft wall)", cls=K.WALL, s0=c1, s1=s_split,
        evidence="1F face AF1 (layer 1); 2F face 12B7", binds=("ST01-MS2-L-W-a2",))
    add(sid="MS2-L.W2", element="MS2-L", side="west (shaft wall)", cls=K.HELD, s0=s_split, s1=run,
        cause="1F window C5A-C5C and 2F window 12CF-12D1 in the west face over this stretch; flight here +7.18 .. "
              "+7.52 against a 1F window whose sill / head are not printed (stacked shaft windows)",
        evidence="1F C5A / C5B / C5C, 2F 12CF / 12D0 / 12D1 (layer W)", binds=("ST01-MS2-L-W-b",))
    add(sid="MS2-L.E", element="MS2-L", side="east (well)", cls=K.OPEN, s0=0.0, s1=run, railing_run="RL-07 MS2-L",
        evidence="well band A8D / A8E")

    # ---------------- MS2-U: 2F east lane from MS2-LD (+7.684, north) to 2F (+9.70, south)
    y0 = d.y("135B", "5")
    f = fl["MS2-U"]
    run = f["goings"] * f["going"]
    for h in ("B16", "129A"):
        lo, hi = d.yspan(h, "1")
        assert lo <= y0 - run / MM and hi >= y0, h
    add(sid="MS2-U.E", element="MS2-U", side="east (lift wall)", cls=K.WALL, s0=0.0, s1=run,
        evidence="1F face B16 and 2F face 129A (layer 1), continuous, no opening", binds=("ST01-MS2-U-E",))
    add(sid="MS2-U.W", element="MS2-U", side="west (well)", cls=K.OPEN, s0=0.0, s1=run, railing_run="RL-07 MS2-U",
        evidence="well band 1358 / 1359 (2F)")

    # ---------------- D1 lobby flight: GF east lane, +0.30 (north) -> +1.00 (south)
    y0, y_last = d.y("481", "5"), d.y("490", "5")
    f = fl["D1"]
    run = (y0 - y_last) * MM
    assert abs(run - f["goings"] * f["going"]) < 1e-6
    lo, hi = d.yspan("21B", "1")
    assert lo <= y_last and hi >= y0
    add(sid="D1.E", element="D1", side="east (lift wall)", cls=K.WALL, s0=0.0, s1=run,
        evidence="GF face 21B (layer 1) over the whole run", binds=("ST01b-D1-E",))
    add(sid="D1.W", element="D1", side="west (well band)", cls=K.OPEN, s0=0.0, s1=run, railing_run="RL-08",
        evidence="well band 47F / 4A4 (layer 5)")

    # ---------------- ST-03 E1 entrance: risers along x, south side against wall face 15A
    xs = [d.x(h, "5") for h in ("30A", "30B", "36A", "36C", "36E")]
    f = fl["E1"]
    run = (max(xs) - min(xs)) * MM
    assert abs(run - f["goings"] * f["going"]) < 1e-6
    lo, hi = d.xspan("15A", "1")
    ylo, yhi = d.yspan("30A", "5")
    assert lo <= min(xs) and hi >= max(xs) and abs(d.y("15A", "1") - ylo) < 1
    add(sid="E1.S", element="E1", side="south (wall)", cls=K.WALL, s0=0.0, s1=run,
        evidence="GF wall face 15A (layer 1) along the whole run; riser lines end on it", binds=("ST03-E1-S",))
    add(sid="E1.N", element="E1", side="north (edge)", cls=K.OPEN, s0=0.0, s1=run, railing_run="RL-11 (held)",
        evidence="edge 368 (layer 5); no guard drawn (T-164 RL-11)")

    # ---------------- ST-02 straight flight RS-S (1F plan risers), outer (south) side wall 336 on the GF plan
    f = fl["RS-S"]
    x0_1f, x1_1f = d.x("B43", "5"), d.x("B4D", "5")
    run = (x1_1f - x0_1f) * MM
    assert abs(run - f["goings"] * f["going"]) < 1e-6
    off = x0_1f - d.x("22F", "5")       # GF -> 1F sheet offset, from the same first riser on both plans
    w_lo, w_hi = d.xspan("336", "1")
    assert abs(d.y("336", "1") - d.y("A7", "5")) < 1 and abs(d.yspan("B43", "5")[0] - d.y("336", "1")) < 1
    s_w = (w_lo + off - x0_1f) * MM
    x0g = d.x("22F", "5")
    cx0, cy0, cx1, cy1 = d.box("2FD2")     # GF column on the outer side, 0.050 proud of the flight edge A7
    assert abs(cx1 - w_lo) < 1 and abs(cy1 - d.y("336", "1") - 50) < 1 and cx0 > x0g
    c0 = (cx0 - x0g) * MM
    add(sid="RS-S.S0", element="RS-S", side="south (outer)", cls=K.UNKNOWN, s0=0.0, s1=c0, no_face=True,
        cause="no wall or column face on this stretch (wall layer 1 and column layer S-COL.BON both read): only the "
              "50 mm outer band A7 / A9 (layer 5), the continuation of the curved flight's outer band RL-09 whose "
              "role (guard or string) is not established; the 0.050 west return of column 2FD2 waits on it",
        evidence="GF A7 / A9; S-COL.BON: nothing before 2FD2", binds=("ST02-RS-S-S-a",))
    add(sid="RS-S.S1", element="RS-S", side="south (outer)", cls=K.WALL, s0=c0, s1=s_w, face="column",
        returns_lm=0.050, evidence="GF column 2FD2 (S-COL.BON, 0.800 x 0.250) 0.050 proud of the flight edge A7, "
        "ends on 336: 1 return x 0.050 confirmed (the west return HELD with RS-S.S0); ST plan 380",
        binds=("ST02-RS-S-S-col",))
    add(sid="RS-S.S2", element="RS-S", side="south (outer)", cls=K.WALL, s0=s_w, s1=run,
        evidence="GF wall face 336 (layer 1) from its west end to beyond the last riser", binds=("ST02-RS-S-S-b",))
    add(sid="RS-S.N", element="RS-S", side="north (void)", cls=K.OPEN, s0=0.0, s1=run, railing_run="RL-05",
        evidence="inner band 22C / 22E (GF), B76 (1F)")

    # ---------------- ST-02 corner landing RS-LD (+4.696): south side partly on 336, east side guard D-23
    land_end = d.x("AF5", "5")
    wall_end_1f = w_hi + off
    assert x1_1f < wall_end_1f < land_end
    kx0, ky0, kx1, ky1 = d.box("2FC6")     # GF column where 336 stops, 0.050 proud, runs past the landing edge
    assert abs(kx0 - w_hi) < 1 and abs(ky1 - d.y("336", "1") - 50) < 1 and kx1 > land_end - off
    add(sid="RS-LD.S1", element="RS-LD", side="south", cls=K.WALL, s0=0.0, s1=(wall_end_1f - x1_1f) * MM,
        evidence="GF wall face 336 to its east end", binds=("ST02-RS-LD-S-a",))
    add(sid="RS-LD.S2", element="RS-LD", side="south", cls=K.WALL, s0=(wall_end_1f - x1_1f) * MM,
        s1=(land_end - x1_1f) * MM, face="column", returns_lm=0.050,
        evidence="GF column 2FC6 (S-COL.BON, 0.600 x 0.250) where 336 stops, 0.050 proud: its face to the landing "
        "edge AF5 + 1 return x 0.050 at the 336 end (the east end runs past the edge); ST plan 374",
        binds=("ST02-RS-LD-S-b",))
    add(sid="RS-LD.E", element="RS-LD", side="east", cls=K.OPEN, plan=(d.y("B59", "5") - d.yspan("B43", "5")[0]) * MM, railing_run="RL-06",
        evidence="1F floor-edge band AF5 / AF6 (D-23)")
    ra = (d.y("D22", "5") - d.y("B59", "5")) * MM
    add(sid="RS-A.E", element="RS-A", side="east", cls=K.OPEN, plan=ra, railing_run="RL-06",
        evidence="AF5 / AF6 beside the short flight")
    add(sid="RS-A.W", element="RS-A", side="west (void)", cls=K.OPEN, plan=ra, railing_run="RL-05",
        evidence="void band B75 / B77")

    # ---------------- ST-02 curved flight RS-C: outer side on its developed arc (never a chord)
    (cx, cy), r_out = d.arc("23D")
    a_first = _ang(d, "256", cx, cy)
    a_last = math.degrees(math.atan2(d.yspan("22F", "5")[0] - cy, d.x("22F", "5") - cx)) % 360
    sweep = (a_last - a_first) % 360
    add(sid="RS-C.OUT", element="RS-C", side="outer", cls=K.UNKNOWN, curved_radius=r_out * MM,
        curved_angle_deg=sweep, cause="outer 50 mm band 23D / 23E (RL-09): guard or string not established, no wall "
        "face drawn; the curved flight itself is UNRESOLVED (T-398, RFI-S27)",
        evidence="GF arcs 23D / 23E, radial tread lines 240 .. 256", binds=("ST02-RS-C-OUT",))
    add(sid="RS-C.IN", element="RS-C", side="inner (void)", cls=K.OPEN, curved_radius=d.arc("23F")[1] * MM,
        curved_angle_deg=sweep, railing_run="RL-05", evidence="inner arcs 23F / 239")

    # ---------------- landings and the winder corner of ST-01
    gf_e_lo, gf_e_hi = d.yspan("21B", "1")
    y_ld = d.y("481", "5")               # MS1-LD south edge = the D1 / MS1-U first-riser line (-793144)
    y_n = d.y("26E", "1")                # north wall face
    add(sid="MS1-LD.E", element="MS1-LD", side="east (lift wall)", cls=K.WALL, plan=(y_n - y_ld) * MM,
        evidence="GF face 21B and 1F face B16 over the whole landing side (+3.50)", binds=("ST01-MS1-LD-E",))
    xl0, xl1 = d.x("4A4", "5"), d.x("21B", "1")
    w_a = (d.xspan("2AB", "1")[1] - xl0) * MM
    o_lo, o_hi = d.xspan("3FD", "5")
    w_b = (xl1 - d.xspan("26F", "1")[0]) * MM
    assert abs(d.xspan("26F", "1")[1] - xl1) < 1 and abs((o_hi - o_lo) * MM - 0.900) < 1e-6
    add(sid="MS1-LD.N", element="MS1-LD", side="north", cls=K.HELD, plan=(xl1 - xl0) * MM,
        cause=f"the north side holds {w_a:.3f} wall (2AB) + {(o_hi - o_lo) * MM:.3f} opening (3FD / 3FE; a D120 door "
              f"block 3FF sits in it, inserted on layer S-COL.BON, contents on layer D: not a column) + {w_b:.3f} wall "
              "(26F / 2AC); 1F window CE2-CE5 above it; the opening's head / sill against the landing level +3.50 not "
              "printed", evidence="GF 2AB / 3FD / 3FE / 3FF / 26F, 1F CE2", binds=("ST01-MS1-LD-N",))
    add(sid="MS1-T.W", element="MS1-T", side="west", cls=K.HELD, plan=(y_n - d.y("485", "2")) * MM, level_rise=0.833333,
        cause="winder corner: 5 risers on section A-A, 4 wedges on the plans (T-184 MS1-T); winders never generated "
              "(owner S-9)", evidence="GF 49E / 4A0 / 4A2", binds=("ST01-MS1-T-W",))
    add(sid="MS1-T.N", element="MS1-T", side="north", cls=K.HELD, plan=(d.x("157", "5") - d.x("298", "1")) * MM,
        level_rise=0.833333, cause="winder corner (as MS1-T.W)", evidence="GF 26E", binds=("ST01-MS1-T-N",))
    ld_s = d.y("A97", "5")
    add(sid="MS2-LD.W", element="MS2-LD", side="west", cls=K.HELD, plan=(d.y("ADE", "1") - ld_s) * MM, level_rise=0.168,
        cause="closing riser MS2-TR (+7.516 -> +7.684) on this landing: position not drawn (T-184 / T-393); 0.150 m "
              "of the side is also in the 1F window C5C stretch", evidence="1F AF0 / C5C", binds=("ST01-MS2-LD-W",))
    add(sid="MS2-LD.N", element="MS2-LD", side="north", cls=K.HELD, plan=(d.x("B16", "1") - d.x("AF0", "1")) * MM,
        level_rise=0.168, cause="closing riser MS2-TR position not drawn; 1.000 m of the face is the 1F window CE2 "
        "opening (with jambs) whose head / sill against +7.516 is not printed", evidence="1F ADE / CE2 / ADD",
        binds=("ST01-MS2-LD-N",))
    add(sid="MS2-LD.E", element="MS2-LD", side="east (lift wall)", cls=K.HELD, plan=(d.y("ADE", "1") - ld_s) * MM,
        level_rise=0.168, cause="closing riser MS2-TR position not drawn", evidence="1F B16, 2F 129A",
        binds=("ST01-MS2-LD-E",))

    flights = {k: v for k, v in fl.items()}
    census, faces = column_census(d)
    return {"schema": "T410_SIDES_V2", "units": "m", "dxf_sha8": "ab54dd55",
            "flights": flights, "stretches": [{k: (list(v) if isinstance(v, tuple) else v) for k, v in s.items()}
                                              for s in S],
            "faces": faces, "column_census": census}


def _probes(d):
    """Every side line by its own handles: (element, side, plan, axis, line coord, origin, direction, stair-side sign,
    length). axis 'x' = a line at constant x; positions s = (coordinate - origin) x direction, in metres."""
    off = d.x("B43", "5") - d.x("22F", "5")
    ld_e = d.x("AF5", "5") - off
    return [
        ("MS1-L", "west (shaft wall)", "GF", "x", d.x("298", "1"), d.y("DC", "5"), 1, 1, 2.70),
        ("MS1-L", "east (well)", "GF", "x", d.x("157", "5"), d.y("DC", "5"), 1, -1, 2.70),
        ("MS1-U", "east (lift wall)", "GF", "x", d.x("21B", "1"), d.y("A92", "5"), -1, -1, 3.30),
        ("MS1-U", "east (lift wall)", "1F", "x", d.x("B16", "1"), d.y("A92", "5"), -1, -1, 3.30),
        ("MS1-U", "west (well)", "1F", "x", d.x("A8F", "5"), d.y("A92", "5"), -1, 1, 3.30),
        ("MS2-L", "west (shaft wall)", "1F", "x", d.x("AF1", "1"), d.y("AC0", "5"), 1, 1, 3.30),
        ("MS2-L", "west (shaft wall)", "2F", "x", d.x("12B7", "1"), d.y("AC0", "5"), 1, 1, 3.30),
        ("MS2-L", "east (well)", "1F", "x", d.xspan("AC0", "5")[1], d.y("AC0", "5"), 1, -1, 3.30),
        ("MS2-U", "east (lift wall)", "2F", "x", d.x("129A", "1"), d.y("135B", "5"), -1, -1, 3.30),
        ("MS2-U", "east (lift wall)", "1F", "x", d.x("B16", "1"), d.y("135B", "5"), -1, -1, 3.30),
        ("MS2-U", "west (well)", "2F", "x", d.xspan("135B", "5")[0], d.y("135B", "5"), -1, 1, 3.30),
        ("D1", "east (lift wall)", "GF", "x", d.x("21B", "1"), d.y("481", "5"), -1, -1, 0.90),
        ("D1", "west (well band)", "GF", "x", d.x("4A4", "5"), d.y("481", "5"), -1, 1, 0.90),
        ("E1", "south (wall)", "GF", "y", d.y("15A", "1"), d.x("30A", "5"), -1, 1, 1.20),
        ("E1", "north (edge)", "GF", "y", d.y("368", "5"), d.x("30A", "5"), -1, -1, 1.20),
        ("RS-S", "south (outer)", "GF", "y", d.y("336", "1"), d.x("22F", "5"), 1, 1, 3.00),
        ("RS-S", "north (void)", "GF", "y", d.yspan("22F", "5")[1], d.x("22F", "5"), 1, -1, 3.00),
        ("RS-LD", "south", "GF", "y", d.y("336", "1"), d.x("22F", "5") + 3000, 1, 1, 1.20),
        ("RS-LD", "east", "GF", "x", ld_e, d.y("336", "1"), 1, -1, 1.15),
        ("RS-A", "east", "GF", "x", ld_e, d.y("336", "1") + 1150, 1, -1, 1.20),
        ("RS-A", "west (void)", "GF", "x", d.xspan("B76", "5")[1] - off, d.y("336", "1") + 1150, 1, 1, 1.20),
        ("MS1-LD", "east (lift wall)", "GF", "x", d.x("21B", "1"), d.y("481", "5"), 1, -1, 1.15),
        ("MS1-LD", "north", "GF", "y", d.y("26E", "1"), d.x("4A4", "5"), 1, -1, 1.15),
        ("MS1-T", "west", "GF", "x", d.x("298", "1"), d.y("485", "2"), 1, 1, 1.20),
        ("MS1-T", "north", "GF", "y", d.y("26E", "1"), d.x("298", "1"), 1, -1, 1.15),
        ("MS2-LD", "west", "1F", "x", d.x("AF0", "1"), d.y("A97", "5"), 1, 1, 1.20),
        ("MS2-LD", "north", "1F", "y", d.y("ADE", "1"), d.x("AF0", "1"), 1, -1, 2.50),
        ("MS2-LD", "east (lift wall)", "1F", "x", d.x("B16", "1"), d.y("A97", "5"), 1, -1, 1.20),
    ]


def column_census(d):
    """R-T410-4: every closed S-COL.BON outline within 0.30 m of a side line and overlapping its extent."""
    TOL = 300
    boxes = {h: d.box(h) for h in d.outlines("S-COL.BON")}
    rows, faces = [], []
    for el, side, plan, ax, c, org, dr, n, length in _probes(d):
        hits = 0
        for h, (x0, y0, x1, y1) in sorted(boxes.items()):
            p0, p1, a0, a1 = (x0, x1, y0, y1) if ax == "x" else (y0, y1, x0, x1)
            t = sorted(((p0 - c) * n * MM, (p1 - c) * n * MM))
            s = sorted(((a0 - org) * dr * MM, (a1 - org) * dr * MM))
            if t[1] < -TOL * MM or t[0] > TOL * MM or min(s[1], length) - max(s[0], 0.0) <= 1e-6:
                continue
            hits += 1
            if t[0] < 1e-3 and 1e-3 < t[1] <= 0.15:
                rel, proud = "PROUD", round(t[1], 6)
            elif abs(t[1]) <= 5e-3:
                rel, proud = "FLUSH", 0.0
            elif t[0] < 0 < t[1]:
                rel, proud = "CROSSES (body across the side line at its end; its faces belong to the other side)", None
            elif t[0] > 0:
                rel, proud = "IN THE STAIR (freestanding)", None
            else:
                rel, proud = "BEHIND (not a face)", None
            row = {"element": el, "side": side, "plan": plan, "column": h, "relation": rel.split(" (")[0],
                   "s0": round(s[0], 6), "s1": round(s[1], 6), "proud_m": proud, "st_plan": ST_CROSS.get(h, "")}
            rows.append(row)
            if rel in ("PROUD", "FLUSH"):
                # the same column read on two plans (stacked storeys) is one physical face on this side
                same = next((f for f in faces if (f["element"], f["side"], f["s0"], f["s1"], f["proud"])
                             == (el, side, row["s0"], row["s1"], proud)), None)
                if same:
                    same["ref"] += "+" + h
                else:
                    faces.append({"element": el, "side": side, "kind": "column", "s0": row["s0"], "s1": row["s1"],
                                  "proud": proud, "ref": h})
        if not hits:
            rows.append({"element": el, "side": side, "plan": plan, "column": "", "relation": "NONE", "s0": None,
                         "s1": None, "proud_m": None, "st_plan": ""})
    (cx, cy), r_out = d.arc("23D")
    a0, a1 = d.db["23D"].dxf.start_angle, d.db["23D"].dxf.end_angle
    for h, (x0, y0, x1, y1) in sorted(boxes.items()):
        ang = [math.degrees(math.atan2(py - cy, px - cx)) % 360 for px in (x0, x1) for py in (y0, y1)]
        dmin = math.hypot(max(x0 - cx, 0, cx - x1), max(y0 - cy, 0, cy - y1))
        if dmin < r_out + TOL and all(not (a0 <= a <= a1) for a in ang) is False:
            rows.append({"element": "RS-C", "side": "outer", "plan": "GF", "column": h, "relation": "ON ARC",
                         "s0": None, "s1": None, "proud_m": None, "st_plan": ""})
    if not any(r["element"] == "RS-C" for r in rows):
        rows.append({"element": "RS-C", "side": "outer", "plan": "GF", "column": "", "relation": "NONE", "s0": None,
                     "s1": None, "proud_m": None, "st_plan": ""})
    return rows, faces


def _ang(d, h, cx, cy):
    a, b = d.line(h, "5")
    p = a if math.dist(a, (cx, cy)) > math.dist(b, (cx, cy)) else b
    return math.degrees(math.atan2(p[1] - cy, p[0] - cx)) % 360


# ------------------------------------------------------------------ table from the committed sides file

def table(sides):
    flights = {k: K.Flight(k, v["risers"], v["riser"], v["goings"], v["going"]) for k, v in sides["flights"].items()}
    sts = []
    for s in sides["stretches"]:
        kw = dict(s)
        kw["binds"] = tuple(kw.get("binds", ()))
        for k in ("s0", "s1", "plan", "curved_radius", "curved_angle_deg"):
            if isinstance(kw.get(k), float):
                kw[k] = round(kw[k], 9)
        sts.append(K.Stretch(**kw))
    rows = K.measure(flights, sts)
    faces = [K.Face(**f) for f in sides.get("faces", [])]
    return rows, K.check_faces(sts, faces)


def _fmt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.6f}"
    return str(v)


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: _fmt(r[k]) for k in COLS})


def census_csv(census, fchk):
    import io
    by = {}
    for f in fchk:
        for ref in f["ref"].split("+"):
            by[(f["element"], f["side"], ref)] = f
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=CCOLS, lineterminator="\n")
    w.writeheader()
    for r in census:
        fc = by.get((r["element"], r["side"], r["column"]), {})
        w.writerow({**{k: _fmt(r.get(k)) for k in CCOLS}, "carrier": fc.get("carrier", ""),
                    "returns_confirmed_lm": _fmt(fc.get("returns_confirmed_lm")),
                    "returns_held_lm": _fmt(fc.get("returns_held_lm"))})
    return buf.getvalue()


def summary(rows):
    t = K.totals(rows)
    per_stair = {}
    for r in rows:
        st = ("ST-01" if r["element"].startswith(("MS", "D1")) else "ST-02" if r["element"].startswith("RS")
              else "ST-03")
        p = per_stair.setdefault(st, {"wall_side_risers_form_held": 0, "held_risers": 0})
        if r["status"] == K.FORM_HELD:
            p["wall_side_risers_form_held"] += r["risers_in"]
        elif r["class"] == K.HELD and r["risers_in"]:
            p["held_risers"] += r["risers_in"]
    return {"task": "T-410", "stretches": len(rows), "totals_lm": t, "per_stair": per_stair,
            "line_quantity_lm": {"confirmed_horizontal": t["confirmed_horizontal_lm"],
                                 "sloping_wall_sides": "HELD (form, ORR-007)",
                                 "form_conditional_beside_blank": {"zigzag": t["form_held_zigzag_lm"],
                                                                   "sloped": t["form_held_sloped_lm"]}}}


def main(argv):
    if "--check" in argv:
        sides = json.loads(SIDES_JSON.read_text())
        rows, fchk = table(sides)
        with open(TABLE_CSV, newline="", encoding="utf-8") as f:
            committed = list(csv.DictReader(f))
        same = committed == [{k: _fmt(r[k]) for k in COLS} for r in rows]
        same = same and census_csv(sides["column_census"], fchk) == COLUMN_CSV.read_text(encoding="utf-8")
        same = same and json.loads(SUMMARY.read_text()) == json.loads(json.dumps(summary(rows)))
        print("REPRODUCED" if same else "DIFFERS")
        return 0 if same else 1
    dxf = argv[argv.index("--dxf") + 1]
    sides = build(dxf)
    rows, fchk = table(sides)
    print(json.dumps(summary(rows), indent=1))
    if "--write" in argv:
        SIDES_JSON.write_text(json.dumps(sides, indent=1, ensure_ascii=False) + "\n")
        write_csv(rows, TABLE_CSV)
        COLUMN_CSV.write_text(census_csv(sides["column_census"], fchk), encoding="utf-8")
        SUMMARY.write_text(json.dumps(summary(rows), indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
