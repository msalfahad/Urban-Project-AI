"""T-660: HELD beam pieces restated member by member (research/agents_t660, R-T660-1 .. 6). Hand villa "V660" (not the
training villa) with normal and adverse cases, then the development-villa ledger rebuilt from merged repository files."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t660"))
import t660_rules as R  # noqa: E402
import t660_beams as B  # noqa: E402

D = Decimal
OUT = ROOT / "research" / "agents_t660" / "out" / "T660_BEAM_LEDGER.json"


# ---- villa "V660" (hand) -----------------------------------------------------------------------------------------
# Piece past a column, drawn 0.30 wide on the plan, 2.40 face to face; a section cut crosses it and prints 45 + 15 =
# 0.60 deep with a 15 x 15 round on its top outer corner; its width is not dimensioned.
#   (0.30 x 0.60 - 0.15^2 (1 - pi/4)) x 2.40 = (0.180000 - 0.004829) x 2.40 = 0.420412 m3
def test_hand_value_from_printed_section():
    v = R.value_from_section(width_plan="0.30", depth_chain=("0.45", "0.15"), length_f2f="2.40",
                             round_extents=("0.15", "0.15"))
    assert v == D("0.420412")
    assert R.value_from_section(width_plan="0.30", depth_chain=("0.45", "0.15"), length_f2f="2.40") == D("0.432000")


@pytest.mark.parametrize("kw", [
    dict(section_crosses_piece=False),          # a section elsewhere never values this piece
    dict(chain_closes_outline=False),           # a chain that does not close the outline
    dict(depth_chain=()),                       # 'AS PER SCH.' on a bar leader is no depth
    dict(round_extents=("0.15", "0.10")),       # a round with unequal extents
    dict(length_f2f="2400"),                    # mm
    dict(width_plan=None),                      # width not drawn
])
def test_hand_value_adverse(kw):
    base = dict(width_plan="0.30", depth_chain=("0.45", "0.15"), length_f2f="2.40", round_extents=("0.15", "0.15"))
    base.update(kw)
    with pytest.raises(R.Refused):
        R.value_from_section(**base)


# Unlabelled piece drawn 0.25 wide, 1.60 face to face; schedule rows (b, D): 0.25 x 0.50, 0.25 x 0.90, 0.20 x 1.20,
# 0.30 x 0.40. Only the 0.25 rows count: low 0.25 x 0.50 x 1.60 = 0.200000, high 0.25 x 0.90 x 1.60 = 0.360000.
ROWS = [("0.25", "0.50"), ("0.25", "0.90"), ("0.20", "1.20"), ("0.30", "0.40")]


def test_hand_schedule_envelope_of_drawn_width():
    assert R.schedule_envelope("0.25", "1.60", ROWS) == (D("0.200000"), D("0.360000"))


def test_hand_schedule_envelope_adverse():
    assert R.schedule_envelope("0.35", "1.60", ROWS) is None          # no row of that width: HELD blank, never 0
    with pytest.raises(R.Refused):
        R.schedule_envelope("250", "1.60", ROWS)                      # mm


def test_hand_projection_held_with_area_no_m3():
    p = R.projection_strip("0.60")
    assert p["status"] == "HELD_NO_DRAWN_DEPTH" and p["m3_low"] is None and p["m3_high"] is None
    assert p["plan_area_m2"] == "0.600000" and "ONE family" in p["guard"]
    for kw in (dict(has_mark=True), dict(has_bars=True), dict(printed_depth="0.40"), dict(section_draws_it=True)):
        with pytest.raises(R.Refused):
            R.projection_strip("0.60", **kw)
    with pytest.raises(R.Refused):
        R.projection_strip(None)


def test_hand_two_marks_bound_never_sum():
    assert R.two_marks("0.3975", "0.212") == (D("0.212000"), D("0.397500"))
    with pytest.raises(R.Refused):
        R.two_marks("0", "0.212")


def test_hand_span_crosscheck_is_evidence_only():
    c = R.span_crosscheck(("3.4", "3.3", "3.8"), ("3.670", "3.350", "3.850"))
    assert c["count_agrees"] and c["diffs"] == ["0.270", "0.050", "0.050"] and c["within_tol"] == [False, True, True]
    assert R.span_crosscheck(("3.4", "3.3"), ("3.670", "3.350", "3.850"))["count_agrees"] is False


def test_hand_net_shift_with_slab_pairing():
    # schedule 0.05 wider over 4.0 m, D 0.60: beam +0.120; slab gives up 0.05 x 4.0 x 0.16 = 0.032 -> net +0.088
    assert R.net_shift("0.48", "0.60", "0.032", "0.032", True) == (D("0.088000"), D("0.088000"))
    # schedule narrower: beam -0.120, slab takes the gap 0 .. 0.032 -> -0.120 .. -0.088
    assert R.net_shift("0.48", "0.60", "0", "0.032", False) == (D("-0.120000"), D("-0.088000"))
    with pytest.raises(R.Refused):
        R.net_shift("0.48", "0.60", "0.05", "0.01", True)


def _mirror(r):
    return (-r[1], -r[0], r[2], r[3])


def _rot90(r):
    return (-r[3], -r[2], r[0], r[1])


def test_hand_piece_column_overlap_once_mirror_rotation():
    col = (D("2.00"), D("2.50"), D("0.00"), D("0.25"))
    piece = (D("2.50"), D("4.90"), D("-0.05"), D("0.25"))          # starts at the column face: owned once
    bad = (D("2.00"), D("4.90"), D("-0.05"), D("0.25"))            # starts at the column's far face: double
    for f in (lambda r: r, _mirror, _rot90, lambda r: _rot90(_mirror(r))):
        assert not R.rect_overlap(f(piece), f(col))
        assert R.rect_overlap(f(bad), f(col))


def test_hand_check_once_adverse():
    ok = {"line_id": "a", "status": "HELD_BOUNDED_AS_DRAWN", "m3_value": None, "m3_low": "0.1", "m3_high": "0.2"}
    assert R.check_once([ok])
    with pytest.raises(R.Refused):
        R.check_once([ok, dict(ok)])                                                   # twice
    with pytest.raises(R.Refused):
        R.check_once([dict(ok, m3_low="0", m3_high="0")])                              # HELD closed as 0
    with pytest.raises(R.Refused):
        R.check_once([dict(ok, m3_low="0.3")])                                         # low > high
    with pytest.raises(R.Refused):
        R.check_once([dict(ok, m3_value="0.15")])                                      # HELD with a value


# ---- development villa (committed files only) ---------------------------------------------------------------------
@pytest.fixture(scope="module")
def doc():
    return B.build()


def test_ledger_equals_committed_output(doc):
    assert json.loads(OUT.read_text(encoding="utf-8")) == json.loads(json.dumps(doc, ensure_ascii=False))


def test_ledger_ids_are_the_r4_held_lines_once(doc):
    ids = [r["line_id"] for r in doc["beams"]]
    assert len(ids) == len(set(ids)) == 27
    assert set(ids) == set(B._r4())


def test_ledger_reconciles_exactly(doc):
    t = doc["totals"]
    assert t["before_r4"] == {"bounded": 22, "blank": 5, "low_m3": "8.332829", "high_m3": "13.684510"}
    a = t["after"]
    assert (a["valued"], a["bounded_as_drawn"], a["held_no_drawn_depth"]) == (1, 14, 12)
    for end in ("low", "high"):
        r = t["reconciliation"][end]
        assert (D(r["after_bounded"]) - D(r["unlabelled_face_to_face_length_term"]) + D(r["valued_line_old_bound"])
                + D(r["projection_ranges_set_aside"])) == D(r["before"])


def test_gf059_by_hand(doc):
    r = next(x for x in doc["beams"] if x["line_id"] == "L-8ea71184fff91b4357b7")
    # (0.500 x 0.75 - 0.20^2 (1 - pi/4)) x 1.500 = (0.375 - 0.008584) x 1.5 = 0.549624
    assert r["status"] == "VALUED_AS_DRAWN" and r["m3_value"] == "0.549624"
    assert D(r["before_r4"]["low"]) <= D(r["m3_value"]) <= D(r["before_r4"]["high"])
    # owned once: column 335 (x 71.4634 .. 71.9634, y 49.598 .. 49.848) and the piece (east of its face)
    assert not R.rect_overlap((D("71.9634"), D("73.4634"), D("49.348"), D("49.848")),
                              (D("71.4634"), D("71.9634"), D("49.598"), D("49.848")))


def test_held_never_zero_and_projections_carry_no_m3(doc):
    for r in doc["beams"]:
        if r["status"] == "HELD_NO_DRAWN_DEPTH":
            assert r["m3_low"] is None and r["m3_high"] is None and D(r["plan_area_m2"]) > 0
        if r["status"] == "HELD_BOUNDED_AS_DRAWN":
            assert D(r["m3_high"]) > 0 and D(r["m3_low"]) <= D(r["m3_high"])


def test_unlabelled_inside_old_bound_up_to_length_and_width_conflicts_unchanged(doc):
    for r in doc["beams"]:
        if r["cls"] == "UNLABELLED":
            assert abs(D(r["m3_low"]) - D(r["before_r4"]["low"])) < D("0.0005")
            assert abs(D(r["m3_high"]) - D(r["before_r4"]["high"])) < D("0.0005")
        if r["cls"] in ("WIDTH", "TWO_MARKS", "DEPTH_COMPANION"):
            assert (r["m3_low"], r["m3_high"]) == (r["before_r4"]["low"], r["before_r4"]["high"])


def test_no_freelancer_or_client_text_tracked():
    s = OUT.read_text(encoding="utf-8").lower()
    for w in ("his row", "freelancer workbook", "his_share", "sheet name"):
        assert w not in s
