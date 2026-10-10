"""engine/source/shaft_geometry.py - synthetic known answers and independent shapely constructions (no project
data)."""

from __future__ import annotations

import random

import pytest

from engine.source import shaft_geometry as SG

shapely = pytest.importorskip("shapely")
from shapely.geometry import box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402


def _u(rects):
    return unary_union([box(*r) for r in rects])


# ------------------------------------------------------------------ shaft walls and corners
def test_rectangular_shaft_every_corner_once():
    s = SG.shaft([(0, 0, 1800, 1500)], 200)
    assert s["INSIDE_CLEAR_AREA"] == 1800 * 1500
    assert s["GROSS_OUTER_AREA"] == 2200 * 1900
    assert s["WALL_RING_AREA"] == 2200 * 1900 - 1800 * 1500
    # centreline x thickness is the ring exactly: the four corner squares are counted once, not twice or never
    assert s["CENTRELINE_PERIMETER"] * 200 == s["WALL_RING_AREA"]
    assert s["INSIDE_PERIMETER"] == 2 * (1800 + 1500) and s["OUTER_PERIMETER"] == 2 * (2200 + 1900)
    # a naive side-by-side sum of four full outer lengths counts each corner twice
    naive = 2 * (2200 + 1900) * 200
    assert naive - s["WALL_RING_AREA"] == 4 * 200 * 200


def test_irregular_shaft_against_shapely():
    rnd = random.Random(88)
    for _ in range(150):
        rects = []
        for _ in range(rnd.randint(1, 4)):
            x, y = rnd.randint(0, 3000), rnd.randint(0, 3000)
            rects.append((x, y, x + rnd.randint(300, 2500), y + rnd.randint(300, 2500)))
        t = rnd.choice([150, 200, 250, 300])
        s = SG.shaft(rects, t)
        inner = _u(rects)
        outer = inner.buffer(t, join_style=2, cap_style=3)    # mitred: exact for an orthogonal outline
        assert abs(s["INSIDE_CLEAR_AREA"] - inner.area) < 1e-6
        assert abs(s["GROSS_OUTER_AREA"] - outer.area) < 1e-6
        assert abs(s["WALL_RING_AREA"] - outer.difference(inner).area) < 1e-6
        assert abs(s["INSIDE_PERIMETER"] - inner.length) < 1e-6
        assert abs(s["OUTER_PERIMETER"] - outer.length) < 1e-6


def test_wall_pieces_close_and_match_shapely():
    rnd = random.Random(7)
    for _ in range(200):
        w, d, t = rnd.randint(1200, 3000), rnd.randint(1200, 3000), rnd.choice([150, 200, 250])
        inner = (0.0, 0.0, float(w), float(d))
        cols, used = [], []
        for cid, (cx, cy) in enumerate([(-t, -t), (w, -t), (-t, d), (w, d)]):
            if rnd.random() < 0.7:
                a, b = rnd.randint(t, 600), rnd.randint(t, 600)
                sx = -1 if cx < 0 else 1
                sy = -1 if cy < 0 else 1
                # a column in the corner, square to the wall, covering the full thickness of both walls it meets
                x0 = -t if sx < 0 else w + t - a
                y0 = -t if sy < 0 else d + t - b
                cols.append((f"C{cid}", (x0, y0, x0 + a, y0 + b)))
        res = SG.wall_pieces(inner, t, cols)
        ring = box(-t, -t, w + t, d + t).difference(box(*inner))
        members = _u([r for _, r in cols]) if cols else None
        net = ring.difference(members) if members is not None else ring
        assert abs(res["ring_area"] - ring.area) < 1e-6
        assert abs(res["net_footprint"] - net.area) < 1e-6
        assert abs(sum(res["member_overlap"].values()) - (ring.area - net.area)) < 1e-6
        # the pieces tile the net region with no overlap
        assert abs(_u([p["rect"] for p in res["pieces"]]).area - net.area) < 1e-6
        assert abs(sum(p["footprint"] for p in res["pieces"]) - net.area) < 1e-6


def test_corner_columns_two_band_member_deducted_once():
    # a corner column 200 x 500 occupies the south band (200 x 200) and the west band (200 x 300): once in total
    res = SG.wall_pieces((0, 0, 1800, 1800), 200, [("C", (-200, -200, 0, 300))])
    assert res["member_overlap"]["C"] == 200 * 500
    assert res["ring_area"] - res["net_footprint"] == 200 * 500
    w = [p for p in res["pieces"] if p["side"] == "W"]
    assert len(w) == 1 and w[0]["length"] == 1500
    s = [p for p in res["pieces"] if p["side"] == "S"]
    assert len(s) == 1 and s[0]["length"] == 2000 and s[0]["inner_face"] == 1800 and s[0]["outer_face"] == 2000


