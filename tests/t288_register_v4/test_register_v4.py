"""T-288: wall height pieces under a sunken slab panel (rule R-T288-1, research/agents_t288/register_v4.py) and the
blockwork register v4 of the development villa.

Fixture villa V (NOT Alsenan), storey 3.80 m, roof slab t 0.15 -> block under a normal slab 3.65 m; one sunken panel
drawn as a hatch over x 0 .. 4, y 0 .. 3 (m); drop d printed nowhere. Hand truth:
  V-W1 axis y 1.0, x 0.5 .. 3.5 (3.000 m), wholly under the panel -> sunken piece 3.000 m at 3.65 - d;
       net = 3.000 x 3.65 = 10.950 at d = 0 (upper bound) - 3.000 d.
  V-W2 axis y 1.5, x 2.0 .. 6.0 (census 4.000 m): under the panel x 2.0 .. 4.0 = 2.000 m; beam B1 (30 x 50) over
       x 4.0 .. 4.2 = 0.200 m at 3.80 - 0.50 = 3.30; slab beyond 1.800 m at 3.65 -> U = 2.000 x 3.65 + 0.200 x 3.30 +
       1.800 x 3.65 = 7.300 + 0.660 + 6.570 = 14.530 m2, drop term 2.000 d.
  V-W3 axis x 6.5, y 0 .. 3 under a NORMAL panel -> 3.000 x 3.65 = 10.950 m2, no drop term.
  V-W4 a face ON the panel edge (y 3.0, x 0 .. 4): not under the panel (20 mm shrink).
  An annotation island (a tag inside the hatch, x 1.8 .. 2.2, y 0.8 .. 1.2) does not split V-W1's piece: 3.000, not
  2.600; a hatch stopping 0.05 m short of a column face (nothing drawn in the gap) closes to the column: 0.05 m more.
Adverse: a register booking 3.65 (the normal soffit) on V-W2 refused; a plain net, a 0 and a wrong drop length refused;
  a drop term on V-W3 refused; pieces not closing the census refused; millimetres refused; mirror gives the same.
Alsenan (development villa): outputs reproduce; 7.9131 m on six GF walls, each AGREE with the own clip or its
  difference named; GF-W12 leaves the VERIFIED share; VERIFIED 297.847 m2 on 18 walls; 449.5934 -> 449.6007 -
  7.9131 d (residual 0); no coordinate in the committed clip.
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest
from shapely.geometry import LineString, Polygon, box
from shapely import affinity

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research/agents_t288"
sys.path.insert(0, str(HERE))
import register_v4 as R4  # noqa: E402

STOREY, T = 3.80, 0.15
PANEL = box(0, 0, 4, 3)


def w2_pieces(sunken_h=3.65):
    return [{"length_m": 2.000, "height_m": sunken_h, "sunken": True},
            {"length_m": 0.200, "height_m": 3.30, "sunken": False},
            {"length_m": 1.800, "height_m": 3.65, "sunken": False}]


# ---------- normal case ----------
def test_normal_panel_keeps_storey_minus_t():
    h, held = R4.piece_height(STOREY, T, sunken=False)
    assert h == pytest.approx(3.65) and held is None
    w = R4.wall_with_drop(3.000, [{"length_m": 3.0, "height_m": 3.65, "sunken": False}])
    assert w["state"] == "ESTABLISHED" and w["upper_m2"] == pytest.approx(10.950) and w["drop_length_m"] == 0
    present, L = R4.clip_length(LineString([(6.5, 0), (6.5, 3)]), PANEL)
    assert not present and L == 0.0
    assert R4.check_register_row({"wall_id": "V-W3", "state": "ESTABLISHED", "net_m2": 10.95}, 0.0)


def test_thinned_flush_soffit_only_when_drawn():
    assert R4.piece_height(STOREY, T, sunken=True, thinned_flush_soffit=True) == (pytest.approx(3.65), None)


# ---------- adverse: sunken pieces ----------
def test_sunken_piece_is_held_on_d_never_storey_minus_t():
    h, held = R4.piece_height(STOREY, T, sunken=True)
    assert h is None and "drop d" in held


def test_whole_and_partial_clip_exact_lengths():
    assert R4.clip_length(LineString([(0.5, 1.0), (3.5, 1.0)]), PANEL) == (True, pytest.approx(3.000))
    assert R4.clip_length(LineString([(2.0, 1.5), (6.0, 1.5)]), PANEL) == (True, pytest.approx(2.000))


def test_face_on_panel_edge_is_not_clipped():
    present, L = R4.clip_length(LineString([(0, 3.0), (4, 3.0)]), PANEL)
    assert not present and L == 0.0


def test_annotation_island_does_not_split_the_piece():
    tag = box(1.8, 0.8, 2.2, 1.2)
    hatch_with_hole = PANEL.difference(tag)
    axis = LineString([(0.5, 1.0), (3.5, 1.0)])
    assert axis.intersection(hatch_with_hole).length == pytest.approx(2.600)      # the naive clip splits it
    region = R4.panel_region(Polygon(hatch_with_hole.exterior), [tag])
    assert R4.clip_length(axis, region) == (True, pytest.approx(3.000))


def test_hatch_short_of_a_column_face_closes_to_the_member():
    hatch = box(0.05, 0, 4, 3)                     # stops 0.05 short of the column face x = 0
    gap = box(0, 0, 0.05, 3)                        # nothing drawn in it
    axis = LineString([(0.0, 2.0), (2.0, 2.0)])     # census from the column face
    assert R4.clip_length(axis, hatch)[1] == pytest.approx(1.950)
    assert R4.clip_length(axis, R4.panel_region(hatch, member_gaps=[gap]))[1] == pytest.approx(2.000)
    with pytest.raises(R4.SunkenError, match="REGION_SPLIT"):
        R4.panel_region(hatch, member_gaps=[box(-1, 0, -0.5, 3)])


def test_wall_with_drop_hand_truth():
    w = R4.wall_with_drop(4.000, w2_pieces())
    assert w["upper_m2"] == pytest.approx(14.530) and w["drop_length_m"] == pytest.approx(2.000)
    assert w["state"] == R4.HELD_ON_DROP and w["expression"].startswith("14.5300 - 2.0000 x d")
    w1 = R4.wall_with_drop(3.000, [{"length_m": 3.0, "height_m": 3.65, "sunken": True}])
    assert w1["upper_m2"] == pytest.approx(10.950) and w1["drop_length_m"] == pytest.approx(3.000)


def test_register_booking_normal_soffit_refused():
    with pytest.raises(R4.SunkenError, match="NORMAL_SOFFIT_BOOKED"):
        R4.check_register_row({"wall_id": "V-W2", "state": "ESTABLISHED", "net_m2": 14.53}, 2.000)


def test_plain_net_zero_and_wrong_length_refused():
    ok = {"wall_id": "V-W2", "state_v4": R4.HELD_ON_DROP, "net_m2_v4": "", "upper_m2_v4": "14.5300",
          "drop_length_m": "2.0000"}
    assert R4.check_register_row(ok, 2.000)
    with pytest.raises(R4.SunkenError, match="PLAIN_NET"):
        R4.check_register_row(dict(ok, net_m2_v4="14.5300"), 2.000)
    with pytest.raises(R4.SunkenError, match="HELD_AS_ZERO"):
        R4.check_register_row(dict(ok, upper_m2_v4="0"), 2.000)
    with pytest.raises(R4.SunkenError, match="DROP_LENGTH"):
        R4.check_register_row(dict(ok, drop_length_m="1.9500"), 2.000)
    with pytest.raises(R4.SunkenError, match="DROP_WITHOUT_PANEL"):
        R4.check_register_row({"wall_id": "V-W3", "state": "ESTABLISHED", "drop_length_m": "0.5"}, 0.0)


def test_pieces_must_close_and_units_are_metres():
    bad = w2_pieces()
    bad[2]["length_m"] = 1.750
    with pytest.raises(R4.SunkenError, match="NOT_CLOSED"):
        R4.wall_with_drop(4.000, bad)
    with pytest.raises(R4.SunkenError, match="BAD_UNITS"):
        R4.wall_with_drop(4000.0, w2_pieces())
    with pytest.raises(R4.SunkenError, match="BAD_LEVEL"):
        R4.piece_height(3800, 150, sunken=False)


def test_mirror_and_rotation_same_lengths():
    for geom in (lambda g: affinity.scale(g, -1, 1, origin=(0, 0)), lambda g: affinity.rotate(g, 37, origin=(0, 0))):
        p = geom(PANEL)
        assert R4.clip_length(geom(LineString([(2.0, 1.5), (6.0, 1.5)])), p)[1] == pytest.approx(2.000)
        assert not R4.clip_length(geom(LineString([(0, 3.0), (4, 3.0)])), p)[0]


# ---------- Alsenan (development villa) ----------
def rows(name):
    return list(csv.DictReader(open(HERE / name, encoding="utf-8")))


def test_alsenan_outputs_reproduce():
    r = subprocess.run([sys.executable, "-I", str(HERE / "build_t288.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_alsenan_sunken_pieces_and_totals():
    s = json.loads((HERE / "summary.json").read_text())
    assert s["sunken_pieces_m"] == pytest.approx(7.9131)
    assert s["held_on_drop_walls"] == ["GF-W12", "GF-W16", "GF-W20", "GF-W31", "GF-W32", "GF-W34"]
    A = s["basis_A"]
    assert A["v3_net_m2"] == pytest.approx(449.5934) and A["v4_at_d0_upper_bound_m2"] == pytest.approx(449.6007)
    assert A["drop_term_m"] == pytest.approx(7.9131) and s["residual_A_m2"] == 0 and s["residual_B_m2"] == 0
    assert A["determinate_net_m2"] + A["held_on_drop_upper_m2"] == pytest.approx(A["v4_at_d0_upper_bound_m2"])
    assert sum(A["by_class_determinate_m2"].values()) == pytest.approx(A["determinate_net_m2"])
    assert s["verified_net_m2"] == pytest.approx(297.847) and len(s["verified_walls"]) == 18
    assert "GF-W12" not in s["verified_walls"]


def test_alsenan_register_rows_obey_the_rule():
    pieces = rows("SUNKEN_PIECES_T288.csv")
    by = {}
    for p in pieces:
        by[p["wall_id"]] = by.get(p["wall_id"], 0) + float(p["piece_m"])
        assert p["height_v4"] == "4.34 - d" and p["agreement"]
    for r in rows("BLOCKWORK_WALL_REGISTER_V4.csv"):
        R4.check_register_row(r, by.get(r["wall_id"], 0.0))
        if r["state_v4"] == R4.HELD_ON_DROP:
            assert r["net_m2_v4"] == "" and float(r["upper_m2_v4"]) > 0 and "D-41" in r["held_items"]
            assert r["class_v4"] != "VERIFIED"
    gf16 = next(r for r in rows("BLOCKWORK_WALL_REGISTER_V4.csv") if r["wall_id"] == "GF-W16")
    assert gf16["expression_v4"].startswith("15.4360 - 2.9500 x d")
    gf01 = next(r for r in rows("BLOCKWORK_WALL_REGISTER_V4.csv") if r["wall_id"] == "GF-W01")
    assert gf01["net_m2_v4"] == "62.1640" and gf01["class_v4"] == "VERIFIED"


def test_alsenan_clip_has_no_coordinates():
    txt = (HERE / "CLIP_T288.json").read_text()
    d = json.loads(txt)
    assert d["frames"]["GF"]["columns_matched"] == 30 and d["frames"]["GF"]["max_residual_mm"] == 0
    nums = []

    def walk(x):
        if isinstance(x, dict):
            [walk(v) for v in x.values()]
        elif isinstance(x, list):
            [walk(v) for v in x]
        elif isinstance(x, (int, float)):
            nums.append(abs(x))
    walk(d)
    assert max(nums) < 100     # lengths, areas and counts only; a drawing coordinate would be thousands
    assert d["unclaimed"] == []
