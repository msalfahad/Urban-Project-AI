"""Each quantity declares what it needs. One global geometry flag is not enough.

"Openings unresolved, so no wall quantity" is both too strict and too loose. Too
strict: a GROSS ceramic wall area does not need the openings — whether to deduct
them is the trade rule's decision, and a gross figure with the deduction pending
is a useful, honest number. Too loose: blockwork needs the openings AND the
physical-wall split AND a thickness, and one flag would wave all three through.
"""

from __future__ import annotations

import pytest

from engine.release_matrix import (CLOSED_BOUNDARY, EXTERNAL_SPLIT, FLOOR_AREA,
                                   HEIGHT, NOT_READY, OPENING_RULE, OPENINGS,
                                   PHYSICAL_WALL_SPLIT, READY, REGION_IDENTITY,
                                   SCOPE, TRADE_RULE, USES, WALL_THICKNESS,
                                   ReleaseMatrixError, assess,
                                   gross_alternatives, matrix)

GEOMETRY_ONLY = {SCOPE: True, REGION_IDENTITY: True, CLOSED_BOUNDARY: True,
                 HEIGHT: True, TRADE_RULE: True}


def test_a_gross_wall_area_does_not_need_the_openings():
    """The point of a gross figure."""
    assert assess("GROSS_CERAMIC_WALL", GEOMETRY_ONLY).ready


def test_the_net_form_of_the_same_quantity_does_need_them():
    r = assess("NET_CERAMIC_WALL", GEOMETRY_ONLY)
    assert not r.ready
    assert set(r.missing) == {OPENINGS, OPENING_RULE}


def test_a_blocked_net_quantity_names_the_gross_one_that_could_ship_now():
    assert gross_alternatives("NET_CERAMIC_WALL") == ["GROSS_CERAMIC_WALL"]
    assert gross_alternatives("NET_PLASTER") == ["GROSS_PLASTER"]


def test_gross_and_net_are_different_uses_so_one_cannot_be_read_as_the_other():
    assert USES["GROSS_PLASTER"].is_gross and not USES["NET_PLASTER"].is_gross
    assert USES["GROSS_PLASTER"].gross_of == "NET_PLASTER"


def test_blockwork_needs_far_more_than_a_closed_boundary():
    r = assess("BLOCKWORK", GEOMETRY_ONLY)
    assert not r.ready
    assert set(r.missing) == {PHYSICAL_WALL_SPLIT, EXTERNAL_SPLIT, OPENINGS,
                              OPENING_RULE, WALL_THICKNESS}


def test_paint_is_not_derived_from_plaster_and_carries_its_own_dependencies():
    """Ceramic, stone or cladding may cover what plaster covered."""
    assert set(USES["PAINT"].requires) == set(USES["NET_PLASTER"].requires)
    assert "plaster" in USES["PAINT"].description


def test_skirting_depends_on_boundary_and_openings_never_on_floor_area():
    assert FLOOR_AREA not in USES["SKIRTING"].requires
    assert OPENINGS in USES["SKIRTING"].requires
    assert "never derived from floor area" in USES["SKIRTING"].description


def test_an_external_finish_needs_the_internal_external_split():
    assert EXTERNAL_SPLIT in USES["EXTERNAL_FINISH"].requires


def test_waterproofing_splits_horizontal_from_vertical():
    assert FLOOR_AREA in USES["WATERPROOFING_HORIZONTAL"].requires
    assert HEIGHT in USES["WATERPROOFING_VERTICAL"].requires
    assert HEIGHT not in USES["WATERPROOFING_HORIZONTAL"].requires


def test_a_ceiling_is_not_assumed_equal_to_the_floor():
    assert "Floor area is NOT a substitute" in USES["CEILING"].description


# --- nothing defaults ---------------------------------------------------------

def test_a_dependency_nobody_mentioned_counts_as_missing():
    """Silence is the commonest way a default sneaks in."""
    r = assess("GROSS_PERIMETER", {SCOPE: True})
    assert not r.ready
    assert set(r.missing) == {REGION_IDENTITY, CLOSED_BOUNDARY}
    assert "never established" in r.reasons[REGION_IDENTITY]


def test_an_explicitly_false_dependency_blocks_and_keeps_its_reason():
    r = assess("GROSS_PERIMETER",
               {SCOPE: True, REGION_IDENTITY: False, CLOSED_BOUNDARY: True},
               reasons={REGION_IDENTITY: "WSH-01 may be the shaft, not the washroom"})
    assert r.missing == [REGION_IDENTITY]
    assert "shaft" in r.explain()


def test_an_unknown_use_raises_rather_than_being_allowed():
    with pytest.raises(ReleaseMatrixError, match="unknown use"):
        assess("CEILING_PAINT_MAYBE", GEOMETRY_ONLY)


def test_region_identity_gates_every_single_use():
    """Attach a trade to the wrong polygon and every number after it is wrong."""
    for name, use in USES.items():
        assert REGION_IDENTITY in use.requires, name


def test_scope_gates_every_single_use():
    for name, use in USES.items():
        assert SCOPE in use.requires, name


def test_the_matrix_assesses_every_use_against_one_set_of_facts():
    m = matrix(GEOMETRY_ONLY)
    assert set(m) == set(USES)
    ready = sorted(n for n, r in m.items() if r.ready)
    assert "GROSS_CERAMIC_WALL" in ready and "BLOCKWORK" not in ready


# --- per space, per use -------------------------------------------------------

from engine.release_matrix import (NOT_APPLICABLE, assess_space, project_matrix,
                                   render_matrix)

