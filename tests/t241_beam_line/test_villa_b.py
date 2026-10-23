"""T-241 BEAM_LINE_V1 on a hand-calculated synthetic villa that is NOT Alsenan ('Villa B').

Villa B, roof slab of storey L1 (all values by hand, metres unless stated):
  columns C1 (0, 0), C2 (5, 0), C3 (10, 0), C4 (0, 4): 0.30 x 0.30, under the slab (support the beams).
  BX1: two spans C1-C2-C3, schedule 25 x 60, drawn 0.25; planted column PC 0.25 x 0.25 STARTS on span 2 at x 7.5
       (carried: the beam is continuous under it, R-BEAM-CONT-1). Runs between support faces:
       span 1 = 5.00 - 0.15 - 0.15 = 4.70, span 2 = 4.70 -> 0.25 x 0.60 x 4.70 = 0.7050 m3 each.
  EB1: slab-edge beam C1-C4, schedule 20 x 50, drawn 0.20: 4.00 - 0.30 = 3.70 -> 0.20 x 0.50 x 3.70 = 0.3700.
  BY1: schedule 25 x 50 but drawn 0.30 over 3.70 -> CONFLICT 0.4625 .. 0.5550 (both kept).
  U1 : unlabelled drawn piece 0.20 x 0.50, depth not printed -> HELD, candidate 0.040 .. 0.120 (D 0.40 .. 1.20).
  Measured line: 0.7050 + 0.7050 + 0.3700 = 1.7800 m3; CONFLICT 0.4625 .. 0.5550; HELD 1 run (never 0).
  Slab panel P1 between the faces of BX1 span 1 (y 0.125 .. ), EB1 (x 0.10 ..): 4.70 x 3.70 placed inside the faces.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t241"))
import beam_line as BL  # noqa: E402


def villa(unit="m"):
    k = {"m": 1.0, "cm": 100.0, "mm": 1000.0}[unit]
    return [
        BL.run_row("BX1-1", "L1", "BX1", 4.70 * k, b_schedule=0.25 * k, b_drawn=0.25 * k, depth=0.60 * k, unit=unit),
        BL.run_row("BX1-2", "L1", "BX1", 4.70 * k, b_schedule=0.25 * k, b_drawn=0.25 * k, depth=0.60 * k, unit=unit),
        BL.run_row("EB1", "L1", "EB1", 3.70 * k, b_schedule=0.20 * k, b_drawn=0.20 * k, depth=0.50 * k, unit=unit),
        BL.run_row("BY1", "L1", "BY1", 3.70 * k, b_schedule=0.25 * k, b_drawn=0.30 * k, depth=0.50 * k, unit=unit),
        BL.run_row("U1", "L1", "(none)", 0.50 * k, b_drawn=0.20 * k, depth=None, unit=unit, candidates=(0.04, 0.12)),
    ]


@pytest.mark.parametrize("unit", ["m", "cm", "mm"])
def test_hand_totals_every_unit(unit):
    t = BL.line_total(villa(unit))["L1"]
    assert t["measured_m3"] == pytest.approx(1.78, abs=1e-6)
    assert (t["conflict_low"], t["conflict_high"]) == (pytest.approx(0.4625), pytest.approx(0.555))
    assert t["held_n"] == 1 and (t["held_low"], t["held_high"]) == (pytest.approx(0.04), pytest.approx(0.12))


def test_statuses_by_source():
    rows = {r["run"]: r for r in villa()}
    assert rows["BX1-1"]["status"] == "CALCULATED" and rows["BX1-1"]["m3"] == pytest.approx(0.705)
    assert rows["BY1"]["status"] == "CONFLICT" and rows["BY1"]["m3"] is None
    assert rows["U1"]["status"] == "HELD" and rows["U1"]["m3"] is None


def test_carried_planted_column_never_cuts_the_run():
    # span 2 measured continuous under PC (support faces only): 4.70, not 4.70 - 0.25
    r = villa()[1]
    assert r["length_m"] == pytest.approx(4.70)
    with pytest.raises(BL.Refused):
        BL.check_claim(r, 0.25 * 0.60 * (4.70 - 0.25))          # the cut at the carried member kept: refused


def test_conflict_never_collapsed_to_either_end():
    by1 = villa()[3]
    for v in (0.555, 0.4625):
        with pytest.raises(BL.Refused):
            BL.check_claim(by1, v)


def test_held_never_released_never_zero():
    u1 = villa()[4]
    for v in (0.0, 0.04, 0.12):
        with pytest.raises(BL.Refused):
            BL.check_claim(u1, v)


def test_a_run_once_in_the_line():
    rows = villa() + [villa()[0]]
    with pytest.raises(BL.Refused):
        BL.line_total(rows)


def test_end_at_member_it_meets_in_3d_only():
    # BX1 at roof level: top +3.40, soffit +2.80; C2 column bottom +0.00 top +2.80 (meets the soffit): an end
    assert BL.check_end("BX1-1", "COLUMN", 0.00, 2.80, 2.80, 3.40)
    # a footing outline under the same plan point (top -0.60) is a plan outline at another level: refused
    with pytest.raises(BL.Refused):
        BL.check_end("BX1-1", "FOOTING", -1.20, -0.60, 2.80, 3.40)
    # a member starting above the beam top (a planted column on the next floor) is not an end either
    with pytest.raises(BL.Refused):
        BL.check_end("BX1-2", "PLANTED_COLUMN", 3.40 + 0.01, 6.20, 2.80, 3.40)
    with pytest.raises(BL.Refused):
        BL.check_end("BX1-2", "COLUMN", None, 2.80, 2.80, 3.40)   # level not printed -> HELD, never an end


def test_finished_level_never_a_structural_top():
    assert BL.depth_from_levels("EB1", 3.40, "STRUCTURAL", 2.90, "STRUCTURAL") == pytest.approx(0.50)
    with pytest.raises(BL.Refused):
        BL.depth_from_levels("EB1", 3.50, "FINISHED", 2.90, "STRUCTURAL")


def _sheet(angle=0.0, mirror=False):
    """Villa B plan pieces of the C1 corner bay; every piece turned about the origin by angle (and mirrored)."""
    import math

    def rot(cx, cy, w, d):
        a = math.radians(angle)
        X, Y = cx * math.cos(a) - cy * math.sin(a), cx * math.sin(a) + cy * math.cos(a)
        return BL.rect(X, Y, w, d, angle, mirror)
    beam = [dict(id="BX1-1", poly=rot(2.50, 0.0, 4.70, 0.25)),          # between the C1 / C2 faces
            dict(id="EB1", poly=rot(0.0, 2.0, 0.20, 3.70))]             # between the C1 / C4 faces
    cols = [dict(id="C1", poly=rot(0.0, 0.0, 0.30, 0.30)), dict(id="C2", poly=rot(5.0, 0.0, 0.30, 0.30)),
            dict(id="C4", poly=rot(0.0, 4.0, 0.30, 0.30))]
    panel_c1 = dict(id="P1", poly=rot(0.10 + 4.70 / 2, 0.125 + 3.70 / 2, 4.70, 3.70))   # starts at the beam faces
    plate = dict(id="P1-plate", poly=rot(2.5, 2.0, 5.0, 4.0))                            # drawn over the beams
    return beam, cols, panel_c1, plate


@pytest.mark.parametrize("angle,mirror", [(0.0, False), (30.0, False), (-47.5, True), (90.0, False)])
def test_partition_c1_pass_and_plate_double_refused(angle, mirror):
    beam, cols, panel, plate = _sheet(angle, mirror)
    assert BL.partition([panel], beam, cols)["status"] == "PASS"
    bad = BL.partition([plate], beam, cols)
    assert bad["status"] == "FAIL"
    # the plate over the beams doubles exactly the band areas inside it: BX1 4.70 x 0.125 + EB1 3.70 x 0.10 = 0.9575
    over = sum(a for kind, _b, _s, a in bad["double"] if kind == "BEAM/SLAB")
    assert over == pytest.approx(4.70 * 0.125 + 0.10 * 3.70, abs=1e-6)


def test_beam_through_a_column_is_double():
    beam, cols, panel, _ = _sheet()
    through = [dict(id="BX1-through", poly=BL.rect(2.5, 0.0, 5.30, 0.25))]   # billed over C1 and C2 as well
    res = BL.partition([panel], through, cols)
    assert res["status"] == "FAIL"
    dbl = sum(a for kind, *_x, a in res["double"] if kind == "BEAM/COLUMN")
    # the band runs from the far face of C1 to the far face of C2: each 0.30 x 0.30 column has 0.30 x 0.25 under it
    assert dbl == pytest.approx(2 * 0.30 * 0.25, abs=1e-6)


def test_band_in_no_line_is_a_gap_and_overbilling_is_refused():
    assert BL.gaps(0.74, []) == pytest.approx(0.74)              # a drawn band billed by no line stays visible
    assert BL.gaps(0.74, [0.74]) == 0.0
    with pytest.raises(BL.Refused):
        BL.gaps(0.74, [0.74, 0.1184])                             # band in beam AND slab line


def test_convention_c1_c2_same_slab_plus_beam():
    band = [(4.70 * 0.25 * 2, 0.16), (3.70 * 0.20, 0.16)]
    c1_beam = 1.78
    c2_beam = BL.convention("C2_PLATE_OVER_BEAMS", c1_beam, band)
    moved = sum(a * t for a, t in band)
    assert c2_beam == pytest.approx(c1_beam - moved)
    with pytest.raises(BL.Refused):
        BL.convention("unstated", c1_beam, band)


def test_reconcile_names_the_residual():
    r = BL.reconcile(1.78, 1.50, [("cut at the carried PC", 0.0375), ("span 2 held by the engine", 0.2425)])
    assert r["closed"] and r["residual"] == pytest.approx(0.0, abs=1e-9)
    r2 = BL.reconcile(1.78, 1.50, [("cut at the carried PC", 0.0375)])
    assert not r2["closed"] and r2["residual"] == pytest.approx(0.2425)


def test_metamorphic_order_of_rows():
    a = BL.line_total(villa())
    b = BL.line_total(list(reversed(villa())))
    assert a == b
