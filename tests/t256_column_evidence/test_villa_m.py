"""T-256 COLUMN_EVIDENCE_V1 on a hand-calculated villa that is not Alsenan (Villa M).

Villa M (hand figures): GF structural interval 3.60 m (ground-beam top +0.70 to GF roof slab top +4.30, both printed),
1F interval 3.40 m, slab plates 0.15 m.
  M-C2  GF, schedule GR 25 x 60, slab plan draws 0.25 x 0.50, plot and architectural copy the same, nothing printed at
        the member: CONFLICT (printed vs drawn) 0.125 .. 0.150 m2 x 3.60 = 0.450 .. 0.540 m3; schedule reading moves
        (0.150 - 0.125) x 0.15 = 0.00375 m3 of slab plate into the column line (DOUBLE if the slab stays at the drawn face)
  M-C4  GF, schedule 30 x 70, drawn 0.30 x 0.60, the architectural plan prints a face-to-face 700 and 300 at the member:
        SETTLED 0.21 m2 x 3.60 = 0.756 m3 (the drawn 0.60 is a drafting slip, evidence only)
  M-C5  1F, schedule 20 x 50, drawn 0.25 x 0.50, the architectural plan prints 250 x 500 at the member: still CONFLICT,
        now printed vs printed, 0.100 .. 0.125 x 3.40 = 0.340 .. 0.425 m3
  M-C6  1F, schedule 20 x 40, drawn 400 x 200 (rotated), a size text '0.2 x 0.4' (m): AGREE 0.08 x 3.40 = 0.272
  M-C7  GF, schedule 25 x 50, drawn 0.25 x 0.40 + its PDF plot + its architectural copy: CONFLICT, the copies add nothing
  M-C8  1F turned column, schedule 20 x 90, drawn 0.20 x 1.00, a typical detail printing 20 x 90: CONFLICT (typical
        details are not member-specific)
  M-U1  2F line of type C3 (schedule band only), no outline on the 2F plan, its plot, the architectural 2F plan, no start
        symbol on the 1F plan: NOT_PRESENT, the line is removed (never a line of 0)
  M-U2  same, the plot not searched: UNKNOWN, no value
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t256"))
import column_evidence as CE  # noqa: E402

GF_PLAN, F1_PLAN = "M dxf: GF roof slab plan", "M dxf: 1F roof slab plan"
SCHED = "M dxf: column schedule"


def _src(kind, w, d, u, doc, **k):
    return CE.Source(kind, w, d, u, doc, **k)


def m_c2():
    return [_src("SCHEDULE", 25, 60, "cm", SCHED), _src("DRAWN", 250, 500, "mm", GF_PLAN),
            _src("DRAWN", 250, 500, "mm", "M pdf p.4", copy_of=GF_PLAN),
            _src("DRAWN", 0.25, 0.50, "m", "M arch GF plan", copy_of=GF_PLAN)]


def test_conflict_printed_vs_drawn_keeps_both_readings_and_the_range():
    r = CE.classify("M-C2", m_c2())
    assert r.status == "CONFLICT" and r.basis == "PRINTED_VS_DRAWN"
    assert r.range_m2 == (0.125, 0.15)
    assert r.m3(3.60) == (pytest.approx(0.45), pytest.approx(0.54))
    assert len(r.copies) == 2 and r.third == []
    assert {x["section_m"] for x in r.readings} == {(0.25, 0.5), (0.25, 0.6)}


def test_third_independent_print_agreeing_with_the_schedule_settles():
    r = CE.classify("M-C4", [_src("SCHEDULE", 30, 70, "cm", SCHED), _src("DRAWN", 300, 600, "mm", GF_PLAN),
                             _src("DIM", 300, 700, "mm", "M arch GF plan", ref="dims 7A1 / 7A2 face to face")])
    assert r.status == "SETTLED" and r.basis == "THIRD_PRINTED_SOURCE_AGREES_WITH_PRINT"
    assert r.governing == (0.3, 0.7) and r.codes == [(0.3, 0.6)]
    assert r.value_m3(3.60) == pytest.approx(0.756)


def test_third_print_agreeing_with_the_drawn_reading_is_printed_vs_printed_never_a_vote():
    r = CE.classify("M-C5", [_src("SCHEDULE", 20, 50, "cm", SCHED), _src("DRAWN", 250, 500, "mm", F1_PLAN),
                             _src("TEXT", 250, 500, "mm", "M arch 1F plan")])
    assert r.status == "CONFLICT" and r.basis == "PRINTED_VS_PRINTED"
    assert r.m3(3.40) == (pytest.approx(0.34), pytest.approx(0.425))
    with pytest.raises(CE.ConflictUnresolved):
        r.value_m3(3.40)


def test_rotation_and_units_agree():
    r = CE.classify("M-C6", [_src("SCHEDULE", 20, 40, "cm", SCHED), _src("DRAWN", 400, 200, "mm", F1_PLAN),
                             _src("TEXT", 0.2, 0.4, "m", F1_PLAN)])
    assert r.status == "AGREE" and r.value_m3(3.40) == pytest.approx(0.272)


def test_copies_of_the_same_drawing_are_not_a_third_source():
    srcs = [_src("SCHEDULE", 25, 50, "cm", SCHED), _src("DRAWN", 250, 400, "mm", GF_PLAN),
            _src("DRAWN", 250, 400, "mm", "M pdf p.4", copy_of=GF_PLAN),
            _src("DRAWN", 250, 400, "mm", "M arch GF plan", copy_of=GF_PLAN)]
    r = CE.classify("M-C7", srcs)
    assert r.status == "CONFLICT" and r.basis == "PRINTED_VS_DRAWN" and len(r.copies) == 2


def test_typical_detail_and_type_band_are_not_member_specific():
    r = CE.classify("M-C8", [_src("SCHEDULE", 20, 90, "cm", SCHED), _src("DRAWN", 200, 1000, "mm", F1_PLAN),
                             _src("TEXT", 20, 90, "cm", "M details sheet", member_specific=False),
                             _src("SCHEDULE", 25, 100, "cm", SCHED, member_specific=False, ref="GR band, context")])
    assert r.status == "CONFLICT" and len(r.not_counted) == 2 and r.third == []


def test_drafting_note_when_the_drawing_prints_the_schedule_value():
    r = CE.classify("M-N1", [_src("SCHEDULE", 30, 50, "cm", SCHED), _src("DRAWN", 300, 400, "mm", GF_PLAN),
                             _src("TEXT", 30, 50, "cm", GF_PLAN)])
    assert r.status == "SETTLED" and r.basis.startswith("DRAWING_PRINTS_IT") and r.governing == (0.3, 0.5)


def test_metamorphic_source_order():
    a = CE.classify("M-C2", m_c2())
    b = CE.classify("M-C2", list(reversed(m_c2())))
    assert (a.status, a.basis, a.range_m2) == (b.status, b.basis, b.range_m2)


def test_plate_transfer_signs():
    d = CE.plate_transfer(0.125, 0.150, 0.15)
    assert d == {"m3": pytest.approx(0.00375), "kind": "DOUBLE"}
    g = CE.plate_transfer(0.125, 0.100, 0.15)
    assert g["kind"] == "GAP" and g["m3"] == pytest.approx(-0.00375)
    with pytest.raises(ValueError):
        CE.plate_transfer(0.125, 0.15, None)


ALL = {"storey structural plan": "ABSENT", "plot of the storey plan": "ABSENT",
       "architectural plan of the storey": "ABSENT", "structural plan below (start / stop symbol)": "ABSENT"}


def test_existence_not_present_removes_the_line_never_a_zero():
    r = CE.existence("M-U1", dict(ALL), member_specific_print=False, type_band_only=True)
    assert r["status"] == "NOT_PRESENT" and r["action"] == "REMOVE_LINE" and r["m3"] is None


# ---- adverse --------------------------------------------------------------------------------------------------------

def test_adverse_larger_end_or_schedule_end_refused():
    r = CE.classify("M-C2", m_c2())
    for by in ("larger", "schedule", "closest to the freelancer"):
        with pytest.raises(CE.PreferenceRefused):
            r.pick(by)
    with pytest.raises(CE.ConflictUnresolved):
        r.value_m3(3.60)                                  # a schedule-only reading is never released


def test_adverse_missing_section_never_zero():
    r = CE.classify("M-H1", [_src("DRAWN", 250, 500, "mm", GF_PLAN)])
    assert r.status == "HELD" and r.m3(3.60) == (None, None)
    with pytest.raises(CE.ConflictUnresolved):
        r.value_m3(3.60)
    assert CE.classify("M-C2", m_c2()).m3(None) == (None, None)   # an unprinted height stays open, never 0


def test_adverse_existence_unknown_when_any_sheet_not_searched_or_a_print_names_it():
    s = dict(ALL)
    s["plot of the storey plan"] = "NOT_SEARCHED"
    u = CE.existence("M-U2", s, member_specific_print=False, type_band_only=True)
    assert u["status"] == "UNKNOWN" and u["m3"] is None and "NOT_SEARCHED" in u["why"][0]
    assert CE.existence("M-U3", dict(ALL), member_specific_print=True, type_band_only=True)["status"] == "UNKNOWN"
    assert CE.existence("M-U4", dict(ALL), member_specific_print=False, type_band_only=False)["status"] == "UNKNOWN"
    f = dict(ALL)
    f["architectural plan of the storey"] = "FOUND"
    assert CE.existence("M-U5", f, False, True)["status"] == "EXISTS"
    with pytest.raises(ValueError):
        CE.existence("M-U6", {"a sheet nobody named": "ABSENT"}, False, True)


def test_adverse_bad_inputs():
    with pytest.raises(ValueError):
        CE.classify("X", [_src("SCHEDULE", 25, 0, "cm", SCHED)])
    with pytest.raises(ValueError):
        CE.classify("X", [_src("SCHEDULE", 25, 50, "inch", SCHED)])
    with pytest.raises(ValueError):                       # a copy of a document that is not there
        CE.classify("X", [_src("SCHEDULE", 25, 50, "cm", SCHED), _src("DRAWN", 250, 400, "mm", "pdf", copy_of=GF_PLAN)])
