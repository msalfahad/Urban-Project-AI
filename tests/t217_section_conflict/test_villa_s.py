"""T-217 SECTION_CONFLICT_V1 on a hand-calculated non-Alsenan fixture (Villa S, invented values, not a project).

Hand calculation (m):
  M1 neck  schedule 30x60 cm, plan text 30X60, drawn 300x600 mm          AGREE          0.18 m2   x 1.20 = 0.216 m3
  M2 neck  schedule 30x50, text 30X50, dims 300 + 500, drawn 300x450      DRAFTING_NOTE  0.15 m2   x 1.10 = 0.165 m3
  M3 neck  schedule 30x100, text 25X100, dims 250 x 1000                  CONFLICT       0.25..0.30 x 1.00 = 0.25..0.30
  M4 GF column  schedule 25x70, drawn 250x600, no text / dims             CONFLICT (X6)  0.15..0.175 x 3.60 = 0.54..0.63
  M5 column drawn 200x400 only                                            HELD (never 0)
  Total M1..M4: 1.171 .. 1.311 m3.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t217"))
import section_conflict as SC  # noqa: E402

S = lambda kind, W, D, u, ref="": {"kind": kind, "W": W, "D": D, "units": u, "ref": ref}  # noqa: E731

M1 = [S("SCHEDULE", 30, 60, "cm", "sch"), S("TEXT", 30, 60, "cm", "t1"), S("DRAWN", 300, 600, "mm", "o1")]
M2 = [S("SCHEDULE", 30, 50, "cm", "sch"), S("TEXT", 30, 50, "cm", "t2"), S("DIM", 300, 500, "mm", "d2"),
      S("DRAWN", 300, 450, "mm", "o2")]
M3 = [S("SCHEDULE", 30, 100, "cm", "sch"), S("TEXT", 25, 100, "cm", "t3"), S("DIM", 250, 1000, "mm", "d3"),
      S("DRAWN", 250, 1000, "mm", "o3")]
M4 = [S("SCHEDULE", 25, 70, "cm", "sch GR"), S("DRAWN", 250, 600, "mm", "o4")]
M5 = [S("DRAWN", 200, 400, "mm", "o5")]


def test_agree():
    r = SC.classify("M1", "FOUNDATION", M1)
    assert r.status == "AGREE" and r.area_m2() == pytest.approx(0.18)
    assert r.volume_m3(1.20) == pytest.approx((0.216, 0.216))


def test_drafting_note_needs_the_drawing_to_print_the_section():
    r = SC.classify("M2", "FOUNDATION", M2)
    assert r.status == "DRAFTING_NOTE" and r.governing == (0.3, 0.5)
    assert r.area_m2() == pytest.approx(0.15) and r.volume_m3(1.10) == pytest.approx((0.165, 0.165))
    assert "DRAWN:o2" in r.evidence[0]


def test_printed_vs_printed_conflict_is_a_range():
    r = SC.classify("M3", "FOUNDATION", M3)
    assert (r.status, r.basis) == ("CONFLICT", "PRINTED_VS_PRINTED")
    assert r.range_m2 == pytest.approx((0.25, 0.30))
    assert r.volume_m3() == pytest.approx((0.25, 0.30))          # per metre of height
    with pytest.raises(SC.ConflictUnresolved):
        r.area_m2()


def test_schedule_only_vs_drawn_is_a_conflict_not_a_drafting_note():
    # adverse: the 'printed schedule wins' shortcut (X6) would call this a drafting note at 0.175 m2
    r = SC.classify("M4", "GF", M4)
    assert (r.status, r.basis) == ("CONFLICT", "PRINTED_VS_DRAWN")
    assert r.volume_m3(3.60) == pytest.approx((0.54, 0.63))


@pytest.mark.parametrize("prefer", ["SCHEDULE", "LARGER", "TEXT", "CLOSER_TO_FREELANCER"])
def test_resolution_by_preference_refused(prefer):
    r = SC.classify("M3", "FOUNDATION", M3)
    with pytest.raises(SC.PreferenceRefused):
        SC.resolve(r, prefer)


def test_range_never_collapsed_to_its_larger_end():
    r = SC.classify("M4", "GF", M4)
    lo, hi = r.volume_m3(3.60)
    assert lo < hi and r.governing is None


def test_missing_printed_section_is_held_never_zero():
    r = SC.classify("M5", "1F", M5)
    assert r.status == "HELD" and r.codes == ["SECTION_NOT_PRINTED"]
    assert r.volume_m3(3.0) is None
    with pytest.raises(SC.ConflictUnresolved):
        r.area_m2()


def test_mirrored_and_rotated_plan_and_mixed_units():
    mirrored = [S("SCHEDULE", 100, 30, "cm"), S("TEXT", 100, 25, "cm"), S("DIM", 1.0, 0.25, "m"),
                S("DRAWN", 1000, 250, "mm")]
    a, b = SC.classify("M3", "F", M3), SC.classify("M3m", "F", mirrored)
    assert (a.status, a.range_m2) == (b.status, b.range_m2)
    rot = [S("SCHEDULE", 30, 60, "cm"), S("TEXT", 60, 30, "cm"), S("DRAWN", 0.6, 0.3, "m")]
    assert SC.classify("M1r", "F", rot).status == "AGREE"


def test_villa_total_by_hand():
    recs = [(SC.classify("M1", "F", M1), 1.20), (SC.classify("M2", "F", M2), 1.10),
            (SC.classify("M3", "F", M3), 1.00), (SC.classify("M4", "GF", M4), 3.60)]
    lo = sum(r.volume_m3(h)[0] for r, h in recs)
    hi = sum(r.volume_m3(h)[1] for r, h in recs)
    assert (lo, hi) == pytest.approx((1.171, 1.311))


@pytest.mark.parametrize("bad", [S("SCHEDULE", 0, 50, "cm"), S("SCHEDULE", 30, 50, "inch"), S("PHOTO", 30, 50, "cm")])
def test_invalid_sources_refused(bad):
    with pytest.raises(ValueError):
        SC.classify("X", "F", [bad])


def test_matching_band_is_evidence_only():
    bands = {"FOU": {"W": 30, "D": 50}, "GR": {"W": 20, "D": 50}, "1ST": None}
    assert SC.matching_band((0.2, 0.5), bands) == ["GR"]
    assert SC.matching_band((0.25, 0.5), bands) == []
