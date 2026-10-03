"""E64 — raster challenges the vector result and supplies no millimetre."""

from __future__ import annotations

from dataclasses import dataclass

from engine.document_observations import (PRINTED_DIMENSION, ROOM_LABEL,
                                          USE_FOR_IDENTITY, USE_FOR_SIZE,
                                          ObservationError,
                                          PrintedDimensionObservation,
                                          TextObservation, readiness)
from engine.topology_signals import (AGREES, MISSING_WALL_HYPOTHESIS,
                                     RASTER_ONLY, RASTER_SPLITS_VECTOR,
                                     SPACE_SEPARATION_HYPOTHESIS, VECTOR_ONLY,
                                     compare_topology,
                                     segmentation_vs_validated)


@dataclass(frozen=True)
class C:
    space_geometry_id: str
    area_m2: float = 12.0
    geometry_role: str = "OCCUPIABLE_SPACE_CANDIDATE"
    holds: tuple = ()


def regions(*pairs):
    return {i: {"space_id": s, "centroid_mm": (float(i), 0.0)}
            for i, s in enumerate(pairs, 1)}


def contains(c, pt):
    return pt[0] in c.holds


def test_one_region_in_one_component_is_agreement():
    cands = [C("SG-1", holds=(1.0,))]
    _, out = compare_topology(cands, regions("BED-01"), contains=contains)
    assert out["by_relationship"][AGREES] == 1


def test_two_regions_in_one_component_is_a_missing_wall_hypothesis():
    """The cheapest lead on the sheet — and it is a LEAD, not a boundary."""
    cands = [C("SG-1", holds=(1.0, 2.0))]
    hyps, out = compare_topology(cands, regions("BED-NW", "BTH-01"),
                                 contains=contains)
    assert out["by_relationship"][RASTER_SPLITS_VECTOR] == 1
    assert hyps[0].kind == MISSING_WALL_HYPOTHESIS
    assert hyps[0].labelled_space_ids == ("BED-NW", "BTH-01")
    assert hyps[0].may_supply_measurement is False
    assert "may NOT supply the boundary itself" in hyps[0].why


def test_a_region_in_no_component_is_its_own_hypothesis():
    cands = [C("SG-1", holds=())]
    hyps, out = compare_topology(cands, regions("STR-01"), contains=contains)
    assert out["by_relationship"][RASTER_ONLY] == 1
    assert hyps[0].kind == SPACE_SEPARATION_HYPOTHESIS


def test_a_component_with_no_region_is_vector_only():
    cands = [C("SG-1", holds=())]
    _, out = compare_topology(cands, {}, contains=contains)
    assert out["by_relationship"][VECTOR_ONLY] == 1


def test_no_hypothesis_may_ever_supply_a_measurement():
    cands = [C("SG-1", holds=(1.0, 2.0))]
    hyps, out = compare_topology(cands, regions("A", "B"), contains=contains)
    assert all(not h.may_supply_measurement for h in hyps)
    assert any("millimetre" in m for m in out["raster_may_not"])


# --- §10 the distinction that matters before generalisation -----------------

def test_automatic_segmentation_and_human_validation_are_counted_apart():
    """Quoting 35 human-validated regions as automatic accuracy would credit
    the algorithm with a person's work."""
    out = segmentation_vs_validated(
        auto_regions=36, auto_labelled=36, human_identity_validated=35,
        human_topology_validated=33, validation_source="topology_overlay.json")
    auto = out["RASTER_SEGMENTATION_OUTPUT"]
    human = out["HUMAN_OR_GOLDEN_VALIDATED_REGION_STATE"]
    assert auto["automatic_accuracy_established"] is False
    assert auto["regions_produced"] == 36
    assert human["identity_validated"] == 35
    assert "circular" in out["do_not_conflate"]
    assert "human column starts empty" in out["do_not_conflate"]


# --- §11 evidence roles are fixed before the extraction exists --------------

def test_a_printed_dimension_is_size_evidence_and_never_identity():
    """A bedroom and a bathroom can both be 3.50 m wide."""
    d = PrintedDimensionObservation("PD-1", "3.50", 3500.0, "m", "H")
    assert d.kind == PRINTED_DIMENSION
    assert d.may_be_used_for(USE_FOR_SIZE)
    assert not d.may_be_used_for(USE_FOR_IDENTITY)
    d.require_use(USE_FOR_SIZE)
    try:
        d.require_use(USE_FOR_IDENTITY)
    except ObservationError as exc:
        assert "3.50 m wide" in str(exc)
    else:
        raise AssertionError("a dimension must not carry identity")


def test_an_unparsed_dimension_has_no_value_which_is_not_zero():
    d = PrintedDimensionObservation("PD-1", "3.5O")
    assert d.parsed_value_mm is None
    assert not d.is_parsed


def test_a_room_label_is_identity_evidence_and_never_size():
    t = TextObservation("TX-1", ROOM_LABEL, "BEDROOM 1")
    assert t.may_be_used_for(USE_FOR_IDENTITY)
    assert not t.may_be_used_for(USE_FOR_SIZE)


def test_the_readiness_report_says_no_extraction_exists_yet():
    out = readiness([])
    assert out["extraction_status"] == "MODEL_ONLY_NO_EXTRACTION_BUILT"
    assert out["evidence_roles"][PRINTED_DIMENSION] == [USE_FOR_SIZE]
