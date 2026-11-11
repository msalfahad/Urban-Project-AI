"""T-721: one-sided floors / named blanks of held beams (R-T721-1 .. 3). Villa V721 is hand-made (not the development
villa): a skylight ring 0.25 wide, radii 1.50 / 1.75 m, in a 3.40 x 3.40 bay, whose referenced detail prints links T10,
top 2T20, side 2T12/25cm, bottom 2T16 and a depth 'AS PER ARCH'; a roof-edge strip 0.15 x 6.00 with no section; a beam
whose schedule says 0.30 wide and whose plan draws 0.25. The last tests rebuild the development-villa census from
committed files only (no drawing is opened)."""
from __future__ import annotations

import json
import math
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t721"))
import t721_rules as R  # noqa: E402
import t721_alsenan as A  # noqa: E402

V721_BARS = {"link_dia": "0.010", "top_dia": "0.020", "side_dia": "0.012", "side_levels": 1, "bottom_dia": "0.016"}


def _ring_in_bay(r_i, r_o, half, *, mirror=False, angle_deg=0.0, shift=(0.0, 0.0)):
    from shapely.affinity import rotate, scale, translate
    from shapely.geometry import Point, box
    ring = Point(0, 0).buffer(r_o, 4096).difference(Point(0, 0).buffer(r_i, 4096))
    g = ring.intersection(box(-half, -half, half, half))
    if mirror:
        g = scale(g, xfact=-1, origin=(0, 0))
    g = rotate(g, angle_deg, origin=(0, 0))
    return translate(g, *shift).area


# ------------------------------------------------------------------ normal (hand)
def test_bar_stack_depth_hand():
    # 2 x 0.010 + 0.020 + 0.012 + 0.016 = 0.068
    assert R.bar_stack_depth(**V721_BARS) == X("0.068")


def test_ring_floor_hand():
    # in-bay ring: annulus pi (1.75^2 - 1.50^2) = 2.552544 minus the four corner caps beyond the 1.70 faces
    a = _ring_in_bay(1.50, 1.75, 1.70)
    assert 2.30 < a < 2.5526
    f = R.bar_stack_floor(areas_m2=[str(round(a, 7))], depth=X("0.068"))
    assert f["at_least"] == R.BR.round_low(X(str(round(a, 7))) * X("0.068")) and f["at_most"] is None


def test_ring_area_invariant_under_mirror_rotation_shift():
    base = _ring_in_bay(1.50, 1.75, 1.70)
    for kw in ({"mirror": True}, {"angle_deg": 90}, {"angle_deg": 37.5, "shift": (1000.0, -250.0)}):
        assert math.isclose(_ring_in_bay(1.50, 1.75, 1.70, **kw), base, rel_tol=1e-9)


def test_floor_takes_least_plan_reading_and_floors_down():
    f = R.bar_stack_floor(areas_m2=["2.0000004", "1.9999996"], depth="0.068")
    assert f["area_min_m2"] == X("1.9999996") and f["at_least"] == X("0.135999")   # 0.13599997 floored


def test_projection_blank_hand():
    b = R.projection_blank(item="D-X roof-edge strip", area_m2="0.90")    # 0.15 x 6.00
    assert b["class"] == "BLANK_NAMED" and b["at_least"] is None and b["at_most"] is None
    assert b["m3_per_m_depth"] == "0.900000" and "ONE family" in b["guard"]


def test_disagreeing_sizes_smaller_reading_floor_hand():
    # schedule 0.30, drawn 0.25, depth 0.60 agreed, length 4.00 stopper to stopper
    r = R.disagreeing_sizes(length_m="4.00", readings=["0.30", "0.25"], other_m="0.60")
    assert r["at_least"] == X("0.600000") and r["at_most"] is None             # 4 x 0.25 x 0.60, never the 0.66 mean
    r2 = R.disagreeing_sizes(length_m="4.00", readings=["0.25", "0.30"], other_m="0.60", one_geometry_bounds=True)
    assert r2["at_most"] == X("0.720000")


def test_statement_classes():
    s = R.statement("L-1", "E-1", "AT_LEAST", at_least="0.1", item="D-X")
    assert s["class_after"] == "HELD" and s["measured_net"] is None and s["at_most_m3"] is None
    b = R.statement("L-2", "E-2", "BLANK_NAMED", item="D-Y")
    assert b["at_least_m3"] is None and b["at_most_m3"] is None


