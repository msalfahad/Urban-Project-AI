"""Special-column components: synthetic known answers (no project data).

A label names an event (turn, dead end, planted start), never a second column or its bars. A spiral's length is its
helix centreline, never its pitch; an inscribed spiral only bounds it from above. A beam extra is released over its
horizontal projection only. A role another stage holds is never added again, and a role is added only when the
source requires it and fixes its quantity."""

from __future__ import annotations

import math

import pytest

from engine.source import rebar_unit_mass as UM
from engine.source import special_column_components as SC

D162 = {"method": UM.D2_OVER_162}


# ------------------------------------------------------------------ reading
@pytest.mark.parametrize("text,family,section", [("T.C", SC.TURN, None), ("D.C", SC.DEAD, None),
                                                 ("P.C 20x70", SC.PLANTED, (20.0, 70.0)),
                                                 ("P.C20X50", SC.PLANTED, (20.0, 50.0)),
                                                 (" P . C 25 x 40 ", SC.PLANTED, (25.0, 40.0))])
def test_special_labels(text, family, section):
    assert SC.parse_special_label(text) == {"family": family, "section_cm": section}


def test_other_legend_codes_and_noise_are_not_special_columns():
    for t in ("C.S", "F.C", "C.A", "B.W", "PC 20x70", "P.C 20", "T.C 20x", "TC", "T.CC", "", None, "C8", "P.C 20x70 X"):
        assert SC.parse_special_label(t) is None, t


def test_bar_count_texts():
    assert SC.parse_bar_count("10%%C16") == {"count": 10, "dia_mm": 16}
    assert SC.parse_bar_count(" 8 %%c 16 ") == {"count": 8, "dia_mm": 16}
    assert SC.parse_bar_count("4Ø16") == {"count": 4, "dia_mm": 16}
    for t in ("6%%C12/m", "16", "0%%C16", "%%C16", "10%%C0", "T.C", "", None):
        assert SC.parse_bar_count(t) is None, t


def test_a_planted_column_belongs_to_the_storey_above_its_slab():
    storeys = ("FOUNDATION", "GF", "1F", "2F")
    closing = {"FOUNDATION": "GBP", "GF": "GFRS", "1F": "FFRS", "2F": "SFRS"}
    assert SC.planted_storey("GFRS", storeys, closing) == "1F"
    assert SC.planted_storey("FFRS", storeys, closing) == "2F"
    with pytest.raises(SC.SpecialColumnError):
        SC.planted_storey("SFRS", storeys, closing)                # nothing above the top slab
    with pytest.raises(SC.SpecialColumnError):
        SC.planted_storey("XYZ", storeys, closing)


# ------------------------------------------------------------------ plan geometry
def test_axis_rect_and_refusals():
    assert SC.axis_rect([(0, 0), (900, 0), (900, 250), (0, 250)]) == (0, 0, 900, 250)
    assert SC.axis_rect([(0, 0), (900, 0), (900, 250), (0, 250), (0, 0)]) == (0, 0, 900, 250)
    with pytest.raises(SC.SpecialColumnError):
        SC.axis_rect([(0, 0), (100, 10), (90, 110), (-10, 100)])  # rotated
    with pytest.raises(SC.SpecialColumnError):
        SC.axis_rect([(0, 0), (100, 0), (100, 0), (0, 0)])
    with pytest.raises(SC.SpecialColumnError):
        SC.axis_rect([(0, 0), (1, 0), (1, 1)])


def test_turn_overlap_is_the_common_rectangle():
    lower = (0.0, 0.0, 900.0, 250.0)                               # 25 x 90 along x
    upper = (500.0, -325.0, 700.0, 575.0)                          # 20 x 90 along y, offset along x
    ov = SC.rect_intersection(lower, upper)
    assert ov == (500.0, 0.0, 700.0, 250.0) and (ov[2] - ov[0], ov[3] - ov[1]) == (200.0, 250.0)
    assert SC.rect_intersection(lower, (900.0, 0.0, 1000.0, 250.0)) is None      # touching only
    assert SC.rect_intersection(lower, (1000.0, 0.0, 1100.0, 250.0)) is None


def test_extent_along_a_beam():
    r = [(0, 0), (700, 0), (700, 200), (0, 200)]
    assert SC.extent_along(r, 0) == pytest.approx(700)
    assert SC.extent_along(r, 90) == pytest.approx(200)
    a = -53.57
    want = 700 * abs(math.cos(math.radians(a))) + 200 * abs(math.sin(math.radians(a)))
    assert SC.extent_along(r, a) == pytest.approx(want) and SC.extent_along(r, a + 180) == pytest.approx(want)
    with pytest.raises(SC.SpecialColumnError):
        SC.extent_along([(0, 0)], 0)


def test_span_relation():
    assert SC.span_relation(5000, 1000, 9000, 350) == SC.INSIDE
    assert SC.span_relation(5000, 9000, 1000, 350) == SC.INSIDE                   # either span direction
    assert SC.span_relation(8800, 1000, 9000, 350) == SC.AT_END                   # footprint reaches the end
    assert SC.span_relation(9000, 1000, 9000, 350) == SC.AT_END
    assert SC.span_relation(9300, 1000, 9000, 350) == SC.AT_END                   # past the end, still over it
    assert SC.span_relation(9400, 1000, 9000, 350) == SC.OUTSIDE
    assert SC.span_relation(1350.5, 1000, 9000, 350, tol=1.0) == SC.AT_END        # tolerance at the face
    with pytest.raises(SC.SpecialColumnError):
        SC.span_relation(0, 0, 1, -1)


