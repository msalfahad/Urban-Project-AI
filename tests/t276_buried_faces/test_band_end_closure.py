"""T-276 r2 (Checker 2026-10-24 20:59): a member ends on its carrier's drawn face on EACH of its own edges; a sub-mm
offset between outlines is not a member. Villa Q (synthetic, not Alsenan), hand-calculated.

Q1 (curved carrier): ring r 2250 / 2550 mm round the origin; a 300 mm band (edges y 1350 and 1650) comes from x -6000
and frames into the ring's convex face. Edge A (y 1350) meets r 2550 at x = -sqrt(2550^2 - 1350^2) = -2163.33, edge B
(y 1650) at -sqrt(2550^2 - 1650^2) = -1944.22: 219.1 mm apart. The paired strip is the overlap (to -2163.33, square).
Drawn concrete beyond the square cut: area = int_1350^1650 (-sqrt(R^2 - y^2) + 2163.33) dy (by hand, formula below).
Faces: side A 6000 - 2163.33 = 3.8367 m, side B 6000 - 1944.22 = 4.0558 m, END only at the free end x -6000 (0.30 m).

Q2 (re-entrant corner): carriers x 0..300 (vertical) and y 0..300 (horizontal) meet in an L (inner corner 300, 300). A
45-degree band (u = (1, 1) / sqrt 2; edges at offsets -100 / +200 from the axis through the corner) frames into the
corner: edge A (y = x - 141.42) ends on the horizontal face at (441.42, 300), edge B (y = x + 282.84) on the vertical face
at (300, 582.84); stations 524.26 / 624.26. The restored piece is the quadrilateral (441.42, 300), (300, 300),
(300, 582.84), (512.13, 370.71): shoelace by hand.

Q3 (sub-mm offset): band 0..3000 x 0..300, column 1200..1500 x -0.05..299.95 (drawn 0.05 mm low): the 0.05 mm strip
above it is a drafting offset; the band's top face over the column is the column's own face (neck line), 0.30 m.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t276"))
import buried_faces_v2 as F  # noqa: E402
import face_trace as FT  # noqa: E402

shapely = pytest.importorskip("shapely")
from shapely.geometry import Point, Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

R_OUT, R_IN, LO, HI, X0 = 2550.0, 2250.0, 1350.0, 1650.0, -6000.0
XA = -math.sqrt(R_OUT ** 2 - LO ** 2)        # -2163.33
XB = -math.sqrt(R_OUT ** 2 - HI ** 2)        # -1944.22


def _ring():
    return Point(0, 0).buffer(R_OUT, quad_segs=1024).difference(Point(0, 0).buffer(R_IN, quad_segs=1024))


def _q1(close=True):
    ring = _ring()
    strip = box(X0, LO, XA, HI)
    ends = FT.close_band_ends((1.0, 0.0), LO, HI, X0, XA, (X0, XA), (X0, XB), ring, reach=HI - LO)
    poly = unary_union([strip] + [e["poly"] for e in ends if close and e["status"] == "CLOSED"])
    side_t = {"A": (X0, XA), "B": (X0, XB if close else XA)}
    span = ("SPAN", "Q1", poly, {"u": (1.0, 0.0), "n": (0.0, 1.0), "lo": LO, "hi": HI, "ta": X0, "tb": XA,
                                 "side_t": side_t})
    arc = ("ARC", "RING", ring, {"centre": (0.0, 0.0), "r_out": R_OUT, "r_in": R_IN})
    solid = unary_union([poly, ring]).buffer(FT.SNAP_TOL / 2).buffer(-FT.SNAP_TOL / 2)   # as the extract closes it
    rings = [("OUTER-1", list(solid.exterior.coords))]
    return ends, FT.trace([span, arc], rings, step=1.0)["OUTER-1"]["pieces"]


def _hand_pocket():
    def G(y):
        return 0.5 * (y * math.sqrt(R_OUT ** 2 - y ** 2) + R_OUT ** 2 * math.asin(y / R_OUT))
    return -(G(HI) - G(LO)) - XA * (HI - LO)


def test_q1_band_on_a_curved_carrier_closes_on_the_arc():
    ends, pieces = _q1(close=True)
    e = {r["end"]: r for r in ends}
    assert e["start"]["status"] == "NONE"                         # free end: both edges end at x -6000
    assert e["end"]["status"] == "CLOSED" and e["end"]["free_len"] <= FT.SNAP_TOL
    assert e["end"]["stations"]["B"] - e["end"]["stations"]["A"] == pytest.approx(219.11, abs=0.01)
    assert e["end"]["area"] == pytest.approx(_hand_pocket(), rel=2e-3)
    L = {k: v / 1000.0 for k, v in pieces.items()}
    # +-3 mm: 1 mm steps at an acute junction on a 4096-segment arc
    assert L[("SPAN", "Q1", "A")] == pytest.approx((XA - X0) / 1000.0, abs=3e-3)      # 3.8367
    assert L[("SPAN", "Q1", "B")] == pytest.approx((XB - X0) / 1000.0, abs=3e-3)      # 4.0558
    assert L[("SPAN", "Q1", "END")] == pytest.approx(0.30, abs=2e-3)                   # the free end only


def test_q1_adverse_square_cut_at_the_shorter_edge_invents_a_pocket_and_is_refused():
    _, pieces = _q1(close=False)
    end = pieces[("SPAN", "Q1", "END")] / 1000.0
    assert end > 0.30 + 0.25                       # free end 0.30 + an invented 'end face' at the square cut
    with pytest.raises(F.RefusedError, match="square cut"):
        F.check_end_face("Q1", {"start": {"edge_offset_mm": 0.0, "closed": True},
                                "end": {"edge_offset_mm": 219.1, "closed": False}})
    assert F.check_end_face("Q1", {"start": {"edge_offset_mm": 0.0, "closed": True},
                                   "end": {"edge_offset_mm": 219.1, "closed": True}})


def test_q1_mirrored_and_rotated_give_the_same_restored_area():
    from shapely import affinity
    base = _q1(close=True)[0][1]["area"]
    ring = affinity.rotate(_ring(), 90.0, origin=(0, 0))
    u = (0.0, 1.0)              # (x, y) -> (-y, x): stations = old x, offsets along n = (-1, 0) = old y
    ends = FT.close_band_ends(u, LO, HI, X0, XA, (X0, XA), (X0, XB), ring, reach=HI - LO)
    assert ends[1]["status"] == "CLOSED" and ends[1]["area"] == pytest.approx(base, rel=1e-6)
    ringm = affinity.scale(_ring(), xfact=-1.0, yfact=1.0, origin=(0, 0))
    # mirror x -> -x: u = (-1, 0), n = (0, -1): stations = old x, offsets = -old y (edges swap A / B)
    ends = FT.close_band_ends((-1.0, 0.0), -HI, -LO, X0, XA, (X0, XB), (X0, XA), ringm, reach=HI - LO)
    assert ends[1]["status"] == "CLOSED" and ends[1]["area"] == pytest.approx(base, rel=1e-6)


def test_q2_band_into_a_re_entrant_corner_closes_on_both_carriers():
    s2 = math.sqrt(2.0)
    u = (1 / s2, 1 / s2)
    carriers = unary_union([box(0, 0, 300, 3000), box(0, 0, 3000, 300)])
    ta, tb, t_far = 741.42 / s2, 882.84 / s2, 3000.0
    ends = FT.close_band_ends(u, -100.0, 200.0, tb, t_far, (ta, t_far), (tb, t_far), carriers, reach=300.0)
    e = ends[0]
    assert e["status"] == "CLOSED" and e["pad"] == 300.0          # needs room past the farther edge end (the corner)
    hand = Polygon([(441.42, 300), (300, 300), (300, 582.84), (512.13, 370.71)]).area
    assert e["area"] == pytest.approx(hand, rel=2e-3)


def test_q2_adverse_edge_far_short_of_any_carrier_stays_open():
    # edge B stops 400 mm short of the vertical carrier (more than one band width): OPEN, nothing restored, never
    # closed into a neighbour
    s2 = math.sqrt(2.0)
    u = (1 / s2, 1 / s2)
    carriers = unary_union([box(0, 0, 300, 3000), box(0, 0, 3000, 300)])
    ta, tb, t_far = 741.42 / s2, 882.84 / s2 + 400.0, 3000.0
    ends = FT.close_band_ends(u, -100.0, 200.0, tb, t_far, (ta, t_far), (tb, t_far), carriers, reach=300.0)
    assert ends[0]["status"] == "OPEN" and ends[0]["poly"] is None


def test_ray_closure_of_an_edge_drawn_short_of_its_carrier():
    # Q1 with edge B drawn 110 mm short of the ring: closed along its own line (reach 300) and the gap is reported
    ring = _ring()
    xb_short = XB - 110.0
    ends = FT.close_band_ends((1.0, 0.0), LO, HI, X0, XA, (X0, XA), (X0, xb_short), ring, reach=HI - LO)
    assert ends[1]["status"] == "CLOSED"
    assert ends[1]["ray_gap"]["B"] == pytest.approx(110.0, abs=0.5)
    assert ends[1]["area"] == pytest.approx(_hand_pocket(), rel=2e-3)


def _q3(low_mm):
    band = box(0, 0, 3000, 300)
    col = box(1200, -low_mm, 1500, 300 - low_mm)
    spans = [("SPAN", "S1", box(0, 0, 1200, 300), {"u": (1.0, 0.0), "n": (0.0, 1.0), "lo": 0.0, "hi": 300.0,
                                                   "ta": 0.0, "tb": 1200.0}),
             ("SPAN", "S2", box(1500, 0, 3000, 300), {"u": (1.0, 0.0), "n": (0.0, 1.0), "lo": 0.0, "hi": 300.0,
                                                      "ta": 1500.0, "tb": 3000.0})]
    rest = band.difference(unary_union([s[2] for s in spans] + [col]))
    pieces = [g for g in getattr(rest, "geoms", [rest]) if g.area > 0]
    return band, col, spans, pieces


def test_q3_a_0_05_mm_offset_is_the_column_face():
    band, col, spans, pieces = _q3(0.05)
    assert len(pieces) == 1 and FT.is_sliver(pieces[0])
    with pytest.raises(ValueError, match="thinner than"):        # adverse: the sliver kept as a member is refused
        FT.check_owners(spans + [("PIECE", "SLIVER", pieces[0], {})])
    owners = spans + [("COLUMN", "C1", col, {})]
    solid = unary_union([band, col]).buffer(FT.SNAP_TOL / 2).buffer(-FT.SNAP_TOL / 2)
    got = FT.trace(owners, [("OUTER-1", list(solid.exterior.coords))], step=1.0)["OUTER-1"]["pieces"]
    assert got[("COLUMN", "C1", None)] / 1000.0 == pytest.approx(0.60, abs=2e-3)   # top 0.30 + bottom 0.30: neck
    assert not [k for k in got if k[0] == "PIECE"]
    with pytest.raises(F.RefusedError):                                # a column face is never a beam face
        F.face_row("C1 | OUTER-1", "COLUMN", "column face", "OUTER", None, 0.30, {"depth": 0.95})


def test_q3_normal_a_2_mm_strip_is_a_member():
    _, _, _, pieces = _q3(2.0)
    assert len(pieces) == 1 and not FT.is_sliver(pieces[0])          # 2 mm > SNAP_TOL: a drawn band strip
