"""T-412 development-villa nosing / tread / riser census (Alsenan is one sample; the method is nosing_census.py).

Build (needs the PRIVATE architectural DXF, Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip, decoded into
.work/private only):
    python3 -I research/agents_t412/t412_alsenan.py --dxf <P7757.dxf> --write
reads every edge BY ENTITY HANDLE, asserts layer / orientation / spacing / extent, converts to run positions and lengths
(metres; no coordinates) and writes ALSENAN_EDGES_T412.json, NOSING_TABLE_T412.csv, FLIGHT_TABLE_T412.csv and
summary.json beside this file. Check (no private input):
    python3 -I research/agents_t412/t412_alsenan.py --check
recomputes both tables and the summary from the committed ALSENAN_EDGES_T412.json and prints REPRODUCED.

Drawing reading (own, this run, layer 5 = solid, layer 2 = hidden / above the cut): every flight is drawn as PAIRS of
parallel lines 0.050 apart, a solid / first line and a companion offset 0.050 UPHILL (MS1-L DC / DE, MS2-L AC0 / AC2,
E1 30B / 30E, RS-S B43 / B4E, RS-C 256 / 257 at +1.33 deg = 0.050 at the mid radius): the front (nosing) edge and the
riser face behind it, i.e. a drawn nosing projection of 0.050 m. The front edge is the downhill line of each pair.
Riser counts: section A-A for ST-01 (Q-46 A, T-184), plan reconstruction for ST-02 / ST-03 / D1 (Q-50 A cond, T-184).
No drawing text, client name or freelancer row text is written; the freelancer's piece counts are quantities only.
"""

from __future__ import annotations

import csv
import io
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nosing_census as N  # noqa: E402

MM = 0.001
EDGES_JSON = HERE / "ALSENAN_EDGES_T412.json"
NOSING_CSV = HERE / "NOSING_TABLE_T412.csv"
FLIGHT_CSV = HERE / "FLIGHT_TABLE_T412.csv"
SUMMARY = HERE / "summary.json"
NCOLS = ["eid", "flight", "stair", "riser_no", "kind", "status", "shape", "length_m", "radius_m", "angle_deg",
         "notch_m", "qty_lm", "beside_lm", "in_step_basis", "handles", "cause", "evidence", "binds"]
FCOLS = ["flight", "stair", "risers", "risers_source", "visible_risers", "treads", "treads_confirmed", "landing_edges",
         "floor_edges", "nosings_confirmed", "nosings_held", "nosings_unknown", "nosing_lm_confirmed",
         "nosing_lm_confirmed_in_step_basis", "nosing_lm_confirmed_landing_floor", "held_beside_lm"]

# The freelancer's stair piece rows (FIN workbook on Drive, read through the connector's search content, read-only):
# per stair, pieces ('count'), one per step; quantities only. No nosing row exists in his workbook.
FREELANCER_PIECES = {"ST-03": 5, "ST-01": 63, "ST-02": 28}
FREELANCER_WIDTH_PER_PIECE = {"ST-03": 2.80, "ST-01": 1.20, "ST-02": 1.20}


class Dxf:
    def __init__(self, path):
        import ezdxf
        self.msp = ezdxf.readfile(path).modelspace()
        self.h = {e.dxf.handle: e for e in self.msp if e.dxftype() in ("LINE", "LWPOLYLINE", "ARC")}

    def line(self, h, layer=None):
        e = self.h[h]
        assert e.dxftype() == "LINE", (h, e.dxftype())
        if layer is not None:
            assert e.dxf.layer == layer, (h, e.dxf.layer, layer)
        a, b = e.dxf.start, e.dxf.end
        return (a.x, a.y), (b.x, b.y)

    def hline(self, h, layer=None):      # horizontal: y, x0, x1
        (ax, ay), (bx, by) = self.line(h, layer)
        assert abs(ay - by) < 1, h
        return ay, min(ax, bx), max(ax, bx)

    def vline(self, h, layer=None):      # vertical: x, y0, y1
        (ax, ay), (bx, by) = self.line(h, layer)
        assert abs(ax - bx) < 1, h
        return ax, min(ay, by), max(ay, by)

    def box(self, h):
        e = self.h[h]
        assert e.dxftype() == "LWPOLYLINE" and e.closed and e.dxf.layer == "S-COL.BON", h
        xs = [p[0] for p in e.get_points()]
        ys = [p[1] for p in e.get_points()]
        return min(xs), min(ys), max(xs), max(ys)

    def arc(self, h):
        e = self.h[h]
        assert e.dxftype() == "ARC", h
        return (e.dxf.center.x, e.dxf.center.y), e.dxf.radius, e.dxf.start_angle, e.dxf.end_angle


