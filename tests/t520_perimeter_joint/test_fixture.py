"""T-520 (R-T520-1): perimeter joint mortar on a hand-calculated villa that is not the development villa (villa P520).

Villa P520, one storey, black blocks 0.20 m, module 0.40 x 0.20 with a 0.39 x 0.19 face, joint 10 mm (kappa = 0.92625,
factor f = kappa x b x j = 0.0018525 m3 per m of joint):
  wall A: column 0.30 | block 3.00 m under a beam (underside 3.00) | column 0.30 | block 2.00 m under the same beam
          | column 0.30: 3 columns, 2 course segments each between two concrete faces, one soffit 5.00 m.
          soffit 5.00 f = 0.0092625; vertical 2 x 3.00 f = 0.011115; top corners 2 x f x 0.010 = 0.00003705;
          perimeter = 0.02034045 m3 (on a panel 15 m2 x 0.01475 = 0.22125 m3: +9.19 %).
  wall B: 2.00 m between a block wall face and a free end, under a slab (underside 3.00): no concrete side face,
          soffit 2.00 f = 0.003705 m3.
Independent proof of 'no double count': the block count of a real lay-out, (L - j)(H - j) / 0.08 units in a panel
between two concrete faces under a soffit, gives the true joint volume; panel (R-T367-1) + perimeter equals it.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t520"))
import perimeter_joint_v1 as PJ  # noqa: E402

MOD = (0.39, 0.19, 0.40, 0.20)
F = 0.92625 * 0.20 * 0.010


def wall_a(**kw):
    ps = [PJ.Piece("COLUMN", 0.30, None, "C1"), PJ.Piece("BLOCK", 3.00, 3.00, "B-a"),
          PJ.Piece("COLUMN", 0.30, None, "C2"), PJ.Piece("BLOCK", 2.00, 3.00, "B-a"),
          PJ.Piece("COLUMN", 0.30, None, "C3")]
    args = dict(wall_id="P520-A", b=0.20, j=0.010, module=MOD, pieces=ps, end_start="O", end_end="O")
    args.update(kw)
    return PJ.Wall(**args)


def wall_b(**kw):
    args = dict(wall_id="P520-B", b=0.20, j=0.010, module=MOD, pieces=[PJ.Piece("BLOCK", 2.00, 3.00, "slab S1")],
                end_start="O", end_end="F")
    args.update(kw)
    return PJ.Wall(**args)


def true_joint(L, H, b=0.20, j=0.010, n_conc=2, soffit=True):
    """block count of a real lay-out: joints at every unit, both concrete ends, the soffit (independent of the module)."""
    units = (L - (n_conc - 1) * j) * (H - (j if soffit else 0.0)) / 0.08
    return L * H * b - units * 0.39 * 0.19 * b


def panel(L, H, b=0.20):
    return L * H * b * (1 - 0.0741 / 0.08)


def test_kappa_and_factor():
    assert PJ.kappa(MOD) == pytest.approx(0.92625, abs=1e-12)
    r = PJ.measure(wall_a())
    assert r["factor_m3_per_m"] == pytest.approx(0.0018525, abs=1e-12)


def test_wall_a_by_hand():
    r = PJ.measure(wall_a())
    assert r["soffit_m"] == pytest.approx(5.00)
    assert r["soffit_m3"] == pytest.approx(0.0092625, abs=1e-12)
    assert r["vertical_exact_m"] == pytest.approx(6.00, abs=1e-12)
    assert r["top_corners"] == 2
    assert r["m3"] == pytest.approx(0.02034045, abs=1e-11)
    assert r["status"] == "COMPUTED"


def test_wall_b_by_hand():
    r = PJ.measure(wall_b())
    assert r["m3"] == pytest.approx(0.003705, abs=1e-12)
    assert r["vertical_exact_m"] == 0.0 and r["range_block_end_m"] == 0.0


def test_no_double_count_with_panel_joints():
    for L in (3.00, 2.00, 4.37):
        w = wall_a(pieces=[PJ.Piece("COLUMN", 0.3, None, "C"), PJ.Piece("BLOCK", L, 3.00, "B"),
                           PJ.Piece("COLUMN", 0.3, None, "C")])
        assert panel(L, 3.0) + PJ.measure(w)["m3"] == pytest.approx(true_joint(L, 3.0), abs=1e-12)
    # one column face and a free end: the module's one head joint per course IS the column joint: soffit only
    w = PJ.Wall("P520-C", 0.20, 0.010, MOD, [PJ.Piece("COLUMN", 0.3, None, "C"), PJ.Piece("BLOCK", 2.5, 3.0, "B")],
                "O", "F")
    r = PJ.measure(w)
    assert r["vertical_exact_m"] == 0.0 and r["status"] == "COMPUTED"
    assert panel(2.5, 3.0) + r["m3"] == pytest.approx(true_joint(2.5, 3.0, n_conc=1), abs=1e-12)


def test_column_met_on_one_face_and_a_block_wall_is_a_range():
    w = PJ.Wall("P520-D", 0.20, 0.010, MOD, [PJ.Piece("BLOCK", 2.5, 3.0, "B"), PJ.Piece("COLUMN", 0.3, None, "C")],
                "O", "O")
    r = PJ.measure(w)
    assert r["vertical_exact_m"] == 0.0
    assert r["range_block_end_m"] == pytest.approx(3.0)
    assert r["status"] == "COMPUTED_WITH_RANGE"
    assert r["m3_low"] == pytest.approx(2.5 * F) and r["m3_high"] == pytest.approx(2.5 * F + 3.0 * F)


def test_checker_bound_is_an_upper_bound():
    r = PJ.measure(wall_a())
    bound = PJ.checker_bound(5.0, 3.0, 0.20, 0.010, 4)
    assert bound == pytest.approx(0.034, abs=1e-12)
    assert r["m3"] < bound


def test_beam_drop_side_is_a_concrete_face():
    # block under a slab (3.30) beside a beam drop (3.00) between two columns: the band 3.00 .. 3.30 ends on the beam
    # side and a column -> +0.30 exact
    w = wall_a(pieces=[PJ.Piece("COLUMN", 0.3, None, "C"), PJ.Piece("BLOCK", 1.0, 3.00, "beam"),
                       PJ.Piece("BLOCK", 2.0, 3.30, "slab"), PJ.Piece("COLUMN", 0.3, None, "C")])
    r = PJ.measure(w)
    assert r["vertical_exact_m"] == pytest.approx(3.30)
    assert r["soffit_m"] == pytest.approx(3.0)


def test_mirror_is_identical():
    a = PJ.measure(wall_a())
    w = wall_a()
    w.pieces = list(reversed(w.pieces))
    b = PJ.measure(w)
    assert a["m3"] == pytest.approx(b["m3"], abs=1e-15)


def test_unprinted_top_datum_is_held_never_zero():
    r = PJ.measure(wall_a(held="storey datum not printed"))
    assert r["status"] == "HELD" and r["m3"] is None


def test_held_piece_is_named_and_not_counted():
    w = wall_a(pieces=[PJ.Piece("COLUMN", 0.3, None, "C"), PJ.Piece("BLOCK", 3.0, 3.0, "B"),
                       PJ.Piece("BLOCK", 1.0, None, "dome", "top not drawn")])
    r = PJ.measure(w)
    assert r["status"] == "COMPUTED_WITH_HELD_PARTS"
    assert r["held_soffit"] and "dome" in r["held_soffit"][0]
    assert r["soffit_m"] == pytest.approx(3.0)
    assert r["m3"] is not None and r["m3"] > 0
    with pytest.raises(PJ.PerimeterError):
        PJ.measure(wall_a(pieces=[PJ.Piece("BLOCK", 1.0, None, "dome")]))      # a held piece must name why


def test_opening_position_inside_a_segment_does_not_move_the_result():
    res = []
    for x0 in (0.80, 1.20, 1.60):
        w = wall_a(openings=[PJ.Opening("D1", x0, x0 + 0.9, 2.20, 0.0, 0.20, (0.40, 0.40), (0.40, 0.40))])
        res.append(PJ.measure(w)["m3"])
    assert res[0] == pytest.approx(res[1], abs=1e-15) and res[1] == pytest.approx(res[2], abs=1e-15)
    # below the head each sub-segment has a jamb and a column: 0; the lintel band 2.20 .. 2.40: each sub-segment runs
    # from a column to a lintel end (concrete): +0.20 twice; above the lintel 2.40 .. 3.00: +0.60; segment 2: +3.00
    w = wall_a(openings=[PJ.Opening("D1", 1.0, 1.9, 2.20, 0.0, 0.20, (0.40, 0.40), (0.40, 0.40))])
    r = PJ.measure(w)
    assert r["vertical_exact_m"] == pytest.approx(2 * 0.20 + 0.60 + 3.0)


def test_lintel_reaching_the_column_is_the_low_scenario():
    w = wall_a(openings=[PJ.Opening("D1", 1.0, 1.9, 2.20, 0.0, 0.20, (0.40, 0.70), (0.40, 1.40))])
    r = PJ.measure(w)
    assert r["vertical_exact_m"] - r["vertical_exact_m_other_bearing"] == pytest.approx(0.40)
    assert r["status"] == "COMPUTED_WITH_RANGE" and r["m3_low"] < r["m3"]


def test_unknown_lintel_bearing_is_held():
    w = wall_a(openings=[PJ.Opening("D1", 1.0, 1.9, 2.20, 0.0, 0.20, None, None)])
    r = PJ.measure(w)
    assert r["held_bands"] >= 1 and r["status"] == "COMPUTED_WITH_HELD_PARTS"


@pytest.mark.parametrize("kw", [dict(b=200), dict(j=10), dict(j=0.0)])
def test_units_refused(kw):
    with pytest.raises(PJ.PerimeterError):
        PJ.measure(wall_a(**kw))


def test_millimetre_lengths_refused():
    with pytest.raises(PJ.PerimeterError):
        PJ.measure(wall_a(pieces=[PJ.Piece("BLOCK", 3000, 3.0, "B")]))
    with pytest.raises(PJ.PerimeterError):
        PJ.measure(wall_a(pieces=[PJ.Piece("BLOCK", 3.0, 3000, "B")]))


def test_module_needed_and_mix_needs_a_masonry_source():
    with pytest.raises(PJ.PerimeterError):
        PJ.kappa((0.39, None, 0.40, 0.20))
    with pytest.raises(PJ.PerimeterError):
        PJ.kappa((0.40, 0.20, 0.39, 0.19))
    with pytest.raises(PJ.PerimeterError):
        PJ.materials(0.1, 8.0, 1.1, "")
    assert PJ.materials(None, 8.0, 1.1, "Q-78") is None                       # held stays held
    m = PJ.materials(0.1, 8.0, 1.1, "Q-78 A")
    assert m["cement_bags"] == pytest.approx(0.8) and m["sand_m3"] == pytest.approx(0.11)


def test_opening_reaching_a_soffit_refused():
    with pytest.raises(PJ.PerimeterError):
        PJ.measure(wall_a(openings=[PJ.Opening("W1", 1.0, 1.9, 2.90, 0.0, 0.20, (0.4, 0.4), (0.4, 0.4))]))
