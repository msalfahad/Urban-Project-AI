"""E38 — eight named heights, each with its own provenance, and no default.

The Test 1 takeoff applied one 3.30 m height to an entire floor. Every wall
quantity on that job was wrong by a constant, and nothing in the record said so.
These tests are about the shapes that make that inexpressible.
"""

from __future__ import annotations

from decimal import Decimal as D

import pytest

from engine.heights import (APPROVED, APPROVED_PROJECT_RULE, AS_BUILT_SURVEY,
                            ASSUMED, CERAMIC, COMMERCIAL, DESIGN, DOMAIN_SOURCES,
                            DOMAINS, HEIGHT_NAMES, HEIGHT_REQUIRED, PAINT,
                            PLASTER, PROPOSED, REJECTED, REVIEW_REQUIRED,
                            SECTION_DRAWING, SITE, SITE_MEASURED, SPECIFICATION,
                            VALIDATED, Height, HeightError, HeightRegistry)

REAL = HeightRegistry.load("data/registry/23010_heights.json")


def h(**kw) -> Height:
    base = dict(height_id="T:ceramic", name=CERAMIC, value_m=D("3.00"),
                source_type=SPECIFICATION, source="spec clause 09.30",
                validation_status=VALIDATED)
    base.update(kw)
    return Height(**base)


# --- eight heights, not one --------------------------------------------------

def test_there_are_eight_named_heights_and_no_generic_one():
    assert len(HEIGHT_NAMES) == 8
    for expected in ("structural_wall_height", "blockwork_height",
                     "plaster_height", "paint_height", "ceramic_height",
                     "waterproofing_height", "clear_height", "ceiling_height"):
        assert expected in HEIGHT_NAMES
    for generic in ("room_height", "roomHeight", "wall_height", "height"):
        assert generic not in HEIGHT_NAMES


def test_a_generic_room_height_cannot_be_recorded():
    with pytest.raises(HeightError, match="generic room height is the mistake"):
        h(name="room_height")


def test_ceramic_and_plaster_hold_different_values_on_the_same_project():
    """3.00 m and 3.20 m. One field could not state both."""
    assert REAL.get(CERAMIC).value_m == D("3.00")
    assert REAL.get(PLASTER).value_m == D("3.20")


# --- a missing height is a routable question, never a number -----------------

def test_a_missing_height_names_itself_rather_than_defaulting():
    with pytest.raises(HeightError, match=HEIGHT_REQUIRED):
        REAL.get(PAINT)


@pytest.mark.parametrize("plausible", ["3.0", "3.2", "3.3"])
def test_no_plausible_default_appears_anywhere_in_a_refusal(plausible):
    try:
        REAL.get(PAINT)
    except HeightError as exc:
        # 3.30 may be NAMED as the historic mistake; it must not be OFFERED.
        assert "substituted" in str(exc) or "No generic height" in str(exc)


def test_the_registry_reports_what_every_trade_would_find():
    status = REAL.status()
    assert status[CERAMIC] == "RELEASABLE"
    assert status[PAINT] == HEIGHT_REQUIRED
    assert len(REAL.missing()) == 6


# --- ASSUMED may be recorded and may never be released -----------------------

def test_an_assumed_height_cannot_be_marked_validated():
    with pytest.raises(HeightError, match="blessing it is not"):
        h(source_type=ASSUMED, validation_status=VALIDATED)


def test_an_assumed_height_can_be_recorded_honestly():
    a = h(source_type=ASSUMED, source="typical Kuwaiti villa storey",
          validation_status=REVIEW_REQUIRED)
    assert a.value_m == D("3.00") and not a.releasable


def test_an_assumed_height_never_releases_a_quantity():
    reg = HeightRegistry("T", {CERAMIC: h(source_type=ASSUMED,
                                          source="typical storey height",
                                          validation_status=REVIEW_REQUIRED)})  # noqa
    with pytest.raises(HeightError, match="may never produce a released quantity"):
        reg.for_release(CERAMIC)


def test_an_unvalidated_height_from_a_good_source_also_does_not_release():
    reg = HeightRegistry("T", {CERAMIC: h(validation_status=REVIEW_REQUIRED)})
    with pytest.raises(HeightError, match="An engineer validates it"):
        reg.for_release(CERAMIC)
    assert reg.get(CERAMIC).value_m == D("3.00")      # readable, just not usable


def test_a_rejected_height_does_not_release_either():
    reg = HeightRegistry("T", {CERAMIC: h(validation_status=REJECTED)})
    with pytest.raises(HeightError):
        reg.for_release(CERAMIC)


# --- provenance is mandatory --------------------------------------------------

def test_a_height_with_no_citation_is_refused():
    with pytest.raises(HeightError, match="assumption wearing a measurement"):
        h(source="   ")


