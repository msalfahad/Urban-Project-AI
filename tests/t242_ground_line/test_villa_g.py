"""T-242 GROUND_LINE_V1 on a hand-calculated synthetic villa that is NOT Alsenan ('Villa G').

Villa G ground-beam plan (all values by hand, metres): necks N1 (0, 0), N2 (4.30, 0), N3 (4.30, 6.30), 0.30 x 0.30;
GF structural slab top +0.95 (main part) and +0.25 (a raised-annex part); outer ground printed as +-0.00 or +0.15.
  GB1 interior N1-N2: face to face 4.30 - 0.30 = 4.00 m ('less than 5 m', 0.30 x 0.40): 0.30 x 0.40 x 4.00 = 0.4800
  GB2 interior, 2.00 m: 'less than 2.5 m' AND 'less than 5 m' both hold literally (D-34): 0.1800 .. 0.2400 HELD
  GB3 interior N2-N3, 6.00 m ('more than 5 m', 0.60) with GB4 ending on it mid-span (D-33): 1.0800 HELD (candidate)
  GB5 exterior, 5.00 m, top +0.95: D = 0.95 - 0.15 .. 0.95 - 0.00 = 0.80 .. 0.95: 1.2000 .. 1.4250 HELD (D-35)
  GB6 exterior at the annex, 5.00 m, top +0.25: D 0.10 .. 0.25 < 0.30 (every printed section): CONFLICT 0.15 .. 0.375
  GB7 curved exterior, plan 0.5000 m2 net: 0.4000 .. 0.4750 HELD
  GB1 with a neck DOUBLE of 0.03 m2 at one end: (1.20 - 0.03) x 0.40 = 0.4680
Interior measured component = GB1 0.4800; every other run is held, never 0.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t242"))
import ground_line as GL  # noqa: E402

EXT_MAIN = GL.exterior_depth([0.95], [0.00, 0.15])
EXT_ANNEX = GL.exterior_depth([0.25], [0.00, 0.15])


def runs():
    return [
        GL.run_volume("GB1", GL.INTERIOR, 0.30, 4.00, depths=GL.title_depths(["P13-GB-LT5M"])),
        GL.run_volume("GB2", GL.INTERIOR, 0.30, 2.00, depths=GL.title_depths(["P13-GB-LT2_5M", "P13-GB-LT5M"])),
        GL.run_volume("GB3", GL.INTERIOR, 0.30, 6.00, depths=GL.title_depths(["P13-GB-GT5M"]), d33=True),
    ]


def test_interior_runs_by_hand():
    r1, r2, r3 = runs()
    assert r1["status"] == GL.CALCULATED and r1["value_m3"] == pytest.approx(0.4800)
    assert r2["status"] == GL.HELD and (r2["low_m3"], r2["high_m3"]) == pytest.approx((0.18, 0.24))
    assert r3["status"] == GL.HELD and r3["value_m3"] is None and r3["low_m3"] == pytest.approx(1.08)
    assert any(x.startswith("D-33") for x in r3["reasons"])


def test_exterior_follow_arch_range():
    assert EXT_MAIN[:2] == pytest.approx((0.80, 0.95)) and EXT_MAIN[2] == []
    r = GL.run_volume("GB5", GL.EXTERIOR, 0.30, 5.00, ext=EXT_MAIN)
    assert r["status"] == GL.HELD and (r["low_m3"], r["high_m3"]) == pytest.approx((1.20, 1.425))


def test_annex_exterior_is_a_conflict_not_a_quantity():
    assert EXT_ANNEX[:2] == pytest.approx((0.10, 0.25)) and "BELOW_TYPICAL" in EXT_ANNEX[2]
    r = GL.run_volume("GB6", GL.EXTERIOR, 0.30, 5.00, ext=EXT_ANNEX)
    assert r["status"] == GL.CONFLICT and r["value_m3"] is None
    assert (r["low_m3"], r["high_m3"]) == pytest.approx((0.15, 0.375))


def test_curved_run_by_plan_area():
    r = GL.run_volume("GB7", GL.EXTERIOR, 0.30, None, ext=EXT_MAIN, plan_m2=0.50)
    assert (r["low_m3"], r["high_m3"]) == pytest.approx((0.40, 0.475))


def test_neck_double_removed_once():
    r = GL.run_volume("GB1", GL.INTERIOR, 0.30, 4.00, depths=[0.40], end_adjust_m2=(-0.03, -0.03))
    assert r["value_m3"] == pytest.approx(0.468)
    # a neck CONFLICT gives a range: the run is never released at one end of it
    r = GL.run_volume("GB1", GL.INTERIOR, 0.30, 4.00, depths=[0.40], end_adjust_m2=(-0.03, 0.0))
    assert r["status"] == GL.CONFLICT and (r["low_m3"], r["high_m3"]) == pytest.approx((0.468, 0.48))


def test_component_total_keeps_held_apart():
    t = GL.component_total(runs())
    assert t["calculated_m3"] == pytest.approx(0.48) and t["calculated_runs"] == 1
    assert (t["held_low_m3"], t["held_high_m3"]) == pytest.approx((1.26, 1.32))


def test_units_explicit():
    assert GL.metres(4000, "mm") == pytest.approx(4.0)
    assert GL.metres(400, "cm") == pytest.approx(4.0)
    with pytest.raises(GL.GroundLineError):
        GL.metres(4.0, "ft")


def test_classification_sources():
    # S1 printed levels on both sides decide first; one source alone never makes an exterior beam
    assert GL.s1_reading(["+1.00"], ["+0.15"]) == (GL.EXTERIOR, "strong")
    assert GL.s1_reading(["+0.15"], ["+1.00"]) == (GL.EXTERIOR, "strong")          # mirrored sides
    assert GL.s1_reading(["NO_MARK"], ["BEYOND"]) == (GL.EXTERIOR, "weak")
    assert GL.s1_reading(["+0.15"], ["+0.15"])[0] == GL.COURT
    assert GL.classify(GL.EXTERIOR, "strong", GL.INTERIOR, "EXT")[0] == GL.EXTERIOR   # engine plate overruled
    assert GL.classify("UNKNOWN", "UNK/UNK", "NOWALL", "EXT")[0] == GL.CANDIDATES    # S3 alone: not exterior
    assert GL.classify(GL.EXTERIOR, "weak", "NOWALL", "EXT_OR_INT")[0] == GL.CANDIDATES
    assert GL.classify("UNKNOWN", "UNK/UNK", GL.INTERIOR, "INT")[0] == GL.INTERIOR
    # S4: architectural rooms on both sides make an unmarked, wall-less beam interior; a room-less enclosed panel on
    # the only side that is not printed outside makes it a court beam (no slab either side)
    assert GL.s4_reading([1.0], [0.95]) == "BOTH_INDOOR"
    assert GL.s4_reading([], [0.0]) == "OUTDOOR_ONLY"
    assert GL.s4_reading([1.0], []) is None
    assert GL.classify("UNKNOWN", "UNK/IN", "NOWALL", "EXT_OR_INT", "BOTH_INDOOR")[0] == GL.INTERIOR
    assert GL.classify(GL.EXTERIOR, "weak", "NOWALL", "EXT_OR_INT", "OUTDOOR_ONLY")[0] == GL.COURT
    assert GL.classify(GL.EXTERIOR, "strong", GL.EXTERIOR, "EXT", "BOTH_INDOOR")[0] == GL.EXTERIOR   # S1 printed wins


# ---------------------------------------------------------------------------------------------- adverse cases
def test_adverse_exterior_depth_never_defaulted():
    with pytest.raises(GL.GroundLineError):
        GL.exterior_depth([0.95], [])
    with pytest.raises(GL.GroundLineError):
        GL.exterior_depth([], [0.0])
    with pytest.raises(GL.GroundLineError):
        GL.run_volume("GB5", GL.EXTERIOR, 0.30, 5.00)          # no D-35 range given: refused, not 0.30 x 0.40
    with pytest.raises(GL.GroundLineError):
        GL.exterior_depth([0.95], [1.00])                      # ground above the slab top


def test_adverse_footing_outline_is_not_an_end():
    assert GL.end_support("COLUMN")
    with pytest.raises(GL.GroundLineError):
        GL.end_support("FOOTING", vertical_gap_m=0.28)
    with pytest.raises(GL.GroundLineError):
        GL.end_support("OUTLINE")


def test_adverse_intersection_twice_refused():
    assert GL.intersections_once([("N2/GB1", "NECK"), ("N2/GB3", "NECK")])
    with pytest.raises(GL.GroundLineError):
        GL.intersections_once([("N2/GB1", "NECK"), ("N2/GB1", "GROUND_BEAM")])


def test_adverse_held_shown_as_zero_refused():
    r = GL.run_volume("GB2", GL.INTERIOR, 0.30, 2.00, depths=[0.30, 0.40])
    bad = dict(r, low_m3=0.0, high_m3=0.0)
    with pytest.raises(GL.GroundLineError):
        GL.component_total([bad])
    bad = dict(r, value_m3=0.18)
    with pytest.raises(GL.GroundLineError):
        GL.component_total([bad])                              # a held run carrying one end as its value
    with pytest.raises(GL.GroundLineError):
        GL.component_total([r, r])                             # a run twice in the line


def test_adverse_no_title_no_default():
    with pytest.raises(GL.GroundLineError):
        GL.title_depths([])
    with pytest.raises(GL.GroundLineError):
        GL.title_depths(["P13-GB-WITH-LOAD"])
    with pytest.raises(GL.GroundLineError):
        GL.run_volume("GB1", GL.INTERIOR, 0.30, None, depths=[0.40])     # missing length never 0
    r = GL.run_volume("GBc", GL.COURT, 0.30, 1.30, depths=[])
    assert r["status"] == GL.HELD and r["low_m3"] is None


def test_line_not_closable_with_a_held_or_unmeasured_component():
    ok, why = GL.line_closable({"interior": GL.component_total(runs()[:1]), "ground_slab": {"status": "NOT_MEASURED"}})
    assert not ok and any("ground_slab" in w for w in why)
    ok, why = GL.line_closable({"interior": GL.component_total(runs()[:1])})
    assert ok and why == []
