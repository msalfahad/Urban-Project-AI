"""T-436: ground-slab parts with no owner (stair-zone panel, area beyond the network, three small face reads).

Villa G436 (hand fixture, NOT Alsenan; t = 0.10 m):
  P1 stair-hall panel 4.00 x 3.00 = 12.000 m2, flight lines HIDDEN, no void / pit / stair base, floored -> SLAB 1.2000 m3
  P2 pit panel 2.00 x 2.50 = 5.000 m2 with a drawn pit ring -> NOT_SLAB
  P3 panel 3.00 x 2.00 with the flight lines CONTINUOUS (cut at the plan), no section -> HELD (never 0)
  S  45-degree band stub w 0.30 between two orthogonal band faces, short face 1.200 m:
     drawn strip w (Ls + w) = 0.30 x 1.50 = 0.4500 m2; a rectangle w Ls = 0.3600 m2 misses w^2 = 0.0900 m2 (two end
     triangles 0.045 each); long face drawn 0.050 short of the face it meets (< w): closed, square end beside it.
  Other side: one bare plate 100.00 m2 (to 0.01); drawn network 96.000 m2; printed area-table pieces 60.00 / 30.00 /
     7.50 / 4.00; constructions: network 96.00 (-4.00), 60+30+7.5 = 97.50 (-2.50), 60+30+7.5+4 = 101.50 (+1.50),
     60+30+4 = 94.00 ...: none within 0.005 -> UNRESOLVED; the nearest (a+b+c+d, +1.50) is listed, not taken.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t436"))
import t436_rules as R  # noqa: E402

T = 0.10


def panel(**kw):
    base = dict(area_m2=12.0, closed_by_bands=True, stair_linetypes=["HIDDEN"] * 9, void_or_pit_drawn=False,
                stair_base_drawn=False, section_replaces_slab=False, floored_above=True)
    base.update(kw)
    return R.stair_zone_panel(**base)


# ---------------------------------------------------------------- R-T436-1 stair on grade
def test_stair_panel_hidden_flight_is_slab():
    p = panel()
    assert p["class"] == "SLAB" and p["status"] == "DRAWING-CONFIRMED"
    assert round(p["area_m2"] * T, 6) == 1.2


def test_pit_panel_not_slab():
    assert panel(area_m2=5.0, void_or_pit_drawn=True)["class"] == "NOT_SLAB"


def test_stair_base_or_section_not_slab():
    assert panel(stair_base_drawn=True)["class"] == "NOT_SLAB"
    assert panel(section_replaces_slab=True)["class"] == "NOT_SLAB"


def test_continuous_flight_lines_held_not_zero():
    p = panel(area_m2=6.0, stair_linetypes=["CONTINUOUS"])
    assert p["class"] == "HELD" and p["area_m2"] == 6.0
    with pytest.raises(R.RefusedT436, match="never 0"):
        R.drop_whole(p)


def test_adverse_slab_panel_dropped_whole():
    with pytest.raises(R.RefusedT436, match="dropped whole"):
        R.drop_whole(panel())


def test_adverse_missing_area():
    with pytest.raises(R.RefusedT436):
        panel(area_m2=0)
    with pytest.raises(R.RefusedT436):
        panel(area_m2=None)


def test_not_closed_by_bands_held():
    assert panel(closed_by_bands=False)["class"] == "HELD"


# ---------------------------------------------------------------- R-T436-2 own partition closed on drawn faces
def _stub(ls, w):
    """45-degree band between a vertical face x = 0 and a horizontal face y = 0, short face from (0, ls/sqrt2) to
    (ls/sqrt2, 0); the strip lies away from the corner."""
    from shapely.geometry import Polygon
    a = ls / math.sqrt(2)
    off = w * math.sqrt(2)
    return Polygon([(0, a), (a, 0), (a + off, 0), (0, a + off)])


def test_stub_area_hand_formula():
    s = _stub(1.2, 0.30)
    assert abs(s.area - 0.30 * (1.2 + 0.30)) < 1e-9          # 0.4500
    assert abs(s.area - 0.30 * 1.2 - 0.09) < 1e-9            # rectangle misses w^2
    # Alsenan figures obey the same closed form (BAND0038: short face 0.789, w 0.300)
    assert abs(0.30 * (0.789 + 0.30) - 0.3267) < 1e-4


def test_band_end_closed_and_range():
    r = R.band_end_closure(gap_m=0.05, band_width_m=0.30, closed_m2=0.45, square_m2=0.44875)
    assert r["state"] == "CLOSED" and r["reading_m2"] == 0.45 and r["range_m2"] == [0.44875, 0.45]


def test_band_end_gap_wider_than_band_held():
    r = R.band_end_closure(gap_m=0.35, band_width_m=0.30, closed_m2=0.45, square_m2=0.40)
    assert r["state"] == "HELD" and r["range_m2"] == [0.4, 0.45]


def test_adverse_square_end_larger():
    with pytest.raises(R.RefusedT436):
        R.band_end_closure(gap_m=0.05, band_width_m=0.30, closed_m2=0.40, square_m2=0.45)


def test_adverse_strip_read_as_panel():
    with pytest.raises(R.RefusedT436, match="strip read as panel"):
        R.strip_merged([("177", "7CD", 0.300)], 0.30)
    assert R.strip_merged([("A", "B", 1.20)], 0.30)


def test_chords_do_not_node_a_face_ending_on_the_arc():
    """A band whose faces end exactly on a circle: a 48-chord polyline lies inside the circle, the face ends stop short
    of it (inside the sagitta) and polygonize merges the strip into the panel; with the ends carried onto the curve
    (noded) the 0.30 strip is its own face."""
    from shapely.geometry import LineString
    from shapely.ops import polygonize, unary_union
    r = 2000.0
    a0, a1 = 180 - math.degrees(math.asin(1700 / r)), 180 + math.degrees(math.asin(1700 / r))
    arc = LineString([(r * math.cos(math.radians(a0 + (a1 - a0) * i / 48)), r * math.sin(math.radians(a0 + (a1 - a0) * i / 48)))
                      for i in range(49)])
    p0, p1 = arc.coords[0], arc.coords[-1]
    frame = [LineString([(-4000, p1[1]), (-4000, p0[1])]), LineString([(-4000, p0[1]), p0]),
             LineString([(-4000, p1[1]), p1])]
    y1, y2 = -1650.0 + 1000, -1350.0 + 1000                     # band faces 300 apart, ending on the true circle
    x1, x2 = -math.sqrt(r * r - y1 * y1), -math.sqrt(r * r - y2 * y2)
    coarse = list(polygonize(unary_union(frame + [arc, LineString([(-4000, y1), (x1, y1)]),
                                                  LineString([(-4000, y2), (x2, y2)])])))
    fine = list(polygonize(unary_union(frame + [arc, LineString([(-4000, y1), (x1 + 3, y1)]),
                                                LineString([(-4000, y2), (x2 + 3, y2)])])))
    assert len(coarse) == 1 and len(fine) == 3
    strip = sorted(fine, key=lambda f: f.area)[0]
    assert abs((strip.bounds[3] - strip.bounds[1]) - 300.0) < 1e-6
    with pytest.raises(R.RefusedT436):
        R.strip_merged([("y1", "y2", (y2 - y1) / 1000)], 0.30)


# ---------------------------------------------------------------- R-T436-3 bare area
PIECES = {"a": 60.0, "b": 30.0, "c": 7.5, "d": 4.0}


def _rows(other=100.0, extra=None):
    cons = {"drawn network": 96.0, **{"+".join(k): v for k, v in R.subset_sums(PIECES).items()}}
    cons.update(extra or {})
    return R.bare_area_tests(other, cons, precision_m2=0.01)


def test_bare_area_no_reproduction_unresolved_nearest_listed():
    rows = _rows()
    assert not any(x["reproduces"] for x in rows)
    c = R.beyond_cause(rows)
    assert c["class"] == "UNRESOLVED" and c["nearest"] == "a+b+c+d" and c["nearest_misfit_m2"] == 1.5


def test_adverse_beyond_drawn_edge_without_drawn_line():
    rows = _rows(other=97.5)                                     # a+b+c reproduces exactly
    with pytest.raises(R.RefusedT436, match="without a drawn line"):
        R.beyond_cause(rows)
    assert R.beyond_cause(rows, drawn_line="layer-1 face 9A")["class"] == "TRACED"


def test_two_reproductions_none_chosen():
    rows = _rows(other=97.5, extra={"other outline": 97.5})
    c = R.beyond_cause(rows, drawn_line="x")
    assert c["class"] == "UNRESOLVED" and len(c["candidates"]) == 2


def test_adverse_no_construction_or_missing():
    with pytest.raises(R.RefusedT436):
        R.bare_area_tests(100.0, {}, precision_m2=0.01)
    with pytest.raises(R.RefusedT436):
        R.bare_area_tests(None, {"n": 1.0}, precision_m2=0.01)
    with pytest.raises(R.RefusedT436):
        R.bare_area_tests(100.0, {"n": None}, precision_m2=0.01)


def test_units_mm2_not_m2():
    rows = R.bare_area_tests(100.0, {"network in mm2": 96.0e6}, precision_m2=0.01)
    assert not rows[0]["reproduces"]


# ---------------------------------------------------------------- R-T436-4 sub-trace bookkeeping (fixture)
def _split():
    return {"P-STAIR": [{"id": "s", "m3": -1.2, "verdict": "ENGINE_WRONG", "cause": "panel dropped", "correction_owner": "lane I"}],
            "P-FACES": [{"id": "f1", "m3": -0.045, "verdict": "ENGINE_RIGHT", "cause": "stub strip"},
                        {"id": "f2", "m3": 0.009, "verdict": "ENGINE_WRONG", "cause": "stub ends", "correction_owner": "lane I"},
                        {"id": "f3", "m3": -0.004, "verdict": "UNRESOLVED", "cause": "lift side"}]}


PARTS = {"P-STAIR": -1.2, "P-FACES": -0.040}


def test_split_re_adds():
    assert R.check_split(_split(), PARTS)
    assert R.totals(_split()) == {"TRACED": -1.236, "HELD": 0.0, "UNEXPLAINED": -0.004}


@pytest.mark.parametrize("mut,msg", [
    (lambda s: s["P-FACES"][0].update(m3=-0.05), "re-add"),
    (lambda s: s["P-STAIR"][0].pop("correction_owner"), "owner"),
    (lambda s: s["P-FACES"].append({"id": "s", "m3": 0.0, "verdict": "AGREE", "cause": "x"}), "two parts"),
    (lambda s: s["P-FACES"][2].update(verdict="MAYBE"), "unknown verdict"),
    (lambda s: s["P-FACES"][2].update(cause=" "), "cause"),
    (lambda s: s["P-FACES"].append({"id": "h", "m3": 0.0, "verdict": "HELD", "cause": "held"}), "never 0"),
])
def test_split_adverse(mut, msg):
    s = _split()
    mut(s)
    with pytest.raises(R.RefusedT436, match=msg):
        R.check_split(s, PARTS)


def test_disjoint():
    assert R.disjoint(["GS-STAIR-ZONE"], ["PL-WALLS"])
    with pytest.raises(R.RefusedT436):
        R.disjoint(["GS-FACES"], ["GS-FACES"])


# ---------------------------------------------------------------- Alsenan pins (committed summary, no private input)
SUM = json.loads((ROOT / "research" / "agents_t436" / "summary_t436.json").read_text(encoding="utf-8"))


def test_alsenan_check_reproduces():
    out = subprocess.run([sys.executable, "-I", str(ROOT / "research" / "agents_t436" / "t436_alsenan.py"), "--check"],
                         capture_output=True, text=True, check=True)
    assert "REPRODUCED" in out.stdout


def test_alsenan_parts_and_totals():
    assert SUM["t428_parts_m3"] == {"GS-STAIR-ZONE": -0.83723, "GS-BEYOND-NETWORK": -0.63864, "GS-FACES": -0.0847}
    R.check_split(SUM["subparts"], SUM["t428_parts_m3"])
    tot = R.totals(SUM["subparts"])
    assert abs(sum(tot.values()) - (-1.56057)) <= 2e-6


def test_alsenan_stair_panel():
    sz = SUM["stair_zone"]
    assert sz["class"]["class"] == "SLAB" and abs(sz["area_m2"] - 8.372326) < 1e-6
    assert {x["linetype"] for x in sz["layer2_inside"]} == {"HIDDEN"} and len(sz["layer2_inside"]) == 11
    assert all(x["column_outlines_inside"] for x in sz["foundation_plan_below"])        # column footings only


def test_alsenan_faces():
    f = SUM["faces"]
    assert abs(f["f18"]["strip_closed_to_face_m2"] + f["f18"]["panel_closed_m2"] - f["f18"]["own_m2"]) < 2e-6
    assert abs(f["engine_m2"]["49a7dae5"] - f["f18"]["panel_closed_m2"] - 0.09) < 1e-6
    assert f["f18"]["face_181_gap_to_band_face_m"] < f["f18"]["band_width_m"]
    c = f["court"]
    assert abs(c["pieces_true_arc_m2"][0] - f["engine_m2"]["d74f3fe2"]) < 1e-6
    assert abs(c["pieces_true_arc_m2"][1] - f["engine_m2"]["0caa2bd2"]) < 1e-6
    assert c["band_faces_end_on_arc158_mm"] == {"177": 0.0, "7CD": 0.0}


def test_alsenan_disjoint_from_t430_t437():
    t428 = json.loads((ROOT / "research" / "agents_t428" / "summary_t428.json").read_text(encoding="utf-8"))
    txt = json.dumps(t428)
    assert "GS-SLAB" in txt
    other_rows = {"GB-MAIN", "PL-WALLS", "BM-GF", "BM-1F", "BM-2F", "BW-BAND", "GB-BOUNDARY", "CL-1F"}  # T-430, T-437
    assert R.disjoint({"GS-SLAB"}, other_rows)
    ids = [sp["id"] for subs in SUM["subparts"].values() for sp in subs]
    assert len(ids) == len(set(ids))


def test_alsenan_no_freelancer_row_value():
    assert "other_area_m2" not in SUM and len(SUM["bare_area_misfits_m2"]) <= 8