def _straight(fid, stair, handles_layers, axis, uphill, d, lane=None):
    """front edges of a straight flight: [(handle, layer, companion handle)], in riser order (lowest first).
    Asserts: parallel, same extent, 0.300 apart, companion 0.050 uphill. Returns [(s, length, handle, companion)]."""
    out = []
    pos0 = None
    for i, (h, lay, comp) in enumerate(handles_layers):
        if axis == "y":
            p, a, b = d.hline(h, lay)
            pc, ac, bc = d.hline(comp)
        else:
            p, a, b = d.vline(h, lay)
            pc, ac, bc = d.vline(comp)
        if pos0 is None:
            pos0 = p
        s = abs(p - pos0) * MM
        assert abs(s - 0.300 * i) < 1e-6, (fid, h, s)
        assert abs((pc - p) * uphill - 50) < 1, (fid, h, comp, pc - p)
        if lane is None:
            assert abs(ac - a) < 1 and abs(bc - b) < 1, (fid, h, comp)
            ln = (b - a) * MM
        else:
            ln = (lane[1] - lane[0]) * MM
            assert lane[0] - 1 <= a and b <= lane[1] + 1, (fid, h)
        out.append((round(s, 6), round(ln, 6), h, comp))
    return out


def build(dxf_path):
    d = Dxf(dxf_path)
    E = []

    def add(**kw):
        for k in ("length_m", "notch_m", "beside_lm", "s"):
            if kw.get(k) is not None:
                kw[k] = round(float(kw[k]), 6)
        kw.setdefault("shape", N.STRAIGHT)
        kw.setdefault("notch_m", 0.0)
        kw.setdefault("source", "drawn")
        kw.setdefault("cause", "")
        kw.setdefault("binds", [f"B7-05:{kw['eid']}"] if kw["status"] == N.CONFIRMED else [])
        E.append(kw)

    # ---------------- ST-01 MS1-L (GF, west lane, ascends north; 10 risers +1.00 -> +2.667, section A-A / T-184)
    ms1l = [("DC", "5", "DE"), ("DD", "5", "DF"), ("CE", "5", "D0"), ("CF", "5", "D1"), ("C6", "5", "CA"),
            ("C7", "5", "CB"), ("C9", "5", "CC")]
    rows = _straight("MS1-L", "ST-01", ms1l, "y", +1, d)
    y0 = d.hline("DC", "5")[0]
    # C8 (s 2.1) is drawn solid only to the cut break (0.575); C5 (2.4) and 485 (2.7, drawn twice: 485 / C4) hidden
    yc8, a8, b8 = d.hline("C8", "5")
    assert abs((yc8 - y0) * MM - 2.1) < 1e-6 and abs((b8 - a8) * MM - 0.575) < 1e-6
    assert abs(d.hline("CD", "2")[0] - yc8 - 50) < 1
    lane = (d.vline("298", "1")[0], d.vline("157", "5")[0])           # wall face 298 .. well band 157
    assert abs((lane[1] - lane[0]) * MM - 1.150) < 1e-6 and abs(a8 - lane[0]) < 1
    yc5 = d.hline("C5", "2")[0]
    y485, a485, b485 = d.hline("485", "2")
    yc4, a4, b4 = d.hline("C4", "2")
    assert abs((yc5 - y0) * MM - 2.4) < 1e-6 and abs((y485 - y0) * MM - 2.7) < 1e-6
    assert abs(yc4 - y485) < 1 and abs(a4 - a485) < 1 and abs(b4 - b485) < 1          # one edge drawn twice
    assert abs(d.hline("486", "2")[0] - y485 - 50) < 1
    cx0, cy0, cx1, cy1 = d.box("2FBD")
    proud = (cx1 - lane[0]) * MM
    c0, c1 = (cy0 - y0) * MM, (cy1 - y0) * MM
    assert abs(proud - 0.050) < 1e-6 and abs(c0 - 0.40) < 1e-6 and abs(c1 - 0.90) < 1e-6
    rows += [(2.1, 1.150, "C8", "CD"), (2.4, 1.150, "C5", "?"), (2.7, round((b485 - a485) * MM, 6), "485", "486")]
    for i, (s, ln, h, comp) in enumerate(rows, start=1):
        nt = N.notch_on_edge(s, c0, c1, proud)
        ev = f"GF {h} ({'layer 5' if h in dict((x[0], 1) for x in ms1l) or h == 'C8' else 'layer 2, above the cut'})"
        if h == "C8":
            ev += "; drawn 0.575 to the cut break, edge = lane 298 .. 157 (1.150)"
        if h == "485":
            ev += " (also drawn as C4: one edge, counted once); front of the first winder of the turn"
        if nt:
            ev += f"; column 2FBD 0.050 proud of 298 over s {c0:.2f} .. {c1:.2f} (T-410 R-T410-4)"
        add(eid=f"ST01-MS1L-N{i:02d}", flight="MS1-L", stair="ST-01", riser_no=i,
            kind=N.WINDER if i == 10 else N.TREAD, status=N.CONFIRMED, length_m=ln, notch_m=nt,
            handles=[h] + ([comp] if comp != "?" else []), evidence=ev, s=s)

    # ---------------- MS1-T winder turn (+2.667 -> +3.50): section A-A 5 risers, plans 4 wedges (T-184 MS1-T)
    radial = []
    for h, comp in (("4A2", "4A3"), ("49E", "49F"), ("4A0", "4A1")):
        (ax, ay), (bx, by) = d.line(h, "2")
        radial.append((h, comp, round(math.hypot(bx - ax, by - ay) * MM, 6)))
        assert abs(ax - lane[1]) < 1 and abs(ay - y485 - 50) < 1, h      # all radiate from the inner corner
    turn_cause = ("winder turn: section A-A draws 5 risers (+2.667 -> +3.50), the architectural plans 4 wedges (fronts "
                  "485 / 4A2 / 49E / 4A0), and the structural GF roof slab plan (ST p.4) 12 straight lines in this lane "
                  "(45A .. 25E, 3.30) + 3 radial (2F6 / 2F4 / 2F5): split 10 + 5 (A-A) vs 12 + 3 (ST p.4) of the same "
                  "15 risers to +3.50; count conflict (T-184 MS1-T, Q-51 A cond, C-ST-3); winders never generated "
                  "(owner S-9)")
    for i, (h, comp, ln) in enumerate(radial, start=1):
        add(eid=f"ST01-MS1T-N{i:02d}", flight="MS1-T", stair="ST-01", riser_no=i, kind=N.WINDER, status=N.HELD,
            beside_lm=ln, handles=[h, comp], cause=turn_cause,
            evidence=f"GF {h} radial front edge from the inner corner, {ln:.3f} (never the lane width)")
    add(eid="ST01-MS1T-N04", flight="MS1-T", stair="ST-01", riser_no=4, kind=N.WINDER, status=N.HELD,
        handles=[], cause=turn_cause, evidence="the fifth section riser has no front edge on the plans")
    add(eid="ST01-MS1T-N05", flight="MS1-T", stair="ST-01", riser_no=5, kind=N.LANDING_EDGE, status=N.HELD,
        beside_lm=round((d.vline("2C6", "2")[2] - d.vline("2C6", "2")[1]) * MM, 6), handles=["2C6"],
        cause=turn_cause + "; the MS1-LD edge at the well head (band 2C6 / 49C / 49D) is not established as the riser",
        evidence="GF 2C6 (layer 2) band line 1.150 between the turn and MS1-LD")

    # ---------------- MS1-U (1F plan, east lane, from MS1-LD +3.50 ascending south to 1F +5.50; 12 risers A-A)
    ms1u = [("A92", "5", "A93"), ("A95", "5", "A94"), ("AA5", "5", "A9E"), ("AA6", "5", "AA0"), ("AA7", "5", "A9F"),
            ("AA8", "5", "A9D"), ("AA9", "5", "AA4"), ("AAA", "5", "AA3"), ("AAB", "5", "AA2"), ("AAC", "5", "AA1"),
            ("ABE", "5", "ABD")]
    for i, (s, ln, h, comp) in enumerate(_straight("MS1-U", "ST-01", ms1u, "y", -1, d), start=1):
        add(eid=f"ST01-MS1U-N{i:02d}", flight="MS1-U", stair="ST-01", riser_no=i, kind=N.TREAD, status=N.CONFIRMED,
            length_m=ln, handles=[h, comp], evidence=f"1F {h} (layer 5)", s=s)
    add(eid="ST01-MS1U-N12", flight="MS1-U", stair="ST-01", riser_no=12, kind=N.FLOOR_EDGE, status=N.HELD,
        beside_lm=1.150, handles=[], s=3.3,
        cause="12th riser (section A-A, Q-46 A) arrives on the 1F floor: no edge line on the architectural plans (11 "
              "lines); the structural GF roof slab plan draws it (459 at s 3.30, 1.150); its position lies in the B20 "
              "head clash (HEAD-CLASH, Q-46 RFI)",
        evidence="1F east lane: nothing drawn at s 3.30 (lane 1.150 beside); ST p.4 459")

    # ---------------- MS2-L (1F, west lane, ascends north, +5.50 -> landing MS2-LD +7.516; 12 risers)
    ms2l = [("AC0", "5", "AC2"), ("ABF", "5", "AC1"), ("AB5", "5", "AB9"), ("AB6", "5", "ABA"), ("AB7", "5", "ABB"),
            ("AB8", "5", "ABC"), ("AAD", "5", "AB1"), ("AAE", "5", "AB2"), ("AB0", "5", "AB3"), ("AAF", "5", "AB4"),
            ("A98", "5", "A99"), ("A97", "5", "A9A")]
    rows = _straight("MS2-L", "ST-01", ms2l, "y", +1, d)
    ya0 = d.hline("AC0", "5")[0]
    kx0, ky0, kx1, ky1 = d.box("3005")
    proud = (kx1 - d.vline("AF1", "1")[0]) * MM
    c0, c1 = (ky0 - ya0) * MM, (ky1 - ya0) * MM
    assert abs(proud - 0.050) < 1e-6 and abs(c0 - 1.00) < 1e-6 and abs(c1 - 1.50) < 1e-6
    for i, (s, ln, h, comp) in enumerate(rows, start=1):
        nt = N.notch_on_edge(s, c0, c1, proud)
        ev = f"1F {h} (layer 5)" + (f"; column 3005 0.050 proud of AF1 over s {c0:.2f} .. {c1:.2f}" if nt else "")
        add(eid=f"ST01-MS2L-N{i:02d}", flight="MS2-L", stair="ST-01", riser_no=i,
            kind=N.LANDING_EDGE if i == 12 else N.TREAD, status=N.CONFIRMED, length_m=ln, notch_m=nt,
            handles=[h, comp], evidence=ev + (" = MS2-LD landing edge (+7.516)" if i == 12 else ""), s=s)

    # ---------------- MS2-TR closing riser on MS2-LD (+7.516 -> +7.684)
    add(eid="ST01-MS2TR-N01", flight="MS2-TR", stair="ST-01", riser_no=1, kind=N.LANDING_EDGE, status=N.HELD,
        handles=[], cause="closing riser MS2-TR (section A-A, +7.516 -> +7.684): its position on MS2-LD is not drawn "
                          "(T-184 / T-393 / T-410); the upper landing surface's edge is unknown",
        evidence="1F / 2F: no line on MS2-LD")

    # ---------------- MS2-U (2F plan, east lane, from MS2-LD +7.684 ascending south to 2F +9.70; 12 risers)
    ms2u = [("135B", "5", "135C"), ("135E", "5", "135D"), ("136D", "5", "1366"), ("136E", "5", "1368"),
            ("136F", "5", "1367"), ("1370", "5", "1365"), ("1371", "5", "136C"), ("1372", "5", "136B"),
            ("1373", "5", "136A"), ("1374", "5", "1369"), ("1386", "5", "1385")]
    for i, (s, ln, h, comp) in enumerate(_straight("MS2-U", "ST-01", ms2u, "y", -1, d), start=1):
        add(eid=f"ST01-MS2U-N{i:02d}", flight="MS2-U", stair="ST-01", riser_no=i, kind=N.TREAD, status=N.CONFIRMED,
            length_m=ln, handles=[h, comp], evidence=f"2F {h} (layer 5)", s=s)
    add(eid="ST01-MS2U-N12", flight="MS2-U", stair="ST-01", riser_no=12, kind=N.FLOOR_EDGE, status=N.HELD,
        beside_lm=1.150, handles=[], s=3.3,
        cause="12th riser (section A-A) arrives on the 2F floor: no edge line on the architectural plans (11 lines) "
              "nor on the structural 1F roof slab plan (62F .. 644, 11 lines); its position lies in the B23 head clash "
              "(HEAD-CLASH, Q-46 RFI)",
        evidence="2F east lane: nothing drawn at s 3.30 (lane 1.150 beside)")

    # ---------------- D1 lobby flight (GF east lane, +0.30 north -> +1.00 south; 4 riser lines)
    d1 = [("481", "5", "482"), ("484", "5", "483"), ("48F", "5", "488"), ("490", "5", "48A")]
    for i, (s, ln, h, comp) in enumerate(_straight("D1", "ST-01", d1, "y", -1, d), start=1):
        add(eid=f"ST01-D1-N{i:02d}", flight="D1", stair="ST-01", riser_no=i,
            kind=N.FLOOR_EDGE if i == 4 else N.TREAD, status=N.CONFIRMED, length_m=ln, handles=[h, comp],
            evidence=f"GF {h} (layer 5)" + (" = GF stair-room floor edge (+1.00)" if i == 4 else ""), s=s)

    # ---------------- ST-03 E1 entrance (GF, risers along x, ascends east; +0.15 -> +1.00, 5 lines 2.800)
    e1 = [("36E", "5", "36F"), ("36C", "5", "36D"), ("36A", "5", "36B"), ("30B", "5", "30E"), ("30A", "5", "30D")]
    for i, (s, ln, h, comp) in enumerate(_straight("E1", "ST-03", e1, "x", +1, d), start=1):
        add(eid=f"ST03-E1-N{i:02d}", flight="E1", stair="ST-03", riser_no=i,
            kind=N.LANDING_EDGE if i == 5 else N.TREAD, status=N.CONFIRMED, length_m=ln, handles=[h, comp],
            evidence=f"GF {h} (layer 5)" + (" = entrance platform edge (+1.00)" if i == 5 else ""), s=s)

    # ---------------- ST-02 RS-C curved part (GF, 12 radial front edges 256 .. 240, +1.00 -> +2.929): HELD Q-50 A cond
    (cx, cy), r_out, _, _ = d.arc("23D")
    _, r_in, _, _ = d.arc("239")
    rc = ["256", "254", "252", "250", "24E", "24C", "24A", "248", "246", "244", "242", "240"]
    for i, h in enumerate(rc, start=1):
        (ax, ay), (bx, by) = d.line(h, "5")
        ln = math.hypot(bx - ax, by - ay) * MM
        ra, rb = math.hypot(ax - cx, ay - cy), math.hypot(bx - cx, by - cy)
        assert abs(min(ra, rb) - r_in) < 2, h                          # radial, from the inner band
        assert abs(max(ra, rb) - (r_out + (50 if h == "256" else 0))) < 2, h
        add(eid=f"ST02-RSC-N{i:02d}", flight="RS-C", stair="ST-02", riser_no=i, kind=N.TREAD, status=N.HELD,
            beside_lm=round(ln, 6), handles=[h, "%X" % (int(h, 16) + 1)],
            cause="curved part of the round stair HELD (owner Q-50 A cond: curved parts held; no section; T-398 "
                  "RFI-S27)" + ("; this first edge runs over the outer 50 mm band (RL-09 role open)" if h == "256"
                                else ""),
            evidence=f"GF {h} radial straight front edge r {r_in * MM:.3f} .. {max(ra, rb) * MM:.3f} (not an arc)")

    # ---------------- RS-S straight (1F lines B43 .. B4D, ascends east, +2.929 -> landing RS-LD +4.696; 11 risers)
    rss = [("B43", "B4E"), ("B4A", "B55"), ("B49", "B54"), ("B48", "B53"), ("B47", "B52"), ("B46", "B51"),
           ("B45", "B50"), ("B44", "B4F"), ("B4B", "B56"), ("B4C", "B57"), ("B4D", "B58")]
    rows = _straight("RS-S", "ST-02", [(h, "5", c) for h, c in rss], "x", +1, d)
    x0g = d.vline("22F", "5")[0]
    gx0, gy0, gx1, gy1 = d.box("2FD2")
    ya7 = d.hline("A7", "5")[0]
    proud = (gy1 - ya7) * MM
    c0, c1 = (gx0 - x0g) * MM, (gx1 - x0g) * MM
    assert abs(proud - 0.050) < 1e-6 and abs(c0 - 0.20) < 1e-6 and abs(c1 - 1.00) < 1e-6
    for i, (s, ln, h, comp) in enumerate(rows, start=1):
        nt = N.notch_on_edge(s, c0, c1, proud)
        ev = (f"1F {h} (layer 5)" + (f"; column 2FD2 0.050 proud of A7 over s {c0:.2f} .. {c1:.2f}" if nt else "")
              + (" = RS-LD landing edge (+4.696)" if i == 11 else "") + "; reconstructed, no section (Q-50 A cond)")
        add(eid=f"ST02-RSS-N{i:02d}", flight="RS-S", stair="ST-02", riser_no=i,
            kind=N.LANDING_EDGE if i == 11 else N.TREAD, status=N.CONFIRMED, length_m=ln, notch_m=nt,
            handles=[h, comp], evidence=ev, s=s)

    # ---------------- RS-A arrival (1F lines B59 .. D22, ascends north, +4.696 -> 1F +5.50; 5 risers)
    rsa = [("B59", "5", "B6E"), ("B5A", "5", "B6F"), ("B5B", "5", "B70"), ("B5C", "5", "B71"), ("D22", "5", "D24")]
    for i, (s, ln, h, comp) in enumerate(_straight("RS-A", "ST-02", rsa, "y", +1, d), start=1):
        add(eid=f"ST02-RSA-N{i:02d}", flight="RS-A", stair="ST-02", riser_no=i,
            kind=N.FLOOR_EDGE if i == 5 else N.TREAD, status=N.CONFIRMED, length_m=ln, handles=[h, comp],
            evidence=f"1F {h} (layer 5)" + (" = 1F floor edge (+5.50)" if i == 5 else "")
            + "; reconstructed, no section (Q-50 A cond)", s=s)

    flights = [
        {"flight": "MS1-L", "stair": "ST-01", "risers": 10, "risers_source": "section A-A 10 (T-184, Q-46 A); plan 10 lines"},
        {"flight": "MS1-T", "stair": "ST-01", "risers": 5, "risers_source": "section A-A 5; plans 4 wedges (CONFLICT)"},
        {"flight": "MS1-U", "stair": "ST-01", "risers": 12, "risers_source": "section A-A 12 (Q-46 A); plans 11 lines"},
        {"flight": "MS2-L", "stair": "ST-01", "risers": 12, "risers_source": "section A-A 12; plan 12 lines"},
        {"flight": "MS2-TR", "stair": "ST-01", "risers": 1, "risers_source": "section A-A closing riser; not on plans"},
        {"flight": "MS2-U", "stair": "ST-01", "risers": 12, "risers_source": "section A-A 12; plans 11 lines"},
        {"flight": "D1", "stair": "ST-01", "risers": 4, "risers_source": "GF plan 4 lines, +0.30 -> +1.00 (T-184 ST-01b)"},
        {"flight": "E1", "stair": "ST-03", "risers": 5, "risers_source": "GF plan 5 lines, +0.15 -> +1.00 (T-184 ST-03)"},
        {"flight": "RS-C", "stair": "ST-02", "risers": 12, "risers_source": "GF plan 12 radial lines (Q-50 A cond, no section)"},
        {"flight": "RS-S", "stair": "ST-02", "risers": 11, "risers_source": "1F plan 11 lines (Q-50 A cond, no section)"},
        {"flight": "RS-A", "stair": "ST-02", "risers": 5, "risers_source": "1F plan 5 lines (Q-50 A cond, no section)"},
    ]
    return {"schema": "T412_EDGES_V1", "units": "m", "dxf_sha8": "ab54dd55", "flights": flights, "edges": E,
            "drawn_nosing_projection_m": 0.050}