GOOD = dict(GEOMETRY_ONLY)
BROKEN_REGION = {**GEOMETRY_ONLY, REGION_IDENTITY: False}


def test_readiness_is_a_fact_about_a_space_and_a_use_not_a_project():
    """One defect should block the rooms it affects, not the villa."""
    ok = assess_space("BTH-03", "GROSS_CERAMIC_WALL", GOOD)
    bad = assess_space("WSH-01", "GROSS_CERAMIC_WALL", BROKEN_REGION)
    assert ok.ready and not bad.ready


def test_a_block_is_named_after_the_dependency_that_caused_it():
    s = assess_space("WSH-01", "GROSS_CERAMIC_WALL", BROKEN_REGION)
    assert s.status == "BLOCKED_REGION_IDENTITY"
    s2 = assess_space("BTH-03", "NET_CERAMIC_WALL", GOOD)
    assert s2.status == "BLOCKED_OPENINGS"


def test_region_identity_outranks_later_dependencies_as_the_headline():
    """You cannot discuss a trade rule for a polygon that is not the room."""
    s = assess_space("WSH-01", "BLOCKWORK", {SCOPE: True, REGION_IDENTITY: False})
    assert s.primary_blocker == REGION_IDENTITY
    assert len(s.missing) > 1                  # others are missing too
    assert "+" in s.explain()                  # and the count is shown


def test_not_applicable_is_not_a_block():
    """A bedroom has no ceramic wall. That is not the same queue as a broken
    polygon, and counting them together would hide both."""
    s = assess_space("BED-01", "NET_CERAMIC_WALL", GOOD, applicable=False)
    assert s.status == NOT_APPLICABLE
    assert not s.ready and not s.applicable


def test_a_reason_survives_into_the_explanation():
    s = assess_space("WSH-01", "GROSS_CERAMIC_WALL", BROKEN_REGION,
                     reasons={REGION_IDENTITY: "polygon is a duct, not the washroom"})
    assert "duct" in s.explain()


# --- aggregation --------------------------------------------------------------

def test_the_project_figure_is_a_count_of_pairs_not_a_verdict():
    m = project_matrix({"BTH-03": GOOD, "WSH-01": BROKEN_REGION},
                       uses=("GROSS_CERAMIC_WALL",))
    t = m["GROSS_CERAMIC_WALL"]
    assert (t.ready, t.blocked, t.not_applicable, t.total) == (1, 1, 0, 2)


def test_the_tally_names_which_spaces_are_blocked_and_why():
    m = project_matrix({"BTH-03": GOOD, "WSH-01": BROKEN_REGION},
                       uses=("GROSS_CERAMIC_WALL",))
    assert m["GROSS_CERAMIC_WALL"].blocked_spaces == {
        "WSH-01": "BLOCKED_REGION_IDENTITY"}


def test_not_applicable_uses_are_counted_separately_from_blocked():
    m = project_matrix({"BED-01": GOOD, "BTH-03": GOOD},
                       applicable={"BED-01": {"GROSS_PLASTER"}},
                       uses=("GROSS_CERAMIC_WALL", "GROSS_PLASTER"))
    assert m["GROSS_CERAMIC_WALL"].not_applicable == 1
    assert m["GROSS_CERAMIC_WALL"].ready == 1
    assert m["GROSS_CERAMIC_WALL"].blocked == 0
    assert m["GROSS_PLASTER"].ready == 2


def test_a_space_with_no_applicability_stated_is_assessed_for_everything():
    """Guessing a trade does not apply is the same error as guessing it does."""
    m = project_matrix({"X": GOOD}, uses=("GROSS_CERAMIC_WALL",))
    assert m["GROSS_CERAMIC_WALL"].not_applicable == 0


def test_every_tally_row_adds_up():
    m = project_matrix({"A": GOOD, "B": BROKEN_REGION, "C": GOOD},
                       applicable={"C": set()})
    for t in m.values():
        assert t.ready + t.blocked + t.not_applicable == t.total == 3


def test_the_rendered_table_shows_counts_rather_than_a_single_word():
    text = render_matrix(project_matrix({"A": GOOD, "B": BROKEN_REGION}))
    assert "READY" in text and "BLOCKED" in text and "N/A" in text
    assert "GROSS_CERAMIC_WALL" in text


# --- the ceiling audit --------------------------------------------------------

def test_ceiling_requires_its_own_geometry_not_floor_area():
    """The audit that found this: CEILING reported READY on 15 spaces while
    ceiling_height was HEIGHT_REQUIRED and no ceiling geometry existed at all.
    The use was silently reading floor area."""
    from engine.release_matrix import CEILING_GEOMETRY
    assert CEILING_GEOMETRY in USES["CEILING"].requires
    assert FLOOR_AREA not in USES["CEILING"].requires


def test_a_ceiling_is_blocked_when_only_floor_area_is_known():
    from engine.release_matrix import CEILING_GEOMETRY
    r = assess("CEILING", {SCOPE: True, REGION_IDENTITY: True, FLOOR_AREA: True,
                           TRADE_RULE: True})
    assert not r.ready and CEILING_GEOMETRY in r.missing


def test_a_ceiling_releases_once_its_geometry_is_established():
    from engine.release_matrix import CEILING_GEOMETRY
    assert assess("CEILING", {SCOPE: True, REGION_IDENTITY: True,
                              CEILING_GEOMETRY: True, TRADE_RULE: True}).ready


def test_the_description_names_what_breaks_the_floor_equality():
    d = USES["CEILING"].description
    for case in ("void", "shaft", "double-height", "drop", "bulkhead"):
        assert case in d
