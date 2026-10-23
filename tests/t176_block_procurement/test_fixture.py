"""T-176: block procurement on a NON-Alsenan hand fixture (villa T176-V) with adverse cases.

Villa T176-V (hand truth, m; black unit 0.39 x 0.19 + 10 mm joints = 0.40 x 0.20 module, Q-75 provisional rule):
  W1 4.00 x 2.00, t 0.20, no opening: 10 units a course x 10 courses = 100 units = 8.00 m2 x 12.5 (exact division).
     Mortar by the joints: bed 5 courses/m x 1 m x 0.010 x 0.20 = 0.0100 + head 12.5 x 0.19 x 0.010 x 0.20 = 0.00475
     -> 0.01475 m3/m2 -> 0.118 m3. Independent: wall 4 x 2 x 0.20 = 1.600 m3 - units 100 x 0.39 x 0.19 x 0.20 =
     1.482 m3 -> 0.118 m3. Edge tolerance (4 x 0.010 + 2 x 0.010) x 0.20 = 0.012 m3 (not added).
  W2 5.00 x 3.00, t 0.15, door 0.90 x 2.10: net 15.00 - 1.89 = 13.11 m2 -> 163.875 installed units; mortar 13.11 x
     0.0110625 = 0.14502938 m3; course grid ceil(5 / 0.4) 13 x ceil(3 / 0.2) 15 = 195 - door modules 2 x 10 = 175
     (no offcut reuse) -> implied cutting 175 / 163.875 - 1 = 6.79 %.
  White on 8.00 m2, t 0.20: 62.5 x 25 -> 51.2; 60 x 20 (t 0.15) -> 66.667; 62.5 x 25 with a 2 mm thin bed -> 8 /
     (0.627 x 0.252) = 50.632.
  W1 cement and sand at mix 1:4 (test parameter), mortar waste 0.10: 0.118 x 1.10 = 0.1298; dry x 1.33 = 0.172634;
     cement 0.172634 / 5 x 1440 = 49.7186 kg = 0.99437 bags; sand 0.172634 x 4 / 5 = 0.1381072 m3.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t176"))

import block_procurement_v1 as B                                           # noqa: E402

DC, AOA, HELD = B.DC, B.AOA, B.HELD
SRC = "test fixture parameter (T176-V)"


def test_exact_division_units_and_grid_agree():
    u = B.installed_units(8.00, "BLACK_40x20", 0.20, DC)
    assert u["units"] == pytest.approx(100.0) and u["per_m2"] == pytest.approx(12.5)
    assert u["status"] == AOA                       # provisional owner rule caps a drawing-confirmed area
    assert B.grid_units(4.00, 2.00, "BLACK_40x20") == 100


def test_mortar_joint_sum_equals_wall_minus_units_volume():
    m = B.mortar_per_m2("BLACK_40x20", 0.20)
    assert m["bed_m3"] == pytest.approx(0.0100) and m["head_m3"] == pytest.approx(0.00475)
    assert m["m3_per_m2"] == pytest.approx(0.01475) and m["identity_m3"] == pytest.approx(0.01475)
    mo = B.mortar(8.00, DC, "BLACK_40x20", 0.20, B.params())
    direct = 4 * 2 * 0.20 - 100 * 0.39 * 0.19 * 0.20
    assert mo["wet_m3"] == pytest.approx(0.118) == pytest.approx(direct)
    assert mo["wet_status"] == AOA
    assert B.edge_tolerance_m3(4.00, 2.00, "BLACK_40x20", 0.20) == pytest.approx(0.012)


def test_mortar_15_vs_20_cm():
    m15 = B.mortar_per_m2("BLACK_40x20", 0.15)["m3_per_m2"]
    m20 = B.mortar_per_m2("BLACK_40x20", 0.20)["m3_per_m2"]
    assert m15 == pytest.approx(0.0110625) and m20 == pytest.approx(0.01475)
    assert m15 / m20 == pytest.approx(0.75)
    # units per m2 do not change with thickness (same face module)
    assert B.units_per_m2("BLACK_40x20") == pytest.approx(12.5)


def _laid_mortar_area(L, H, fw=0.39, fh=0.19, j=0.010, b=0.010):
    """Independent course-by-course lay-out: a bed joint under every course, a head joint after every full unit, the
    last piece of a course and the top course cut to fit (no closing joint). Returns the joint area (m2 of face)."""
    piece_len, x = 0.0, 0.0
    while x + fw <= L + 1e-12:
        piece_len += fw
        x += fw
        if x + j <= L + 1e-12:
            x += j
    piece_len += max(0.0, L - x)
    piece_h, y = 0.0, 0.0
    while y < H - 1e-12:
        y += b
        h = min(fh, H - y)
        piece_h += max(0.0, h)
        y += max(0.0, h)
    return L * H - piece_len * piece_h


def test_identity_vs_laid_out_wall_within_the_edge_tolerance():
    for L, H, t in ((5.00, 3.00, 0.15), (4.00, 2.00, 0.20), (1.279, 4.265, 0.15), (6.125, 3.996, 0.15)):
        laid = _laid_mortar_area(L, H) * t
        ident = L * H * B.mortar_per_m2("BLACK_40x20", t)["m3_per_m2"]
        assert abs(laid - ident) <= B.edge_tolerance_m3(L, H, "BLACK_40x20", t) + 1e-12
    assert _laid_mortar_area(4.00, 2.00) * 0.20 == pytest.approx(0.118)


def test_wall_with_an_opening():
    u = B.installed_units(13.11, "BLACK_40x20", 0.15, AOA)
    assert u["units"] == pytest.approx(163.875)
    assert B.mortar(13.11, AOA, "BLACK_40x20", 0.15, B.params())["wet_m3"] == pytest.approx(0.14502938)
    g = B.grid_units(5.00, 3.00, "BLACK_40x20", [(0.90, 2.10)])
    assert g == 175 and g / u["units"] - 1 == pytest.approx(0.0679, abs=1e-4)


def test_white_62_5x25_vs_black_40x20_vs_white_60x20():
    assert B.installed_units(8.00, "WHITE_62.5x25", 0.20, DC)["units"] == pytest.approx(51.2)
    assert B.installed_units(8.00, "BLACK_40x20", 0.20, DC)["units"] == pytest.approx(100.0)
    assert B.installed_units(8.00, "WHITE_60x20", 0.15, DC)["units"] == pytest.approx(66.6667, abs=1e-4)
    thin = B.installed_units(8.00, "WHITE_62.5x25", 0.20, DC, joint_m=0.002)
    assert thin["units"] == pytest.approx(50.632, abs=1e-3) and thin["joint"] == "GIVEN"
    assert B.installed_units(8.00, "WHITE_62.5x25", 0.20, DC)["joint"] == "JOINT_FREE_UPPER_BOUND"
    # thin-bed adhesive is not a joint volume: white mortar HELD, never a cement-sand figure
    assert B.mortar(8.00, DC, "WHITE_62.5x25", 0.20, B.params())["wet_m3"] is None


def test_waste_is_a_named_parameter_and_its_change_moves_the_order():
    inst = B.installed_units(13.11, "BLACK_40x20", 0.15, AOA)
    held = B.procurement_units(inst, B.params())
    assert held["units"] is None and held["status"] == HELD and "cutting_waste" in held["why"]
    p5 = B.params(cutting_waste=(0.05, SRC), breakage=(0.0, SRC))
    p8 = B.params(cutting_waste=(0.08, SRC), breakage=(0.0, SRC))
    assert B.procurement_units(inst, p5)["units"] == 173            # ceil(172.069)
    assert B.procurement_units(inst, p8)["units"] == 177            # ceil(176.985)
    assert B.procurement_units(inst, p5)["sources"]["cutting_waste"] == SRC
    exact = B.installed_units(8.00, "BLACK_40x20", 0.20, DC)
    assert B.procurement_units(exact, B.params(cutting_waste=(0.0, SRC), breakage=(0.0, SRC)))["units"] == 100


def test_cement_and_sand_only_with_a_named_mix():
    mo = B.mortar(8.00, DC, "BLACK_40x20", 0.20, B.params(mortar_waste=(0.10, SRC)))
    assert mo["ordered_m3"] == pytest.approx(0.1298) and mo["cement_bags"] is None and mo["cement_sand_status"] == HELD
    mo = B.mortar(8.00, DC, "BLACK_40x20", 0.20, B.params(mortar_waste=(0.10, SRC), mix=((1, 4), SRC)))
    assert mo["dry_m3"] == pytest.approx(0.172634)
    assert mo["cement_kg"] == pytest.approx(49.7186, abs=1e-4) and mo["cement_bags"] == pytest.approx(0.99437, abs=1e-5)
    assert mo["sand_m3"] == pytest.approx(0.1381072)
    assert mo["cement_sand_status"] == AOA


def test_white_pallets():
    pl = B.pallets(130, "WHITE_62.5x25", 0.20)
    assert pl == {"pallets": 3, "spare": 62, "per_pallet": 64}
    assert B.pallets(None, "WHITE_62.5x25", 0.20)["pallets"] is None


def test_mirror_and_rotation():
    # a mirrored wall has the same L and H: same count; courses run along L (0.40) and up H (0.20): not symmetric
    assert B.grid_units(1.00, 0.50, "BLACK_40x20") == 9
    assert B.grid_units(0.50, 1.00, "BLACK_40x20") == 10


# ---------------------------------------------------------------- adverse
def test_held_net_never_becomes_zero():
    u = B.installed_units(None, "BLACK_40x20", 0.20, HELD)
    assert u["units"] is None and u["status"] == HELD
    assert B.procurement_units(u, B.params(cutting_waste=(0.05, SRC), breakage=(0.0, SRC)))["units"] is None
    assert B.mortar(12.0, HELD, "BLACK_40x20", 0.20, B.params())["wet_m3"] is None


def test_thickness_not_made_is_held():
    u = B.installed_units(8.00, "BLACK_40x20", 0.10, DC)
    assert u["units"] is None and u["status"] == HELD and "not made" in u["why"]
    assert B.installed_units(8.00, "BLACK_40x20", 0.25, DC)["status"] == HELD     # a D-12 0.25 wall: no black product


def test_hardcoded_percent_and_unsourced_parameter_refused():
    with pytest.raises(ValueError):
        B.params(cutting_waste=(5, SRC))                       # 5 % typed as 5
    with pytest.raises(ValueError):
        B.params(cutting_waste=(0.05, ""))                     # no evidence source
    with pytest.raises(ValueError):
        B.params(cutting_waste=0.05)
    with pytest.raises(ValueError):
        B.params(unknown=(1, SRC))


def test_units_in_millimetres_refused():
    with pytest.raises(ValueError):
        B.installed_units(8.00, "BLACK_40x20", 200, DC)
    with pytest.raises(ValueError):
        B.grid_units(4000, 2000, "BLACK_40x20")
    with pytest.raises(ValueError):
        B.installed_units(8.00, "WHITE_62.5x25", 0.20, DC, joint_m=2)


def test_bad_status_and_bedding_refused():
    with pytest.raises(ValueError):
        B.installed_units(8.00, "BLACK_40x20", 0.20, "CALCULATED")
    with pytest.raises(ValueError):
        B.mortar_per_m2("BLACK_40x20", 0.20, bedding="HALF")


def test_face_shell_bedding_needs_the_shell_width():
    assert B.mortar_per_m2("BLACK_40x20", 0.20, bedding="FACE_SHELL")["status"] == HELD
    m = B.mortar_per_m2("BLACK_40x20", 0.20, bedding="FACE_SHELL", shell_width_m=0.03)
    assert m["m3_per_m2"] == pytest.approx((5 * 0.010 + 12.5 * 0.19 * 0.010) * 0.06)


def test_mix_must_be_positive_parts():
    with pytest.raises(ValueError):
        B.mortar(8.00, DC, "BLACK_40x20", 0.20, B.params(mortar_waste=(0.1, SRC), mix=((0, 4), SRC)))


def test_policy_unwired():
    assert B.policy_record()["wired"] is False
