"""The invariants the generated workbook broke, each now enforced in code.

Every test here corresponds to a contradiction a reader actually found in the
exported .xlsx. They are collected in one file on purpose: these are the rules
that make every other number on the sheet believable, and a regression in any
one of them quietly devalues the rest.
"""

from __future__ import annotations

import pytest

from engine.quantity_trace import (CANDIDATE, OBSERVATION, RELEASABLE_QUANTITY,
                                   QuantityTrace, TraceError, quantity_id)
from engine.release_matrix import (BLOCKED, NOT_APPLICABLE, PHYSICAL_TOPOLOGY,
                                   READY, REGION_IDENTITY, SCOPE, USES,
                                   ReleaseMatrixError, SpaceUseStatus,
                                   assess_space)
from engine.space_model import (IDENTITY_WRONG_REGION,
                                PHYSICAL_TOPOLOGY_VALIDATED,
                                RASTER_REGION_AVAILABLE,
                                REGION_IDENTITY_VALIDATED, TOPOLOGY_MERGED,
                                FunctionalZone, PhysicalSpace,
                                SemanticObservation, SpaceModel,
                                SpaceModelError)

QID = quantity_id("23010", "2F", "WSH-01", "PERIM", "GROSS")


# --- READY may never carry a blocker -----------------------------------------

def test_ready_with_a_blocker_is_refused_at_the_type_level():
    """The workbook had 17 rows reading READY beside primary_blocker =
    trade_rule. A reader cannot tell which half to believe, and the safe half
    is the one that stops them using the number — so the contradiction
    destroys every other READY row on the sheet."""
    with pytest.raises(TraceError, match="READY and blocked"):
        QuantityTrace(quantity_id=QID, space_id="WSH-01",
                      use="GROSS_PERIMETER", unit="m", value=4.19,
                      quantity_role=CANDIDATE, release_status="READY",
                      primary_blocker="trade_rule")


def test_a_release_status_that_is_ready_and_missing_something_is_refused():
    with pytest.raises(ReleaseMatrixError, match="READY with"):
        SpaceUseStatus("WSH-01", "GROSS_PERIMETER", READY,
                       missing=["region_identity"])


def test_a_block_must_name_its_cause():
    """A block that cannot name its cause cannot be cleared."""
    with pytest.raises(ReleaseMatrixError, match="nothing.*missing"):
        SpaceUseStatus("X", "GROSS_PERIMETER", "BLOCKED_SCOPE", missing=[])
    with pytest.raises(TraceError, match="names no blocker"):
        QuantityTrace(quantity_id=QID, space_id="X", use="GROSS_PERIMETER",
                      unit="m", quantity_role=CANDIDATE,
                      release_status="BLOCKED_SCOPE")


def test_not_applicable_must_say_why():
    """N/A was being used both for "this trade does not apply" and for "we are
    not measuring this". A reader cannot tell those apart from the word."""
    with pytest.raises(ReleaseMatrixError, match="no reason"):
        SpaceUseStatus("X", "GROSS_PERIMETER", NOT_APPLICABLE)


# --- OUT_OF_SCOPE is N/A, not blocked ----------------------------------------

def test_out_of_scope_is_not_applicable_not_blocked():
    """OUT_OF_SCOPE is excluded by owner instruction: there is no work queued
    and nothing to unblock. Counting it as BLOCKED puts it in the same list as
    a room whose geometry is broken."""
    st = assess_space("TRC-01", "GROSS_PERIMETER", {},
                      applicable=False,
                      not_applicable_reason="OUT_OF_SCOPE: excluded")
    assert st.status == NOT_APPLICABLE
    assert not st.applicable
    assert st.primary_blocker == ""


def test_ambiguous_scope_is_blocked_because_it_is_real_work():
    """An undecided space IS work — the work is an owner decision."""
    established = {k: True for k in USES["GROSS_PERIMETER"].requires}
    st = assess_space("COR-02", "GROSS_PERIMETER", {**established, SCOPE: False})
    assert st.applicable and not st.ready
    assert st.primary_blocker == SCOPE
    assert st.status == "BLOCKED_SCOPE"


# --- identity and topology gate every attributed quantity --------------------

def test_region_identity_unresolved_releases_nothing():
    """WSH-01: the region is the hatched shaft beside the washroom."""
    for use in USES:
        st = assess_space("WSH-01", use,
                          {k: True for k in USES[use].requires
                           if k != REGION_IDENTITY} | {REGION_IDENTITY: False})
        assert not st.ready, use
        assert st.primary_blocker == REGION_IDENTITY, use


def test_physical_topology_unresolved_releases_nothing():
    """BED-04: a real bedroom with an unseparated bathroom inside it. Identity
    holds; the polygon is still not the whole of that room and only that room."""
    for use in USES:
        st = assess_space("BED-04", use,
                          {k: True for k in USES[use].requires
                           if k != PHYSICAL_TOPOLOGY}
                          | {PHYSICAL_TOPOLOGY: False})
        assert not st.ready, use
        assert st.primary_blocker == PHYSICAL_TOPOLOGY, use


# --- observation vs releasable quantity --------------------------------------

