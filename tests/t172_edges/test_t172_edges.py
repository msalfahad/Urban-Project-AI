"""T-172 regression tests: parapets and corners as physical items (ENGINEERING_REASONING_STANDARD sections 3 and 4C).

Synthetic, hand-calculated, NOT the development villa. Normal and adverse cases:
- a parapet's top is an AREA (centreline x t) plus TWO external top arrises (outer and inner); a third 'line per metre'
  is not a physical arris of a plain rectangular parapet;
- a half-rate payment convention never changes the physical length;
- the inner face stops at higher construction (ABUT), runs square at a free end (FREE, stop-end arrises), and is HELD
  where the end condition is unknown; a niche shallower than the wall does not move the inner face;
- rotation, mirror and units do not change a length; a missing thickness or height is HELD, never 0.
"""
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t172"))

import t172_edges as E  # noqa: E402


def S(name, a, b, normal, t=0.20, kind="STRAIGHT", c=None, r=None):
    s = {"name": name, "a": a, "b": b, "normal": normal, "t": t, "kind": kind}
    if kind == "ARC":
        s.update(c=c, r=r)
    return s


def ring_10x6(t=0.20):
    # clockwise outline 10 x 6 m: south, west, north, east with outward normals
    return [S("S", (10, 0), (0, 0), (0, -1), t), S("W", (0, 0), (0, 6), (-1, 0), t),
            S("N", (0, 6), (10, 6), (0, 1), t), S("E", (10, 6), (10, 0), (1, 0), t)]


CLOSED = {"type": "CLOSED"}


def h05(_s):
    return 0.50


# ------------------------------------------------------------------------------------------- normal cases
def test_closed_parapet_components_by_hand():
    c = E.parapet_components(ring_10x6(), CLOSED, CLOSED, h05)
    # outer 2 x (10 + 6) = 32.00; inner 2 x (9.60 + 5.60) = 30.40
    assert c["outer_top_arris_ml"] == pytest.approx(32.0)
    assert c["inner_top_arris_ml"] == pytest.approx(30.4)
    # top surface = centreline (32 + 30.4) / 2 = 31.2 m x 0.20 = 6.24 m2 (an area, not a line)
    assert c["top_surface_m2"] == pytest.approx(6.24)
    assert c["outer_face_m2"] == pytest.approx((16.0, 16.0))
    assert c["inner_face_m2"] == pytest.approx((15.2, 15.2))
    # the inner base junction with the roof is a termination line, equal to the inner run, not an arris
    assert c["inner_base_junction_ml"] == pytest.approx(30.4)
    assert c["stop_ends"] == []
    # physical external arrises per metre of parapet: 1.95 (outer + inner), never 3
    assert E.edges_per_metre(c) == pytest.approx(1.95)


def test_two_sided_chain_abutting_a_higher_storey():
    # parapet on the south and east edges only; the west and north edges carry a higher wall (roof-side faces at
    # x = 0.20 and y = 5.80)
    ch = [S("S", (0, 0), (10, 0), (0, -1)), S("E", (10, 0), (10, 6), (1, 0))]
    start = {"type": "ABUT", "line": ((0.20, 0.0), (0.0, 1.0))}
    end = {"type": "ABUT", "line": ((0.0, 5.80), (1.0, 0.0))}
    r = E.inner_runs(ch, start, end)
    assert dict(r["parts"]) == pytest.approx({"S": 9.60, "E": 5.60})
    c = E.parapet_components(ch, start, end, h05)
    assert c["outer_top_arris_ml"] == pytest.approx(16.0)
    assert c["stop_ends"] == []                      # abutting ends are internal angles, no stop-end arris


def test_free_end_gives_stop_end_arrises():
    ch = [S("S", (0, 0), (10, 0), (0, -1)), S("E", (10, 0), (10, 6), (1, 0))]
    end = {"type": "ABUT", "line": ((0.0, 5.80), (1.0, 0.0))}
    c = E.parapet_components(ch, {"type": "FREE"}, end, h05)
    assert dict(E.inner_runs(ch, {"type": "FREE"}, end)["parts"])["S"] == pytest.approx(9.80)
    (st,) = c["stop_ends"]
    assert st["status"] == "DRAWING-CONFIRMED"
    assert st["vertical_ml"] == pytest.approx((1.0, 1.0))   # two vertical arrises of 0.50 m
    assert st["top_ml"] == pytest.approx(0.20)


