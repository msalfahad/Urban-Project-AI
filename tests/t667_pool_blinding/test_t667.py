"""T-667: pool blinding and pool steps (research/agents_t667, R-T667-1 .. 5). Hand villa "V667" (not the training villa):
normal and adverse cases worked by hand below, then the development-villa ledger rebuilt from committed, pinned files."""
from __future__ import annotations

import copy
import json
import math
import sys
from decimal import Decimal
from pathlib import Path

import pytest
from shapely import affinity
from shapely.geometry import Point, Polygon, box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t667"))
import t667_rules as R  # noqa: E402
import t667_alsenan as A  # noqa: E402

D = Decimal
WRAP = [("screed", "0.05", "V667 S-5 '5cm screed'"), ("membrane", "0.05", "V667 S-5 '5cm membrane'")]
T = R.dim("0.10", "V667 S-5 '10cm plain concrete'")
FLAT = {"kind": "flat", "basis": "V667 S-5 flat base drawn"}


def rect():
    return R.outline("rect", L=R.dim("6.00", "V667 A-1 pool 600"), W=R.dim("4.00", "V667 A-1 pool 400"))


# ---- normal: rectangle 6.00 x 4.00, flat, wrap 5 + 5 cm, t 0.10 ---------------------------------------------------
# grown = 24.00 + 20.00 x 0.10 + 4 x 0.10^2 = 26.04 m2 -> 2.604 m3
def test_rect_flat_hand():
    p = R.pool_blinding(rect(), T, WRAP, FLAT)
    assert p["core_m2"] == "24.000000" and p["apron_in_plot_m2"] == "2.040000"
    assert p["own_layer_in_plot_m2"] == "26.040000" and p["own_layer_in_plot_m3"] == "2.604000"
    assert p["status"] == "LOWER_ONLY" and "not dimensioned" in p["open_item"]


# printed projection 0.15 beyond the wrap: d = 0.25 -> 24 + 20 x 0.25 + 4 x 0.0625 = 29.25 m2 -> 2.925 m3
def test_rect_projection_printed():
    p = R.pool_blinding(rect(), T, WRAP, FLAT, projection=("0.15", "V667 S-5 '15' projection"))
    assert p["status"] == "VALUED_GEOMETRY" and p["own_layer_in_plot_m3"] == "2.925000"


# sloped floor along L: 2.00 flat + 2.40 at a 0.70 drop (true 2.50) + 1.60 flat -> 6.10 m; core 4.00 x 6.10 = 24.40
# + plan apron 2.04 = 26.44 m2 -> 2.644 m3
def test_rect_sloped_true_length():
    seg = [("2.00", "0", "V667 S-6"), ("2.40", "0.70", "V667 S-6"), ("1.60", "0", "V667 S-6")]
    p = R.pool_blinding(rect(), T, WRAP, {"kind": "sloped", "segments": seg})
    assert p["core_m2"] == "24.400000" and p["own_layer_in_plot_m3"] == "2.644000"


# adverse: the slope's drop not printed -> HELD (refused), never the plan area as a stand-in, never 0
@pytest.mark.parametrize("seg", [
    [("2.00", "0", "V667 S-6"), ("2.40", None, "V667 S-6"), ("1.60", "0", "V667 S-6")],
    [("2.00", "0", "V667 S-6"), ("2.40", "0.70", "depth AS PER ARCH"), ("1.60", "0", "V667 S-6")],
    [("2.00", "0", "V667 S-6"), ("2.40", "0.70", "V667 S-6")],                      # horizontals 4.40 != 6.00
])
def test_sloped_unprinted_or_open_section_held(seg):
    with pytest.raises(R.Refused):
        R.pool_blinding(rect(), T, WRAP, {"kind": "sloped", "segments": seg})


def test_floor_profile_unknown_held():
    with pytest.raises(R.Refused):
        R.pool_blinding(rect(), T, WRAP, {"kind": None})


# adverse: the pool plan overlaps a slab / footing blinding already counted -> counted once in plan (low end),
# own layer beside; overlap 1.20 m2: 26.04 - 1.20 = 24.84 m2 -> 2.484 m3
def test_overlap_counted_once():
    p = R.pool_blinding(rect(), T, WRAP, FLAT, counted_overlap_m2="1.20", counted_line="L-slab-blinding")
    assert p["plan_distinct_m3"] == "2.484000" and p["own_layer_in_plot_m3"] == "2.604000"
    with pytest.raises(R.Refused):
        R.pool_blinding(rect(), T, WRAP, FLAT, counted_overlap_m2="1.20")             # no counted line named
    with pytest.raises(R.Refused):
        R.pool_blinding(rect(), T, WRAP, FLAT, counted_overlap_m2="26.05", counted_line="L-x")  # more than the plan


# plot line: the 6.00 edge on the plot line: beyond (6.00 + 2 x 0.10) x 0.10 = 0.62; in plot 26.04 - 0.62 = 25.42
def test_edge_on_plot_line():
    p = R.pool_blinding(rect(), T, WRAP, FLAT, edges_on_plot=("L1",))
    assert p["beyond_plot_m2"] == "0.620000" and p["own_layer_in_plot_m2"] == "25.420000"
    with pytest.raises(R.Refused):
        R.pool_blinding(rect(), T, WRAP, FLAT, edges_on_plot=("arc",))


