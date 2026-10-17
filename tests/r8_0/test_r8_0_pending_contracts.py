"""R8.0 contracts for modules that do not exist yet (TARGET_NOT_IMPLEMENTED).

Each row is: id, fixture/mutation, target (see targets.py), inputs, and the
REQUIRED outcome. Expectations are structural (statuses, roles, refusals);
none is a quantity, total, room reference or project answer. Real-source
rows (MT-22, MT-33) take their source only from the environment variable
URBAN_R8_REAL_SOURCE and assert behaviour, never a count.

Result access: dotted paths into the returned dict ("DET.status"), integer
segments index lists ("rejected.0.reason").
"""

from __future__ import annotations

import os

import pytest

from . import libredwg_builder as B, targets
from .test_r8_0_digests import DIRECT_WCS


def _dec(scene):
    return B.build(scene)


def _drop_line(scene):
    ents = list(scene["entities"])
    i = next(i for i, e in enumerate(ents) if e["kind"] == "LINE")
    return dict(scene, entities=ents[:i] + ents[i + 1:])


def _move_line(scene, mm):
    ents = [dict(e) for e in scene["entities"]]
    i = next(i for i, e in enumerate(ents) if e["kind"] == "LINE")
    ents[i]["b"] = (ents[i]["b"][0] + mm, ents[i]["b"][1])
    return dict(scene, entities=ents)


CAD_TWO_VIEWS = {"kind": "CAD", "layouts": {"MODEL": {}, "PAPER": {"viewports": [{"id": "VP1", "scale": 1 / 50}]}}}
TWO_REGIONS = {"kind": "CAD", "regions": [{"id": "R1", "scale_evidence": ["SCALE_TEXT_1:100", "DIMENSION_FAMILY_A"]},
                                          {"id": "R2", "scale_evidence": ["SCALE_TEXT_1:50", "DIMENSION_FAMILY_B"]}]}
DETAIL_X5 = {"kind": "CAD", "regions": [{"id": "DET", "scale_text": "DETAIL 1:10 (x5 of plan 1:50)", "dimlfac": 0.2,
                                          "dimensions": [{"geometry_native": 1000.0, "display": 200.0}]}]}
DETAIL_NO_EVIDENCE = {"kind": "CAD", "regions": [{"id": "DET2", "enlarged_geometry": True, "local_evidence": []}]}

W = {"wall_ground_external": {"WALL_ROLE": "EXTERNAL", "FLOOR": "GROUND"},
     "wall_ground_internal": {"WALL_ROLE": "INTERNAL_PARTITION", "FLOOR": "GROUND"}}