def st_cross_read(st_path):
    """Second drawing: the structural DXF (Drive "ST7757 dxf.dxf", sha 9f9d1179) draws the same stair lanes on the
    slab plans. Counted BY HANDLE of the first / last line of each lane, every line 1.150 long, 0.300 apart."""
    import ezdxf
    msp = ezdxf.readfile(st_path).modelspace()
    hl = {e.dxf.handle: e for e in msp.query("LINE")}

    def lane(h_first, h_last):
        a, b = hl[h_first], hl[h_last]
        x0, x1 = sorted((a.dxf.start.x, a.dxf.end.x))
        y0, y1 = sorted((a.dxf.start.y, b.dxf.start.y))
        ys = sorted({round(e.dxf.start.y) for e in msp.query("LINE")
                     if abs(e.dxf.start.y - e.dxf.end.y) < 1 and abs(min(e.dxf.start.x, e.dxf.end.x) - x0) < 2
                     and abs(max(e.dxf.start.x, e.dxf.end.x) - x1) < 2 and y0 - 1 <= e.dxf.start.y <= y1 + 1})
        assert abs((x1 - x0) - 1150) < 1, h_first
        assert all(abs((ys[i + 1] - ys[i]) - 300) < 2 for i in range(len(ys) - 1)), h_first
        return {"lines": len(ys), "span_m": round((ys[-1] - ys[0]) * MM, 3), "width_m": 1.150,
                "first_last": [h_first, h_last]}

    out = {"p4_west_MS1-L": lane("45A", "25E"), "p4_east_MS1-U": lane("459", "25B"),
           "p5_west_MS2-L": lane("646", "632"), "p5_east_MS2-U": lane("644", "62F"), "D1": lane("1C7", "1C4")}
    rad = [h for h in ("2DF", "2E0", "2E1", "2E2", "2E3", "2E4", "2E5", "2E6", "2E7", "2E8", "2E9", "2EA")]
    lens = [hl[h].dxf.start.distance(hl[h].dxf.end) * MM for h in rad]
    assert all(abs(x - 1.150) < 0.003 for x in lens)
    out["p4_RS-C_radial"] = {"lines": len(rad), "width_m": 1.150, "first_last": ["2DF", "2EA"]}
    for h in ("2F4", "2F5", "2F6"):
        e = hl[h]
        assert abs(e.dxf.start.x - e.dxf.end.x) > 1 and abs(e.dxf.start.y - e.dxf.end.y) > 1, h
    out["p4_turn_radial"] = {"lines": 3, "handles": ["2F6", "2F4", "2F5"]}
    assert out["p4_west_MS1-L"]["lines"] == 12 and out["p4_east_MS1-U"]["lines"] == 12
    assert out["p5_west_MS2-L"]["lines"] == 12 and out["p5_east_MS2-U"]["lines"] == 11 and out["D1"]["lines"] == 4
    return out


