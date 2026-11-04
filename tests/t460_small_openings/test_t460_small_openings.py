"""T-460 item C5: SMALL_OPENING_CENSUS_V1 on a non-training hand fixture (villa K, one 6.00 m x 0.20 m wall).

Hand calculation (villa K, drawn in mm): wall faces y = 0 and y = 200 from x = 0 to 6000;
    window gap x 2000 .. 2400 = 0.400 m between masonry jambs, glazing two lines 0.400 m each = 0.800 m >= 0.5 x 0.400
    door gap   x 4000 .. 5000 = 1.000 m (>= 0.50: an engine opening, unchanged)
    window height 1.20 m (scheduled) -> deduction 0.400 x 1.20 = 0.480 m2 per masonry area / per finished face
    wall gross 6.00 x 3.00 = 18.000 m2 -> net after the small window 18.000 - 0.480 = 17.520 m2 (door is the engine's)
Adverse: the engine's own band path loses the 0.40 m window (reproduction); rotation 37 deg, mirror and metre units
read alike; a height not scheduled keeps the deduction HELD (never 0); a cross junction is NOT an opening; a bare gap
with no symbol is HELD; units missing refuse.
"""

import inspect
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t460"))

import small_opening_census_v1 as SC  # noqa: E402
from engine.source import lintel_measure as LM  # noqa: E402


def _xf(p, rot=0.0, mirror=False, scale=1.0, at=(0.0, 0.0)):
    x, y = p
    if mirror:
        x = -x
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return ((x * c - y * s) * scale + at[0], (x * s + y * c) * scale + at[1])


def villa_k(rot=0.0, mirror=False, scale=1.0, gap=(2000, 2400), glazing=True, door=True):
    """scale: drawing units per mm (1.0 = mm drawing, 0.001 = m drawing)"""
    g0, g1 = gap
    walls = [((0, 0), (g0, 0)), ((g1, 0), (4000, 0)), ((5000, 0), (6000, 0)),
             ((0, 200), (g0, 200)), ((g1, 200), (4000, 200)), ((5000, 200), (6000, 200)),
             ((0, 0), (0, 200)), ((6000, 0), (6000, 200)),
             ((g0, 0), (g0, 200)), ((g1, 0), (g1, 200)), ((4000, 0), (4000, 200)), ((5000, 0), (5000, 200))]
    if not door:
        walls = [w for w in walls if w not in (((g1, 0), (4000, 0)), ((5000, 0), (6000, 0)), ((g1, 200), (4000, 200)),
                                               ((5000, 200), (6000, 200)), ((4000, 0), (4000, 200)),
                                               ((5000, 0), (5000, 200)))] + [((g1, 0), (6000, 0)), ((g1, 200), (6000, 200))]
    segs = [{"id": f"W{i}", "layer": "WALLS", "a": _xf(a, rot, mirror, scale), "b": _xf(b, rot, mirror, scale)}
            for i, (a, b) in enumerate(walls)]
    if glazing:
        segs += [{"id": f"G{i}", "layer": "GLZ", "a": _xf((g0, y), rot, mirror, scale), "b": _xf((g1, y), rot, mirror, scale)}
                 for i, y in enumerate((90, 110))]
    return segs, 0.001 / scale


def _small(res):
    return [r for r in res["records"] if r["probe_id"]]


def test_engine_minimum_is_the_one_reproduced():
    assert inspect.signature(LM.openings).parameters["min_gap_m"].default == SC.ENGINE_MIN_GAP_M == 0.5


def test_reproduction_engine_band_path_loses_the_040_window():
    segs, u = villa_k()
    ops, _ = LM.openings(segs, u, ["WALLS"], (), tol="UNIT_RELATIVE")
    widths = sorted(round(o["width_m"], 3) for o in ops)
    assert widths == [1.0]                      # the door only: the 0.400 m window has no opening record