CONTRACTS = [
    # ------------------------------------------------ frames and units (stage B)
    ("F15", "FRAMES", dict(source=CAD_TWO_VIEWS),
     {"VP1.kind": "VIEWPORT_FRAME", "VP1.parent": "MODEL", "VP1.measurement_allowed": False, "MODEL.measurement_allowed": True}),
    ("MT-26", "FRAMES", dict(source=CAD_TWO_VIEWS, measure_in="VP1"),
     {"refused": True, "reason": "MEASURE_IN_MODEL_FRAME"}),
    ("F16", "FRAMES", dict(source=TWO_REGIONS),
     {"frame_count": 2, "R1.independently_statused": True, "R2.independently_statused": True}),
    ("MT-08", "FRAMES", dict(source=TWO_REGIONS, overrides=[{"region": "R1", "status": "VERIFIED", "by": "AGENT"}]),
     {"override_rejected": True, "R1.status_set_by_agent": False}),
    ("F17", "UNIT_CONTEXT", dict(header={"INSUNITS": 1}, evidence=[{"kind": "GEOMETRY_PLAUSIBILITY", "suggests": "METRE"}]),
     {"status": "PROVISIONAL", "final_allowed": False, "conflict": True}),
    ("MT-07", "UNIT_CONTEXT", dict(header={"INSUNITS": 1}, evidence=[{"kind": "PRINTED_DIMENSION", "display_mm": 3000.0, "geometry_native": 3000.0}]),
     {"status": "CONFLICT", "native_unit_to_mm": None, "final_allowed": False}),
    ("MT-32", "UNIT_CONTEXT", dict(header={"INSUNITS": 1}, evidence=[{"kind": "GEOMETRY_PLAUSIBILITY", "suggests": "METRE"},
                                                                     {"kind": "GEOMETRY_PLAUSIBILITY", "suggests": "METRE"}]),
     {"status": "PROVISIONAL", "plausibility_counted_toward_verified": False}),
    ("MT-51", "UNIT_CONTEXT", dict(header={"INSUNITS": 4}, evidence=[{"kind": "INFERRED_UNIT", "suggests": "METRE", "producer": "GEOMETRY_PLAUSIBILITY"}]),
     {"status": "CONFLICT", "inferred_unit_applied": False, "final_allowed": False}),
    ("F30", "UNIT_CONTEXT", dict(raster={"dpi": 300, "page_size_in": [11.0, 17.0], "pixels": [2000, 2000]}),
     {"status": "CONFLICT"}),
    ("MT-23", "FRAMES", dict(source={"kind": "CAD", "regions": [{"id": "D1", "native_unit_to_mm": 1.0}]}),
     {"rejected": True, "rule": "U-1"}),
    ("F26", "FRAMES", dict(source=DETAIL_X5),
     {"DET.real_per_presented": 0.2, "DET.status": "VERIFIED", "DET.unit_context": "PARENT"}),
    ("MT-24", "FRAMES", dict(source=DETAIL_X5, force={"DET": {"real_per_presented": 1.0}}),
     {"DET.status": "CONFLICT"}),
    ("F27", "FRAMES", dict(source=DETAIL_NO_EVIDENCE), {"DET2.status": "BLOCKED", "DET2.rule": "U-2"}),
    ("MT-25", "FRAMES", dict(source=DETAIL_NO_EVIDENCE, accept_enlargement=True), {"DET2.status": "BLOCKED"}),
    ("F28", "FRAME_EVIDENCE", dict(evidence=[{"kind": "AUTO_DIMENSION", "dimstyle": "A"}] * 3), {"independent_set_size": 0}),
    ("MT-27", "FRAME_EVIDENCE", dict(evidence=[{"kind": "AUTO_DIMENSION", "dimstyle": "A", "claimed_independent": True}] * 3),
     {"independent_set_size": 0}),
    ("MT-28", "FRAME_EVIDENCE", dict(evidence=[{"kind": "OVERRIDDEN_DIMENSION_TEXT", "dimstyle": "A"},
                                               {"kind": "OVERRIDDEN_DIMENSION_TEXT", "dimstyle": "B"}]),
     {"families": 1}),
    ("F29", "FRAME_EVIDENCE", dict(evidence=[{"kind": "OVERRIDDEN_DIMENSION_TEXT", "dimstyle": "A"}]),
     {"members.0.family": "DOCUMENT_SOURCE", "independent_set_size": 1}),
    ("MT-29", "FRAME_EVIDENCE", dict(evidence=[{"kind": "DWG_GEOMETRY"}, {"kind": "PDF_PLOT", "plot_of": "DWG_GEOMETRY"}]),
     {"independent_set_size": 1, "rejected.0.reason": "SHARED_SOURCE_PRIMITIVE"}),
    ("F18", "FRAMES", dict(source={"kind": "VECTOR_PDF", "page_rotation_deg": 270, "scale_bar": {"length_pt": 100.0, "label_m": 5.0}}),
     {"PAGE.rotation_deg": 270, "PAGE.scale_bar_is_evidence": True}),
    ("MT-30", "FRAME_EVIDENCE", dict(evidence=[{"kind": "VECTOR_PAGE"}, {"kind": "RASTER_RENDER", "of": "VECTOR_PAGE"}]),
     {"independent_set_size": 1}),
    ("MT-44", "SOURCE_PROFILE", dict(profile="VECTOR_PDF_PROFILE", request="FINAL", profile_implemented=False), {"release": "PREVIEW"}),
    ("MT-45", "SOURCE_PROFILE", dict(profile="RASTER_PDF_PROFILE", request="FINAL", bound_px=2, mm_per_px=10.0, item_tolerance_mm=5.0),
     {"release": "PREVIEW"}),
    ("MT-46", "SOURCE_PROFILE", dict(profile="CAD_PROFILE", request="FINAL", checks={"V-CAD-1": "FAIL"}), {"release": "PREVIEW"}),
    ("MT-09", "PUBLISH_WITH_FRAME", dict(rows=[{"id": "r1", "value": 10.0, "frame_status": "PROVISIONAL"},
                                               {"id": "r2", "value": 5.0, "frame_status": "VERIFIED"}]),
     {"subtotal": None, "state": "BLOCKED", "violations.0": "r1"}),
    # ---------------------------------------------- reconciliation (stage A)
    ("MT-05", "RECONCILE", dict(route_a={"decode": _dec(DIRECT_WCS)}, route_b={"decode": _dec(_drop_line(DIRECT_WCS))}),
     {"verdict": "BLOCK", "field_class": "PRESENCE"}),
    ("MT-06", "RECONCILE", dict(route_a={"decode": _dec(DIRECT_WCS)}, route_b={"decode": _dec(_move_line(DIRECT_WCS, 1.0))}),
     {"verdict": "SOURCE_DECODE_CONFLICT", "scope": "SOURCE"}),
    # ------------------------------------------------ fact policy (stage C)
    ("MT-10", "CLAIM_FROM", dict(producer="A2_CHALLENGER", record={"fact_kind": "WINDOW_HEIGHT", "value": 2.1}),
     {"__raises__": "ProducerNotAllowed"}),
    ("MT-11", "FACT_POLICY_RESOLVE", dict(fact_kind="WALL_MATERIAL", mode="PROJECT_EVIDENCE_ONLY", subject={},
                                          claims=[{"evidence_kind": "SOURCE_GEOMETRY_MEASURED", "basis": "THICKNESS", "value": "BLOCKWORK"}]),
     {"status": "NOT_ESTABLISHED", "inadmissible.0": 0}),
    ("MT-12a", "FACT_POLICY_RESOLVE", dict(fact_kind="PROJECT_SCOPE", mode="PROJECT_EVIDENCE_ONLY", subject={},
                                           claims=[{"evidence_kind": "URBAN_STANDARD", "value": "INCLUDED"}]),
     {"status": "NOT_ESTABLISHED"}),
    ("MT-12b", "FACT_POLICY_RESOLVE", dict(fact_kind="PROJECT_SCOPE", mode="STANDARD_ASSISTED", subject={},
                                           claims=[{"evidence_kind": "URBAN_STANDARD", "value": "INCLUDED"}]),
     {"status": "NOT_ESTABLISHED"}),
    ("MT-13", "FACT_POLICY_RESOLVE", dict(fact_kind="WINDOW_HEIGHT", mode="STANDARD_ASSISTED", subject={"OPENING_TYPE": "W1"},
                                          claims=[{"evidence_kind": "URBAN_STANDARD", "value": "STANDARD_VALUE"},
                                                  {"evidence_kind": "SOURCE_SCHEDULE", "value": "SCHEDULE_VALUE", "selector": {"ALL": [{"OPENING_TYPE": "W1"}]}}]),
     {"value": "SCHEDULE_VALUE", "superseded.0": "URBAN_STANDARD"}),
    ("MT-18", "FACT_POLICY_RESOLVE", dict(fact_kind="FACT_KIND_WITH_NO_POLICY", mode="PROJECT_EVIDENCE_ONLY", subject={}, claims=[]),
     {"status": "NOT_ESTABLISHABLE"}),
    ("MT-19", "FACT_POLICY_RESOLVE", dict(fact_kind="WINDOW_HEIGHT", mode="PROJECT_EVIDENCE_ONLY", subject={},
                                          claims=[{"evidence_kind": "EVIDENCE_KIND_NOT_IN_POLICY", "value": "X"}]),
     {"inadmissible.0": 0}),
    ("MT-20", "FACT_POLICY_RESOLVE", dict(fact_kind="WINDOW_HEIGHT", mode="PROJECT_EVIDENCE_ONLY", subject={},
                                          claims=[{"evidence_kind": "SOURCE_SCHEDULE", "value": "A"}, {"evidence_kind": "SOURCE_SCHEDULE", "value": "B"}]),
     {"status": "CONFLICT", "value": None}),
    ("MT-21", "FACT_POLICY_RESOLVE", dict(fact_kind="DOOR_WIDTH", mode="PROJECT_EVIDENCE_ONLY", subject={},
                                          claims=[{"evidence_kind": "SOURCE_SCHEDULE", "basis": "LEAF", "value": "A"},
                                                  {"evidence_kind": "SOURCE_GEOMETRY_MEASURED", "basis": "STRUCTURAL_OPENING", "value": "B"}]),
     {"compared": False, "reason": "DIFFERENT_BASIS"}),
    ("MT-22", "FACT_POLICY_RESOLVE", dict(fact_kind="WINDOW_HEIGHT", mode="R7_COMPATIBLE", subject={}, claims=[],
                                          standards_in_effect_remove=["US-19"], real_source=os.environ.get("URBAN_R8_REAL_SOURCE")),
     {"every_value_answered_only_by_removed_standard_becomes_a_question": True}),
    ("MT-33", "FRAME_EVIDENCE", dict(evidence=None, real_source=os.environ.get("URBAN_R8_REAL_SOURCE")),
     {"status": "PROVISIONAL", "independent_set_size": 1}),
    # --------------------------------------------------- scope (stage C)
    ("F21", "SCOPE_APPLIES", dict(selector={"ALL": [{"WALL_ROLE": "INTERNAL_PARTITION"}]}, subject=W["wall_ground_internal"]),
     {"applies": True}),
    ("MT-34", "SCOPE_APPLIES", dict(selector={"ALL": [{"WALL_ROLE": "INTERNAL_PARTITION"}]}, subject={"WALL_ROLE": None}),
     {"applies": False, "question": "MEMBERSHIP"}),
    ("F22", "SCOPE_APPLIES", dict(selector={"ALL": [{"WALL_TYPE_CODE": "W3"}]}, subject={"WALL_TYPE_CODE": "W3"}), {"applies": True}),
    ("F23", "SCOPE_APPLIES", dict(selector={"ALL": [{"WALL_ROLE": "EXTERNAL"}, {"FLOOR": "GROUND"}]},
                                  subject={"WALL_ROLE": "EXTERNAL", "FLOOR": "FIRST"}), {"applies": False}),
    ("F24", "SCOPE_VALIDATE", dict(selector={"PROJECT_WIDE": True}, tier="OWNER_PROJECT_INPUT"), {"valid": True}),
    ("F24b", "FACT_POLICY_RESOLVE", dict(fact_kind="WALL_MATERIAL", mode="PROJECT_EVIDENCE_ONLY", subject={"WALL_TYPE_CODE": "W3"},
                                         claims=[{"evidence_kind": "OWNER_PROJECT_INPUT", "value": "BLOCKWORK", "selector": {"PROJECT_WIDE": True}},
                                                 {"evidence_kind": "SOURCE_LEGEND", "value": "AAC", "selector": {"ALL": [{"WALL_TYPE_CODE": "W3"}]}}]),
     {"value": "AAC"}),
    ("MT-35", "SCOPE_VALIDATE", dict(selector={"PROJECT_WIDE": True}, tier="URBAN_STANDARD"), {"valid": False}),
    ("MT-36a", "FACT_POLICY_RESOLVE", dict(fact_kind="WALL_MATERIAL", mode="PROJECT_EVIDENCE_ONLY", subject=W["wall_ground_external"],
                                           claims=[{"evidence_kind": "SOURCE_SPECIFICATION", "value": "AAC", "selector": {"ALL": [{"FLOOR": "GROUND"}]}},
                                                   {"evidence_kind": "SOURCE_SPECIFICATION", "value": "BLOCKWORK", "selector": {"ALL": [{"WALL_ROLE": "EXTERNAL"}]}}]),
     {"status": "CONFLICT"}),
    ("MT-36b", "FACT_POLICY_RESOLVE", dict(fact_kind="WALL_MATERIAL", mode="PROJECT_EVIDENCE_ONLY", subject=W["wall_ground_internal"],
                                           claims=[{"evidence_kind": "SOURCE_SPECIFICATION", "value": "AAC", "selector": {"ALL": [{"FLOOR": "GROUND"}]}},
                                                   {"evidence_kind": "SOURCE_SPECIFICATION", "value": "BLOCKWORK", "selector": {"ALL": [{"WALL_ROLE": "EXTERNAL"}]}}]),
     {"value": "AAC"}),
    ("MT-37", "FACT_POLICY_RESOLVE", dict(fact_kind="WALL_MATERIAL", mode="PROJECT_EVIDENCE_ONLY", subject={"WALL_TYPE_CODE": "W3"},
                                          claims=[{"evidence_kind": "SOURCE_SPECIFICATION", "value": "AAC", "selector": {"ALL": [{"ELEMENT": "WALL"}]}},
                                                  {"evidence_kind": "SOURCE_SPECIFICATION", "value": "BLOCKWORK", "selector": {"ALL": [{"WALL_TYPE_CODE": "W3"}]}}]),
     {"status": "CONFLICT", "override_rejected_without_except": True}),
    ("MT-38", "SCOPE_VALIDATE", dict(selector={"PROJECT_WIDE": True}, tier="OWNER_PROJECT_INPUT", forced_keys=["FLOOR", "LAYER", "THICKNESS"]),
     {"valid": False, "reason": "FABRICATED_SCOPE"}),
    ("F25", "SCOPE_APPLIES", dict(selector={"ALL": [{"SPACE_ID": "ROOM-07"}, {"SURFACE": "WALL"}], "anchor": "SUBJECT_ANCHOR"},
                                  subject={"SPACE_ID": "ROOM-07", "SURFACE": "WALL"}), {"applies": True, "bound_via": "SUBJECT_ANCHOR"}),
    # ------------------------------------------ transcription / inference (stage C)
    ("F31", "TRANSCRIPTION_PROMOTE", dict(records=[{"transcriber": "MODEL_A", "crop_sha256": "c1", "literal_text": "3.60"},
                                                   {"transcriber": "MODEL_B", "crop_sha256": "c1", "literal_text": "3.60"}]),
     {"role": "SOURCE_DIMENSION_TEXT", "parsed_by": "CODE"}),
    ("MT-31", "TRANSCRIPTION_PROMOTE", dict(records=[{"transcriber": "MODEL_A", "crop_sha256": "c1", "literal_text": "3.60"},
                                                     {"transcriber": "MODEL_A", "crop_sha256": "c1", "literal_text": "3.60"}]),
     {"instances": 1, "role": "CANDIDATE"}),
    ("MT-39", "TRANSCRIPTION_RECORD", dict(transcriber="MODEL_A", crop_sha256="c1", literal_text="3.60", parsed_value=3.6),
     {"__raises__": "ParsedValueNotAllowed"}),
    ("F32", "TRANSCRIPTION_PROMOTE", dict(records=[{"transcriber": "MODEL_A", "crop_sha256": "row1", "literal_text": "D03 900x2100"}]),
     {"role": "CANDIDATE"}),
    ("MT-40", "TRANSCRIPTION_PROMOTE", dict(records=[{"transcriber": "MODEL_A", "crop_sha256": "row1", "literal_text": "D03 900x2100"}],
                                            force_promote=True), {"role": "CANDIDATE"}),
    ("F33", "CLAIM_FROM", dict(producer="VISION_MODEL", record={"record_kind": "AI_INFERENCE", "space": "S1", "room_name": "KITCHEN"}),
     {"role": "CANDIDATE", "space_name_status": "UNNAMED_ON_DRAWING"}),
    ("MT-41", "CLAIM_FROM", dict(producer="VISION_MODEL", record={"record_kind": "AI_INFERENCE", "space": "S1", "room_name": "KITCHEN"},
                                 requested_role="SOURCE"), {"__raises__": "InferenceNotSource"}),
    ("MT-42", "FACT_POLICY_LOAD", dict(policy={"fact_kind": "ROOM_NAME", "admissible": [{"evidence_kind": "AI_INFERENCE", "role": "SOURCE"}]}),
     {"__raises__": "PolicyInvalid"}),
    ("MT-43", "TRANSCRIPTION_RECORD", dict(transcriber="MODEL_A", crop_sha256="c1", literal_text="3.60",
                                           crop_bbox=[0, 0, 10, 10], cited_bbox=[50, 50, 60, 60]),
     {"__raises__": "CropDoesNotContainCitation"}),
    # ------------------------------------------ regression harness (stage D)
    ("MT-14", "SOURCE_DELTA", dict(deltas=[{"defect_class": "XREF"}], census={"classes": ["MIRROR"]}), {"round": "FAIL"}),
    ("MT-15", "SOURCE_DELTA", dict(deltas=[{"defect_class": "MIRROR", "explained_by": "AREA_CHANGE_ONLY"}], census={"classes": ["MIRROR"]}),
     {"explained": False}),
    ("MT-16", "SOURCE_DELTA", dict(deltas=[], census={"classes": []}, inputs={"benchmark_path": "data/benchmarks/any.xlsx"}),
     {"status": "VALIDATION_INVALID"}),
    ("MT-17", "SOURCE_DELTA", dict(deltas=[], census={"classes": [], "frozen_parameter_sha256": "a" * 64},
                                   current_parameter_sha256="b" * 64), {"run": "FAIL"}),
]

IDS = [c[0] for c in CONTRACTS]


def _get(obj, path):
    cur = obj
    for part in path.split("."):
        cur = cur[int(part)] if part.isdigit() and isinstance(cur, (list, tuple)) else cur[part]
    return cur


@pytest.mark.parametrize("row", CONTRACTS, ids=IDS)
def test_contract(row):
    rid, target, kwargs, expect = row
    fn = targets.resolve(target)
    if "__raises__" in expect:
        with pytest.raises(Exception) as err:
            fn(**kwargs)
        assert type(err.value).__name__ == expect["__raises__"]
        return
    result = fn(**kwargs)
    for path, value in expect.items():
        assert _get(result, path) == value, f"{rid}: {path} = {_get(result, path)!r}, required {value!r}"