# engine flight (candidate calculation input 'flight_id') -> drawn flight, with the basis of the binding: the engine's
# own cross-plan repeat record (ARCH_PLAN run/cross_plan_stairs, overlap 1.0) plus its kind / lines / run / layer
ENGINE_TO_DRAWN = {
    "SITE-3759f2457b22cb4a:F1": ("MS1-L", "stacked under 1F F2 (= MS2-L, west lane); 8 hidden lines run 2.1 = the riser "
                                          "faces DE .. CD of MS1-L"),
    "SITE-3759f2457b22cb4a:F2": ("D1", "4 solid lines run 0.9 (481 .. 490); stacked under 1F F3 (east lane)"),
    "SITE-735e111dcf9b22c8:F1": ("RS-C", "RADIAL 13 lines, 12 treads, width 1.150"),
    "SITE-735e111dcf9b22c8:F2": ("RS-S", "seen through the void as 1F F4 (= RS-S B43 .. B4D); GF reading 7 lines"),
    "SITE-735e111dcf9b22c8:F3": ("RS-S", "BY ELIMINATION (no repeat recorded): the rest of the GF reading of RS-S"),
    "SITE-735e111dcf9b22c8:F4": ("RS-A", "seen through the void as 1F F6 (= RS-A B59 .. D22)"),
    "SITE-a95bf979baf4cfae:F1": ("RS-C", "seen through the void (exposure; measured on GF F1)"),
    "SITE-a95bf979baf4cfae:F2": ("MS2-L", "12 solid lines run 3.3 (AC0 .. A97), west lane"),
    "SITE-a95bf979baf4cfae:F3": ("MS1-U", "11 solid lines run 3.0 (A92 .. ABE), east lane"),
    "SITE-a95bf979baf4cfae:F4": ("RS-S", "11 lines run 3.0 (B43 .. B4D), exposure (measured on GF F2)"),
    "SITE-a95bf979baf4cfae:F5": (None, "UNBOUND: a 4-tread RADIAL reading of width 1.247 (layer 2) matches no drawn "
                                       "flight on the 1F plan (no radial line at RS-LD): B7-02 owner row"),
    "SITE-a95bf979baf4cfae:F6": ("RS-A", "5 lines run 1.2 (B59 .. D22), exposure (measured on GF F4)"),
    "SITE-d7254c68fd33723d:F1": ("MS2-L", "stacked over 1F F2: the west lane seen from 2F, no flight of 2F (T-184 "
                                          "R-STAIR-CONT-1, T-129)"),
    "SITE-d7254c68fd33723d:F2": ("MS2-U", "stacked over 1F F3 (east lane); 11 lines 135B .. 1386, engine 11 lines"),
}
STAIR_CODES = ("FIN.MARBLE.TREAD", "FIN.STAIR.STEP_LM", "FIN.MARBLE.RISER", "FIN.STAIR.FLIGHT", "FIN.RAILING")


