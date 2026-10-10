"""R8.11 §34: the wall-band / cap / passage architecture challenged by a second synthetic family (angled walls,
nested and mirrored block walls, dimension rectangles, wall cores, columns). P7757 is not used: TS01 does not run
without a resolved unit (UNIT_UNRESOLVED), and the band detector needs the unit-derived eps_r."""

from __future__ import annotations

import math

from engine.source import room_topology as RT, topology_closures as TC, wall_bands as WB
from tests.r8_8 import helpers as H

POL = TC.POLICY_ID
LAB = [H.text(5, "A", 300, 100), H.text(6, "B", 300, 700)]


def box(w=1000, h=800):
    return [H.seg(1, 0, 0, w, 0), H.seg(2, w, 0, w, h), H.seg(3, w, h, 0, h), H.seg(4, 0, h, 0, 0)]


def run(parts, texts=LAB):
    return RT.run(H.inp(parts, texts=texts), frame_insert=None, closure_policy=POL)


def est(r):
    return [b for b in r["wall_bands"]["bands"] if b["state"] == WB.ESTABLISHED]


def test_an_angled_wall_band_is_established_and_its_closure_uses_the_face_end_points():
    a = math.radians(30)
    ux, uy, nx, ny = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    x0, y0, L, w = 100.0, 100.0, 500.0, 20.0
    f1 = (x0, y0, x0 + L * ux, y0 + L * uy)
    f2 = (x0 + w * nx, y0 + w * ny, x0 + w * nx + L * ux, y0 + w * ny + L * uy)
    r = run(box() + [H.seg(10, *f1), H.seg(11, *f2), H.seg(12, f1[0], f1[1], f2[0], f2[1])])
    (b,) = est(r)
    assert abs(b["width"] - w) < 1e-6
    (c,) = [c for c in r["topology_closures"]["closures"]]
    g = c["geometry"]
    assert {(round(g[0], 6), round(g[1], 6)), (round(g[2], 6), round(g[3], 6))} == \
        {(round(f1[2], 6), round(f1[3], 6)), (round(f2[2], 6), round(f2[3], 6))}
    assert c["physical_material"] == "NONE"


def block(path, dx=0.0, mirror=False):
    """A whole floor-plan block (closed walls + a stub + two room labels: a BUILDING_ASSEMBLY occurrence)."""
    X = (lambda x: dx - x) if mirror else (lambda x: dx + x)
    segs = [(1, 0, 0, 1000, 0), (2, 1000, 0, 1000, 800), (3, 1000, 800, 0, 800), (4, 0, 800, 0, 0),
            (10, 0, 400, 600, 400), (11, 0, 420, 600, 420)]
    return ([H.seg(h, X(a), b, X(c), d, path=path) for h, a, b, c, d in segs],
            [H.text(5, "A", X(300), 100, path=path), H.text(6, "B", X(300), 700, path=path)])


def test_mirrored_block_occurrences_give_two_distinct_source_derived_bands():
    p1, t1 = block(("900",))
    p2, t2 = block(("901",), dx=3000, mirror=True)
    r = run(p1 + p2, t1 + t2)
    bands = est(r)
    assert len(bands) == 2 and len({b["band_id"] for b in bands}) == 2
    assert {b["face_a"].split("|")[2] for b in bands} == {"900", "901"}          # traceable to the occurrence
    r2 = run(p2 + p1, t2 + t1)
    assert sorted(b["band_id"] for b in est(r2)) == sorted(b["band_id"] for b in bands)


def test_walls_of_an_unadmitted_nested_block_form_no_band_fail_closed():
    """A band forms only from ADMITTED boundary: the role authority decides whether nested block walls are walls;
    the band model never promotes them."""
    p, t = block(("900", "901"))
    r = run(p, t)
    if not any(a.role == "TOPOLOGY_BOUNDARY" for a in r["roles"]["roles"].values()):
        assert r["wall_bands"]["bands"] == [] and r["topology_closures"]["closures"] == []
    else:                                                                     # admitted: the band must exist
        assert len(est(r)) == 1


def test_a_dimension_rectangle_is_never_a_wall_band():
    r = run(box() + H.box(30, 200, 380, 800, 420, layer="DIM"))
    assert est(r) == [] and r["topology_closures"]["closures"] == []


def test_a_closed_wall_core_has_capped_ends_and_needs_no_closure():
    core = [H.seg(10, 200, 400, 800, 400), H.seg(11, 200, 420, 800, 420), H.seg(12, 200, 400, 200, 420),
            H.seg(13, 800, 400, 800, 420)]
    r = run(box() + core)
    (b,) = est(r)
    assert [e["kind"] for e in b["ends"]] == [WB.CAPPED, WB.CAPPED]
    assert r["topology_closures"]["closures"] == []


def test_a_square_column_is_not_a_wall_band():
    r = run(box() + H.box(30, 480, 380, 520, 420))          # a 40 x 40 square on the WALL layer
    assert est(r) == []


def test_a_wall_band_beside_a_column_keeps_its_own_faces():
    walls = [H.seg(10, 0, 400, 600, 400), H.seg(11, 0, 420, 600, 420)]
    r = run(box() + walls + H.box(30, 700, 300, 740, 340))
    (b,) = est(r)
    assert {b["face_a"].split("|")[1], b["face_b"].split("|")[1]} == {"H10", "H11"}