def test_member_outside_ring_counts_only_its_ring_part():
    # a column that stands proud of the outer face by 50 mm: only the part inside the ring is deducted
    res = SG.wall_pieces((0, 0, 1800, 1800), 200, [("C", (1800, -200, 2050, 800))])
    assert res["member_overlap"]["C"] == 200 * 1000


def test_unclean_cuts_refused():
    with pytest.raises(SG.ShaftGeometryError):        # covers half the wall thickness
        SG.wall_pieces((0, 0, 1800, 1800), 200, [("C", (-100, 500, 0, 900))])
    with pytest.raises(SG.ShaftGeometryError):        # two members on top of each other
        SG.wall_pieces((0, 0, 1800, 1800), 200, [("A", (-200, 500, 0, 900)), ("B", (-200, 800, 0, 1200))])
    with pytest.raises(SG.ShaftGeometryError):
        SG.shaft([(0, 0, 0, 100)], 200)
    with pytest.raises(SG.ShaftGeometryError):
        SG.offset([(0, 0, 1, 1)], 0)


# ------------------------------------------------------------------ openings in walls
def test_door_opening_split():
    res = SG.wall_pieces((0, 0, 1800, 1800), 200)
    o = SG.split_opening(res["pieces"], "S", 400, 1400)
    assert o["width_in_wall"] == 1000 and o["width_not_in_wall"] == 0
    s = sorted((p["from"], p["to"], p["inner_face"], p["outer_face"]) for p in o["pieces"] if p["side"] == "S")
    # the south band runs the full outer width: the left part keeps its corner on the outer face only
    assert s == [(-200, 400, 400, 600), (1400, 2000, 400, 600)]
    assert sum(p["footprint"] for p in o["pieces"]) == res["net_footprint"] - 1000 * 200
    assert SG.opening_volume(1000, 2100, 200) == pytest.approx(0.42)
    assert SG.opening_volume(1000, None, 200) is None


def test_opening_over_a_member_not_deducted_twice():
    res = SG.wall_pieces((0, 0, 1800, 1800), 200, [("C", (-200, -200, 300, 0))])
    o = SG.split_opening(res["pieces"], "S", 0, 900)
    assert o["width_in_wall"] == 600 and o["width_not_in_wall"] == 300


# ------------------------------------------------------------------ wall / foundation intersections, pit slabs
def test_walls_on_footing_and_off_it():
    res = SG.wall_pieces((0, 0, 1800, 1800), 200)
    on = SG.plan_overlap(res["pieces"], [(-1000, -1000, 2800, 2800)])
    assert on["on"] == res["net_footprint"] and on["off"] == 0
    half = SG.plan_overlap(res["pieces"], [(-1000, -1000, 900, 2800)])
    ring = box(-200, -200, 2000, 2000).difference(box(0, 0, 1800, 1800))
    assert abs(half["on"] - ring.intersection(box(-1000, -1000, 900, 2800)).area) < 1e-6
    assert abs(half["on"] + half["off"] - res["net_footprint"]) < 1e-6


def test_wall_starts_at_base_top_no_double_interface():
    # a base 600 thick from -2.10 to -1.50, walls from the base top to +1.00: the interface layer is counted once
    base = SG.region_area([(-200, -200, 2000, 2000)]) / 1e6 * 0.60
    walls = SG.wall_volume(SG.wall_pieces((0, 0, 1800, 1800), 200)["net_footprint"], -1.50, 1.00)
    solid = box(-200, -200, 2000, 2000).area / 1e6 * 0.60 + \
        box(-200, -200, 2000, 2000).difference(box(0, 0, 1800, 1800)).area / 1e6 * 2.50
    assert abs(base + walls - solid) < 1e-9
    # a wall measured from the base bottom would overlap the base by ring x thickness
    wrong = SG.wall_volume(SG.wall_pieces((0, 0, 1800, 1800), 200)["net_footprint"], -2.10, 1.00)
    assert abs((base + wrong) - solid - 1.60 * 0.60) < 1e-9


