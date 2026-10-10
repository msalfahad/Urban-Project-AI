"""§2: three objects, three questions, and no reading one as the next.

Collapsing them is how a raster blob became an area. These tests assert the
separation holds in the types, not only in the prose.
"""

import pytest

from engine import space_objects as so


def _interval(i, src, length=1000.0, fixed=0.0, start=0.0):
    return so.BoundaryInterval(
        interval_id=i, axis="H", fixed_mm=fixed, start_mm=start,
        end_mm=start + length, source_type=src,
        chosen_object_id=f"OBJ-{i}", support_length_mm=length)


def _candidate(sources, *, closed=True, area=20.0, basis="CLEAR_INTERNAL_FINISH_FACE"):
    ivs = tuple(_interval(f"BI-{n}", s, start=n * 1000.0)
                for n, s in enumerate(sources))
    return so.MeasuredSpaceCandidate(
        candidate_id="MSC-0001", region_id="RTR-0001", intervals=ivs,
        area_m2=area, perimeter_m=18.0, measurement_basis=basis,
        geometry_hash="abc123", polygon_closed=closed)


# --- A. the topology region ----------------------------------------------

def test_a_topology_region_names_its_area_approximate():
    r = so.TopologyRegion(
        region_id="RTR-0001", source="RASTER_SEGMENTATION",
        approximate_area_m2=21.4, centroid_mm=(1000.0, 2000.0),
        bbox_mm=(0.0, 0.0, 5000.0, 4000.0))
    rec = r.record()
    assert "APPROXIMATE_area_m2" in rec
    assert "area_m2" not in rec, "a bare area_m2 would be read as measured"
    assert rec["carries_no_released_geometry"] is True
    assert "NO released millimetre" in rec["what_this_is_not"]


def test_a_region_is_not_resolved_merely_by_existing():
    r = so.TopologyRegion("RTR-1", "RASTER_SEGMENTATION", 1.0, (0, 0),
                          (0, 0, 1, 1))
    assert r.status == so.TOPOLOGY_PROPOSED
    assert not r.is_resolved


# --- B. the measured space candidate -------------------------------------

def test_raster_only_is_never_production_eligible():
    """§3: a pixel may localise a wall and may never measure one."""
    assert so.SRC_RASTER_ONLY not in so.PRODUCTION_ELIGIBLE_SOURCES
    assert so.SRC_UNRESOLVED not in so.PRODUCTION_ELIGIBLE_SOURCES
    assert not _interval("BI-1", so.SRC_RASTER_ONLY).is_production_eligible


def test_the_source_priority_matches_the_stated_order():
    """§9's candidate priority for AR-00, in order."""
    assert so.SOURCE_PRIORITY[so.SRC_VECTOR_WALL_FACE] == 0
    for a, b in zip(so.BOUNDARY_SOURCES, so.BOUNDARY_SOURCES[1:]):
        assert so.SOURCE_PRIORITY[a] < so.SOURCE_PRIORITY[b]


def test_one_unresolved_interval_makes_the_measurement_partial():
    """§12: partial measurement is kept, not thrown away."""
    c = _candidate([so.SRC_VECTOR_WALL_FACE] * 3 + [so.SRC_UNRESOLVED])
    assert c.measurement_status == so.MEASUREMENT_PARTIAL
    assert not c.is_complete
    assert len(c.unresolved_intervals) == 1
    cov = c.record()["boundary_source_coverage"]
    assert cov["measured_pct"] == 75.0
    assert cov["unresolved_pct"] == 25.0
    assert cov["unresolved_intervals"] == 1


def test_a_diagnostic_source_completes_the_polygon_but_not_for_release():
    c = _candidate([so.SRC_VECTOR_WALL_FACE] * 3 + [so.SRC_DIAGNOSTIC_VECTOR])
    assert c.measurement_status == so.MEASUREMENT_COMPLETE_DIAGNOSTIC
    assert c.is_complete
    assert c.measured_pct == 100.0
    assert c.production_pct == 75.0


def test_all_production_sources_give_a_production_complete_candidate():
    c = _candidate([so.SRC_VECTOR_WALL_FACE, so.SRC_VECTOR_OPENING_JAMB,
                    so.SRC_VECTOR_EXTERNAL_BOUNDARY,
                    so.SRC_RECOVERED_FRAGMENT])
    assert c.measurement_status == so.MEASUREMENT_COMPLETE_PRODUCTION
    assert c.production_pct == 100.0


def test_an_unclosed_polygon_is_partial_however_good_its_sources():
    c = _candidate([so.SRC_VECTOR_WALL_FACE] * 4, closed=False)
    assert c.measurement_status == so.MEASUREMENT_PARTIAL


def test_the_candidate_states_the_polygon_was_not_warped_into_place():
    """§11: raster identifies topology, vector reconstructs measurement."""
    rec = _candidate([so.SRC_VECTOR_WALL_FACE]).record()
    built = rec["polygon_built_from"]
    for forbidden in ("scaled", "warped", "offset", "smoothed"):
        assert forbidden in built


