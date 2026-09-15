"""E54 — a closed polygon is not a room, and a label nearby is not proof."""

from __future__ import annotations

import pytest

from engine.space_identity import (AMBIGUOUS_GEOMETRIC_FACE,
                                   E_ADJACENCY, E_LABEL_ANCHOR,
                                   E_PRINTED_DIMENSIONS,
                                   E_RASTER_CORRESPONDENCE, E_ROOM_SCHEDULE,
                                   IDENTITY_AMBIGUOUS, IDENTITY_PROBABLE,
                                   IDENTITY_REJECTED, IDENTITY_UNRESOLVED,
                                   IDENTITY_VALIDATED, NOT_ACCEPTED,
                                   PHYSICAL_SPACE_GEOMETRY_ACCEPTED,
                                   VALIDATED_GEOMETRIC_FACE, SpaceIdentity,
                                   identity_status, summary)


def verdict(geometry=VALIDATED_GEOMETRIC_FACE, evidence=(), rejected_by="",
            space="BED-03"):
    status, why = identity_status(
        {__import__("engine.space_identity", fromlist=["x"]).EVIDENCE_FAMILY[e]
         for e in evidence}, rejected_by=rejected_by)
    return SpaceIdentity("SF-1", space, geometry, status,
                         identity_evidence=tuple(evidence),
                         rejected_by=rejected_by, why_identity=why)


# --- the WSH-01 regression --------------------------------------------------

def test_a_valid_cycle_around_a_shaft_is_not_a_validated_washroom():
    """The regression: a genuinely sound 1.981 m2 cycle was reported as a
    VALIDATED_PHYSICAL_FACE for WSH-01. The cycle was probably a perfectly
    good shaft; the washroom's geometry was never recovered."""
    v = verdict(evidence=(E_LABEL_ANCHOR, E_RASTER_CORRESPONDENCE),
                rejected_by="region identity FAILED: the region is the hatched "
                            "shaft beside the wash room",
                space="WSH-01")
    assert v.geometry_status == VALIDATED_GEOMETRIC_FACE
    assert v.identity_status == IDENTITY_REJECTED
    assert v.acceptance == NOT_ACCEPTED
    assert "the geometry is sound and the identity is not" in v.why_not_accepted


def test_a_rejection_outranks_any_amount_of_supporting_evidence():
    """The support is exactly what was mistaken."""
    v = verdict(evidence=(E_LABEL_ANCHOR, E_RASTER_CORRESPONDENCE,
                          E_ADJACENCY, E_PRINTED_DIMENSIONS),
                rejected_by="a reviewer says this region is not that room")
    assert v.identity_status == IDENTITY_REJECTED


# --- one label is a candidate, never a validation ---------------------------

def test_one_semantic_label_inside_a_cycle_is_ambiguous():
    """It can still be a shaft, a closet, an adjacent enclosure, a wrongly
    nested cycle or the wrong side of a wall."""
    status, why = identity_status({"SEMANTIC"})
    assert status == IDENTITY_AMBIGUOUS
    assert "wrong side of a wall" in why


def test_centroid_containment_alone_never_reaches_acceptance():
    v = verdict(evidence=(E_LABEL_ANCHOR,))
    assert v.identity_status == IDENTITY_AMBIGUOUS
    assert not v.accepted


def test_a_label_plus_an_independent_raster_region_is_probable():
    v = verdict(evidence=(E_LABEL_ANCHOR, E_RASTER_CORRESPONDENCE))
    assert v.identity_status == IDENTITY_PROBABLE
    assert v.accepted


def test_a_label_plus_a_document_validates():
    v = verdict(evidence=(E_LABEL_ANCHOR, E_ROOM_SCHEDULE))
    assert v.identity_status == IDENTITY_VALIDATED


def test_no_evidence_is_unresolved_not_rejected():
    """'Nobody looked' and 'we looked and it is wrong' are different facts."""
    assert identity_status(set())[0] == IDENTITY_UNRESOLVED


def test_more_evidence_never_lowers_an_identity():
    weak = identity_status({"SEMANTIC", "RASTER"})[0]
    strong = identity_status({"SEMANTIC", "RASTER", "TOPOLOGY"})[0]
    from engine.space_identity import IDENTITY_RANK
    assert IDENTITY_RANK[strong] >= IDENTITY_RANK[weak]


# --- the two axes are required together -------------------------------------

def test_acceptance_needs_both_axes():
    good_geo_bad_id = verdict(evidence=(E_LABEL_ANCHOR,))
    assert not good_geo_bad_id.accepted

    bad_geo_good_id = verdict(geometry=AMBIGUOUS_GEOMETRIC_FACE,
                              evidence=(E_LABEL_ANCHOR,
                                        E_RASTER_CORRESPONDENCE))
    assert not bad_geo_good_id.accepted
    assert "no sound polygon" in bad_geo_good_id.why_not_accepted

    both = verdict(evidence=(E_LABEL_ANCHOR, E_RASTER_CORRESPONDENCE))
    assert both.acceptance == PHYSICAL_SPACE_GEOMETRY_ACCEPTED


def test_the_summary_counts_the_two_axes_separately():
    vs = [verdict(evidence=(E_LABEL_ANCHOR, E_RASTER_CORRESPONDENCE)),
          verdict(evidence=(E_LABEL_ANCHOR,), space="WSH-01",
                  rejected_by="the region is the shaft beside it")]
    out = summary(vs)
    assert out["physical_space_geometry_accepted"] == 1
    assert out["identity_rejected"] == 1
    assert out["geometry_sound_identity_not"] == 1
    assert "closed polygon plus a nearby label" in out["note"]