# ------------------------------------------------------------------ adverse
@pytest.mark.parametrize("kw", [
    {"shared_verticals": False},
    {"cover": "0.025"},                                  # cover supplied but not printed: a default value
    {"link_dia": None},                                  # missing diameter: HELD by name
    {"top_dia": 16},                                     # mm, not metres
    {"side_levels": 0},
    {"bottom_dia": 0},
])
def test_bar_stack_refusals(kw):
    with pytest.raises(R.Refused):
        R.bar_stack_depth(**{**V721_BARS, **kw})


def test_printed_cover_is_added_when_printed():
    assert R.bar_stack_depth(**V721_BARS, cover="0.025", cover_printed=True) == X("0.118")


@pytest.mark.parametrize("kw", [{"referenced": False}, {"net_of_slab": False}, {"net_of_framing": False},
                                {"areas_m2": []}, {"areas_m2": ["0"]}, {"areas_m2": ["2500"]}])
def test_ring_floor_refusals(kw):
    base = {"areas_m2": ["2.0"], "depth": "0.068"}
    with pytest.raises(R.Refused):
        R.bar_stack_floor(**{**base, **kw})


@pytest.mark.parametrize("kw", [{"section_prints_depth": True}, {"mark": "B4"}, {"bars": "2T12"},
                                {"material_printed": True}, {"item": ""}, {"area_m2": None}, {"area_m2": "0"}])
def test_projection_refusals(kw):
    with pytest.raises(R.Refused):
        R.projection_blank(**{**{"item": "D-X", "area_m2": "0.9"}, **kw})


@pytest.mark.parametrize("readings", [["0.30"], ["0.30", "0.25", "0.275"], ["0.30", "250"]])
def test_disagreeing_sizes_refusals(readings):
    with pytest.raises(R.Refused):
        R.disagreeing_sizes(length_m="4.0", readings=readings, other_m="0.60")


@pytest.mark.parametrize("cls,kw", [
    ("AT_LEAST", {"at_least": "0", "item": "D"}),                   # HELD as 0 refused
    ("AT_LEAST", {"at_least": None, "item": "D"}),
    ("AT_LEAST", {"at_least": "0.2", "at_most": "0.3", "item": "D"}),   # AT_LEAST carries no high
    ("BOUNDED", {"at_least": "0.3", "at_most": "0.2", "item": "D"}),
    ("BLANK_NAMED", {"at_least": "0.1", "item": "D"}),
    ("BLANK_NAMED", {"item": ""}),
    ("RANGE", {"item": "D"}),
])
def test_statement_refusals(cls, kw):
    with pytest.raises(R.Refused):
        R.statement("L-x", "E-x", cls, **kw)


# ------------------------------------------------------------------ development villa (committed files only)
def test_dev_villa_census_12_of_12():
    led = A.build()
    c = led["census"]
    assert c["lines"] == 12 and c["AT_LEAST"] == 1 and c["BLANK_NAMED"] == 11
    assert c["zero"] == 0 and c["ranges"] == 0
    assert len({r["line_id"] for r in led["rows"]}) == 12
    assert c["bounded_untouched"]["lines"] == 14


def test_dev_villa_ring_floor_by_hand():
    led = A.build()
    ring = [r for r in led["rows"] if r["line_id"] == A.RING_LINE][0]
    assert ring["depth_floor_m"] == "0.064"                       # 2 x 0.008 + 0.016 + 0.014 + 0.018
    assert X(ring["plan_area_used_m2"]) == X("1.7993")                 # least of 1.7993 (line) / 1.7994065 (own)
    assert ring["at_least_m3"] == "0.115155"                      # 0.1151552 floored
    assert ring["at_most_m3"] is None and "D-28" in ring["item"]


def test_dev_villa_projections_blank_with_plan_area():
    led = A.build()
    proj = [r for r in led["rows"] if r["bound"] == "BLANK_NAMED"]
    assert len(proj) == 11 and all(r["at_least_m3"] is None and r["at_most_m3"] is None for r in proj)
    assert sum(X(r["m3_per_m_depth"]) for r in proj) == X("6.947100")
    assert all("D-26" in r["item"] for r in proj)


def test_committed_outputs_match_build():
    led = A.build()
    on_disk = json.loads(A.OUT_JSON.read_text(encoding="utf-8"))
    assert on_disk == json.loads(json.dumps(led, ensure_ascii=False))