def test_normal_window_detected_and_deducted():
    segs, u = villa_k()
    res = SC.census(segs, u, ["WALLS"], window_layers={"GLZ"}, heights={"SG-001": 1.20})
    sm = _small(res)
    assert len(sm) == 1
    r = sm[0]
    assert r["cls"] == "SMALL_WINDOW" and r["status"] == "DEDUCT_MEASURED"
    assert r["width_m"] == pytest.approx(0.400, abs=1e-6)
    assert r["deduct_m2"] == pytest.approx(0.480, abs=1e-6)
    assert r["evidence"]["glazing_m"] == pytest.approx(0.800, abs=1e-6)
    eng = [x for x in res["records"] if x["cls"] == "ENGINE_OPENING"]
    assert [round(x["width_m"], 3) for x in eng] == [1.0]
    assert res["summary"]["lost_by_engine"] == 1
    net = SC.wall_deduction(18.0, sm)
    assert net == {"net_m2": 17.52, "net_low_m2": 17.52, "state": "MEASURED"}
    assert SC.wall_deduction(18.0, sm, faces=1)["net_m2"] == pytest.approx(17.52)


@pytest.mark.parametrize("rot,mirror,scale", [(37.0, False, 1.0), (0.0, True, 1.0), (211.0, True, 0.001),
                                              (90.0, False, 0.001)])
def test_adverse_rotation_mirror_units_read_alike(rot, mirror, scale):
    segs, u = villa_k(rot=rot, mirror=mirror, scale=scale)
    res = SC.census(segs, u, ["WALLS"], window_layers={"GLZ"}, heights={"SG-001": 1.20})
    sm = _small(res)
    assert len(sm) == 1 and sm[0]["cls"] == "SMALL_WINDOW"
    assert sm[0]["width_m"] == pytest.approx(0.400, abs=1e-6)
    assert sm[0]["deduct_m2"] == pytest.approx(0.480, abs=1e-6)


def test_adverse_height_missing_is_held_never_zero():
    segs, u = villa_k()
    res = SC.census(segs, u, ["WALLS"], window_layers={"GLZ"})
    r = _small(res)[0]
    assert r["status"] == "DEDUCT_HEIGHT_HELD" and r["deduct_m2"] is None and r["width_m"] == pytest.approx(0.4)
    net = SC.wall_deduction(18.0, [r])
    assert net["state"] == "HELD" and net["net_low_m2"] is None and net["held"] == ["SG-001"]
    assert res["summary"]["deduct_width_height_held_m"] == pytest.approx(0.4)


def test_adverse_bare_gap_without_symbol_is_held():
    segs, u = villa_k(gap=(2000, 2300), glazing=False)
    r = _small(SC.census(segs, u, ["WALLS"], window_layers={"GLZ"}))[0]
    assert r["cls"] == "SUB_MIN_GAP_UNEXPLAINED" and r["status"] == "HELD" and r["deduct_m2"] is None
    assert r["width_m"] == pytest.approx(0.300, abs=1e-6)


def test_adverse_cross_junction_is_not_an_opening():
    # band along x (faces y 0 / 150) crossed at x 3000 .. 3150 by a wall along y (faces x 3000 / 3150), the crossing
    # wall running 2.0 m on one side and only a 73 mm nib on the other (a door beside it): continuous masonry
    W = [((0, 0), (3000, 0)), ((3150, 0), (6000, 0)), ((0, 150), (3000, 150)), ((3150, 150), (6000, 150)),
         ((0, 0), (0, 150)), ((6000, 0), (6000, 150)),
         ((3000, 0), (3000, -2000)), ((3150, 0), (3150, -2000)), ((3000, 150), (3000, 223)), ((3150, 150), (3150, 223)),
         ((3000, 223), (3150, 223))]
    for rot, mirror in ((0.0, False), (53.0, True)):
        segs = [{"id": f"W{i}", "layer": "WALLS", "a": _xf(a, rot, mirror), "b": _xf(b, rot, mirror)}
                for i, (a, b) in enumerate(W)]
        res = SC.census(segs, 0.001, ["WALLS"], window_layers=set())
        jn = [r for r in _small(res) if abs(r["width_m"] - 0.150) < 1e-6]
        assert jn and all(r["cls"] == "WALL_JUNCTION" and r["status"] == "NOT_AN_OPENING" for r in jn)
        assert res["summary"]["lost_by_engine"] == 0


def test_adverse_glazing_beats_junction_and_units_missing_refused():
    segs, u = villa_k()
    with pytest.raises(ValueError, match="UNITS_MISSING"):
        SC.census(segs, None, ["WALLS"])
    # glazing in the gap is a window even if the jamb faces were crossing walls: the first class that holds wins
    res = SC.census(segs, u, ["WALLS"], window_layers={"GLZ"})
    assert _small(res)[0]["cls"] == "SMALL_WINDOW"