def test_tangent_convex_arc_and_concave_bay():
    # convex quarter arc r = 1.30 tangent to two straights (as a rounded corner): inner r = 1.10
    ch = [S("A", (0, 2.3), (1.0, 2.3), (0, 1)),
          S("R", (1.0, 2.3), (2.3, 1.0), (0.7071, 0.7071), kind="ARC", c=(1.0, 1.0), r=1.3),
          S("B", (2.3, 1.0), (2.3, 0.0), (1, 0))]
    r = E.inner_runs(ch, {"type": "FREE"}, {"type": "FREE"})
    p = dict(r["parts"])
    assert E.side_length(ch[1]) == pytest.approx(1.3 * math.pi / 2)
    assert p["R"] == pytest.approx(1.1 * math.pi / 2)
    assert p["A"] == pytest.approx(1.0) and p["B"] == pytest.approx(1.0)
    # concave bay: centre OUTSIDE the building (x = 3.0, outline at x = 2.0): the inner arc grows to r + t
    bay = [S("N1", (2.0, 4.0), (2.0, 2.8), (1, 0)),
           S("BAY", (2.0, 2.8), (2.0, 1.2), (1, 0), kind="ARC", c=(3.0, 2.0), r=math.hypot(1.0, 0.8)),
           S("N2", (2.0, 1.2), (2.0, 0.0), (1, 0))]
    rb = E.inner_runs(bay, {"type": "FREE"}, {"type": "FREE"})
    r_in = math.hypot(1.0, 0.8) + 0.20
    dy = math.sqrt(r_in ** 2 - 1.2 ** 2)            # inner line x = 1.80 is 1.20 from the centre
    pb = dict(rb["parts"])
    assert pb["BAY"] == pytest.approx(r_in * 2 * math.asin(dy / r_in))
    assert pb["N1"] == pytest.approx(4.0 - (2.0 + dy))


def test_niche_does_not_move_the_inner_face():
    # 10 m wall face with a niche 0.08 deep x 0.50 wide in its middle; free ends
    ch = [S("a", (0, 0), (4.75, 0), (0, -1)), S("r1", (4.75, 0), (4.75, 0.08), (-1, 0)),
          S("m", (4.75, 0.08), (5.25, 0.08), (0, -1)), S("r2", (5.25, 0.08), (5.25, 0), (1, 0)),
          S("b", (5.25, 0), (10, 0), (0, -1))]
    c = E.parapet_components(ch, {"type": "FREE"}, {"type": "FREE"}, h05)
    assert c["outer_top_arris_ml"] == pytest.approx(10.16)  # the outer top edge follows the niche returns
    assert c["inner_top_arris_ml"] == pytest.approx(10.0)   # the inner face is the straight wall's
    assert c["niches"] == [[0, 1, 2, 3, 4]]
    assert dict(c["inner_by_side"]) == pytest.approx({"a": 4.75, "r1": 0.0, "m": 0.5, "r2": 0.0, "b": 4.75})

    # adverse: different parapet heights either side of the niche; each part of the inner face keeps its own
    def h(s):
        return 1.0 if s["name"] == "b" else 0.5
    c2 = E.parapet_components(ch, {"type": "FREE"}, {"type": "FREE"}, h)
    assert c2["inner_face_m2"] == pytest.approx((4.75 * 0.5 + 0.5 * 0.5 + 4.75 * 1.0,) * 2)
    # an inner face is never larger than the outer face of the same parapet heights here
    assert c2["inner_face_m2"][0] <= c2["outer_face_m2"][0]


def test_half_rate_never_changes_physical_length():
    f = E.four_figures(physical_ml=1000.0, contract_ml=1000.0, payable_factor=0.5, rate_qty_ml=1000.0,
                       rate_per_ml=1.25, equiv_rate_per_payable=2.50)
    assert f["physical_ml"] == 1000.0 and f["contract_ml"] == 1000.0
    assert f["payable_ml"] == 500.0
    # same money two ways: full length at half rate == half length at full rate
    assert f["rate_basis_amount"] == pytest.approx(f["payable_amount_at_equiv_rate"])
    # a payable quantity is never a conversion of metres into square metres: no m2 key appears
    assert not any("m2" in k for k in f)


def test_cell_decoder_is_evidence_not_proof():
    # 3 lines per metre on a 12.5 m parapet: one cell of 12.5 (A) and one of 25.0 (B)
    assert (1, 0) in E.decode_cell(12.5, 12.5, 0.7)
    assert (2, 0) in E.decode_cell(25.0, 12.5, 0.7)
    assert E.decode_cell(None, 12.5, 0.7) == []


