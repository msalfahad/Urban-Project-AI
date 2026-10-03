"""Synthetic face sets for the wall-treatment engine. No P7757 value."""

from __future__ import annotations

import pytest

from engine import wall_face_set as FS
from engine import wall_treatment_engine as E
from research.a21_trace_sufficiency_01 import parameters as PM

PL = "NORMAL_INTERNAL_PLASTER"


def _face(fid, L, role="WALL_FACE", status="TRACE_ESTABLISHED",
          basis="PRINTED_DIMENSION", obj=None, **kw):
    return {"FACE_ID": fid, "PHYSICAL_OBJECT_ID": obj or f"PO:{fid}",
            "MATERIAL_ROLE": role, "SIDE": "INTERNAL", "length_m": L,
            "length_source": "DRAWING_PRINTED_DIMENSION" if L is not None else None,
            "length_basis": basis if L is not None else None,
            "VISUAL_TRACE_STATUS": status, "trace_ids": [fid], **kw}


def _reg(h=3.0):
    reg = PM.default_registry()
    reg = PM.with_owner_value(reg, "NORMAL_INTERNAL_PLASTER_HEIGHT", h, "m", 2, "synthetic")
    reg["DOOR_WIDTH"] = PM.parameter("DOOR_WIDTH", 1.0, "m", "TEMPORARY_DEFAULT", "t",
                                     default_or_actual="DEFAULT")
    reg["WINDOW_WIDTH"] = PM.parameter("WINDOW_WIDTH", 1.5, "m", "TEMPORARY_DEFAULT", "t",
                                       default_or_actual="DEFAULT")
    reg["DOOR_REVEAL_DEPTH"] = PM.parameter("DOOR_REVEAL_DEPTH", 0.15, "m",
                                            "TEMPORARY_DEFAULT", "t", default_or_actual="DEFAULT")
    reg["STEEL_PROFILE_RULE"] = PM.parameter("STEEL_PROFILE_RULE", None, None, "UNKNOWN", "n")
    return reg


def test_face_set_needs_no_ring_and_keeps_three_buckets_apart():
    faces = [_face("A", 4.0), _face("B", 3.0), _face("C", 2.0, status="TRACE_PROVISIONAL"),
             _face("D", None), _face("G", 5.0, role="GLAZING"),
             _face("X", 2.5, role="OPEN_BALUSTRADE")]
    fs = FS.build_face_set(set_id="S", faces=faces, openings=[], trade=PL,
                           basis="WALL_FACE_SET")
    assert fs["NO_CLOSED_POLYGON_REQUIRED"] is True
    assert fs["GROSS_BASIS"]["ESTABLISHED_LM"] == 7.0
    assert fs["GROSS_BASIS"]["PROVISIONAL_LM"] == 2.0
    assert {f["FACE_ID"] for f in fs["UNRESOLVED_FACES"]} == {"D"}
    assert {f["FACE_ID"] for f in fs["EXCLUDED_FACES"]} == {"G", "X"}
    assert fs["COVERAGE_STATUS"] == "PARTIAL"
    assert fs["COMPLETE_TOTAL_STATUS"] == "NOT_ESTABLISHED"
    assert fs["THE_ESTABLISHED_SUBTOTAL_IS_NOT_THE_TOTAL"] is True


def test_traced_subset_can_never_claim_a_complete_total():
    fs = FS.build_face_set(set_id="S", faces=[_face("A", 4.0)], openings=[],
                           trade=PL, basis="WALL_FACE_SET")
    assert fs["COMPLETE_TOTAL_STATUS"] == "NOT_ESTABLISHED"
    assert any(u["FACE_ID"] == "*" for u in fs["UNRESOLVED_SCOPE"])
    full = FS.build_face_set(set_id="S", faces=[_face("A", 4.0)], openings=[],
                             trade=PL, basis="WALL_FACE_SET",
                             set_completeness="ALL_FACES_DECLARED")
    assert full["COMPLETE_TOTAL_STATUS"] == "ESTABLISHED"


