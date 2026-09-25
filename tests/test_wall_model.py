"""E25.2 — the per-space wall model, and the pipe that lets it see a drawing.

E25 could always decompose a space's boundary. What it could never do was reach
a real drawing: `VectorPdfSource.regions()` built the label map and ink mask
inside one method and discarded them, so every caller in the repo was a unit
test on a hand-built array. These tests cover the pipe, the per-space records it
produces, and the rules about what such a record may and may not be used for.
"""

from __future__ import annotations

from decimal import Decimal as D

import numpy as np
import pytest

from engine.geometry import Segmentation
from engine.wall_model import (KNOWN_DEFECT, SAME, UNRESOLVED, VALIDATED,
                               reconcile_against_prior, run_wall_model)

PX = D("100")          # 100 mm per pixel keeps the arithmetic readable


def toy() -> Segmentation:
    """Two rooms side by side, sharing a wall, inside an outer wall.

    ink = wall. Region 1 is the paper outside, 2 and 3 are the rooms.
    """
    g = np.zeros((9, 13), np.int32)
    wall = np.ones((9, 13), bool)
    g[2:7, 2:6] = 2                    # left room, 4 x 5 cells
    g[2:7, 7:11] = 3                   # right room
    g[0, :] = 1                        # paper margin all round
    g[-1, :] = 1
    g[:, 0] = 1
    g[:, -1] = 1
    wall[g > 0] = False
    for a in (g, wall):
        a.setflags(write=False)
    return Segmentation(labels=g, wall_mask=wall, px_mm=PX, outside_id=1,
                        drawing_id="TOY-01", revision="R1",
                        source_path="toy.pdf", source_sha256="deadbeef")


SPACES = {"LEFT": 2, "RIGHT": 3}


def test_the_runner_traces_every_mapped_space():
    res = run_wall_model(toy(), SPACES)
    assert sorted(r.space_id for r in res.records) == ["LEFT", "RIGHT"]
    assert not res.failures


def test_a_closed_boundary_validates_and_produces_a_wall_length():
    res = run_wall_model(toy(), SPACES).by_id()
    left = res["LEFT"]
    assert left.status == VALIDATED and left.releasable
    assert left.open_length_m > 0 or left.gross_wall_perimeter_m > 0
    assert left.gross_wall_perimeter_m == left.gross_room_perimeter_m


def test_the_shared_wall_names_the_space_on_the_other_side():
    res = run_wall_model(toy(), SPACES).by_id()
    adj = {s.adjoining_space for s in res["LEFT"].walls.segments}
    assert "RIGHT" in adj


def test_an_external_run_is_classified_external_not_guessed_from_position():
    res = run_wall_model(toy(), SPACES).by_id()
    kinds = {s.classification for s in res["LEFT"].walls.segments}
    assert "EXTERNAL" in kinds


def test_a_space_the_segmentation_does_not_contain_is_a_failure_not_a_zero():
    res = run_wall_model(toy(), {"GHOST": 99})
    assert "GHOST" in res.failures and not res.records


def test_an_unclosed_boundary_is_unresolved_and_not_releasable():
    """A wall quantity from an open outline measures a room with no edge there."""
    g = np.zeros((9, 13), np.int32)
    wall = np.ones((9, 13), bool)
    g[2:7, 2:11] = 2               # one wide room
    g[2:7, 6] = 3                  # a strip through it that is floor, not wall
    g[0, :] = 1; g[-1, :] = 1; g[:, 0] = 1; g[:, -1] = 1
    wall[g > 0] = False
    for a in (g, wall):
        a.setflags(write=False)
    seg = Segmentation(labels=g, wall_mask=wall, px_mm=PX, outside_id=1)
    rec = run_wall_model(seg, {"WIDE": 2, "STRIP": 3}).by_id()["WIDE"]
    assert rec.status == UNRESOLVED and not rec.releasable
    assert "does not close" in rec.status_reason


def test_physical_wall_excludes_open_transitions():
    """Blockwork may only ever see masonry."""
    res = run_wall_model(toy(), SPACES).by_id()
    for rec in res.values():
        assert rec.physical_wall_m <= rec.gross_wall_perimeter_m


# --- persistence carries enough to trace a number back ----------------------