def test_only_one_inside_span_names_a_host():
    r = SC.resolve_host([("B26", SC.INSIDE)])
    assert r["state"] == SC.RESOLVED and r["host"] == "B26"
    r = SC.resolve_host([("B26", SC.INSIDE), ("B28", SC.AT_END)])               # a beam framing in at the column
    assert r["state"] == SC.RESOLVED and r["host"] == "B26" and r["at_end"] == ["B28"]
    r = SC.resolve_host([("B27", SC.AT_END), ("B5", SC.AT_END), ("B4", SC.AT_END)])
    assert r["state"] == SC.NODE and r["host"] is None and r["at_end"] == ["B27", "B4", "B5"]
    assert SC.resolve_host([("A", SC.INSIDE), ("B", SC.INSIDE)])["state"] == SC.CROSSING
    assert SC.resolve_host([])["state"] == SC.NONE


# ------------------------------------------------------------------ quantities
def test_pitch_and_turns_come_from_the_stated_rate():
    assert SC.pitch_from_rate(6) == pytest.approx(1000 / 6)
    assert SC.turns_over(2000, 6) == 12.0                                         # never rounded, never +1
    assert SC.turns_over(1500, 4) == 6.0
    for bad in (0, -1, None):
        with pytest.raises(SC.SpecialColumnError):
            SC.pitch_from_rate(bad)
    with pytest.raises(SC.SpecialColumnError):
        SC.turns_over(0, 6)


def test_ellipse_perimeter():
    assert SC.ellipse_perimeter(71, 71) == pytest.approx(2 * math.pi * 71, rel=1e-15)
    n = 200000                                                                    # numerical arc length
    a, b = 96.0, 71.0
    num = math.fsum(math.hypot(a * (math.cos(2 * math.pi * (i + 1) / n) - math.cos(2 * math.pi * i / n)),
                               b * (math.sin(2 * math.pi * (i + 1) / n) - math.sin(2 * math.pi * i / n)))
                    for i in range(n))
    assert SC.ellipse_perimeter(a, b) == pytest.approx(num, rel=1e-8)
    with pytest.raises(SC.SpecialColumnError):
        SC.ellipse_perimeter(0, 1)


def test_helix_length_is_not_the_pitch():
    P, p, n = math.pi * 142, 1000 / 6, 12
    L = SC.helix_length(P, p, n)
    assert L == pytest.approx(n * math.sqrt(P * P + p * p))
    assert L > n * P and L > n * p                                                # longer than either alone
    with pytest.raises(SC.SpecialColumnError):
        SC.helix_length(P, 0, n)


def test_inscribed_centreline_bounds_from_above():
    assert SC.inscribed_centreline(200, 250, 25, 8) == (142, 192)
    with pytest.raises(SC.SpecialColumnError):
        SC.inscribed_centreline(58, 250, 25, 8)               # 58 - 50 - 8 = 0


def test_beam_extra_projection_and_mass():
    assert SC.beam_extra_projection_mm(4, 850, 200) == 4 * (2 * 850 + 200)
    assert SC.straight_kg(4 * 1900, 16, D162) == pytest.approx(7.6 * 256 / 162)
    assert SC.straight_kg(8000, 16, D162) == pytest.approx(8 * 256 / 162)
    for args in ((0, 850, 200), (4, 0, 200), (4, 850, 0)):
        with pytest.raises(SC.SpecialColumnError):
            SC.beam_extra_projection_mm(*args)
    with pytest.raises(SC.SpecialColumnError):
        SC.straight_kg(-1, 16, D162)


# ------------------------------------------------------------------ ownership
@pytest.mark.parametrize("required,existing,established,want", [
    (True, "LOWER_BOUND", True, SC.ALREADY_OWNED),          # another stage holds it: never added again
    (True, "VERIFIED", False, SC.ALREADY_OWNED),
    (None, "PROVISIONAL", False, SC.ALREADY_OWNED),
    (True, "BLOCKED+LOWER_BOUND", True, SC.ALREADY_OWNED),  # held with a blocked part
    (True, "BLOCKED", False, SC.BLOCKED),                   # held blocked stays blocked
    (True, "BLOCKED", True, SC.INCREMENTAL),                # a blocked role the source now fixes
    (True, None, True, SC.INCREMENTAL),
    (True, None, False, SC.BLOCKED),
    (None, None, True, SC.BLOCKED),                         # requirement not established
    (False, None, False, SC.NOT_REQUIRED),
])
def test_decide(required, existing, established, want):
    assert SC.decide(required, existing, established) == want


def test_duplicate_roles():
    rows = [{"PHYSICAL_ROLE_KEY": "C8|EXTRA"}, {"PHYSICAL_ROLE_KEY": "C9|EXTRA"}, {"PHYSICAL_ROLE_KEY": "C8|EXTRA"}]
    assert SC.duplicate_roles(rows) == [("C8|EXTRA",)]
    assert SC.duplicate_roles(rows[:2]) == []
