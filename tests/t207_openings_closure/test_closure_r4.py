"""T-207: openings-closure rules on a NON-Alsenan hand fixture (villa T207-V) with adverse cases.

Villa T207-V (hand truth, drawing units mm on an elevation, plan widths printed in m):
- window A, plan 1.50: louvred leaves drawn beside both jambs (500 .. 1000 and 2512 .. 3012), the outline between them
  1000 .. 2512 (1.512, within 0.02 of 1.50), sill / head lines 900 / 3000, an aluminium frame 80 mm inside.
  Truth: height 3000 - 900 = 2.10 m; area 1.50 x 2.10 = 3.150 m2; reveal 2 x 2.10 + 1.50 + 1.50 = 7.200 m.l.
- twins B1 / B2 at plan centres 0.00 / 2.40, drawn outlines 0 .. 1200 and 2400 .. 3600, both 900 .. 3000.
- a 5.00 m glazed run: no transverse line, no overlay column; a structural neck NK stops at the foundation.
- doorless opening D 0.90 in a 0.20 wall, head +2.40, lowest member soffit +3.80; a 1.20 passage between paving
  (ceramic) and a court (interlock) at one level.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t207"))

import closure_r4 as C                                                  # noqa: E402

LEAVES = [(500, 1000), (2512, 3012)]


def test_shuttered_window_normal_case():
    r = C.opening_between_leaves(1.50, (1000, 2512), (900, 3000), "mm", leaves=LEAVES,
                                 frame=(1080, 980, 2432, 2920), source="T207-V street elevation")
    assert r["status"] == C.DC and r["height_m"] == 2.10
    assert round(r["width_m"] * r["height_m"], 3) == 3.150                  # hand: 1.50 x 2.10
    assert r["leaves"] == [0.5, 0.5] and r["frame"] == (1.352, 1.94)       # own items, never the opening
    assert round(2 * r["height_m"] + 2 * r["width_m"], 3) == 7.200          # reveal incl. sill


def test_frame_taken_as_the_opening_is_held():
    r = C.opening_between_leaves(1.50, (1080, 2432), (980, 2920), "mm", source="T207-V")
    assert r["status"] == C.HELD and r["height_m"] is None                  # 1.352 vs 1.50: not the opening


def test_metres_read_as_millimetres_is_held_not_scaled():
    r = C.opening_between_leaves(1.50, (1.000, 2.512), (0.9, 3.0), "mm", source="T207-V")
    assert r["status"] == C.HELD                                            # 0.0015 m wide: refused as the opening


def test_refusals():
    with pytest.raises(C.ClosureError):
        C.opening_between_leaves(1.50, (1000, 2512), (900, 3000), "mm", source="x", neighbour_of="W-next")
    with pytest.raises(C.ClosureError):
        C.opening_between_leaves(1.50, (1000, 2512), (900, 3000), "mm", source=None)
    with pytest.raises(C.ClosureError):
        C.opening_between_leaves(1.50, (1000, 2512), (900, 3000), "in", source="x")
    with pytest.raises(C.ClosureError):                                     # a leaf over the opening
        C.opening_between_leaves(1.50, (1000, 2512), (900, 3000), "mm", leaves=[(1100, 1600)], source="x")
    with pytest.raises(C.ClosureError):
        C.opening_between_leaves(1.50, (1000, 2512), (3000, 3000), "mm", source="x")


def test_missing_data_is_held_never_zero():
    r = C.opening_between_leaves(1.50, None, None, "mm", source="x")
    assert r["status"] == C.HELD and r["height_m"] is None


def test_twins_bind_when_identical():
    b = C.bind_twins([("B1", 0.0), ("B2", 2.40)], [(0, 1200, 900, 3000), (2400, 3600, 900, 3000)], "mm")
    assert b["status"] == "BOUND"


def test_twins_with_different_outlines_are_ambiguous():
    b = C.bind_twins([("B1", 0.0), ("B2", 2.40)], [(0, 1200, 900, 3000), (2400, 3600, 900, 2700)], "mm")
    assert b["status"] == "AMBIGUOUS"


def test_twins_spacing_mismatch_held():
    b = C.bind_twins([("B1", 0.0), ("B2", 2.40)], [(0, 1200, 900, 3000), (2500, 3700, 900, 3000)], "mm")
    assert b["status"] == C.HELD


def test_glazed_run_count():
    assert C.glazed_run_count(0, 0, [])["count"] == 1
    r = C.glazed_run_count(0, 0, [("NK", False)])
    assert (r["count"], r["status"]) == (1, C.DC)                           # a neck that stops below is no pier
    assert C.glazed_run_count(1, 0, [])["count"] == 2                       # a drawn mullion / pier line


def test_render_count_holds_but_never_changes_the_drawn_count():
    r = C.glazed_run_count(0, 0, [("NK", False)], render_count=2)
    assert r["status"] == C.HELD and r["count"] == 1 and r["candidates"] == [1, 2]


def test_structural_column_through_the_span_without_architecture_is_a_conflict():
    r = C.glazed_run_count(0, 0, [("C5", True)])
    assert r["status"] == C.HELD and r["count"] is None and r["candidates"] == [1, 2]
    with pytest.raises(C.ClosureError):
        C.glazed_run_count(-1, 0, [])


def test_head_soffit_is_the_reveal_head_term():
    h = C.head_reveal(0.90, 0.20)
    assert (h["head_lm"], h["head_m2"], h["separate_line"], h["status"]) == (0.9, 0.18, False, C.DC)
    assert C.head_reveal(0.90, None)["status"] == C.HELD and C.head_reveal(0.90, None)["head_m2"] is None


def test_lintel_need():
    n = C.lintel_need(2.40, 3.80, 0.20)
    assert n["status"] == C.DC and n["needed"] is True and n["gap_lower_bound_m"] == 1.40
    assert C.lintel_need(3.70, 3.80, 0.20)["status"] == C.HELD                 # room under a full lintel not shown
    assert C.lintel_need(3.80, 3.80, 0.20)["needed"] is None                  # member may be the lintel
    assert C.lintel_need(None, 3.80, 0.20)["status"] == C.HELD


def test_threshold_only_for_door_level_or_rule():
    assert C.threshold_at("DOOR", door=True, width_m=0.90)["line"] == "THRESHOLD"
    assert C.threshold_at("PASSAGE", level_change=True, width_m=1.20)["status"] == C.DC
    e = C.threshold_at("PASSAGE", finish_a="ceramic", finish_b="interlock", width_m=1.20)
    assert (e["line"], e["m"], e["status"]) == ("FINISH EDGE", 1.20, C.UNKNOWN)   # length kept, item unknown
    assert C.threshold_at("PASSAGE", finish_a="ceramic", finish_b="ceramic", width_m=1.20)["line"] is None
