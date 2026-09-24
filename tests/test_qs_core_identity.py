"""Identity has to survive the drawing being redrawn.

Scan-order numbering is the defect: insert one component near the start of a plan and every reference after it
moves, so an owner's decision about a room silently lands on a different room.  These tests hold the replacement
to a harder standard than "the numbers look stable" - they insert, move, split, merge, delete and collide, and
require the engine either to carry identity forward on geometric evidence or to say that it cannot.
"""

from __future__ import annotations

import pytest

from engine.qs_core import geom, identity, invariants, pipeline, synthetic as syn
from engine.qs_core.entities import (LINEAGE_MERGED, LINEAGE_MODIFIED, LINEAGE_NEW, LINEAGE_REMOVED,
                                     LINEAGE_SPLIT, LINEAGE_UNCHANGED)

TOL = 0.05          # the search radius for "is this the same object, moved a little"


def comps(plan):
    return plan["COMPONENTS"]


def ident(plan):
    identity.assign_identity(plan["COMPONENTS"], plan["REVISION"])
    return {c.component_ref: c for c in plan["COMPONENTS"]}


def states(records):
    return identity.lineage_summary(records)


# ------------------------------------------------------------------ the same drawing twice
def test_an_identical_rerun_produces_identical_identity():
    a, b = syn.small_plan("R1"), syn.small_plan("R1")
    ident(a), ident(b)
    assert {c.component_ref: c.uid for c in comps(a)} == {c.component_ref: c.uid for c in comps(b)}
    recs = identity.match_revisions(comps(a), comps(b), TOL)
    assert states(recs) == {LINEAGE_UNCHANGED: len(comps(a))}
    assert all(r["DECISIONS_CARRY_FORWARD"] for r in recs)


def test_identity_does_not_depend_on_the_order_the_components_arrive_in():
    plan = syn.small_plan("R1")
    check = invariants.identity_is_order_independent(comps(plan), "R1")
    assert check["PASS"], check["RESULT"]


def test_a_fingerprint_is_geometry_and_nothing_else():
    a = syn.floor_region("C-1", [(0, 0, 3, 4)])
    b = syn.floor_region("SOMETHING-ELSE", [(0, 0, 3, 4)])
    c = syn.floor_region("C-1", [(0, 0, 3, 4.001)])
    assert identity.fingerprint(a) == identity.fingerprint(b)
    assert identity.fingerprint(a) != identity.fingerprint(c)


# ------------------------------------------------------------------ small changes, big renumbering risk
def test_a_five_millimetre_wall_move_keeps_every_unrelated_component_unchanged():
    a, b = syn.small_plan("R1"), syn.small_plan("R2", shift=0.005)
    ident(a), ident(b)
    recs = identity.match_revisions(comps(a), comps(b), TOL)
    by_ref = {r["CURRENT_REF"]: r for r in recs if r["CURRENT_REF"]}
    assert by_ref["C-ROOM-A"]["STATE"] == LINEAGE_UNCHANGED
    assert by_ref["C-CORRIDOR"]["STATE"] == LINEAGE_UNCHANGED
    assert by_ref["W-A-B"]["STATE"] == LINEAGE_MODIFIED
    assert by_ref["C-ROOM-B"]["STATE"] == LINEAGE_MODIFIED
    assert all(r["DECISIONS_CARRY_FORWARD"] for r in recs)
    before = {c.component_ref: c.persistent_id for c in comps(a)}
    after = {c.component_ref: c.persistent_id for c in comps(b)}
    assert before == after, "a wall that moved 5 mm must not renumber the building"


def test_inserting_a_component_does_not_renumber_the_ones_that_were_there():
    a = syn.small_plan("R1")
    b = syn.small_plan("R2")
    b["COMPONENTS"].insert(0, syn.floor_region("C-NEW-FIRST", [(0.0, 9.0, 2.0, 11.0)], revision="R2"))
    ident(a), ident(b)
    recs = identity.match_revisions(comps(a), comps(b), TOL)
    by_ref = {r["CURRENT_REF"]: r for r in recs if r["CURRENT_REF"]}
    assert by_ref["C-NEW-FIRST"]["STATE"] == LINEAGE_NEW
    assert all(by_ref[c.component_ref]["STATE"] == LINEAGE_UNCHANGED
               for c in comps(a) if c.component_ref in by_ref)


# ------------------------------------------------------------------ changes that change what a thing IS
def test_a_component_that_splits_is_reported_as_a_split_and_carries_no_decision():
    a = syn.small_plan("R1")
    b = syn.small_plan("R2")
    b["COMPONENTS"] = [c for c in b["COMPONENTS"] if c.component_ref != "C-ROOM-A"]
    b["COMPONENTS"] += [syn.floor_region("C-ROOM-A1", [(0.0, 0.0, 4.0, 2.0)], revision="R2"),
                        syn.floor_region("C-ROOM-A2", [(0.0, 2.0, 4.0, 4.0)], revision="R2")]
    ident(a), ident(b)
    recs = identity.match_revisions(comps(a), comps(b), TOL)
    split = [r for r in recs if r["STATE"] == LINEAGE_SPLIT]
    assert split, states(recs)
    assert all(not r["DECISIONS_CARRY_FORWARD"] for r in split)
    assert any("re-attached deliberately" in (r.get("WHY_NOT") or "") for r in split)


