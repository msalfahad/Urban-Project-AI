"""T-277 BEAM_WIDTH_CENSUS_V1 on a hand-built villa W (not Alsenan): drawn-vs-scheduled beam widths and the per-trade
readings of a CONFLICT, with adverse cases (non-parallel edges, a label on the wrong band, the larger width picked,
a cm width read as m, mirror, rotation, missing data, a projection strip outside an edge beam).

Hand calculation (villa W, metres; schedule W / H in cm):
  beam A 'BA' drawn between y = 0.00 and y = 0.25 (edges parallel, x 0 .. 4.00), schedule BA 20 x 50; label beside it
      at y = 0.45 (text height 0.30, centre 0.20 m clear of the edge): drawn 0.25 vs 0.20 = CONFLICT.
      L 4.00, D 0.50, slab t 0.16: CONC.BEAM 0.25 x 0.50 x 4.00 = 0.500 m3 (drawn) / 0.20 x 0.50 x 4.00 = 0.400 m3;
      beam soffit 1.000 / 0.800 m2; sides 2 x (0.50 - 0.16) x 4.00 = 2.720 m2 at both readings;
      slab soffit 0 .. -0.200 m2 (0.05 x 4.00) and slab m3 0 .. -0.032 (x 0.16) at the drawn reading vs the schedule one;
      a block wall crossing under the band: strip 0.05 m x (0.50 - 0.16) = 0.017 m2 changes height.
  beam B 'BB' drawn y 3.00 .. 3.20, schedule 20 x 40, label beside at y 3.40: AGREE.
  beam C 'BC' drawn y 6.00 .. 6.60, schedule 60 x 75, label INSIDE, centred at y 6.30: AGREE.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t277"))
import beam_width_census as C  # noqa: E402

HH = 0.15
SCHED = C.schedule_table([("BA", "20", "50", "cm", "s1"), ("BB", "20", "40", "cm", "s2"),
                          ("BC", "60", "75", "cm", "s3")])


def L(h, y, x0=0.0, x1=4.0, layer="1"):
    return (h, (x0, y), (x1, y), layer)


VILLA = [L("a1", 0.00), L("a2", 0.25), L("b1", 3.00), L("b2", 3.20), L("c1", 6.00), L("c2", 6.60)]


def _xf(lines, f):
    return [(h, f(p), f(q)) + tuple(rest) for h, p, q, *rest in lines]


def _bind(c, deg, lines, arcs=()):
    return C.bind_label(c, deg, lines, arcs, hh=HH)


def _cls(b, mark):
    return C.classify_readings([r[2] for r in b["readings"]], SCHED[mark]["w_m"]) if b["status"] == "BOUND" \
        else b["status"]


# ------------------------------------------------------------------------------------------------- normal cases
def test_beside_label_conflict_drawn_025_scheduled_020():
    b = _bind((2.0, 0.45), 0.0, VILLA)
    assert b["status"] == "BOUND" and b["placement"] == "BESIDE"
    assert [r[2] for r in b["readings"]] == [pytest.approx(0.25)]
    assert b["dist_m"] == pytest.approx(0.05)                 # 0.45 - 0.15 - 0.25 clear from text box to edge
    assert _cls(b, "BA") == "CONFLICT"


def test_beside_label_agree_and_centred_inside_label_agree():
    assert _cls(_bind((2.0, 3.40), 0.0, VILLA), "BB") == "AGREE"
    b = _bind((2.0, 6.30), 0.0, VILLA)
    assert b["placement"] == "INSIDE" and _cls(b, "BC") == "AGREE"


def test_consequence_hand_calculation_per_trade():
    q = C.consequence(4.00, 0.50, 0.16, 0.25, 0.20, wall_pieces=[("W1", 0.25, "crossing"), ("W2", 4.00, "along")])
    assert q["conc_beam_m3"] == (pytest.approx(0.500), pytest.approx(0.400))
    assert q["fw_beam_soffit_m2"] == (pytest.approx(1.000), pytest.approx(0.800))
    assert q["fw_beam_sides_m2"] == pytest.approx(2.720)
    assert q["slab_soffit_delta_m2"] == (0.0, pytest.approx(0.200))
    assert q["slab_conc_delta_m3"] == (0.0, pytest.approx(0.032))
    cross, along = q["blockwork"]
    assert cross["m2_range"] == (0.0, pytest.approx(0.017))
    assert along["m2_range"] == (0.0, pytest.approx(1.360))   # a bound only (wall overlay not given), never 0 alone


def test_schedule_width_in_cm_converted_once():
    assert C.schedule_width_m("20", "cm") == pytest.approx(0.20)
    assert SCHED["BC"]["w_m"] == pytest.approx(0.60) and SCHED["BC"]["d_m"] == pytest.approx(0.75)


# ------------------------------------------------------------------------------------------------ adverse cases
def test_adverse_non_parallel_edges_have_no_drawn_width():
    tilt = math.radians(3.0)
    lines = [L("a1", 0.00), ("a2", (0.0, 0.25), (4.0, 0.25 + 4.0 * math.tan(tilt)), "1")]
    b = _bind((2.0, 0.65), 0.0, lines)
    assert b["status"] == "NON_PARALLEL"
    lines = [L("a1", 0.00), ("a2", (0.0, 0.25), (4.0, 0.25 + 4.0 * math.tan(math.radians(1.0))), "1")]
    assert _bind((2.0, 0.65), 0.0, lines)["status"] == "NON_PARALLEL"     # 1 deg apart: still not parallel


def test_adverse_label_equidistant_between_two_bands_of_different_width_is_ambiguous():
    lines = [L("p1", 0.00), L("p2", 0.20), L("q1", 1.50), L("q2", 1.75)]
    b = _bind((2.0, 0.85), 0.0, lines)                        # 0.50 clear of both bands, in a 1.30 m panel
    assert b["status"] == "BOUND" and b["placement"] == "BESIDE_TIE" and len(b["readings"]) == 2
    assert C.classify_readings([r[2] for r in b["readings"]], 0.20) == "AMBIGUOUS"
    assert C.classify_readings([r[2] for r in b["readings"]], 0.30) == "CONFLICT"     # neither reading is 0.30


def test_centred_label_in_a_gap_up_to_1_20_reads_inside_by_the_convention():
    # the drafting convention (a label written inside a member is centred on it) is what binds it; stated, tested
    lines = [L("p1", 0.00), L("p2", 0.20), L("q1", 1.00), L("q2", 1.25)]
    b = _bind((2.0, 0.60), 0.0, lines)
    assert b["placement"] == "INSIDE" and [r[2] for r in b["readings"]] == [pytest.approx(0.80)]


def test_adverse_label_in_a_panel_strip_does_not_take_the_strip_as_its_band():
    # label 0.25 m from a 0.20 beam, inside a 1.00 m panel strip between two beams: the strip is not its band
    lines = [L("p1", 0.00), L("p2", 0.20), L("q1", 1.20), L("q2", 1.40)]
    b = _bind((2.0, 0.55), 0.0, lines)
    assert b["status"] == "BOUND" and [r[2] for r in b["readings"]] == [pytest.approx(0.20)]
    assert b["readings"][0][3] == ["p2"] or b["readings"][0][4] == ["p2"]


def test_adverse_two_labels_of_different_marks_on_one_band_flagged():
    bad = C.clash_check([("L1", "BA", "a1|a2"), ("L2", "BB", "a1|a2"), ("L3", "BB", "b1|b2")])
    assert bad == {"L1", "L2"}


def test_adverse_larger_or_any_chosen_width_refused_for_a_conflict():
    for pick in ("larger", "smaller", "schedule", "drawn"):
        with pytest.raises(C.Refused, match="WIDTH_CONFLICT_NOT_RESOLVED_BY_CHOICE"):
            C.governing_width("CONFLICT", 0.25, 0.20, pick=pick)
    assert C.governing_width("AGREE", 0.20, 0.20) == pytest.approx(0.20)


def test_adverse_schedule_width_unit_misread_refused():
    with pytest.raises(C.Refused, match="UNIT_MISREAD"):
        C.schedule_width_m("20", "m")                         # 20 m is no beam width
    with pytest.raises(C.Refused, match="UNIT_MISREAD"):
        C.schedule_width_m("0.20", "cm")                      # 2 mm is no beam width either
    with pytest.raises(C.Refused, match="UNIT_UNKNOWN"):
        C.schedule_width_m("20", None)
    with pytest.raises(C.Refused, match="NOT_A_NUMBER"):
        C.schedule_width_m("20x50", "cm")


def test_adverse_missing_data_never_zero():
    assert C.classify_readings([0.25], None) == "NO_SCHEDULE"
    with pytest.raises(C.Refused, match="MISSING_D"):
        C.consequence(4.0, None, 0.16, 0.25, 0.20)
    with pytest.raises(C.Refused, match="NO_DRAWN_WIDTH"):
        C.classify_readings([], 0.20)
    assert _bind((2.0, 9.00), 0.0, VILLA)["status"] == "NO_BAND"


def test_adverse_duplicate_schedule_row_with_another_size_is_a_conflict():
    t = C.schedule_table([("SX", "80", "50", "cm", "h1"), ("SX", "100", "50", "cm", "h2")])
    assert t["SX"]["duplicate_conflict"] is True and t["SX"]["handles"] == ["h1", "h2"]


@pytest.mark.parametrize("name,f,deg", [
    ("mirror", lambda p: (-p[0], p[1]), 180.0),
    ("rotate30", lambda p: (p[0] * math.cos(math.radians(30)) - p[1] * math.sin(math.radians(30)),
                            p[0] * math.sin(math.radians(30)) + p[1] * math.cos(math.radians(30))), 30.0),
    ("mm_to_m_shift", lambda p: (p[0] + 1000.0, p[1] - 500.0), 0.0),
])
def test_adverse_mirror_rotation_translation_same_classes(name, f, deg):
    lines = _xf(VILLA, f)
    for c, mark, cls in (((2.0, 0.45), "BA", "CONFLICT"), ((2.0, 3.40), "BB", "AGREE"), ((2.0, 6.30), "BC", "AGREE")):
        b = _bind(f(c), deg, lines)
        assert _cls(b, mark) == cls, name
    w = [r[2] for r in _bind(f((2.0, 0.45)), deg, lines)["readings"]]
    assert w == [pytest.approx(0.25, abs=1e-6)]


def test_adverse_projection_strip_outside_the_edge_beam_gives_two_readings():
    # edge beam 0.25 (schedule 25) with a 0.10 projection strip outside it; label outside the slab beside the strip
    lines = [L("s0", -1.00, layer="BOUND"), L("e1", 0.00), L("e2", 0.25), L("s1", 0.35), L("x1", -5.00), L("x2", -4.80)]
    b = _bind((2.0, 0.60), 0.0, lines)                        # nearest: the 0.10 strip; the 0.25 beam behind it
    assert b["placement"] == "BESIDE_STACKED"
    assert sorted(r[2] for r in b["readings"]) == [pytest.approx(0.10), pytest.approx(0.25)]
    assert C.classify_readings([r[2] for r in b["readings"]], 0.25) == "AMBIGUOUS"   # never AGREE, never CONFLICT
    # the same pair seen from inside the slab (member edges beyond the label): the nearest band only
    b2 = _bind((2.0, -0.40), 0.0, lines + [L("y1", -3.00), L("y2", -2.80)])
    assert [r[2] for r in b2["readings"]] == [pytest.approx(0.25)]


def test_adverse_interior_line_same_class_splits_other_class_does_not():
    # 0.40 beam with a hidden (layer 2) upstand line inside: one 0.40 band for a centred label
    lines = [L("o1", 0.00), L("i1", 0.25, layer="2"), L("o2", 0.40)]
    b = _bind((2.0, 0.20), 0.0, lines)
    assert b["placement"] == "INSIDE" and [r[2] for r in b["readings"]] == [pytest.approx(0.40)]
    assert b["readings"][0][6] == ["i1"]
    # the same with the inner line on the edge layer: two members, the label is not centred on either
    lines = [L("o1", 0.00), L("i1", 0.25), L("o2", 0.40)]
    b = _bind((2.0, 0.20), 0.0, lines)
    assert not (b["status"] == "BOUND" and b["placement"] == "INSIDE" and b["readings"][0][2] == pytest.approx(0.40))


def test_arc_band_width_from_radii():
    # ring beam between R 1.735 and R 1.935 about (0, 0); label beside the outer arc at r 2.135, tangent direction
    arcs = [("r_in", (0.0, 0.0), 1.735, 0.0, 180.0, "1"), ("r_out", (0.0, 0.0), 1.935, 0.0, 180.0, "1")]
    a = math.radians(60.0)
    c = (2.135 * math.cos(a), 2.135 * math.sin(a))
    b = _bind(c, 150.0, [], arcs)
    assert b["status"] == "BOUND" and b["readings"][0][5] == "arc"
    assert b["readings"][0][2] == pytest.approx(0.200, abs=1e-9)
