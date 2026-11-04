"""T-510: BAND_GAP_CLASSES_V1 on a non-training hand fixture (villa M, drawn in mm, one 8.00 m x 0.20 m wall).

Hand calculation (villa M):
    wall faces y = 0 and y = 200; covers x 0 .. 1700, 2467 .. 5000, 5150 .. 8000 (both faces); jamb line at x 2467
    column 300 x 300 at x 1700 .. 2000 (y -50 .. 250) standing inside the gap 1700 .. 2467
      -> piece 2000 .. 2467 = 0.467 m, start COLUMN_FACE, end MASONRY_JAMB; glazing 2 x 0.467 = 0.934 m >= 0.5 x 0.467
      -> OPENING / WINDOW; the released band path (0.50 m minimum) has no opening there (reproduced)
      -> height 2.16 m (scheduled) -> deduction 0.467 x 2.16 = 1.008720 m2 per masonry area / per finished face
    crossing wall at x 5000 .. 5150 (faces running 2.000 m below the band and a 73 mm nib above)
      -> gap 0.150 m, both ends WALL_JUNCTION -> NOT_AN_OPENING
    wall gross 8.00 x 3.00 = 24.000 m2 -> net 24.000 - 1.008720 = 22.991280 m2
Adverse: the column drawn as 3 pieces (one 5 mm apart) is joined before any piece is measured (no 5 mm sliver);
rotation 37 / 211 deg, mirror, metre units read alike; 0.499 / 0.500 / 0.501 m windows are all OPENING / WINDOW
(only the released path's flag changes at 0.50); a staggered face break with no bounding element is HELD, never 0; a
missing height is HELD; units missing refuse; the robust geometry path gives the same records.
"""

import inspect
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import band_gap_classes_v1 as BG  # noqa: E402
from engine.source import lintel_measure as LM  # noqa: E402
from engine.source import robust_geometry as RG  # noqa: E402


def _xf(p, rot=0.0, mirror=False, scale=1.0):
    x, y = p
    if mirror:
        x = -x
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return ((x * c - y * s) * scale, (x * s + y * c) * scale)