def candidate_binding(lines_json, data):
    """bind every drawn flight to the candidate's stair lines (V3_0_35_BOQ_LINES.json of a run of record). Writes ids,
    states, engine treads and the drawn treads only (no coordinates)."""
    import hashlib
    raw = Path(lines_json).read_bytes()
    lines = json.loads(raw)
    lines = lines["lines"] if isinstance(lines, dict) else lines
    by_el = {}
    for x in lines:
        if x["item_code"] in STAIR_CODES:
            by_el.setdefault(x["location"]["element_id"], []).append(x)
    drawn_treads = {}
    for f in data["flights"]:
        drawn_treads[f["flight"]] = sum(1 for e in data["edges"] if e["flight"] == f["flight"]
                                        and e["kind"] in (N.TREAD, N.WINDER))
    rows = []
    for el, xs in sorted(by_el.items()):
        tread = next((x for x in xs if x["item_code"] == "FIN.MARBLE.TREAD"), None)
        if tread is None or "flight_id" not in (tread["calculation"].get("inputs") or {}):
            continue
        inp = tread["calculation"]["inputs"]
        fid = inp["flight_id"]
        drawn, basis = ENGINE_TO_DRAWN[fid]
        rows.append({"engine_flight": fid, "element_id": el, "drawn_flight": drawn, "basis": basis,
                     "engine_treads": inp["treads"], "engine_lines": inp["tread_lines"], "engine_kind": inp["kind"],
                     "engine_width_m": inp["width_m"],
                     "drawn_treads": drawn_treads.get(drawn) if drawn else None,
                     "lines": {x["item_code"]: {"line_id": x["line_id"], "state": x["evidence_state"],
                                                "net": x["measured_net"]} for x in xs}})
    assert {r["engine_flight"] for r in rows} == set(ENGINE_TO_DRAWN), "a candidate flight is unbound or unknown"
    return {"candidate": "ARCH_TAKEOFF_V3.0.35", "file": "V3_0_35_BOQ_LINES.json",
            "sha256": hashlib.sha256(raw).hexdigest(), "lines": len(lines), "flights": rows,
            "nosing_lines_in_candidate": sum(1 for x in lines if "NOSING" in x["item_code"])}


