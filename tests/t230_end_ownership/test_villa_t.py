"""T-230 END_OWNERSHIP_V1 on the hand fixture Villa T (not Alsenan). Hand truth, worked here:

S1 angled strap into a SHALLOWER footing: footing 2.00 x 2.00 (x, y 0 .. 2), H 0.40; strap B 0.40, D 0.50, axis at 30 deg
through (1, 1), drawn end cut square at (1, 1). Both strap edges cross the face x = 0 (y 0.42265 -/+ 0.23094), so the
plan area inside = B x axis run inside = 0.40 x 1 / cos 30 = 0.40 x 1.154701 = 0.461880 m2; no column in the strip.
At e = 0 (strap soffit = footing soffit): footing owns 0.461880 x 0.40 = 0.184752 m3; strap excess 0.461880 x 0.10 =
0.046188 m3; neck 0.

S2 square strap with the neck in its end: footing 2.00 x 2.00, H 0.30; strap B 0.50, D 0.40 along x at y = 1, drawn to
x = 1.20; neck 0.40 x 0.40 at (1, 1). Strip inside: 1.20 x 0.50 = 0.600 m2; neck in it: 0.40 x 0.40 = 0.160; A_net 0.440.
e = 0: footing 0.440 x 0.30 = 0.1320; excess 0.440 x 0.10 = 0.0440; neck 0.160 x 0.10 = 0.0160 (the neck is billed from
the footing top up, so it owns the strap above the footing top inside its footprint).

S3 one strap, two footings, one soffit level e: D 0.40; A: H 0.40, A_net 0.375; B: H 0.30, A_net 0.300.
excess(e) = 0.375 x (0.40 - ov_A) + 0.300 x (0.40 - ov_B). e = 0: 0 + 0.300 x 0.10 = 0.0300 (the minimum, unique).
Monolithic at both ends (-0.40 < e < 0.30): supremum (0.375 + 0.300) x 0.40 = 0.2700 (e -> -0.40); with the soffit not
below the footings (0 <= e < 0.30): 0.300 x 0.40 + 0.375 x 0.30 = 0.2325. The state 'strap above B and inside A'
(B 0.120, A 0) is no single level: it needs e >= 0.30 at B and e = 0 at A.

G1 ground beam 0.30 wide along x (y 0 .. 0.30), billed face to face from the DRAWN column face x = 0.40 (drawn 0.30 x
0.40); the printed neck 0.30 x 0.50 is drawn on the foundation plan at x 0 .. 0.50: DOUBLE 0.10 x 0.30 = 0.030 m2,
x D 0.60 = 0.0180 m3, owner NECK; the beam is 0.10 m shorter.
G2 band 0.30 wide at 45 deg, centred on the diagonal of a 0.40 x 0.40 column, leaving its corner (0.40, 0.40): the strip
edges leave the column at t = (0.80 - 0.15 sqrt2) / sqrt2 = 0.415685; the face line (furthest column point) is the
corner, t = 0.565685. Strip between them 0.30 x 0.15 = 0.045; column inside it = triangle base 0.30, height 0.15 =
0.0225; GAP (beam concrete in no line) = 0.0225 m2.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t230"))
import end_ownership as EO  # noqa: E402

FOOT = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]
C30, S30 = math.cos(math.radians(30)), math.sin(math.radians(30))


def s1_strip(rot=0.0, mirror=False, k=1.0):
    """S1 strap strip (far end outside the footing, drawn end at (1, 1)), optionally rotated / mirrored / scaled."""
    p1 = (1.0, 1.0)
    p0 = (1.0 - 4.0 * C30, 1.0 - 4.0 * S30)
    return [tf(p, rot, mirror, k) for p in EO.strip(p0, p1, 0.40)]


def tf(p, rot=0.0, mirror=False, k=1.0):
    x, y = p
    if mirror:
        x = -x
    c, s = math.cos(rot), math.sin(rot)
    return ((c * x - s * y) * k, (s * x + c * y) * k)


def foot(rot=0.0, mirror=False, k=1.0):
    return [tf(p, rot, mirror, k) for p in FOOT]


# ------------------------------------------------------------------------------------------- straps
def test_s1_angled_strap_area_by_hand():
    assert EO.overlap_area(s1_strip(), FOOT) == pytest.approx(0.40 / C30, abs=1e-9)   # 0.461880


@pytest.mark.parametrize("rot,mirror", [(0.0, False), (math.radians(90), False), (math.radians(217), True),
                                        (0.0, True)])
def test_s1_rotation_mirror_units(rot, mirror):
    a_m = EO.overlap_area(s1_strip(rot, mirror), foot(rot, mirror))
    a_mm = EO.overlap_area(s1_strip(rot, mirror, 1000.0), foot(rot, mirror, 1000.0)) / 1e6
    assert a_m == pytest.approx(0.461880, abs=1e-6)
    assert a_mm == pytest.approx(a_m, abs=1e-9)


def test_s1_shallower_footing_split():
    r = EO.strap_end(0.50, 0.40, 0.461880, 0.0, 0.0)
    assert r["footing_m3"] == pytest.approx(0.184752, abs=1e-6)
    assert r["strap_excess_m3"] == pytest.approx(0.046188, abs=1e-6)
    assert r["neck_m3"] == 0.0 and r["monolithic"]
    # every cubic metre of the strap solid inside the outline is owned exactly once
    assert r["footing_m3"] + r["strap_excess_m3"] == pytest.approx(0.461880 * 0.50, abs=1e-9)


def test_s2_neck_in_the_strap_end():
    strip = EO.strip((-3.0, 1.0), (1.2, 1.0), 0.50)
    gross = EO.overlap_area(strip, FOOT)
    col = EO.overlap_area(strip, [(0.8, 0.8), (1.2, 0.8), (1.2, 1.2), (0.8, 1.2)])
    assert gross == pytest.approx(0.600, abs=1e-9) and col == pytest.approx(0.160, abs=1e-9)
    r = EO.strap_end(0.40, 0.30, gross - col, col, 0.0)
    assert (r["footing_m3"], r["strap_excess_m3"], r["neck_m3"]) == pytest.approx((0.1320, 0.0440, 0.0160), abs=1e-9)


def test_s3_one_level_for_both_ends():
    ends = [{"end": "A", "H": 0.40, "A_net": 0.375, "A_col": 0.0}, {"end": "B", "H": 0.30, "A_net": 0.300, "A_col": 0.0}]
    r = EO.strap_level_range(0.40, ends)
    assert r["excess_at_e0_m3"] == pytest.approx(0.0300, abs=1e-9)
    assert r["excess_min_m3"] == pytest.approx(0.0300, abs=1e-9) and r["e_at_min_m"] == 0.0
    assert r["excess_sup_m3"] == pytest.approx(0.2700, abs=1e-9)
    assert EO.strap_level_range(0.40, ends, e_min=0.0)["excess_sup_m3"] == pytest.approx(0.2325, abs=1e-9)
    assert r["status"] == EO.HELD                      # a range is never released as a value


def test_s3_adverse_two_levels_for_one_strap_refused():
    """'Strap above footing B while inside footing A' is not a level state: no single e gives it."""
    for i in range(0, 71):
        e = -0.40 + i * 0.01
        a = EO.strap_end(0.40, 0.40, 0.375, 0.0, e)
        b = EO.strap_end(0.40, 0.30, 0.300, 0.0, e)
        assert not (a["strap_excess_m3"] < 1e-12 and b["strap_excess_m3"] == pytest.approx(0.120, abs=1e-12))


def test_adverse_overlap_counted_in_both_refused():
    led = EO.ledger_check([{"element": "STRAP S1", "owns": ["S1/F:in"]}, {"element": "FOOTING F", "owns": ["S1/F:in"]}])
    assert not led["ok"] and led["double"] == ["S1/F:in"]
    gap = EO.ledger_check([{"element": "STRAP S1", "nets": ["S1/F:in"]}, {"element": "FOOTING F", "nets": ["S1/F:in"]}])
    assert not gap["ok"] and gap["gap"] == ["S1/F:in"]
    ok = EO.ledger_check([{"element": "STRAP S1", "nets": ["S1/F:in"]}, {"element": "FOOTING F", "owns": ["S1/F:in"]}])
    assert ok["ok"]


def test_adverse_strap_cut_at_footing_centre_refused():
    # S2 axis face to face = 3.0 (x -3 .. 0); a centre-to-centre billing runs 1.0 m into the footing at D <= H
    r = EO.check_strap_billing(3.0, 4.0, 0.30, [0.30, 0.30])
    assert r["status"] == "REFUSED" and "DOUBLE" in r["reason"]
    r = EO.check_strap_billing(3.0, 2.6, 0.30, [0.30, 0.30])        # a projection gap
    assert r["status"] == "REFUSED" and "GAP" in r["reason"]
    assert EO.check_strap_billing(3.0, 3.0, 0.30, [0.30, 0.30])["status"] == "OK"


def test_missing_data_is_held_never_zero():
    r = EO.strap_end(0.40, None, 0.30, 0.0, 0.0)
    assert r["status"] == EO.HELD and "footing_m3" not in r
    r = EO.strap_level_range(0.40, [{"end": "A", "H": None, "A_net": 0.3}])
    assert r["status"] == EO.HELD and "excess_min_m3" not in r
    assert EO.gb_end((1.0, 0.0), 0.0, 0.30, 0.40, +1, [], [(0, 0), (0.4, 0), (0.4, 0.3), (0, 0.3)], [0.6])["status"] \
        == EO.HELD
    assert EO.vertical_separation(None, 0.60, -0.63) is None


# ------------------------------------------------------------------------------------------- ground beams
DRAWN = [(0.0, 0.0), (0.40, 0.0), (0.40, 0.30), (0.0, 0.30)]
PRINTED = [(0.0, 0.0), (0.50, 0.0), (0.50, 0.30), (0.0, 0.30)]


def test_g1_drafting_outline_double_owned_by_neck():
    r = EO.gb_end((1.0, 0.0), 0.0, 0.30, 0.40, +1, [PRINTED], DRAWN, [0.60], t_drawn_end=0.40)
    assert r["double_plan"] == pytest.approx((0.030, 0.030), abs=1e-9)
    assert r["double_m3"] == pytest.approx((0.0180, 0.0180), abs=1e-9)
    assert r["owner"] == "NECK" and r["status"] == EO.DRAWING_CONFIRMED
    assert r["gb_correction_m3"][1] == pytest.approx(-0.0180, abs=1e-9)
    # drawn = printed: nothing
    z = EO.gb_end((1.0, 0.0), 0.0, 0.30, 0.40, +1, [DRAWN], DRAWN, [0.60], t_drawn_end=0.40)
    assert z["double_plan"] == (0.0, 0.0) and z["gap_plan"] == (0.0, 0.0)


def test_g1_mirror_and_mm():
    # mirrored: the span runs to -x; along u = (-1, 0) the station t = -x, offsets n = -y
    r = EO.gb_end((-1.0, 0.0), -0.30, 0.0, 0.40, +1, [[(-x, y) for x, y in PRINTED]],
                  [(-x, y) for x, y in DRAWN], [0.60])
    assert r["double_plan"][0] == pytest.approx(0.030, abs=1e-9)
    mm = EO.gb_end((1.0, 0.0), 0.0, 300.0, 400.0, +1, [[(x * 1e3, y * 1e3) for x, y in PRINTED]],
                   [(x * 1e3, y * 1e3) for x, y in DRAWN], [0.60])
    assert mm["double_plan"][0] / 1e6 == pytest.approx(0.030, abs=1e-12)


def test_g1_conflict_is_a_range_never_its_larger_end():
    readings = [DRAWN] + EO.widened(DRAWN, 0, 0.10)
    r = EO.gb_end((1.0, 0.0), 0.0, 0.30, 0.40, +1, readings, DRAWN, [0.60], t_drawn_end=0.40)
    assert r["status"] == EO.CONFLICT
    assert r["double_plan"] == pytest.approx((0.0, 0.030), abs=1e-9)


def test_g2_oblique_end_leaves_a_gap_triangle():
    u = (math.sqrt(0.5), math.sqrt(0.5))
    col = [(0.0, 0.0), (0.40, 0.0), (0.40, 0.40), (0.0, 0.40)]
    tf_ = 0.40 * math.sqrt(2.0)
    t1 = (0.80 - 0.15 * math.sqrt(2.0)) / math.sqrt(2.0)
    assert t1 == pytest.approx(0.415685, abs=1e-6)
    r = EO.gb_end(u, -0.15, 0.15, tf_, +1, [col], col, [0.40], t_drawn_end=t1)
    assert r["gap_plan"][0] == pytest.approx(0.0225, abs=1e-9)
    assert r["double_plan"][0] == pytest.approx(0.0, abs=1e-9)
    assert r["gap_m3"][0] == pytest.approx(0.0090, abs=1e-9)


def test_free_end_support_is_the_drawn_wall_not_the_footing():
    cands = [{"id": "RING", "kind": "WALL", "t_face": 5.00, "separation_m": 0.0},
             {"id": "FTG", "kind": "FOOTING", "t_face": 6.00, "separation_m": 0.98}]
    r = EO.free_end_support(5.00, cands, tol=0.005)
    assert r["status"] == EO.DRAWING_CONFIRMED and r["support"] == "RING"
    assert r["refused"] and r["refused"][0][0] == "FTG"
    # adverse: only the footing outline at the drawn end -> refused, HELD (never the footing face)
    r = EO.free_end_support(6.00, cands[1:], tol=0.005)
    assert r["status"] == EO.HELD and r["refused"][0][0] == "FTG"
    # adverse: nothing at the drawn end
    assert EO.free_end_support(7.0, cands[:1], tol=0.005)["status"] == EO.HELD


def test_plan_overlap_is_not_an_intersection():
    # GB top +0.95, D 0.60 -> soffit +0.35; footing top -0.63: 0.98 m apart
    assert EO.vertical_separation(0.95, 0.60, -0.63) == pytest.approx(0.98, abs=1e-12)
    assert EO.vertical_overlap(0.35, 0.95, -1.33, -0.63) == 0.0
    # adverse: a beam actually resting in the footing depth does intersect
    assert EO.vertical_overlap(-0.90, -0.30, -1.33, -0.63) == pytest.approx(0.27, abs=1e-12)