def test_an_observation_keeps_its_value_while_release_stays_blocked():
    """WSH-01's 4.19 m is a real measurement of raster region 361 and is not a
    washroom perimeter. Deleting it loses useful geometry; releasing it puts a
    shaft into a bathroom's takeoff."""
    t = QuantityTrace(
        quantity_id=QID, space_id="WSH-01", use="GROSS_PERIMETER", unit="m",
        value=4.19, quantity_role=OBSERVATION,
        observation_of="the traced boundary of raster region 361",
        release_status="BLOCKED_REGION_IDENTITY",
        primary_blocker="region_identity")
    assert t.value == 4.19
    assert not t.is_released


def test_an_observation_may_never_be_ready():
    """It is attributed to no physical space, so there is nothing to be ready
    FOR."""
    with pytest.raises(TraceError, match="OBSERVATION reported as READY"):
        QuantityTrace(quantity_id=QID, space_id="WSH-01",
                      use="GROSS_PERIMETER", unit="m",
                      quantity_role=OBSERVATION, observation_of="region 361",
                      release_status="READY")


def test_an_observation_must_say_what_it_measured():
    with pytest.raises(TraceError, match="does not say what"):
        QuantityTrace(quantity_id=QID, space_id="WSH-01",
                      use="GROSS_PERIMETER", unit="m",
                      quantity_role=OBSERVATION, release_status="NOT_ASSESSED")


def test_a_releasable_quantity_cannot_be_blocked():
    with pytest.raises(TraceError, match="Releasable and\\s+blocked"):
        QuantityTrace(quantity_id=QID, space_id="X", use="GROSS_PERIMETER",
                      unit="m", quantity_role=RELEASABLE_QUANTITY,
                      release_status="BLOCKED_SCOPE",
                      primary_blocker="scope")


# --- a label is not a room ---------------------------------------------------

def test_a_semantic_label_does_not_validate_a_physical_space():
    """The workbook said WASHROOM = 1 on the strength of a human-verified
    label, while the engine had recovered zero validated washroom polygons."""
    m = SpaceModel(
        observations=[SemanticObservation("SO-1", "WASHROOM",
                                          source="HUMAN_VERIFIED",
                                          seen_at_region=361)],
        spaces=[PhysicalSpace("WSH-01", 361, "IN_SCOPE",
                              frozenset({RASTER_REGION_AVAILABLE}),
                              IDENTITY_WRONG_REGION, "WASHROOM")])
    row = m.room_counts()[0]
    assert row["semantic_observations"] == 1
    assert row["validated_physical_spaces"] == 0
    assert row["unresolved_physical_spaces"] == 1


def test_identity_alone_does_not_validate_a_space():
    """Both layers, or it is not a room. BED-04 has identity and not topology."""
    s = PhysicalSpace("BED-04", 688, "IN_SCOPE",
                      frozenset({RASTER_REGION_AVAILABLE,
                                 REGION_IDENTITY_VALIDATED}),
                      TOPOLOGY_MERGED, "BEDROOM")
    assert not s.validated
    assert s.measurable          # it can still be measured as an observation


def test_a_validated_space_needs_both_layers():
    s = PhysicalSpace("BED-01", 79, "IN_SCOPE",
                      frozenset({RASTER_REGION_AVAILABLE,
                                 REGION_IDENTITY_VALIDATED,
                                 PHYSICAL_TOPOLOGY_VALIDATED}), "", "BEDROOM")
    assert s.validated


def test_geometry_layers_are_never_collapsed_into_one_number():
    """"Geometry ready = 36, unresolved = 0" was true only of the first layer
    and was printed as though it were the last."""
    s = PhysicalSpace("WSH-01", 361, "IN_SCOPE",
                      frozenset({RASTER_REGION_AVAILABLE}),
                      IDENTITY_WRONG_REGION, "WASHROOM")
    g = s.geometry_status()
    assert g[RASTER_REGION_AVAILABLE] is True
    assert g[REGION_IDENTITY_VALIDATED] is False
    assert len(g) == 4


# --- a zone is not a wall ----------------------------------------------------

def test_a_functional_zone_may_not_create_a_wall_boundary():
    """A dining zone inside an open-plan space is a use, not a wall. Giving it
    one would invent wall length the building does not have."""
    with pytest.raises(SpaceModelError, match="not a wall"):
        FunctionalZone("ZONE-DINING-01", "OPEN-01", "DINING",
                       boundary_is_physical=True)


def test_one_polygon_may_carry_several_functional_zones():
    """OPEN-01 is dining + saloon + circulation. Forcing one room_type loses
    two of them."""
    m = SpaceModel(
        spaces=[PhysicalSpace("OPEN-01", 273, "IN_SCOPE",
                              frozenset({RASTER_REGION_AVAILABLE,
                                         REGION_IDENTITY_VALIDATED,
                                         PHYSICAL_TOPOLOGY_VALIDATED}),
                              "", "SALOON")],
        zones=[FunctionalZone("Z1", "OPEN-01", "DINING"),
               FunctionalZone("Z2", "OPEN-01", "SALOON"),
               FunctionalZone("Z3", "OPEN-01", "CORRIDOR")])
    assert len(m.zones_of("OPEN-01")) == 3
    assert all(z.record()["creates_wall_boundary"] is False for z in m.zones)
    assert m.check() == []


def test_a_zone_pointing_at_a_space_that_does_not_exist_is_caught():
    m = SpaceModel(zones=[FunctionalZone("Z1", "GHOST", "DINING")])
    assert any("does not exist" in c for c in m.check())


def test_an_unvalidated_space_must_say_why():
    m = SpaceModel(spaces=[PhysicalSpace("X", 1, "IN_SCOPE", frozenset(), "")])
    assert any("does not say why" in c for c in m.check())