# ------------------------------------------------------------------------------------------- adverse cases
@pytest.mark.parametrize("deg,mirror", [(0, False), (30, False), (-121, False), (0, True), (47, True)])
def test_rotation_mirror_units(deg, mirror):
    a = math.radians(deg)

    def tf(p, k=1.0):
        x, y = p
        if mirror:
            x = -x
        return (k * (x * math.cos(a) - y * math.sin(a)), k * (x * math.sin(a) + y * math.cos(a)))

    def tn(n):
        x, y = n
        if mirror:
            x = -x
        return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))

    ring = ring_10x6()
    if mirror:          # mirroring reverses the travel; keep a consistent chain by reversing the order and ends
        ring = [dict(s, a=s["b"], b=s["a"]) for s in reversed(ring)]
    rr = [dict(s, a=tf(s["a"]), b=tf(s["b"]), normal=tn(s["normal"])) for s in ring]
    c = E.parapet_components(rr, CLOSED, CLOSED, h05)
    assert c["outer_top_arris_ml"] == pytest.approx(32.0)
    assert c["inner_top_arris_ml"] == pytest.approx(30.4)
    # millimetres: every length x 1000, thickness 200
    mm = [dict(s, a=tf(s["a"], 1000.0), b=tf(s["b"], 1000.0), normal=tn(s["normal"]), t=200.0) for s in ring]
    assert E.inner_runs(mm, CLOSED, CLOSED)["inner_m"] == pytest.approx(30400.0)
    # convex junctions of the 10 x 6 ring: all four (in any orientation)
    assert all(E.turn_is_convex(rr[k], rr[(k + 1) % 4]) for k in range(4))


def test_l_ring_one_concave_corner():
    L = [S("W", (0, 0), (0, 6), (-1, 0)), S("N1", (0, 6), (4, 6), (0, 1)), S("E1", (4, 6), (4, 3), (1, 0)),
         S("N2", (4, 3), (10, 3), (0, 1)), S("E2", (10, 3), (10, 0), (1, 0)), S("S", (10, 0), (0, 0), (0, -1))]
    conv = [E.turn_is_convex(L[k], L[(k + 1) % 6]) for k in range(6)]
    assert conv == [True, True, False, True, True, True]
    # inner ring (0.2,0.2) (0.2,5.8) (3.8,5.8) (3.8,2.8) (9.8,2.8) (9.8,0.2): 5.6+3.6+3.0+6.0+2.6+9.6
    assert E.inner_runs(L, CLOSED, CLOSED)["inner_m"] == pytest.approx(30.4)


def test_missing_thickness_is_held_never_zero():
    ring = ring_10x6()
    ring[1]["t"] = None
    with pytest.raises(ValueError, match="HELD"):
        E.inner_runs(ring, CLOSED, CLOSED)


def test_unknown_end_and_held_height_stay_ranges():
    ch = [S("S", (0, 0), (10, 0), (0, -1)), S("E", (10, 0), (10, 6), (1, 0))]

    def h(s):
        return ("HELD", 0.40, 1.60) if s["name"] == "E" else 0.50
    c = E.parapet_components(ch, {"type": "UNKNOWN"}, {"type": "FREE"}, h)
    assert c["held_height_sides"] == ["E"]
    assert c["outer_face_m2"] == pytest.approx((10 * 0.5 + 6 * 0.4, 10 * 0.5 + 6 * 1.6))
    st = {x["end"]: x for x in c["stop_ends"]}
    assert st["start"]["status"] == "HELD" and st["start"]["vertical_ml"] == pytest.approx((0.0, 1.0))
    assert st["end"]["status"] == "HELD" and st["end"]["vertical_ml"] == pytest.approx((0.8, 3.2))


def test_arc_thicker_than_radius_and_open_ring_refused():
    bad = [S("A", (0, 0.2), (0.0, 0.2), (0, 1))]
    with pytest.raises(ValueError):
        E.inner_runs([S("R", (0.0, 0.1), (0.1, 0.0), (0.7071, 0.7071), kind="ARC", c=(0, 0), r=0.1)],
                     {"type": "FREE"}, {"type": "FREE"})
    with pytest.raises(ValueError, match="CLOSED"):
        E.inner_runs(ring_10x6()[:3], CLOSED, CLOSED)
    with pytest.raises(ValueError):
        E.inner_runs(bad, {"type": "FREE"}, {"type": "FREE"})


def test_vertical_corner_overlap_and_held():
    assert E.vertical_corner_ml((0.15, 5.50), (1.00, 6.00)) == pytest.approx(4.50)
    assert E.vertical_corner_ml((0.0, 4.0), (5.0, 8.0)) == 0.0
    assert E.vertical_corner_ml((None, 5.5), (1.0, 6.0)) is None
