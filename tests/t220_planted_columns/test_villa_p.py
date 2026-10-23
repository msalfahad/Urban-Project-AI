"""T-220 hand fixture, synthetic Villa P (not Alsenan): a planted column on a transfer beam.

Hand values (m, m2, m3):
  P1 printed 25x60 cm, drawn 250 x 600 mm -> AGREE, A = 0.15. Transfer beam TB1 0.40 x 0.90, top +4.00, billed
  through. Slab above: top +7.30, t 0.15; framing at the top B2 0.25 x 0.60 and B3 0.25 x 0.50, both net of the column.
  Owner interval 3.30.
  Physical solid = 0.15 x (7.30 - 4.00) = 0.495.
  Owner method: D_ctrl 0.60 -> column 0.15 x 2.70 = 0.405, joint 0.15 x (0.60 - 0.15) = 0.0675, slab part 0.0225;
  0.405 + 0.0675 + 0.0225 = 0.495 = the solid.
  Adverse: from the storey level under the beam 0.15 x (3.30 + 0.90) = 0.630 -> refused.
  TB1 billed net of the footprint: beam line short 0.15 x 0.90 = 0.135 (kept by the beam); the column still 0.495.
  A beam TB2 0.30 x 0.70 billed through the column at the top: top = 7.30 - 0.70 = 6.60, solid 0.15 x 2.60 = 0.390;
  a ledger joint 0.0825 for that column is DOUBLE.
  Section 20x50 printed vs 200 x 400 drawn twice, no dimension chain -> CONFLICT 0.08 .. 0.10 m2; at 3.30 m
  0.264 .. 0.330 m3, never one end.
  Slab top above not printed, finished level +7.35: HELD, bound 0.15 x 3.35 = 0.5025, never 0.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t220"))
import planted_columns as P  # noqa: E402

AP = pytest.approx


def base_pc(**kw):
    d = dict(id="P1", storey="1F",
             sources=[P.Source("TEXT", 25, 60, "cm", "text"), P.Source("DRAWN", 250, 600, "mm", "outline")],
             support=P.Member("TB1 40x90", 0.90, "THROUGH"), support_top=4.00, slab_top=7.30, slab_t=0.15,
             top_members=[P.Member("B2", 0.60, "NET"), P.Member("B3", 0.50, "NET")], interval=3.30,
             ledger_joint_m3=0.0675)
    d.update(kw)
    return P.PlantedColumn(**d)


def test_normal_solid_and_owner_method_side_by_side():
    r = P.evaluate(base_pc())
    assert r["section"]["status"] == "AGREE" and r["section"]["area_lo"] == AP(0.15)
    assert r["base"] == AP(4.00) and r["top"] == AP(7.30) and r["height_m"] == AP(3.30)
    assert r["solid_m3"] == [AP(0.495), AP(0.495)]
    om = r["owner_method"]
    assert om["D_ctrl"] == 0.60 and om["column_m3"][0] == AP(0.405)
    assert om["joint_m3"][0] == AP(0.0675) and om["slab_part_m3"][0] == AP(0.0225)
    assert om["column_m3"][0] + om["joint_m3"][0] + om["slab_part_m3"][0] == AP(r["solid_m3"][0])
    assert r["status"] == "DRAWING-CONFIRMED" and r["release"] == "NOT RELEASED"
    assert P.single_value(r) == AP(0.495)
    assert {o["result"] for o in r["ownership"]} == {"PASS"}


def test_adverse_full_storey_through_the_supporting_beam_refused():
    r = P.evaluate(base_pc())
    with pytest.raises(P.Refused, match="ABOVE_PHYSICAL"):
        P.check_claim(r, 0.15 * (3.30 + 0.90))
    assert P.check_claim(r, 0.495)


def test_beam_billed_net_of_the_footprint_is_short_column_does_not_start_lower():
    r = P.evaluate(base_pc(support=P.Member("TB1 40x90", 0.90, "NET")))
    short = [o for o in r["ownership"] if o["result"] == "BEAM_LINE_SHORT"][0]
    assert short["beam_short_m3"] == [AP(0.135), AP(0.135)] and short["owner"] == "TB1 40x90"
    assert r["base"] == AP(4.00) and r["solid_m3"][0] == AP(0.495)


def test_member_billed_through_at_the_top_owns_the_joint_and_a_ledger_joint_is_double():
    tb2 = P.Member("TB2 30x70", 0.70, "THROUGH")
    r = P.evaluate(base_pc(top_members=[tb2, P.Member("B3", 0.50, "NET")], ledger_joint_m3=0.0825))
    assert r["top"] == AP(6.60) and r["solid_m3"][0] == AP(0.390) and r["top_owner"] == "TB2 30x70"
    dbl = [o for o in r["ownership"] if o["result"] == "DOUBLE"][0]
    assert dbl["double_m3"] == AP(0.0825)
    assert r["owner_method"]["joint_m3"] == [0.0, 0.0]
    assert r["status"] == "HELD"
    ok = P.evaluate(base_pc(top_members=[tb2], ledger_joint_m3=None))
    assert ok["status"] == "DRAWING-CONFIRMED" and ok["solid_m3"][0] == AP(0.390)


def test_section_conflict_is_a_range_never_an_end():
    src = [P.Source("TEXT", 20, 50, "cm", "P.C text"), P.Source("DRAWN", 200, 400, "mm", "start"),
           P.Source("DRAWN", 0.4, 0.2, "m", "own (turned)")]
    r = P.evaluate(base_pc(sources=src))
    assert r["section"]["status"] == "CONFLICT"
    assert (r["section"]["area_lo"], r["section"]["area_hi"]) == (AP(0.08), AP(0.10))
    assert r["solid_m3"] == [AP(0.264), AP(0.330)] and r["status"] == "HELD"
    with pytest.raises(P.Refused, match="RANGE_NOT_COLLAPSED"):
        P.single_value(r)
    with pytest.raises(P.Refused, match="LARGER_END"):
        P.check_claim(r, 0.330)


def test_drafting_note_only_with_text_and_dimensions():
    src = [P.Source("TEXT", 30, 50, "cm"), P.Source("DIM", 300, 500, "mm"), P.Source("DRAWN", 300, 400, "mm")]
    r = P.evaluate(base_pc(sources=src))
    assert r["section"]["status"] == "DRAFTING_NOTE" and r["section"]["area_lo"] == r["section"]["area_hi"] == AP(0.15)


def test_missing_top_is_held_with_a_bound_never_zero():
    r = P.evaluate(base_pc(slab_top=None, slab_top_upper=7.35))
    assert r["solid_m3"] is None and r["solid_upper_bound_m3"] == AP(0.5025) and r["status"] == "HELD"
    with pytest.raises(P.Refused, match="HELD"):
        P.single_value(r)
    with pytest.raises(P.Refused, match="MISSING_AS_ZERO"):
        P.check_claim(r, 0)
    assert r["owner_method"]["status"] == "HELD"


def test_drawn_outline_alone_is_not_a_section():
    r = P.evaluate(base_pc(sources=[P.Source("DRAWN", 200, 400, "mm")]))
    assert r["section"]["status"] == "HELD" and r["solid_m3"] is None and r["status"] == "HELD"


def test_held_framing_depth_holds_the_owner_column_not_the_solid():
    r = P.evaluate(base_pc(top_members=[P.Member("B2", 0.60, "NET"), P.Member("strip", None, "NET")]))
    assert r["solid_m3"][0] == AP(0.495)
    om = r["owner_method"]
    assert om["status"] == "HELD" and om["column_m3_upper"] == AP(0.405)


def test_units_and_unknown_unit():
    r_m = P.evaluate(base_pc(sources=[P.Source("TEXT", 0.25, 0.60, "m"), P.Source("DRAWN", 600, 250, "mm")]))
    assert r_m["section"]["status"] == "AGREE" and r_m["solid_m3"][0] == AP(0.495)
    with pytest.raises(P.Refused, match="UNKNOWN_UNIT"):
        P.evaluate(base_pc(sources=[P.Source("TEXT", 10, 24, "in")]))


@pytest.mark.parametrize("angle,mirror", [(0, False), (30, False), (30, True), (-47.5, True)])
def test_billing_basis_rotation_and_mirror(angle, mirror):
    fp = P.rect(3.0, 2.0, 0.60, 0.25, angle, mirror)
    band = P.rect(3.0, 2.0, 5.00, 0.40, angle, mirror)
    assert P.billing_basis(fp, [band])[0] == "THROUGH"
    # the band cut at the column faces (two pieces either side): NET
    import math
    t = math.radians(angle)
    off = lambda s: (3.0 + s * math.cos(t), 2.0 + s * math.sin(t))
    a, b = off(-1.55), off(1.55)
    pa = P.rect(a[0], a[1], 2.50, 0.40, angle, mirror)
    pb = P.rect(b[0], b[1], 2.50, 0.40, angle, mirror)
    assert P.billing_basis(fp, [pa, pb])[0] == "NET"
    half = P.rect(3.0, 2.0, 0.30, 0.40, angle, mirror)
    assert P.billing_basis(fp, [half])[0] == "PARTIAL"


def test_partial_basis_is_undetermined_never_guessed():
    r = P.evaluate(base_pc(support=P.Member("TB1", 0.90, "PARTIAL")))
    assert r["status"] == "HELD" and any(o["result"] == "UNDETERMINED" for o in r["ownership"])


def test_existence_of_a_released_line():
    req = ["slab plan DXF", "slab plan PDF", "architectural plan"]
    ex = P.classify_existence([], req, req)
    assert ex["class"] == "NOT_DRAWN"
    st = P.released_line_state(0.42, ex)
    assert st["m3"] is None and st["status"] == "NOT_DRAWN" and st["released_was"] == 0.42
    with pytest.raises(P.Refused, match="CONVENTION_AS_BUILT"):
        P.keep_as_built(ex)
    un = P.classify_existence([], req[:2], req)
    assert un["class"] == "UNKNOWN" and un["unsearched"] == ["architectural plan"]
    with pytest.raises(P.Refused):
        P.keep_as_built(un)
    built = P.classify_existence(["slab plan DXF"], req[:1], req)
    assert built["class"] == "BUILT" and P.released_line_state(0.42, built)["m3"] == 0.42 and P.keep_as_built(built)