# ------------------------------------------------------------------ table (no private input)

def _edge(x):
    return N.Edge(eid=x["eid"], flight=x["flight"], riser_no=x["riser_no"], kind=x["kind"], status=x["status"],
                  shape=x.get("shape", N.STRAIGHT), length_m=x.get("length_m"), radius_m=x.get("radius_m"),
                  angle_deg=x.get("angle_deg"), notch_m=x.get("notch_m", 0.0), source=x.get("source", "drawn"),
                  handles=tuple(x.get("handles", ())), cause=x.get("cause", ""), evidence=x.get("evidence", ""),
                  beside_lm=x.get("beside_lm"), binds=tuple(x.get("binds", ())))


def census(data):
    fl = []
    for f in data["flights"]:
        c = N.FlightCensus(flight=f["flight"], stair=f["stair"], risers=f["risers"], risers_source=f["risers_source"],
                           edges=[_edge(x) for x in data["edges"] if x["flight"] == f["flight"]])
        fl.append(c)
    assert sum(len(c.edges) for c in fl) == len(data["edges"]), "an edge belongs to no flight"
    return fl


def _fmt(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return f"{v:.6f}"
    if isinstance(v, (list, tuple)):
        return " ".join(str(x) for x in v)
    return str(v)


def nosing_csv(fl):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=NCOLS, lineterminator="\n")
    w.writeheader()
    for c in fl:
        for e in sorted(c.edges, key=lambda e: e.riser_no):
            w.writerow({k: _fmt(v) for k, v in {
                "eid": e.eid, "flight": e.flight, "stair": c.stair, "riser_no": e.riser_no, "kind": e.kind,
                "status": e.status, "shape": e.shape, "length_m": e.length_m, "radius_m": e.radius_m,
                "angle_deg": e.angle_deg, "notch_m": e.notch_m, "qty_lm": e.qty_lm, "beside_lm": e.beside_lm,
                "in_step_basis": e.in_step_basis, "handles": e.handles, "cause": e.cause, "evidence": e.evidence,
                "binds": e.binds}.items()})
    return buf.getvalue()