def _box(x0, y0, x1, y1, rot, mirror, scale):
    pts = [_xf(p, rot, mirror, scale) for p in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    return pts


WALLS = [((0, 0), (1700, 0)), ((2467, 0), (5000, 0)), ((5150, 0), (8000, 0)),
         ((0, 200), (1700, 200)), ((2467, 200), (5000, 200)), ((5150, 200), (8000, 200)),
         ((0, 0), (0, 200)), ((8000, 0), (8000, 200)), ((2467, 0), (2467, 200)),
         # crossing wall at x 5000 .. 5150: 2.0 m below the band, a 73 mm nib above
         ((5000, 0), (5000, -2000)), ((5150, 0), (5150, -2000)), ((5000, 200), (5000, 273)),
         ((5150, 200), (5150, 273)), ((5000, 273), (5150, 273))]


def villa_m(rot=0.0, mirror=False, scale=1.0, column=((1700, 2000),), glazing=True):
    """scale: drawing units per mm (1.0 = mm, 0.001 = m). column: x ranges of the column pieces (y -50 .. 250)."""
    segs = [{"id": f"W{i}", "layer": "WALLS", "a": _xf(a, rot, mirror, scale), "b": _xf(b, rot, mirror, scale)}
            for i, (a, b) in enumerate(WALLS)]
    if glazing:
        segs += [{"id": f"G{i}", "layer": "GLZ", "a": _xf((2000, y), rot, mirror, scale),
                  "b": _xf((2467, y), rot, mirror, scale)} for i, y in enumerate((90, 110))]
    polys = [_box(x0, -50, x1, 250, rot, mirror, scale) for x0, x1 in column]
    return segs, 0.001 / scale, polys


def _bbox(p):
    xs, ys = [q[0] for q in p], [q[1] for q in p]
    return (min(xs), min(ys), max(xs), max(ys))


def _run(rot=0.0, mirror=False, scale=1.0, column=((1700, 2000),), heights=None, glazing=True, robust=False):
    """axis-aligned columns go in as boxes (the legacy path, or the robust one); rotated columns as polygons on the
    robust path (ARCH_TAKEOFF_V2.7.1 column_polys), as the candidate reads them"""
    segs, u, polys = villa_m(rot, mirror, scale, column, glazing)
    if rot % 90 == 0:
        return BG.classify(segs, u, ["WALLS"], [_bbox(p) for p in polys], window_layers={"GLZ"}, heights=heights,
                           geom=RG.Geometry(u) if robust else None)
    return BG.classify(segs, u, ["WALLS"], column_polys=polys, window_layers={"GLZ"}, heights=heights,
                       geom=RG.Geometry(u))


def _own(res):
    return [r for r in res["records"] if r["gap_id"]]


def _w(r):
    return round(r["width_m"], 6)


def test_released_minimum_is_the_one_replaced():
    assert inspect.signature(LM.openings).parameters["min_gap_m"].default == BG.ENGINE_MIN_GAP_M == 0.5
    assert inspect.signature(RG.openings).parameters["min_gap_m"].default == BG.ENGINE_MIN_GAP_M


def test_reproduction_released_path_loses_the_0467_window_beside_the_column():
    segs, u, polys = villa_m()
    ops, _ = LM.openings(segs, u, ["WALLS"], [_bbox(p) for p in polys], tol="UNIT_RELATIVE")
    assert ops == []


def test_normal_window_beside_split_column_kept_and_junction_refused():
    res = _run(heights={"SG-001": 2.16})
    own = _own(res)
    win = [r for r in own if r["cls"] == "OPENING"]
    assert len(win) == 1
    r = win[0]
    assert r["kind"] == "WINDOW" and r["status"] == "DEDUCT_MEASURED" and not r["engine_opening"]
    assert _w(r) == pytest.approx(0.467, abs=1e-6)
    assert (r["start_bound"], r["end_bound"]) == ("COLUMN_FACE", "MASONRY_JAMB") and r["split_at_column"]
    assert r["deduct_m2"] == pytest.approx(1.008720, abs=1e-6)
    assert r["evidence"]["glazing_m"] == pytest.approx(0.934, abs=1e-6)
    jn = [x for x in own if x["cls"] == "WALL_JUNCTION"]
    assert len(jn) == 1 and _w(jn[0]) == pytest.approx(0.150, abs=1e-6) and jn[0]["status"] == "NOT_AN_OPENING"
    assert (jn[0]["start_bound"], jn[0]["end_bound"]) == ("WALL_JUNCTION", "WALL_JUNCTION")
    assert res["summary"]["by_class"]["NO_BOUNDING_ELEMENT"] == 0
    assert res["summary"]["new_openings"] == 1
    net = BG.wall_deduction(24.0, res["records"])
    assert net == {"net_m2": 22.99128, "net_low_m2": 22.99128, "state": "MEASURED", "held": []}


def test_robust_path_gives_the_same_records():
    a = _run(heights={"SG-001": 2.16})
    b = _run(heights={"SG-001": 2.16}, robust=True)
    key = lambda res: [(r["cls"], r["kind"], _w(r), r["start_bound"], r["end_bound"], r["status"]) for r in _own(res)]
    assert key(a) == key(b)


@pytest.mark.parametrize("rot,mirror,scale", [(37.0, False, 1.0), (0.0, True, 1.0), (211.0, True, 0.001),
                                              (90.0, False, 0.001)])
def test_adverse_rotation_mirror_units_read_alike(rot, mirror, scale):
    # gap ids follow the band direction (a mirror reverses it): the window's id is read first, then its height given
    first = [r for r in _own(_run(rot, mirror, scale)) if r["cls"] == "OPENING"]
    res = _run(rot, mirror, scale, heights={first[0]["gap_id"]: 2.16})
    own = _own(res)
    win = [r for r in own if r["cls"] == "OPENING"]
    assert len(win) == 1 and win[0]["kind"] == "WINDOW"
    assert _w(win[0]) == pytest.approx(0.467, abs=1e-6)
    assert win[0]["deduct_m2"] == pytest.approx(1.008720, abs=1e-6)
    assert [x["cls"] for x in own if abs(x["width_m"] - 0.150) < 1e-6] == ["WALL_JUNCTION"]


def test_adverse_column_drawn_in_three_pieces_is_joined_before_measuring():
    # 1700 .. 1800 | 1800 .. 1900 (touching) | 1905 .. 2000 (5 mm apart): one physical column
    res = _run(column=((1700, 1800), (1800, 1900), (1905, 2000)), heights={"SG-001": 2.16})
    own = _own(res)
    assert not [r for r in own if r["width_m"] < 0.03 and r["cls"] != "COINCIDENT_FACES"]
    assert not [r for r in own if abs(r["width_m"] - 0.005) < 1e-6]          # no 5 mm sliver
    win = [r for r in own if r["cls"] == "OPENING"]
    assert len(win) == 1 and _w(win[0]) == pytest.approx(0.467, abs=1e-6)
    assert len(win[0]["column_pieces"]) == 3
    assert win[0]["deduct_m2"] == pytest.approx(1.008720, abs=1e-6)
    # rotated and mirrored the same
    res2 = _run(rot=211.0, mirror=True, column=((1700, 1800), (1800, 1900), (1905, 2000)))
    assert [_w(r) for r in _own(res2) if r["cls"] == "OPENING"] == [pytest.approx(0.467, abs=1e-6)]


def test_join_helper_hand_case():
    band = {"u": (1.0, 0.0), "n": (0.0, 1.0), "A": {"off": 0.0}, "B": {"off": 200.0}}
    g = {"s0": 1000.0, "s1": 3000.0, "start_jamb": "MASONRY_JAMB", "end_jamb": "MASONRY_JAMB"}
    obst = [("a", [(1500, -50), (1600, -50), (1600, 250), (1500, 250)]),
            ("b", [(1620, -50), (1700, -50), (1700, 250), (1620, 250)]),     # 20 mm from a: joined
            ("c", [(2000, -50), (2100, -50), (2100, 250), (2000, 250)])]     # 300 mm from b: separate column
    cols = BG.joined_columns(g, band, obst, 30.0)
    assert cols == [(1500, 1700, ["a", "b"]), (2000, 2100, ["c"])]
    ps = BG.pieces(g, band, obst, 30.0)
    assert [(p["s0"], p["s1"]) for p in ps] == [(1000, 1500), (1700, 2000), (2100, 3000)]


def _straight(gap_mm):
    g0, g1 = 2000, 2000 + gap_mm
    W = [((0, 0), (g0, 0)), ((g1, 0), (6000, 0)), ((0, 200), (g0, 200)), ((g1, 200), (6000, 200)),
         ((0, 0), (0, 200)), ((6000, 0), (6000, 200)), ((g0, 0), (g0, 200)), ((g1, 0), (g1, 200))]
    segs = [{"id": f"W{i}", "layer": "WALLS", "a": a, "b": b} for i, (a, b) in enumerate(W)]
    segs += [{"id": f"G{i}", "layer": "GLZ", "a": (g0, y), "b": (g1, y)} for i, y in enumerate((90, 110))]
    return segs


@pytest.mark.parametrize("gap_mm,engine", [(499, False), (500, True), (501, True)])
def test_boundary_0499_0500_0501_same_class(gap_mm, engine):
    res = BG.classify(_straight(gap_mm), 0.001, ["WALLS"], window_layers={"GLZ"})
    recs = [r for r in res["records"] if r["cls"] == "OPENING"]
    assert len(recs) == 1
    r = recs[0]
    assert r["kind"] == "WINDOW" and _w(r) == pytest.approx(gap_mm / 1000.0, abs=1e-9)
    assert r["engine_opening"] is engine
    assert r["status"] == ("ENGINE" if engine else "DEDUCT_HEIGHT_HELD")
    assert not r["differs_from_engine"]


def test_adverse_gap_with_no_bounding_element_is_held_never_zero():
    # face A breaks 3000 .. 3300, face B breaks 3100 .. 3400: no jamb line, no column -> the common break 3100 .. 3300
    W = [((0, 0), (3000, 0)), ((3300, 0), (6000, 0)), ((0, 200), (3100, 200)), ((3400, 200), (6000, 200)),
         ((0, 0), (0, 200)), ((6000, 0), (6000, 200))]
    segs = [{"id": f"W{i}", "layer": "WALLS", "a": a, "b": b} for i, (a, b) in enumerate(W)]
    res = BG.classify(segs, 0.001, ["WALLS"])
    own = _own(res)
    assert len(own) == 1
    r = own[0]
    assert r["cls"] == "NO_BOUNDING_ELEMENT" and r["status"] == "HELD" and r["deduct_m2"] is None
    assert _w(r) == pytest.approx(0.200, abs=1e-6)
    net = BG.wall_deduction(18.0, res["records"])
    assert net["state"] == "HELD" and net["net_low_m2"] is None and net["held"] == ["SG-001"]
    # the released path drops it without a record
    assert LM.openings(segs, 0.001, ["WALLS"], (), tol="UNIT_RELATIVE")[0] == []


def test_adverse_height_missing_held_and_units_missing_refused():
    res = _run()
    r = [x for x in _own(res) if x["cls"] == "OPENING"][0]
    assert r["status"] == "DEDUCT_HEIGHT_HELD" and r["deduct_m2"] is None and _w(r) == pytest.approx(0.467)
    net = BG.wall_deduction(24.0, res["records"])
    assert net["state"] == "HELD" and net["net_low_m2"] is None
    assert res["summary"]["deduct_height_held_width_m"] == pytest.approx(0.467, abs=1e-6)
    segs, _u, _p = villa_m()
    with pytest.raises(ValueError, match="UNITS_MISSING"):
        BG.classify(segs, None, ["WALLS"])


def test_bare_jambed_gap_without_symbol_is_an_unmarked_opening_with_area_held():
    segs = [s for s in _straight(300) if s["layer"] == "WALLS"]
    r = _own(BG.classify(segs, 0.001, ["WALLS"]))[0]
    assert (r["cls"], r["kind"], r["status"]) == ("OPENING", "UNMARKED", "DEDUCT_HEIGHT_HELD")
    assert _w(r) == pytest.approx(0.300, abs=1e-6)


def test_policy_record_unwired():
    p = BG.policy_record()
    assert p["policy"] == "BAND_GAP_CLASSES_V1" and p["wired"] is False and "R-T510-1" in p["rules"]


def test_agrees_with_the_checker_verified_t460_census_on_its_own_fixtures():
    """R-T460-1 classes map one to one: SMALL_WINDOW -> OPENING / WINDOW, WALL_JUNCTION -> WALL_JUNCTION,
    SUB_MIN_GAP_UNEXPLAINED (jambed, no symbol) -> OPENING / UNMARKED with the area HELD (same quantity effect)"""
    sys.path.insert(0, str(ROOT / "tests" / "t460_small_openings"))
    sys.path.insert(0, str(ROOT / "research" / "agents_t460"))
    import small_opening_census_v1 as SC
    import test_t460_small_openings as T460
    for kw in ({}, {"gap": (2000, 2300), "glazing": False}, {"rot": 211.0, "mirror": True, "scale": 0.001}):
        segs, u = T460.villa_k(**kw)
        old = [r for r in SC.census(segs, u, ["WALLS"], window_layers={"GLZ"})["records"] if r["probe_id"]]
        new = _own(BG.classify(segs, u, ["WALLS"], window_layers={"GLZ"}))
        mp = {"SMALL_WINDOW": ("OPENING", "WINDOW"), "SUB_MIN_GAP_UNEXPLAINED": ("OPENING", "UNMARKED"),
              "WALL_JUNCTION": ("WALL_JUNCTION", None)}
        assert sorted((round(r["width_m"], 6), mp[r["cls"]]) for r in old) == \
            sorted((_w(r), (r["cls"], r["kind"])) for r in new)
        assert all(r["deduct_m2"] is None for r in new)                   # no height given: never a number, never 0