def test_every_interval_carries_its_own_decision_record():
    """§10: no black-box "polygon snapped successfully"."""
    iv = so.BoundaryInterval(
        interval_id="BI-1", axis="V", fixed_mm=100.0, start_mm=0.0,
        end_mm=2000.0, source_type=so.SRC_VECTOR_WALL_FACE,
        chosen_object_id="WB-00042", candidate_object_ids=("WB-00042",
                                                           "WB-00043"),
        rejected=(("WB-00043", "ORIENTATION_DIFFERS_BY_90_DEG"),),
        distance_mm=12.4, orientation_difference_deg=0.0,
        support_length_mm=1950.0, validation_class="ESTABLISHED",
        reason_chosen="nearest established face on the same axis")
    rec = iv.record()
    for key in ("region_boundary_interval_id", "candidate_vector_object_ids",
                "chosen_vector_object_id", "distance_mm",
                "orientation_difference_deg", "support_length_mm",
                "source_type", "validation_class", "reason_chosen",
                "alternatives_rejected"):
        assert key in rec
    assert rec["alternatives_rejected"] == [
        {"object_id": "WB-00043", "reason": "ORIENTATION_DIFFERS_BY_90_DEG"}]


# --- C. the released physical space --------------------------------------

def test_release_needs_every_requirement_and_names_each_failure():
    c = _candidate([so.SRC_VECTOR_WALL_FACE] * 3 + [so.SRC_RASTER_ONLY])
    r = so.assess_release(c, space_id="BTH-09", identity_valid=False)
    assert r.status == so.RELEASE_BLOCKED
    assert so.REQ_SOURCES in r.requirements_failed
    assert so.REQ_NO_UNRESOLVED in r.requirements_failed
    assert so.REQ_IDENTITY in r.requirements_failed
    assert so.REQ_POLYGON in r.requirements_met


def test_a_complete_production_polygon_with_identity_releases():
    c = _candidate([so.SRC_VECTOR_WALL_FACE] * 4)
    r = so.assess_release(c, space_id="BTH-09", identity_valid=True)
    assert r.status == so.RELEASE_ELIGIBLE
    assert not r.requirements_failed
    assert set(r.requirements_met) == set(so.REQUIREMENTS)


def test_a_missing_basis_blocks_release_on_its_own():
    c = _candidate([so.SRC_VECTOR_WALL_FACE] * 4, basis="")
    r = so.assess_release(c, identity_valid=True)
    assert r.requirements_failed == (so.REQ_BASIS,)


def test_an_unapproved_portal_blocks_release():
    """§19: a probable portal may help topology and may not release."""
    c = _candidate([so.SRC_VECTOR_WALL_FACE] * 4)
    r = so.assess_release(c, identity_valid=True,
                          portal_evidence_approved=False,
                          portal_note="PT-1 is PROBABLE on SAME_DRAWING only")
    assert r.status == so.RELEASE_BLOCKED
    assert r.requirements_failed == (so.REQ_PORTALS,)
    assert "SAME_DRAWING" in r.why


def test_a_diagnostic_complete_candidate_does_not_release():
    c = _candidate([so.SRC_VECTOR_WALL_FACE] * 3 + [so.SRC_DIAGNOSTIC_VECTOR])
    r = so.assess_release(c, identity_valid=True)
    assert r.status == so.RELEASE_BLOCKED
    assert r.requirements_failed == (so.REQ_SOURCES,)


def test_release_is_not_an_identity_claim():
    c = _candidate([so.SRC_VECTOR_WALL_FACE] * 4)
    rec = so.assess_release(c, identity_valid=True).record()
    # The key already carries the negation: what_this_is_not = "an
    # identity claim".
    assert rec["what_this_is_not"].startswith("an identity claim")


# --- the three together ---------------------------------------------------

def test_the_three_counts_are_reported_as_incomparable():
    s = so.summary(
        regions=[so.TopologyRegion("RTR-1", "RASTER_SEGMENTATION", 1.0,
                                   (0, 0), (0, 0, 1, 1))],
        candidates=[_candidate([so.SRC_VECTOR_WALL_FACE] * 4)],
        releases=[so.assess_release(
            _candidate([so.SRC_VECTOR_WALL_FACE] * 4), identity_valid=True)])
    assert s["A_TOPOLOGY_REGIONS"]["carries"] == "no released millimetre"
    assert "one funnel" in s["these_counts_are_not_comparable"]
    # Each object answers its own question, and says so.
    assert s["A_TOPOLOGY_REGIONS"]["answers"] != s[
        "B_MEASURED_SPACE_CANDIDATES"]["answers"]
    assert s["C_RELEASED_PHYSICAL_SPACES"]["release_eligible"] == 1


def test_a_topology_region_cannot_be_passed_where_a_candidate_is_required():
    """The separation is a type boundary, not a status convention."""
    r = so.TopologyRegion("RTR-1", "RASTER_SEGMENTATION", 21.4, (0, 0),
                          (0, 0, 1, 1))
    with pytest.raises(AttributeError):
        so.assess_release(r, identity_valid=True)