def test_every_segment_records_mm_coordinates_as_well_as_pixels():
    """Pixels are a rendering artefact that changes with dpi."""
    rec = run_wall_model(toy(), SPACES).by_id()["LEFT"]
    seg0 = rec.segments_json()[0]
    assert seg0["start_mm"] != seg0["start_px"]
    assert seg0["length_m"] and seg0["boundary_type"]


def test_wall_thickness_is_none_and_says_so_rather_than_defaulting():
    """100/150/200 mm are the common answers and none of them is evidence."""
    rec = run_wall_model(toy(), SPACES).by_id()["LEFT"]
    for s in rec.segments_json():
        assert s["wall_thickness_mm"] is None
        assert s["wall_thickness_source"] == "NOT_MEASURED"


def test_a_segment_traces_back_to_the_exact_source_bytes():
    rec = run_wall_model(toy(), SPACES).by_id()["LEFT"]
    s = rec.segments_json()[0]
    assert s["source_sha256"] == "deadbeef" and s["drawing_id"] == "TOY-01"
    assert s["revision"] == "R1" and s["measurement_basis"]


def test_openings_are_not_given_an_invented_height():
    rec = run_wall_model(toy(), SPACES).by_id()["LEFT"]
    for o in rec.openings_json():
        assert o["height_mm"] is None and o["type"] == "UNCLASSIFIED"


# --- reconciliation is a change detector, not a pass/fail -------------------

def test_reconciliation_names_the_prior_figure_as_a_prior_output_not_a_target():
    res = run_wall_model(toy(), SPACES)
    lines = reconcile_against_prior(
        res, prior_total_m=res.by_id()["LEFT"].gross_wall_perimeter_m,
        prior_basis="toy", known_defects={},
        applicable_space_ids={"LEFT"},
        applicable_definition="LEFT only, gross wall perimeter")
    assert lines[0].classification == SAME
    assert "not an authority and not a target" in lines[0].note


def test_a_known_defect_is_classified_rather_than_counted_against_the_new_model():
    res = run_wall_model(toy(), SPACES)
    lines = reconcile_against_prior(
        res, prior_total_m=D("1.00"), prior_basis="toy",
        known_defects={"LEFT": "the prior trace measured the wrong polygon"},
        applicable_space_ids={"LEFT"}, applicable_definition="LEFT only")
    defects = [l for l in lines if l.classification == KNOWN_DEFECT]
    assert [l.label for l in defects] == ["LEFT (recorded defect)"]


def test_reconciling_without_a_scope_definition_is_refused():
    """The defect this parameter exists to prevent: comparing all 36 traced
    spaces (734.57 m) against an aggregate that covered nine (95.42 m), and
    reporting +639.15 m as if something had gone wrong."""
    from engine.wall_model import WallModelError
    res = run_wall_model(toy(), SPACES)
    with pytest.raises(WallModelError, match="has a scope and a boundary definition"):
        reconcile_against_prior(res, prior_total_m=D("1.00"), prior_basis="toy",
                                known_defects={})
    with pytest.raises(WallModelError, match="nobody can read back"):
        reconcile_against_prior(res, prior_total_m=D("1.00"), prior_basis="toy",
                                known_defects={}, applicable_space_ids={"LEFT"})


def test_a_wider_scope_is_recorded_but_never_subtracted_from_a_narrower_one():
    res = run_wall_model(toy(), SPACES)
    lines = reconcile_against_prior(
        res, prior_total_m=res.by_id()["LEFT"].gross_wall_perimeter_m,
        prior_basis="toy", known_defects={}, applicable_space_ids={"LEFT"},
        applicable_definition="LEFT only")
    wider = [l for l in lines if "all traced spaces" in l.label][0]
    assert wider.prior_m is None and wider.delta_m is None


# --- the segmentation pipe ---------------------------------------------------

def test_the_segmentation_arrays_are_read_only():
    """A module that could edit the label map could move a wall with nothing
    recording that it had."""
    seg = toy()
    with pytest.raises(ValueError, match="read-only"):
        seg.labels[0, 0] = 999
    with pytest.raises(ValueError, match="read-only"):
        seg.wall_mask[0, 0] = True


def test_the_segmentation_carries_its_own_provenance():
    p = toy().provenance()
    assert p["sha256"] == "deadbeef" and p["drawing_id"] == "TOY-01"
    assert p["px_mm"] == str(PX) and p["outside_id"] == 1