def test_a_height_read_from_a_section_must_name_the_drawing():
    with pytest.raises(HeightError, match="must name the drawing"):
        h(source_type=SECTION_DRAWING, source="read off the section")
    ok = h(source_type=SECTION_DRAWING, source="section A-A, storey height",
           drawing_id="AR-12", revision="MAR.2023")
    assert ok.releasable


def test_every_height_carries_its_whole_provenance():
    p = REAL.get(CERAMIC).provenance()
    for field in ("height_id", "name", "value_m", "unit", "source_type",
                  "source", "validation_status", "releasable"):
        assert field in p


def test_heights_are_metres_and_a_millimetre_value_is_refused():
    with pytest.raises(HeightError, match="stored in metres"):
        h(unit="mm", value_m=D("3000"))


def test_a_non_physical_height_is_refused():
    with pytest.raises(HeightError, match="non-physical"):
        h(value_m=D("0"))


# --- the source hierarchy is ordered ------------------------------------------

def test_the_hierarchy_is_within_a_domain_and_never_across_domains():
    """Comparing a section drawing to a site tape is a category error."""
    from engine.heights import SOURCE_RANK
    assert SOURCE_RANK[SECTION_DRAWING] < SOURCE_RANK[SPECIFICATION]
    assert SOURCE_RANK[SPECIFICATION] < SOURCE_RANK[APPROVED_PROJECT_RULE]
    # SITE has its own ladder starting again at 0 — the two are not comparable
    assert SOURCE_RANK[SITE_MEASURED] < SOURCE_RANK[AS_BUILT_SURVEY]
    assert SOURCE_RANK[SITE_MEASURED] == SOURCE_RANK[SECTION_DRAWING]


def test_the_real_project_records_that_its_heights_are_project_rules_not_sections():
    """23010's 3.00 and 3.20 were never read from a drawing, and say so."""
    for name in (CERAMIC, PLASTER):
        got = REAL.get(name)
        assert got.source_type == APPROVED_PROJECT_RULE
        assert "NOT read from a section" in got.source


# --- truth domains ------------------------------------------------------------

def test_design_and_site_are_separate_facts_not_two_sources_for_one():
    reg = HeightRegistry("T", {
        (DESIGN, PLASTER): h(name=PLASTER, value_m=D("3.20")),
        (SITE, PLASTER): h(name=PLASTER, value_m=D("3.15"),
                           source_type=SITE_MEASURED,
                           source="site tape, 14 Sep 2026"),
    })
    assert reg.get(PLASTER, DESIGN).value_m == D("3.20")
    assert reg.get(PLASTER, SITE).value_m == D("3.15")


def test_a_site_measurement_never_overwrites_the_design_height():
    reg = HeightRegistry("T", {
        (DESIGN, PLASTER): h(name=PLASTER, value_m=D("3.20")),
        (SITE, PLASTER): h(name=PLASTER, value_m=D("3.15"),
                           source_type=SITE_MEASURED, source="site tape"),
    })
    v = reg.variance(PLASTER)
    assert v["design"] == "3.20" and v["site"] == "3.15"
    assert v["variance_m"] == "-0.05"            # both preserved, neither corrected


def test_production_reads_design_by_default():
    assert REAL.get(CERAMIC).domain == DESIGN


def test_a_site_source_cannot_be_filed_under_design():
    with pytest.raises(HeightError, match="not a design height"):
        HeightRegistry("T", {(DESIGN, PLASTER): h(
            name=PLASTER, source_type=SITE_MEASURED, source="site tape")})


def test_every_source_belongs_to_exactly_one_domain():
    seen = [s for ss in DOMAIN_SOURCES.values() for s in ss]
    assert len(seen) == len(set(seen))
    assert ASSUMED not in seen               # an assumption is in no domain
    assert h(source_type=ASSUMED, source="typical",
             validation_status=REVIEW_REQUIRED).domain == ""


def test_an_unknown_domain_is_refused():
    with pytest.raises(HeightError, match="is not one of"):
        REAL.get(CERAMIC, "PROBABLY")


# --- a project rule is a human decision ---------------------------------------

def test_a_project_rule_without_an_approver_cannot_exist():
    """A model may propose a project rule; it may not sign one."""
    with pytest.raises(HeightError, match="may not sign one"):
        h(source_type=APPROVED_PROJECT_RULE, source="owner said so")


def test_a_proposed_project_rule_is_refused_until_approved():
    with pytest.raises(HeightError, match="may not sign one"):
        h(source_type=APPROVED_PROJECT_RULE, source="owner said so",
          approved_by="someone", approved_on="2026-09-14", rule_version="1.0",
          approval_status=PROPOSED)


def test_an_approved_project_rule_carries_who_and_when():
    got = REAL.get(CERAMIC)
    assert got.approval_status == APPROVED
    assert got.approved_by and got.approved_on and got.rule_version


def test_approval_fields_appear_in_the_provenance():
    p = REAL.get(CERAMIC).provenance()
    for field in ("domain", "approved_by", "approval_status", "approved_on",
                  "rule_version"):
        assert field in p
