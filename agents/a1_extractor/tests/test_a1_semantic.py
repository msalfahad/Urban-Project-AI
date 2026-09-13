"""A1 as the semantic agent: it attaches meaning and never returns a number."""

from __future__ import annotations

import pytest

from agents.a1_extractor.semantic import (SemanticError, SemanticOutput,
                                          SpaceSemantics)


def rec(**kw):
    base = dict(space_id="S1", semantic_label="BEDROOM", label_source="PDF_TEXT",
                label_confidence="HIGH", confidence_basis="text + polygon + schedule",
                scope_status="IN_SCOPE")
    base.update(kw)
    return base


def test_a_valid_record_parses():
    out = SemanticOutput.from_dict({"spaces": [rec()]})
    assert out.spaces[0].semantic_label == "BEDROOM"


@pytest.mark.parametrize("key", ["area_m2", "perimeter_m", "width_mm", "polygon", "dimensions"])
def test_any_geometry_field_is_refused(key):
    """A1 cannot edit E23/E25 because the schema gives it nowhere to put a number."""
    with pytest.raises(SemanticError, match="belongs to E23/E25"):
        SemanticOutput.from_dict({"spaces": [rec(**{key: 12.5})]})


def test_a_geometry_challenge_is_the_allowed_way_to_object():
    out = SemanticOutput.from_dict({"spaces": [rec(geometry_challenge="region looks clipped")]})
    assert out.spaces[0].geometry_challenge


def test_confidence_must_name_its_evidence():
    with pytest.raises(SemanticError, match="must name the evidence"):
        SemanticOutput.from_dict({"spaces": [rec(confidence_basis="  ")]})


def test_a_vision_only_label_cannot_be_high_confidence():
    with pytest.raises(SemanticError, match="cannot rest on VISION_MODEL alone"):
        SemanticOutput.from_dict({"spaces": [rec(label_source="VISION_MODEL")]})


def test_no_label_source_caps_the_confidence():
    with pytest.raises(SemanticError, match="no label source"):
        SemanticOutput.from_dict({"spaces": [rec(label_source="UNKNOWN",
                                                 label_confidence="MEDIUM")]})


def test_an_unknown_semantic_label_is_refused():
    with pytest.raises(SemanticError, match="not one of"):
        SemanticOutput.from_dict({"spaces": [rec(semantic_label="SNUG")]})


def test_a_space_cannot_be_classified_twice():
    with pytest.raises(SemanticError, match="classified twice"):
        SemanticOutput.from_dict({"spaces": [rec(), rec()]})


def test_a_space_cannot_be_both_a_room_and_not_a_room():
    with pytest.raises(SemanticError, match="both classified and marked"):
        SemanticOutput.from_dict({"spaces": [rec()], "not_a_space": ["S1"]})


def test_covers_reports_the_spaces_left_semantically_invisible():
    out = SemanticOutput.from_dict({"spaces": [rec()], "not_a_space": ["S2"]})
    assert out.covers(["S1", "S2", "S3"]) == ["S3"]


def test_the_iron_room_trap_records_the_conflict_rather_than_following_the_old_name():
    """AR-00 says كوي IRON; the old qiyal calls the same space مطبخ."""
    out = SemanticOutput.from_dict({"spaces": [rec(
        space_id="IRN-01", semantic_label="IRON_ROOM",
        original_drawing_label="كوي IRON",
        semantic_conflicts=["historical takeoff labels this space مطبخ (kitchen)"],
    )]})
    s = out.spaces[0]
    assert s.semantic_label == "IRON_ROOM" and s.semantic_conflicts


def test_an_out_of_scope_space_still_gets_a_record():
    out = SemanticOutput.from_dict({"spaces": [rec(
        space_id="TRC-01", semantic_label="TERRACE", scope_status="OUT_OF_SCOPE")]})
    assert out.spaces[0].scope_status == "OUT_OF_SCOPE"