def test_pit_slab_and_missing_depth():
    p = SG.pit([(0, 0, 1800, 1800)])
    assert p["state"] == SG.NOT_ESTABLISHED and p["VOID_VOLUME"] is None and p["INSIDE_CLEAR_AREA"] == 3.24e6
    q = SG.pit([(0, 0, 1800, 1800)], depth=1200, floor_level=1.00)
    assert q["VOID_VOLUME"] == pytest.approx(3.888) and q["pit_bottom"] == pytest.approx(-0.20)
    with pytest.raises(SG.ShaftGeometryError):
        SG.pit([(0, 0, 1800, 1800)], depth=0)
    assert SG.wall_volume(1.1e6, None, 1.0) is None and SG.wall_volume(1.1e6, -1.5, None) is None


# ------------------------------------------------------------------ multiple storeys and tie beams
def test_multi_storey_segments_skip_owned_bands():
    # a shaft wall from -1.50 to +13.90 with 600 mm ring beams under each floor owned elsewhere
    segs = SG.vertical_segments(-1.50, 13.90, [(4.90, 5.50), (9.10, 9.70), (13.30, 13.90)])
    assert segs == [(-1.50, 4.90), (5.50, 9.10), (9.70, 13.30)]
    assert SG.vertical_segments(None, 13.90) is None
    assert SG.storey_heights([1.0, 5.5, 9.7]) == {(1.0, 5.5): 4.5, (5.5, 9.7): pytest.approx(4.2)}
    with pytest.raises(SG.ShaftGeometryError):
        SG.storey_heights([1.0, 1.0])


def test_tie_beam_trigger_measures():
    lv = [1.00, 5.50, 9.70, 13.90]
    ff = SG.tie_beam_trigger(lv, 4.30, 3.00, SG.FLOOR_TO_FLOOR)
    assert [r["state"] for r in ff] == [SG.TRIGGERED, SG.NOT_TRIGGERED, SG.NOT_TRIGGERED]
    assert ff[0]["elevation"] == pytest.approx(4.00) and ff[1]["elevation"] is None
    cl = SG.tie_beam_trigger(lv, 4.30, 3.00, SG.CLEAR_TO_SLAB_SOFFIT)
    assert all(r["state"] == SG.NOT_ESTABLISHED for r in cl)
    cl2 = SG.tie_beam_trigger(lv, 4.30, 3.00, SG.CLEAR_TO_SLAB_SOFFIT, slab=0.25, finish=0.0)
    assert [r["state"] for r in cl2] == [SG.NOT_TRIGGERED] * 3      # 4.25 is not above 4.30
    exact = SG.tie_beam_trigger([0.0, 4.30], 4.30, 3.00)
    assert exact[0]["state"] == SG.NOT_TRIGGERED                    # "exceeds" is strict


# ------------------------------------------------------------------ repeated representations and ownership
def test_repeated_floor_plan_views_are_one_shaft():
    items = [("A1", "FOUNDATION", (0, 0, 1800, 1800)), ("A2", "GROUND_BEAM", (0.0004, 0, 1800, 1800.0003)),
             ("A3", "GF_ROOF", (0, 0, 1800, 1800)), ("B1", "GROUND_BEAM", (5000, 0, 7000, 2000))]
    g = SG.group_representations(items, tol=1.0)
    assert [x["ids"] for x in g] == [["A1", "A2", "A3"], ["B1"]]
    with pytest.raises(SG.ShaftGeometryError):
        SG.group_representations([("A", "V", (0, 0, 1, 1)), ("B", "V", (0, 0, 1, 1))])


def test_ownership_states():
    assert SG.ownership_state(owner="S4", measured=True) == SG.ALREADY_OWNED_AND_MEASURED
    assert SG.ownership_state(owner="S4") == SG.OWNED_BUT_UNMEASURED        # an owner is not a quantity
    assert SG.ownership_state(blocked="depth") == SG.BLOCKED_UNQUANTIFIED
    assert SG.ownership_state(derived=True) == SG.NEW_SOURCE_DERIVED
    assert SG.ownership_state(project_basis=True) == SG.NEW_PROJECT_BASIS_QTO
    assert SG.ownership_state(owner="S6", measured=True, conflict="two sections") == SG.SOURCE_CONFLICT
    assert SG.ownership_state() == SG.BLOCKED_UNQUANTIFIED


# ------------------------------------------------------------------ bars
def test_rates():
    assert SG.rate_count(6, 1800) == 11            # ceil(10.8)
    assert SG.rate_count(6, 1000) == 6
    assert SG.rate_length(6, 1800, 2500) == pytest.approx(27.0)
    with pytest.raises(SG.ShaftGeometryError):
        SG.rate_count(0, 1000)