# D pool r 2.00, b 1.20, back on the plot line (a villa other than the training one):
# A = 2 x 2 x 1.2 + pi 4 / 2 = 11.083185; P = 4 + 2.4 + 2 pi = 12.683185
# grown 0.10 = A + 1.268319 + 2 x 0.01 + pi/2 x 0.01 = 12.387212; beyond (4.00 + 0.20) x 0.10 = 0.42 -> in plot 11.967212
def test_d_pool_hand():
    o = R.outline("D", r=R.dim("2.00", "V667 A-2 r 200"), b=R.dim("1.20", "V667 A-2 120"))
    p = R.pool_blinding(o, T, WRAP, FLAT, edges_on_plot=("back",))
    assert p["core_m2"] == "11.083185" and p["own_layer_in_plot_m2"] == "11.967212"
    assert p["own_layer_in_plot_m3"] == "1.196721" and p["beyond_plot_m3"] == "0.042000"


# the analytic growth equals a polygon offset (mitred) whatever the orientation: rotation 30 deg and mirror
@pytest.mark.parametrize("angle,mirror", [(0, False), (30, False), (30, True), (117, True)])
def test_rotation_mirror_invariant(angle, mirror):
    r, b, d = 2.0, 1.2, 0.10
    poly = box(-b, -r, 0.0, r).union(Point(-b, 0).buffer(r, quad_segs=4096).intersection(box(-b - r, -r, -b, r)))
    if mirror:
        poly = affinity.scale(poly, xfact=-1, origin=(0, 0))
    poly = affinity.rotate(poly, angle, origin=(0, 0))
    o = R.outline("D", r=R.dim("2.00", "V667 A-2"), b=R.dim("1.20", "V667 A-2"))
    assert abs(poly.buffer(d, join_style=2, mitre_limit=10).area - float(R.grown(o, D("0.10")))) < 2e-6
    assert abs(poly.area - float(o["A"])) < 2e-6


# units, missing data, refused bases
@pytest.mark.parametrize("val,src", [("1750mm", "V667"), ("1750", "V667 slip"), ("10cm", "V667"), (None, "V667"),
                                     ("0", "V667"), ("1.75", ""), ("1.75", "AS PER ARCH"), ("1.75", "typical value"),
                                     ("1.75", "freelancer row")])
def test_dimension_refusals(val, src):
    with pytest.raises(R.Refused):
        R.dim(val, src)


def test_no_wrap_no_apron():
    with pytest.raises(R.Refused):
        R.pool_blinding(rect(), T, [], FLAT)


def test_steps_only_when_drawn():
    s = R.steps_line([])
    assert s["status"] == "HELD_BLANK" and s["value"] is None and "no step drawn" in s["item"]
    with pytest.raises(R.Refused):
        R.steps_line([{"L": "2.00", "W": "0.30", "H": "0.38", "source": "freelancer row"}])
    with pytest.raises(R.Refused):
        R.steps_line([{"L": "2.00", "W": "0.30", "H": "0.38", "source": "AS PER ARCH"}])
    v = R.steps_line([{"L": "2.00", "W": "0.30", "H": "0.30", "source": "V667 A-3 step 200 x 30 x 30"}])
    assert v["status"] == "VALUED" and v["value"] == "0.180000"


# ---- development villa: rebuilt from committed, pinned files ------------------------------------------------------
def test_alsenan_rebuild_equals_committed():
    got = A.build()
    committed = json.loads(A.OUT.read_text())
    assert json.loads(json.dumps(got, ensure_ascii=False)) == committed


def test_alsenan_key_figures():
    got = A.build()
    p = got["piece"]
    assert (p["core_m2"], p["own_layer_in_plot_m2"], p["beyond_plot_m2"]) == ("10.935564", "11.851050", "0.370000")
    assert (p["plan_distinct_m3"], p["own_layer_in_plot_m3"], p["beyond_plot_m3"]) == ("0.915529", "1.185105", "0.037000")
    rows = {r["line_id"]: r for r in got["rows"]}
    assert rows[A.NEW_LINE]["status"] == "LOWER_ONLY" and rows[A.NEW_LINE]["low"] == "0.915529"
    assert rows[A.L_STEPS]["status"] == "HELD_BLANK" and rows[A.L_STEPS]["value"] is None
    assert got["totals"]["total_stateable"] is False and got["totals"]["lines"] == 2
    touched = {t["line_id"] for t in got["existing_blinding_lines"]}
    assert len(touched) == 7 and A.L_PITS in touched


def test_alsenan_edited_input_stops_build():
    inp = json.loads(A.INPUT.read_text())
    bad = copy.deepcopy(inp)
    bad["printed"]["outline"]["r"][0] = 1.80                          # no longer the drawn outline
    with pytest.raises(R.Refused):
        A.build(bad)
    bad = copy.deepcopy(inp)
    bad["geometry_read"]["frame_check_columns_inside_a_footing"] = [34, 35]
    with pytest.raises(R.Refused):
        A.build(bad)
    bad = copy.deepcopy(inp)
    bad["printed"]["wrap_layers"][0][2] = "AS PER ARCH"
    with pytest.raises(R.Refused):
        A.build(bad)