def flight_csv(fl):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FCOLS, lineterminator="\n")
    w.writeheader()
    for c in fl:
        w.writerow({k: _fmt(v) for k, v in c.summary().items()})
    return buf.getvalue()


def summary(fl, data):
    per = {}
    for c in fl:
        s = c.summary()
        ints = ("risers", "treads", "treads_confirmed", "landing_edges", "floor_edges", "nosings_confirmed",
                "nosings_held")
        p = per.setdefault(c.stair, {k: 0 for k in ints})
        for k in ints:
            p[k] += s[k]
        for k in ("nosing_lm_confirmed", "nosing_lm_confirmed_in_step_basis", "nosing_lm_confirmed_landing_floor",
                  "held_beside_lm"):
            p[k] = round(p.get(k, 0.0) + s[k], 6)
    ours = {st: v["risers"] for st, v in per.items()}
    tot = {k: round(sum(v[k] for v in per.values()), 6) for k in next(iter(per.values()))}
    notched = [e.eid for c in fl for e in c.edges if e.notch_m]
    return {"task": "T-412", "edges": len(data["edges"]), "flights": len(fl), "per_stair": per, "totals": tot,
            "notched_edges": notched, "drawn_nosing_projection_m": data["drawn_nosing_projection_m"],
            "freelancer_pieces_vs_risers": N.piece_reconciliation(ours, FREELANCER_PIECES),
            "freelancer_width_per_piece_m": FREELANCER_WIDTH_PER_PIECE,
            "b7_05_line": {"confirmed_lm": tot["nosing_lm_confirmed"],
                           "of_which_inside_b7_06_step_basis_lm": tot["nosing_lm_confirmed_in_step_basis"],
                           "landing_and_floor_edges_lm": tot["nosing_lm_confirmed_landing_floor"],
                           "held_edges": tot["nosings_held"], "held_beside_lm": tot["held_beside_lm"],
                           "specification": "HELD: NOSING_FORM_NOT_PRINTED (no Urban rule, no printed note on the "
                                            "profile; the plans draw only a 0.050 projection)"}}