def test_the_outside_is_read_from_the_sheet_corner_not_assumed_largest():
    """On a plan with a big open terrace the largest free region is not the paper."""
    seg = toy()
    assert seg.outside_id == int(seg.labels[0, 0])


def test_the_internal_external_march_does_not_roll_the_whole_array():
    """It used to, once per pixel of march, per segment. On a 17-megapixel sheet
    that turned a two-minute run into hours."""
    import inspect
    from engine import walls
    src = inspect.getsource(walls.space_walls)
    march = src[src.index("march past the wall body"):]
    assert "peek(labels" in march and "look(labels" not in march


# --- one status is too coarse ------------------------------------------------

def test_a_closed_outline_is_usable_as_a_perimeter_but_not_as_masonry():
    """Skirting and blockwork depend on different things. A boundary can be a
    perfectly good room perimeter while every doorway in it is still untyped."""
    rec = run_wall_model(toy(), SPACES).by_id()["LEFT"]
    ok, _ = rec.releasable_for("PERIMETER")
    assert ok
    ok, why = rec.releasable_for("MASONRY")
    assert not ok and "doorway" in why


def test_masonry_is_held_when_no_opening_detection_ran():
    """max_opening_mm=0 means every segment types PHYSICAL_WALL by construction.
    That is a default, not a finding."""
    rec = run_wall_model(toy(), SPACES, max_opening_mm=0).by_id()["LEFT"]
    assert rec.opening_status == UNRESOLVED
    assert "by default" in rec.opening_status_reason


def test_an_external_split_is_held_when_a_segment_cannot_be_classified():
    """"Not proven outside" and "inside" are different claims."""
    g = np.zeros((7, 7), np.int32)
    g[2:5, 2:5] = 2                       # one room, no reachable outside
    wall = ~(g > 0)
    for a in (g, wall):
        a.setflags(write=False)
    seg = Segmentation(labels=g, wall_mask=wall, px_mm=PX, outside_id=99,
                       outside_ids=frozenset({99}))
    rec = run_wall_model(seg, {"ROOM": 2}).by_id()["ROOM"]
    ok, why = rec.releasable_for("EXTERNAL_SPLIT")
    assert not ok and "unresolved, not" in why
    assert rec.unclassified_segments == rec.segment_count
    assert rec.internal_segments == 0


def test_a_segment_is_never_classified_internal_merely_by_falling_through():
    """Every one of AR-00's 703 segments came back INTERNAL this way."""
    from engine.walls import CLASSIFICATION_UNRESOLVED
    g = np.zeros((7, 7), np.int32)
    g[2:5, 2:5] = 2
    wall = ~(g > 0)
    for a in (g, wall):
        a.setflags(write=False)
    seg = Segmentation(labels=g, wall_mask=wall, px_mm=PX, outside_id=99,
                       outside_ids=frozenset({99}))
    rec = run_wall_model(seg, {"ROOM": 2}).by_id()["ROOM"]
    for s in rec.walls.segments:
        assert s.classification == CLASSIFICATION_UNRESOLVED
        assert s.classification_basis and s.classification_basis != "not established"


def test_the_outside_set_is_border_connectivity_not_one_corner_pixel():
    from engine.geometry import outside_region_ids
    g = np.zeros((7, 9), np.int32)
    g[1:6, 1:8] = 5
    g[3, 4] = 7                      # an island enclosed by the room
    g[0, :] = 1; g[-1, :] = 1; g[:, 0] = 2; g[:, -1] = 1
    ids = outside_region_ids(g)
    assert ids == frozenset({1, 2})  # two margin regions, both border-connected
    assert 7 not in ids              # an enclosed island is never outside


def test_an_external_face_names_the_region_that_reaches_the_border():
    rec = run_wall_model(toy(), SPACES).by_id()["LEFT"]
    ext = [s for s in rec.walls.segments if s.classification == "EXTERNAL"]
    assert ext and "connects to the sheet border" in ext[0].classification_basis


def test_an_unknown_use_is_refused_rather_than_defaulting_to_allowed():
    from engine.wall_model import WallModelError
    rec = run_wall_model(toy(), SPACES).by_id()["LEFT"]
    with pytest.raises(WallModelError, match="unknown use"):
        rec.releasable_for("CEILING")