def test_owner_height_gives_owner_parametric_established_subtotal():
    faces = [_face("A", 4.0), _face("B", 3.0)]
    fs = FS.build_face_set(set_id="S", faces=faces, openings=[], trade=PL,
                           basis="WALL_FACE_SET")
    r = E.calculate(fs, _reg(3.0), treatment=PL)
    assert r["RESULT"]["ESTABLISHED_SUBTOTAL_M2"] == 21.0
    assert r["QUANTITY_STATE"]["ESTABLISHED_SUBTOTAL"] == "OWNER_PARAMETRIC_QUANTITY"
    assert r["QUANTITY_STATE"]["REVEALS_AND_RETURNS"] == "NOT_APPLICABLE"
    assert r["RESULT"]["COMPLETE_TOTAL_STATUS"] == "NOT_ESTABLISHED"
    assert r["DOUBLE_COUNT_GUARD"]["GUARD_STATUS"] == "CLEAN"


def test_opening_on_established_face_is_deducted_with_reveal_and_profiles_eligible():
    faces = [_face("A", 4.0)]
    door = {"OPENING_ID": "D1", "TYPE": "DOOR", "HOSTED_IN": "A", "width_m": None,
            "width_source": None, "height_m": None, "height_source": None}
    fs = FS.build_face_set(set_id="S", faces=faces, openings=[door], trade=PL,
                           basis="WALL_FACE_SET")
    r = E.calculate(fs, _reg(3.0), treatment=PL)
    # 4.0 x 3.0 = 12.0 less 1.0 x 2.2 = 9.8 ; door default -> provisional
    assert r["RESULT"]["ESTABLISHED_SUBTOTAL_M2"] == 9.8
    assert r["QUANTITY_STATE"]["ESTABLISHED_SUBTOTAL"] == "PROVISIONAL_DEFAULT_QUANTITY"
    # reveal (2 x 2.2 + 1.0) x 0.15 = 0.81
    assert r["RESULT"]["REVEALS_AND_RETURNS_M2"] == 0.81
    assert r["RESULT"]["PROFILE_ELIGIBLE_LM"]["DOOR_JAMB"] == 4.4
    assert r["RESULT"]["PROFILE_ELIGIBLE_LM"]["DOOR_HEAD"] == 1.0
    assert r["QUANTITY_STATE"]["STEEL_PROFILES"] == "NOT_ESTABLISHED"   # rule UNKNOWN


def test_opening_on_unresolved_face_is_not_deducted_anywhere():
    faces = [_face("A", 4.0), _face("B", None)]
    door = {"OPENING_ID": "D1", "TYPE": "DOOR", "HOSTED_IN": "B"}
    fs = FS.build_face_set(set_id="S", faces=faces, openings=[door], trade=PL,
                           basis="WALL_FACE_SET")
    r = E.calculate(fs, _reg(3.0), treatment=PL)
    assert r["RESULT"]["ESTABLISHED_SUBTOTAL_M2"] == 12.0
    assert any(l["LINE"] == "UNRESOLVED_OPENING" for l in r["SHEET"])


def test_actual_reveal_depth_wins_over_the_default():
    faces = [_face("A", 4.0)]
    door = {"OPENING_ID": "D1", "TYPE": "DOOR", "HOSTED_IN": "A", "width_m": 1.0,
            "width_source": "DRAWING_PRINTED_DIMENSION", "height_m": 2.0,
            "height_source": "DRAWING_PRINTED_DIMENSION", "reveal_depth_m": 0.2,
            "reveal_depth_source": "DRAWING_PRINTED_DIMENSION"}
    fs = FS.build_face_set(set_id="S", faces=faces, openings=[door], trade=PL,
                           basis="WALL_FACE_SET")
    r = E.calculate(fs, _reg(3.0), treatment=PL)
    rv = next(l for l in r["SHEET"] if l["LINE"] == "REVEAL")
    assert rv["DEPTH_M"] == 0.2 and rv["DEPTH_SOURCE"] == "DRAWING_PRINTED_DIMENSION"
    assert r["QUANTITY_STATE"]["REVEALS_AND_RETURNS"] == "SOURCE_ESTABLISHED_QUANTITY"