def main(argv):
    if "--check" in argv:
        data = json.loads(EDGES_JSON.read_text())
        fl = census(data)
        same = (nosing_csv(fl) == NOSING_CSV.read_text(encoding="utf-8")
                and flight_csv(fl) == FLIGHT_CSV.read_text(encoding="utf-8")
                and json.loads(SUMMARY.read_text()) == json.loads(json.dumps(summary(fl, data))))
        print("REPRODUCED" if same else "DIFFERS")
        return 0 if same else 1
    data = build(argv[argv.index("--dxf") + 1])
    if "--st" in argv:
        data["st_cross_read"] = st_cross_read(argv[argv.index("--st") + 1])
    elif "--write" in argv:
        raise SystemExit("--write needs --st <ST7757 dxf.dxf> (the second drawing is part of the evidence)")
    if "--candidate" in argv:
        b = candidate_binding(argv[argv.index("--candidate") + 1], data)
        if "--write" in argv:
            (HERE / "CANDIDATE_BINDING_T412.json").write_text(json.dumps(b, indent=1, ensure_ascii=False) + "\n")
    fl = census(data)
    s = summary(fl, data)
    print(json.dumps(s, indent=1))
    if "--write" in argv:
        EDGES_JSON.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
        NOSING_CSV.write_text(nosing_csv(fl), encoding="utf-8")
        FLIGHT_CSV.write_text(flight_csv(fl), encoding="utf-8")
        SUMMARY.write_text(json.dumps(s, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
