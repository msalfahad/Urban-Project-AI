"""T-248 COLUMN_LINE_V1 on a hand-calculated villa that is not Alsenan (Villa K).

Villa K (hand figures, metres): ground slab top +0.80 (ground-beam top), GF roof slab top +4.30, 1F roof top +7.50
(both printed structural tops), roof finished +11.00 with no structural top printed; formation at least 1.20 below
existing ground (a printed limit), underlay 0.15, footing K1 depth 0.60.
  K-C1  GF column 0.30 x 0.60 on neck N1, framed by beams billed NET: 0.18 x (4.30 - 0.80) = 0.630
        owner split (D_ctrl 0.70, t 0.15): column 0.18 x 2.80 = 0.504, joint 0.18 x 0.55 = 0.099, head 0.027
  K-C2  GF column, schedule 25 x 60 vs drawn 0.25 x 0.50, no print on the plan: CONFLICT 0.125 .. 0.150 x 3.50
        = 0.4375 .. 0.5250
  K-P1  1F planted column 0.20 x 0.40 on beam KB3 (beam billed through under it): base = KB3 top = +4.30,
        0.08 x 3.20 = 0.256
  K-P2  2F planted column 0.20 x 0.50 under roof beam KR1 20 x 70 billed THROUGH: top = soffit = roof top - 0.70,
        roof top only bounded by the finished +11.00: HELD, <= 0.10 x (10.30 - 7.50) = 0.280
  K-C9  2F line carried from the schedule, no 2F plan draws it: UNKNOWN, no value
  N1    neck 0.30 x 0.60: base = formation + 0.15 + 0.60 <= -1.20 + 0.75 = -0.45, top +0.80: HELD, >= 0.18 x 1.25
        = 0.225, no upper end
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t248"))
import t248_column_line as CL  # noqa: E402

GROUND = CL.Level.at(0.80, "Villa K ground-beam top (printed)")
GF_ROOF = CL.Level.at(4.30, "Villa K GF roof slab top (printed)")
F1_ROOF = CL.Level.at(7.50, "Villa K 1F roof slab top (printed)")
ROOF = CL.Level.held(None, 11.00, "Villa K roof: finished +11.00 only (upper bound)", ["ROOF_DATUM"])
FORMATION = CL.Level.held(None, -1.20, "Villa K note: excavation at least 1.20 below existing", ["FORMATION"],
                          kind=CL.LIMIT)


def villa_k(unit="m"):
    f = {"m": 1.0, "cm": 100.0, "mm": 1000.0}[unit]
    c1 = CL.Member("K-C1", "GF", "C1", "COLUMN", CL.Section.of(0.30 * f, 0.60 * f, unit=unit), GROUND, GF_ROOF,
                   framing=(("KB1", "NET"), ("KB2", "NET")))
    c2 = CL.Member("K-C2", "GF", "C2", "COLUMN", CL.Section.conflict(0.125, 0.150, "schedule 25x60 / drawn 0.25x0.50"),
                   GROUND, GF_ROOF)
    p1 = CL.Member("K-P1", "1F", "PC1", "PLANTED", CL.Section.of(0.20, 0.40), GF_ROOF, F1_ROOF)
    p2 = CL.Member("K-P2", "2F", "PC2", "PLANTED", CL.Section.of(0.20, 0.50), F1_ROOF,
                   ROOF.minus(0.70, "soffit of KR1"), top_owner="BEAM_THROUGH", framing=(("KR1", "THROUGH"),))
    c9 = CL.Member("K-C9", "2F", "C9", "COLUMN", CL.Section.of(0.2, 0.5), F1_ROOF, ROOF, existence="NOT_DRAWN")
    n1 = CL.Member("K-N1", "FOUNDATION", "C1", "NECK", CL.Section.of(0.30, 0.60),
                   CL.neck_base(FORMATION, 0.15, 0.60, 0.60, "K1 H 0.60"), GROUND)
    return [c1, c2, p1, p2, c9, n1]


def test_normal_values_by_hand():
    s = {m.id: CL.solid(m) for m in villa_k()}
    assert s["K-C1"]["status"] == "DRAWING-CONFIRMED" and s["K-C1"]["m3_lo"] == pytest.approx(0.630)
    assert s["K-C2"]["status"] == "CONFLICT"
    assert (s["K-C2"]["m3_lo"], s["K-C2"]["m3_hi"]) == (pytest.approx(0.4375), pytest.approx(0.525))
    assert s["K-P1"]["m3_lo"] == pytest.approx(0.256) and s["K-P1"]["status"] == "DRAWING-CONFIRMED"
    assert s["K-P2"]["status"] == "HELD" and s["K-P2"]["m3_lo"] is None
    assert s["K-P2"]["m3_hi"] == pytest.approx(0.280)
    assert s["K-C9"]["status"] == "UNKNOWN" and s["K-C9"]["m3_lo"] is None and s["K-C9"]["m3_hi"] is None
    assert s["K-N1"]["status"] == "HELD" and s["K-N1"]["m3_lo"] == pytest.approx(0.225) and s["K-N1"]["m3_hi"] is None


@pytest.mark.parametrize("unit", ["m", "cm", "mm"])
def test_units_and_orientation(unit):
    a = CL.solid(villa_k(unit)[0])["m3_lo"]
    assert a == pytest.approx(0.630)
    turned = CL.Section.of(0.60, 0.30)          # mirrored / rotated 90 degrees: the same plan area
    assert turned.a_lo == CL.Section.of(0.30, 0.60).a_lo


def test_components_never_count_held_or_unknown_as_zero():
    comp = CL.components([CL.solid(m) for m in villa_k()])
    assert comp["DRAWING-CONFIRMED"] == [2, pytest.approx(0.886)]
    assert comp["CONFLICT"] == [1, pytest.approx(0.4375), pytest.approx(0.525)]
    assert comp["HELD"][0] == 2 and comp["HELD"][3] == 2      # two members with an open side: partial bounds only
    assert comp["UNKNOWN"] == [1]


def test_owner_split_re_adds_to_the_same_solid():
    sp = CL.owner_split(0.18, 3.50, 0.70, 0.70, 0.15)
    assert sp["column"][0] == pytest.approx(0.504) and sp["joint"][0] == pytest.approx(0.099)
    assert sp["head"] == pytest.approx(0.027) and sp["whole"] == pytest.approx(0.630)


def test_adverse_finished_level_default_and_limit_refused():
    with pytest.raises(CL.Refused, match="FINISHED_AS_STRUCTURAL"):
        CL.Level(1.00, 1.00, "DRAWING-CONFIRMED", "FFL +1.00", CL.FINISHED)
    with pytest.raises(CL.Refused, match="DEFAULT_DATUM"):
        CL.Level(0.90, 0.90, "DRAWING-CONFIRMED", "")          # an unprinted neck top defaulted
    with pytest.raises(CL.Refused, match="LIMIT_AS_LENGTH"):
        CL.Level(-1.20, -1.20, "HELD", "min. excavation 1.20", CL.LIMIT)   # a limit used as the formation


def test_adverse_conflict_collapse_refused():
    with pytest.raises(CL.Refused, match="COLLAPSED_CONFLICT"):
        CL.Section(0.15, 0.15, "CONFLICT")
    with pytest.raises(CL.Refused):
        CL.Section(0.125, 0.150, "AGREE")                      # the larger end taken as the agreed section


def test_adverse_top_through_a_beam_counted_twice_or_left_open():
    p2 = villa_k()[3]
    with pytest.raises(CL.Refused, match="DOUBLE"):
        CL.solid(CL.Member("x", "2F", "PC2", "PLANTED", p2.section, p2.base, F1_ROOF, top_owner="COLUMN",
                           framing=(("KR1", "THROUGH"),)))
    with pytest.raises(CL.Refused, match="GAP"):
        CL.solid(CL.Member("y", "GF", "C1", "COLUMN", CL.Section.of(0.3, 0.6), GROUND, GF_ROOF.minus(0.7, "soffit"),
                           top_owner="BEAM_THROUGH", framing=(("KB1", "NET"),)))
    bad = CL.ownership({"K-C1": "COLUMN"}, False, {"K-C1": [("KB1", "THROUGH")]})
    assert len(bad) == 2                                       # slab carries the footprint + beam through


def test_adverse_undrawn_upper_column_is_never_released():
    s = CL.solid(villa_k()[4])
    assert s["status"] == "UNKNOWN" and "EXISTENCE_NOT_DRAWN" in s["causes"]
    comp = CL.components([s])
    assert comp["DRAWING-CONFIRMED"] == [0, 0.0] and comp["UNKNOWN"] == [1]


def test_stack_check_neck_top_is_the_column_base():
    ms = villa_k()
    assert CL.stack_check([("N1", ms[5], ms[0])]) == []
    wrong = CL.Member("K-C1b", "GF", "C1", "COLUMN", ms[0].section, CL.Level.at(1.00, "a different datum"), GF_ROOF)
    assert CL.stack_check([("N1", ms[5], wrong)])                # gap of A x 0.20 between neck and column flagged


def test_footing_two_readings_hold_the_neck():
    b = CL.neck_base(FORMATION, 0.15, 0.30, 0.50, "one outline two tags")
    assert b.status == "HELD" and "FOOTING_DEPTH_TWO_READINGS" in b.causes and b.hi == pytest.approx(-0.55)


def test_reconcile_names_the_residual():
    r = CL.reconcile(1.00, [("count", 0.20), ("height", 0.10)], 1.35)
    assert not r["closed"] and r["residual"] == pytest.approx(0.05)
    assert CL.reconcile(1.00, [("count", 0.20), ("height", 0.15)], 1.35)["closed"]


def test_metamorphic_member_order():
    a = CL.components([CL.solid(m) for m in villa_k()])
    b = CL.components([CL.solid(m) for m in reversed(villa_k())])
    assert a == b