def test_two_components_that_merge_are_reported_as_a_merge():
    a = syn.small_plan("R1")
    a["COMPONENTS"] = [c for c in a["COMPONENTS"] if c.component_ref != "C-ROOM-A"]
    a["COMPONENTS"] += [syn.floor_region("C-A1", [(0.0, 0.0, 4.0, 2.0)]),
                        syn.floor_region("C-A2", [(0.0, 2.0, 4.0, 4.0)])]
    b = syn.small_plan("R2")
    ident(a), ident(b)
    recs = identity.match_revisions(comps(a), comps(b), TOL)
    merged = [r for r in recs if r["STATE"] == LINEAGE_MERGED]
    assert merged and all(not r["DECISIONS_CARRY_FORWARD"] for r in merged)


def test_a_removed_component_is_reported_as_removed_and_a_new_one_as_new():
    a = syn.small_plan("R1")
    b = syn.small_plan("R2")
    b["COMPONENTS"] = [c for c in b["COMPONENTS"] if c.component_ref != "C-RECESS"]
    b["COMPONENTS"].append(syn.floor_region("C-EXTRA", [(12.0, 12.0, 14.0, 14.0)], revision="R2"))
    ident(a), ident(b)
    recs = identity.match_revisions(comps(a), comps(b), TOL)
    by_state = {}
    for r in recs:
        by_state.setdefault(r["STATE"], []).append(r["PREVIOUS_REF"] or r["CURRENT_REF"])
    assert "C-RECESS" in by_state[LINEAGE_REMOVED]
    assert "C-EXTRA" in by_state[LINEAGE_NEW]


def test_a_centroid_collision_does_not_produce_a_false_match():
    a = [syn.floor_region("C-SQUARE", [(0.0, 0.0, 4.0, 4.0)])]
    b = [syn.floor_region("C-CROSS", [(1.8, 0.0, 2.2, 4.0), (0.0, 1.8, 4.0, 2.2)], revision="R2")]
    identity.assign_identity(a, "R1"), identity.assign_identity(b, "R2")
    assert geom.centroid(a[0].rects) == pytest.approx(geom.centroid(b[0].rects))
    recs = identity.match_revisions(a, b, TOL)
    assert states(recs) == {LINEAGE_NEW: 1, LINEAGE_REMOVED: 1}
    assert a[0].persistent_id != b[0].persistent_id


# ------------------------------------------------------------------ rooms, which is what decisions attach to
def test_a_renamed_room_keeps_its_identity_so_a_decision_survives_the_rename():
    a = pipeline.run(syn.small_plan("R1"), max_opening_span=syn.MAX_OPENING_SPAN, wall_height=3.0,
                        wall_geometry_includes_openings=syn.WALL_GEOMETRY_SPANS_OPENINGS)
    plan_b = syn.small_plan("R2")
    plan_b["LABELS"] = [lb if lb.text != "ROOM B" else type(lb)("STORE", lb.x, lb.y) for lb in plan_b["LABELS"]]
    b = pipeline.run(plan_b, max_opening_span=syn.MAX_OPENING_SPAN, wall_height=3.0,
                        wall_geometry_includes_openings=syn.WALL_GEOMETRY_SPANS_OPENINGS)
    recs = identity.match_revisions(a["SPACE_OBJECTS"], b["SPACE_OBJECTS"], TOL)
    assert states(recs) == {LINEAGE_UNCHANGED: len(a["SPACE_OBJECTS"])}
    old = {s.label: s.persistent_id for s in a["SPACE_OBJECTS"]}
    new = {s.label: s.persistent_id for s in b["SPACE_OBJECTS"]}
    assert old["ROOM B"] == new["STORE"], "the room did not change; only its name did"


def test_a_room_that_grows_is_modified_and_still_carries_its_decision():
    a = pipeline.run(syn.small_plan("R1"), max_opening_span=syn.MAX_OPENING_SPAN, wall_height=3.0,
                        wall_geometry_includes_openings=syn.WALL_GEOMETRY_SPANS_OPENINGS)
    b = pipeline.run(syn.small_plan("R2", shift=0.005), max_opening_span=syn.MAX_OPENING_SPAN,
                     wall_height=3.0, wall_geometry_includes_openings=syn.WALL_GEOMETRY_SPANS_OPENINGS)
    recs = identity.match_revisions(a["SPACE_OBJECTS"], b["SPACE_OBJECTS"], TOL)
    assert set(states(recs)) <= {LINEAGE_UNCHANGED, LINEAGE_MODIFIED}
    assert all(r["DECISIONS_CARRY_FORWARD"] for r in recs)