def test_normal_height_is_not_propagated_to_double_height_or_parapets():
    reg = _reg(3.0)
    faces = [_face("A", 4.0)]
    fs = FS.build_face_set(set_id="S", faces=faces, openings=[],
                           trade="DOUBLE_HEIGHT_PLASTER", basis="WALL_FACE_SET")
    r = E.calculate(fs, reg, treatment="DOUBLE_HEIGHT_PLASTER")
    assert r["RESULT"]["ESTABLISHED_SUBTOTAL_M2"] is None
    assert r["QUANTITY_STATE"]["ESTABLISHED_SUBTOTAL"] == "NOT_ESTABLISHED"
    par = [_face("P", 6.0, role="PARAPET_SOLID_FACE")]           # no traced height
    fsp = FS.build_face_set(set_id="P", faces=par, openings=[],
                            trade="ROOF_PARAPET_EXTERNAL_FACE", basis="LINEAR_SURFACE_RUN")
    rp = E.calculate(fsp, reg, treatment="ROOF_PARAPET_EXTERNAL_FACE")
    assert rp["RESULT"]["ESTABLISHED_SUBTOTAL_M2"] is None
    par2 = [_face("P", 6.0, role="PARAPET_SOLID_FACE", height_m=0.5,
                  height_source="DRAWING_PRINTED_DIMENSION")]
    fsp2 = FS.build_face_set(set_id="P", faces=par2, openings=[],
                             trade="ROOF_PARAPET_EXTERNAL_FACE", basis="LINEAR_SURFACE_RUN")
    rp2 = E.calculate(fsp2, reg, treatment="ROOF_PARAPET_EXTERNAL_FACE")
    assert rp2["RESULT"]["ESTABLISHED_SUBTOTAL_M2"] == 3.0
    assert rp2["QUANTITY_STATE"]["ESTABLISHED_SUBTOTAL"] == "SOURCE_ESTABLISHED_QUANTITY"


def test_external_plaster_takes_the_floor_storey_height_and_never_invents_joints():
    reg = _reg(3.0)
    reg = PM.with_owner_value(reg, "EXTERNAL_STOREY_HEIGHT_GROUND", 4.0, "m", 2, "synthetic")
    reg["CONTROL_JOINT_RULE"] = PM.parameter("CONTROL_JOINT_RULE", None, None, "UNKNOWN", "n")
    fs = FS.build_face_set(set_id="F", faces=[_face("A", 10.0)], openings=[],
                           trade="EXTERNAL_PLASTER", basis="LINEAR_SURFACE_RUN", floor="GROUND")
    r = E.calculate(fs, reg, treatment="EXTERNAL_PLASTER")
    assert r["RESULT"]["ESTABLISHED_SUBTOTAL_M2"] == 40.0
    cj = next(l for l in r["SHEET"] if l["LINE"] == "CONTROL_JOINTS")
    assert cj["VALUE"] is None
    assert r["QUANTITY_STATE"]["CONTROL_JOINTS"] == "NOT_ESTABLISHED"
    r1 = E.calculate(FS.build_face_set(set_id="F", faces=[_face("A", 10.0)], openings=[],
                                       trade="EXTERNAL_PLASTER", basis="LINEAR_SURFACE_RUN",
                                       floor="FIRST"), reg, treatment="EXTERNAL_PLASTER")
    assert r1["RESULT"]["ESTABLISHED_SUBTOTAL_M2"] is None   # FIRST height not given here


def test_capping_uses_width_and_a_closed_region_basis_is_refused_here():
    reg = _reg(3.0)
    cap = [_face("C", 7.0, role="CAPPING_BAND", width_m=0.2,
                 width_source="DRAWING_PRINTED_DIMENSION")]
    fs = FS.build_face_set(set_id="C", faces=cap, openings=[],
                           trade="ROOF_PARAPET_CAPPING", basis="LINEAR_SURFACE_RUN")
    r = E.calculate(fs, reg, treatment="ROOF_PARAPET_CAPPING")
    assert r["RESULT"]["ESTABLISHED_SUBTOTAL_M2"] == 1.4
    with pytest.raises(ValueError):
        FS.build_face_set(set_id="X", faces=[], openings=[], trade=PL, basis="CLOSED_REGION")


def test_guard_blocks_a_balustrade_face_and_a_duplicate_object_face():
    reg = _reg(3.0)
    faces = [_face("A", 4.0, obj="PO-1"), _face("A2", 4.0, obj="PO-1")]   # same object+side
    fs = FS.build_face_set(set_id="S", faces=faces, openings=[], trade=PL,
                           basis="WALL_FACE_SET")
    r = E.calculate(fs, reg, treatment=PL)
    assert r["DOUBLE_COUNT_GUARD"]["GUARD_STATUS"] == "CONFLICTS_FOUND"
    assert r["DOUBLE_COUNT_GUARD"]["CONFLICTS"][0]["CONFLICT"] == "DUPLICATE_PHYSICAL_CONTRIBUTION"
