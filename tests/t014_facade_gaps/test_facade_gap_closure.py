"""T-014: FACADE_GAP_CLOSURE_V1 (engine/source/facade_gap_closure.py) against hand truth. Not Alsenan.

Hand plan A (metres): a 10.00 x 8.00 m building. On the south face a window opening x 4.00 .. 5.50 (1.50 m) in a
0.20 m wall; the frame sits at the inner face, so the outline steps 0.20 m in, runs 1.50 m along the glazing and
steps 0.20 m out. Walked run = 2 x (10 + 8) + 2 x 0.20 = 36.40 m. Closed at the face line (UP-FACADE-001) = 36.00 m
(saves 0.40 m); the window is reported as an opening the census missed, 1.50 m wide.
    A1 no glazing in the step              -> HELD, run 36.00 .. 36.40 m (never closed on its size)
    A2 glazing 1.00 of 1.50 m              -> HELD (partly glazed)
    A3 a porch 1.50 m deep, 0.20 m wall    -> KEPT (deeper than its wall: the building steps back), run 39.00 m
    A4 wall thickness not known            -> HELD
    A5 a measured threshold in the step    -> KEPT (already an opening)
    A6 one jamb is a column side           -> CLOSED, beside_column
    A7 two steps, one glazed, one not      -> 36.80 walked, HELD range 36.00 .. 36.40
Hand plan B, a corner notch (the frame end of a glazed bay beside a column): building 0..4 x 0..3.20 m; east face
glazing x = 4.00 from y 0 to 3.00; the wall's south face y = 3.00 from x 4.00 to 4.08; a column 4.08..4.58 x
2.95..3.20. Walked = 4 + 2.95 + 0.05 + 0.08 + 0.05 + 0.50 + 0.25 + 4.58 + 3.20 = 15.66 m; closing the 0.08 x 0.05 m
notch on the column face line would save 0.05 + 0.08 + 0.05 - 0.08 = 0.10 m; with no glass across its mouth its three
sides are exterior faces -> KEPT, 15.66 m; glass drawn across its mouth -> HELD, 15.56 .. 15.66 m.
Hand plan C, glazed gaps on a wall band (faces y = 0 and y = 0.20, x 0 .. 10, gap 4.00 .. 7.00 = 3.00 m with jamb
lines at x 4 and 7; frame lines y 0.08 and 0.12): CLOSED_GLAZED 3.00 m on both faces; no glazing -> HELD; glazing
over 4 .. 6 only -> HELD; a missing jamb -> HELD; a 5.20 m glazed gap (wider than the old reader's 2.60 m) -> CLOSED.
A glass bay (a flattened arc of radius 2.00 m, half a turn = pi x 2 = 6.283185 m) joining two wall lines -> a
boundary of that length; the same arc with one end short of the wall -> open, never extended.
Variants: through the engine's own topology and arch_v29 facade outline (the walked run is the engine's run), the
ring started at another edge, reversed, mirrored, rotated 30 deg, built in millimetres (unit 0.001); empty input.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import facade_gap_closure as G                 # noqa: E402
from engine.source import topology as TP                          # noqa: E402
from engine.source import arch_v29 as V29                         # noqa: E402

T = 0.20


def ring_of(points, roles, t=T):
    """consecutive points (CCW or CW) -> ring edges; roles: {edge index: role}; every WALL edge carries t."""
    out = []
    for i, a in enumerate(points):
        b = points[(i + 1) % len(points)]
        r = roles.get(i, "WALL")
        out.append({"a": list(a), "b": list(b), "roles": [r], "straight": True,
                    "wall_t_m": t if r in ("WALL", "WALL_CAP") else None})
    return out


PLAN_A = [(0, 0), (4, 0), (4, 0.2), (5.5, 0.2), (5.5, 0), (10, 0), (10, 8), (0, 8)]
GLAZED_A = {2: "WINDOW"}


def xf(points, rot_deg=0.0, mirror=False, scale=1.0, dx=0.0, dy=0.0):
    c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
    out = []
    for x, y in points:
        if mirror:
            x = -x
        out.append(((c * x - s * y) * scale + dx, (s * x + c * y) * scale + dy))
    return out


# ---------------------------------------------------------------------------------------- plan A
def test_a_closed_at_face_line():
    r = G.recess_closures(ring_of(PLAN_A, GLAZED_A))
    assert r["state"] == "RESOLVED"
    assert r["walked_m"] == pytest.approx(36.40, abs=1e-6)
    assert r["closed_m"] == pytest.approx(36.00, abs=1e-6)
    (rec,) = r["recesses"]
    assert rec["kind"] == "RECESS" and rec["state"] == "CLOSED"
    assert rec["chord_m"] == pytest.approx(1.50, abs=1e-6)
    assert rec["depth_m"] == pytest.approx(0.20, abs=1e-6)
    assert rec["saved_m"] == pytest.approx(0.40, abs=1e-6)
    assert rec["glazing_cover"] == pytest.approx(1.0)
    (op,) = r["undetected_openings"]
    assert op["width_m"] == pytest.approx(1.50, abs=1e-6) and op["beside_column"] is False


@pytest.mark.parametrize("rot,mirror,start,reverse", [
    (0, False, 3, False), (0, False, 0, True), (30, False, 0, False), (30, True, 5, True),
    (-121, True, 2, False), (90, False, 7, True)])
def test_a_variants(rot, mirror, start, reverse):
    pts = xf(PLAN_A, rot, mirror, dx=1234.5, dy=-987.25)
    ring = ring_of(pts, GLAZED_A)
    ring = ring[start:] + ring[:start]
    if reverse:
        ring = [dict(e, a=e["b"], b=e["a"]) for e in reversed(ring)]
    r = G.recess_closures(ring)
    assert r["state"] == "RESOLVED"
    assert r["walked_m"] == pytest.approx(36.40, abs=1e-6)
    assert r["closed_m"] == pytest.approx(36.00, abs=1e-6)
    assert len(r["undetected_openings"]) == 1


def test_a1_no_glazing_held():
    r = G.recess_closures(ring_of(PLAN_A, {}))
    assert r["state"] == "HELD_RANGE"
    assert r["range_m"] == pytest.approx([36.00, 36.40], abs=1e-6)
    assert r["recesses"][0]["why"].startswith("NO_GLAZING_EVIDENCE")
    assert r["undetected_openings"] == []


def test_a1_glazing_given_apart_closes():
    """the glazing is not on the ring but drawn inside the step (a window insert's frame line)"""
    r = G.recess_closures(ring_of(PLAN_A, {}), glazing=[[(4.0, 0.12), (5.5, 0.12)]])
    assert r["state"] == "RESOLVED" and r["closed_m"] == pytest.approx(36.00, abs=1e-6)


def test_a2_partly_glazed_held():
    pts = [(0, 0), (4, 0), (4, 0.2), (5.0, 0.2), (5.5, 0.2), (5.5, 0), (10, 0), (10, 8), (0, 8)]
    r = G.recess_closures(ring_of(pts, {2: "WINDOW"}))
    assert r["state"] == "HELD_RANGE"
    assert r["range_m"] == pytest.approx([36.00, 36.40], abs=1e-6)
    assert r["recesses"][0]["glazing_cover"] == pytest.approx(1.0 / 1.5, abs=1e-6)
    assert r["recesses"][0]["why"].startswith("PARTLY_GLAZED")


def test_a3_porch_deeper_than_wall_kept():
    pts = [(0, 0), (4, 0), (4, 1.5), (5.5, 1.5), (5.5, 0), (10, 0), (10, 8), (0, 8)]
    r = G.recess_closures(ring_of(pts, {2: "WINDOW"}))
    assert r["walked_m"] == pytest.approx(39.00, abs=1e-6)
    assert r["closed_m"] == pytest.approx(39.00, abs=1e-6)
    assert r["state"] == "RESOLVED" and r["range_m"] is None
    assert r["recesses"][0]["state"] == "KEPT" and r["recesses"][0]["why"].startswith("DEEPER_THAN_ITS_WALL")


def test_a4_thickness_unknown_held():
    r = G.recess_closures(ring_of(PLAN_A, GLAZED_A, t=None))
    assert r["state"] == "HELD_RANGE" and r["recesses"][0]["why"].startswith("WALL_THICKNESS_NOT_READ")


def test_a5_measured_opening_kept():
    r = G.recess_closures(ring_of(PLAN_A, {2: "WINDOW_THRESHOLD"}))
    assert r["recesses"][0]["state"] == "KEPT"
    assert r["closed_m"] == pytest.approx(36.40, abs=1e-6) and r["range_m"] is None


def test_a6_window_beside_column():
    r = G.recess_closures(ring_of(PLAN_A, {1: "WALL_CAP", 2: "WINDOW", 3: "COLUMN"}))
    assert r["state"] == "RESOLVED"
    assert r["undetected_openings"][0]["beside_column"] is True


def test_a7_two_steps():
    pts = [(0, 0), (4, 0), (4, 0.2), (5.5, 0.2), (5.5, 0), (10, 0), (10, 8), (3, 8), (3, 7.8), (2, 7.8), (2, 8),
           (0, 8)]
    r = G.recess_closures(ring_of(pts, {2: "WINDOW"}))
    assert r["walked_m"] == pytest.approx(36.80, abs=1e-6)
    assert r["state"] == "HELD_RANGE"
    assert r["range_m"] == pytest.approx([36.00, 36.40], abs=1e-6)
    assert sorted(x["state"] for x in r["recesses"]) == ["CLOSED", "HELD"]


def test_a_outward_bump_is_not_a_recess():
    """a pilaster standing out of the face (outside the building) is facade, never closed"""
    pts = [(0, 0), (4, 0), (4, -0.2), (5.5, -0.2), (5.5, 0), (10, 0), (10, 8), (0, 8)]
    r = G.recess_closures(ring_of(pts, {2: "WINDOW"}))
    assert r["state"] == "NO_RECESS" and r["closed_m"] == pytest.approx(36.40, abs=1e-6)


def test_a_curved_edge_is_never_a_face_line():
    ring = ring_of(PLAN_A, GLAZED_A)
    ring[0]["straight"] = False
    ring[0]["len_m"] = 4.2
    r = G.recess_closures(ring)
    assert r["recesses"] == [] or all(x["state"] != "CLOSED" for x in r["recesses"])
    assert r["walked_m"] == pytest.approx(36.60, abs=1e-6)


def test_empty_ring_is_no_outline_not_zero():
    r = G.recess_closures([])
    assert r["state"] == "NO_OUTLINE" and r["walked_m"] is None and r["closed_m"] is None


# ---------------------------------------------------------------------------------------- through the engine
def _arrangement(points, roles, scale=1.0):
    items = []
    for i, a in enumerate(points):
        b = points[(i + 1) % len(points)]
        items.append(TP.BoundaryItem("L%d" % i, "SEGMENT", (a[0] * scale, a[1] * scale, b[0] * scale, b[1] * scale),
                                     roles.get(i, "WALL")))
    return TP.build(items, 1e-6 * scale)


@pytest.mark.parametrize("scale,unit_m,rot,mirror", [(1.0, 1.0, 0, False), (1000.0, 0.001, 0, False),
                                                     (1000.0, 0.001, 30, True), (1.0, 1.0, 30, False)])
def test_engine_topology_m_and_mm(scale, unit_m, rot, mirror):
    pts = xf(PLAN_A, rot, mirror)
    arr = _arrangement(pts, GLAZED_A, scale)
    fac = V29.facade_outlines(arr, unit_m, 1.0)
    assert fac["state"] == "ONE_OUTLINE"
    assert fac["outlines"][0]["perimeter_m"] == pytest.approx(36.40, abs=1e-5)    # the engine walks the step
    k = next(k for k, f in enumerate(arr.faces) if f["area"] <= 0 and f["cycle"])
    wt = {"L%d" % i: T for i in range(len(pts)) if i != 2}
    ring = G.ring_from_arrangement(arr, k, unit_m, wt)
    r = G.recess_closures(ring)
    assert r["walked_m"] == pytest.approx(36.40, abs=1e-5)
    assert r["closed_m"] == pytest.approx(36.00, abs=1e-5)
    assert r["undetected_openings"][0]["width_m"] == pytest.approx(1.50, abs=1e-5)


# ---------------------------------------------------------------------------------------- plan B: corner notch
PLAN_B = [(0, 0), (4, 0), (4, 2.95), (4, 3.00), (4.08, 3.00), (4.08, 2.95), (4.58, 2.95), (4.58, 3.20), (0, 3.20)]
ROLES_B = {1: "WINDOW", 2: "WINDOW", 3: "WALL", 4: "COLUMN", 5: "COLUMN", 6: "COLUMN"}


@pytest.mark.parametrize("rot,mirror,reverse", [(0, False, False), (0, False, True), (30, True, False),
                                                (200, False, True)])
def test_b_corner_notch_kept(rot, mirror, reverse):
    ring = ring_of(xf(PLAN_B, rot, mirror), ROLES_B)
    if reverse:
        ring = [dict(e, a=e["b"], b=e["a"]) for e in reversed(ring)]
    r = G.recess_closures(ring)
    assert r["walked_m"] == pytest.approx(15.66, abs=1e-6)
    assert r["state"] == "RESOLVED" and r["range_m"] is None
    assert r["closed_m"] == pytest.approx(15.66, abs=1e-6)
    (n,) = r["recesses"]
    assert n["kind"] == "CORNER_NOTCH" and n["state"] == "KEPT"
    assert n["chord_m"] == pytest.approx(0.08, abs=1e-6) and n["saved_m"] == pytest.approx(0.10, abs=1e-6)


def test_b_frame_line_is_reported():
    r = G.recess_closures(ring_of(PLAN_B, ROLES_B), glazing=[[(3.88, 2.95), (4.00, 2.95)]])
    assert r["recesses"][0]["evidence"]["frame_line_continues_face"] is True
    assert r["recesses"][0]["state"] == "KEPT"


def test_b_glass_across_the_notch_held():
    r = G.recess_closures(ring_of(PLAN_B, ROLES_B), glazing=[[(4.00, 2.96), (4.08, 2.96)]])
    assert r["state"] == "HELD_RANGE"
    assert r["range_m"] == pytest.approx([15.56, 15.66], abs=1e-6)


# ---------------------------------------------------------------------------------------- plan C: glazed gaps
def band(gap=(4.0, 7.0), jamb=(True, True), length=10.0):
    lo, hi = gap
    segs = [((0, 0), (lo, 0)), ((hi, 0), (length, 0)), ((0, 0.2), (lo, 0.2)), ((hi, 0.2), (length, 0.2))]
    if jamb[0]:
        segs.append(((lo, 0), (lo, 0.2)))
    if jamb[1]:
        segs.append(((hi, 0), (hi, 0.2)))
    return segs


def tf(segs, rot=0.0, mirror=False):
    return [tuple(xf([a, b], rot, mirror)) for a, b in segs]


@pytest.mark.parametrize("rot,mirror", [(0, False), (30, False), (30, True), (-121, True)])
def test_c_glazed_gap_closed(rot, mirror):
    wins = [[(4, 0.08), (7, 0.08)], [(4, 0.12), (7, 0.12)]]
    res = G.glazed_gap_closures(tf(band(), rot, mirror), [xf(w, rot, mirror) for w in wins])
    closed = [g for g in res if g["state"] == "CLOSED_GLAZED"]
    assert len(closed) == 2                                   # the gap on each face
    for g in closed:
        assert g["width_m"] == pytest.approx(3.00, abs=1e-6)
        assert g["wall_t_m"] == pytest.approx(0.20, abs=1e-6)
        assert len(g["closure"]) == 2
        assert sum(math.dist(*c) for c in g["closure"]) == pytest.approx(6.00, abs=1e-6)


def test_c_no_glazing_held():
    res = G.glazed_gap_closures(band(), [])
    assert res and all(g["state"] == "HELD" and g["why"].startswith("NO_GLAZING_EVIDENCE") for g in res)
    assert all(g["closure"] == [] for g in res)


def test_c_partly_glazed_held():
    res = G.glazed_gap_closures(band(), [[(4, 0.1), (6, 0.1)]])
    assert all(g["state"] == "HELD" and g["glazing_cover"] == pytest.approx(2 / 3, abs=1e-6) for g in res)


def test_c_missing_jamb_held():
    res = G.glazed_gap_closures(band(jamb=(True, False)), [[(4, 0.1), (7, 0.1)]])
    assert res and all(g["why"].startswith("NO_JAMB_PAIR") for g in res)


def test_c_wide_gap_any_width_and_min_filter():
    segs = band(gap=(2.0, 7.2))
    wins = [[(2.0, 0.1), (7.2, 0.1)]]
    res = G.glazed_gap_closures(segs, wins)
    assert {g["state"] for g in res} == {"CLOSED_GLAZED"}
    assert all(g["width_m"] == pytest.approx(5.20, abs=1e-6) for g in res)
    assert G.glazed_gap_closures(segs, wins, min_gap_m=6.0) == []      # the filter reports less, closes nothing new


def test_c_glazing_leaving_the_band_held_here():
    wins = [[(4, 0.1), (5.5, 1.0), (7, 0.1)]]
    res = G.glazed_gap_closures(band(), wins)
    assert res and all(g["state"] == "HELD" and g["closure"] == [] for g in res)
    # on the outer face the glass goes past the band (1.00 m in); from the inner face it lies behind the face line
    assert any(g["why"].startswith("GLAZING_LEAVES_THE_WALL_BAND") for g in res)


def _arc(c, r, a0, a1, n=2000):
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * i / n), c[1] + r * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def test_c_glass_bay_chain():
    walls = [((-3, 0), (-2, 0)), ((2, 0), (3, 0))]
    arc = _arc((0, 0), 2.0, math.pi, 0.0)                      # from (-2, 0) through (0, -2) to (2, 0)
    res = G.glass_chain_closures(walls, [arc])
    (c,) = res["closed"]
    assert c["length_m"] == pytest.approx(2 * math.pi, abs=1e-5)
    assert len(c["lines"]) == 2000
    short = _arc((0, 0), 2.0, math.pi, 0.02)                   # stops 0.04 m short of the east wall
    res2 = G.glass_chain_closures(walls, [short])
    assert res2["closed"] == [] and res2["open"][0]["ends_on_wall"] == [True, False]


def test_c_glass_chain_in_two_pieces():
    walls = [((0, 0), (0, 1)), ((4, 0), (4, 1))]
    res = G.glass_chain_closures(walls, [[(0, 0.5), (2, 0.5)], [(2, 0.5), (4, 0.5)]])
    (c,) = res["closed"]
    assert c["length_m"] == pytest.approx(4.0, abs=1e-9) and c["pieces"] == [0, 1]
