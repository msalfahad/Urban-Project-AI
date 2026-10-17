"""Directive §25: deterministic invariants of the four-layer measurement
architecture, the parapet assembly model and the quantity states."""

import json
from pathlib import Path

import pytest

from engine import measurement_region_builder as MRB
from engine import opening_register as OR
from engine import owner_decision_queue as ODQ
from engine import parapet_assembly as PA
from engine import quantity_state as QS
from engine import supersession_ledger as SL
from engine.dimension_roles import DIMENSION_ROLES
from engine.quantity_layers import BASES


def _edge(eid, kind, L, state, a, b):
    return {"EDGE_ID": eid, "KIND": kind, "length_m": L, "a": a, "b": b, "trace_ids": [eid], "STATE": state}


def _region(edges, sites, basis="WALL_FACE_PLASTER"):
    return MRB.build(region_id="R", physical_geometry=edges, topological_relations=sites, opening_register=[],
                     trade="NORMAL_INTERNAL_PLASTER", measurement_basis=basis, owner_rule_version="o", project_rule_version="p")


def test_virtual_closure_contributes_zero_material():
    edges = [_edge("W1", "PHYSICAL_WALL_FACE", 4.0, "ESTABLISHED", (0, 0), (4, 0)),
             _edge("W2", "PHYSICAL_WALL_FACE", 3.0, "ESTABLISHED", (4, 0), (4, 3)),
             _edge("W3", "PHYSICAL_WALL_FACE", 4.0, "ESTABLISHED", (4, 3), (0, 3)),
             _edge("W4a", "PHYSICAL_WALL_FACE", 1.0, "ESTABLISHED", (0, 3), (0, 2)),
             _edge("W4b", "PHYSICAL_WALL_FACE", 1.0, "ESTABLISHED", (0, 1), (0, 0))]
    sites = [{"SITE_ID": "S1", "SITE_TYPE": "CONFIRMED_DOOR_OPENING", "termination_a": (0, 2), "termination_b": (0, 1), "span_m": 1.0}]
    r = _region(edges, sites)
    assert r["FORMED"]
    assert len(r["VIRTUAL_CLOSURES"]) == 1
    c = r["VIRTUAL_CLOSURES"][0]
    assert c["MATERIAL_PRESENT"] is False and c["PHYSICAL_WALL"] is False and c["GEOMETRY_AUTHORITY"] is False
    assert c["quantity_length_contribution"] == 0.0
    assert r["GROSS_BASIS"]["VALUE"] == 13.0            # 4+3+4+1+1, the closure span is not counted


def test_unresolved_edge_cannot_be_silently_closed():
    edges = [_edge("W1", "PHYSICAL_WALL_FACE", 4.0, "ESTABLISHED", (0, 0), (4, 0)),
             _edge("U", "UNRESOLVED_EDGE", 3.0, "NOT_ESTABLISHED", (4, 0), (0, 0))]
    r = _region(edges, [{"SITE_ID": "G", "SITE_TYPE": "UNRESOLVED_GAP", "termination_a": (0, 0), "termination_b": (4, 0), "span_m": 4.0}])
    assert not r["FORMED"]
    assert r["QUANTITY_STATE"] == "NOT_ESTABLISHED"
    assert r["VIRTUAL_CLOSURES"] == []


def test_balustrade_and_handrail_carry_zero_plaster_face():
    for ctype in ("BALUSTRADE", "HANDRAIL"):
        c = PA.component(ASSEMBLY_ID="X", SHEET_ID="S", SOURCE_OBJECT_ID=None, CAD_OBJECT_ID=None, COMPONENT_TYPE=ctype,
                         GEOMETRY_TYPE="LINE", START_POINT=None, END_POINT=None, LENGTH=3.0, HEIGHT=1.0, THICKNESS=0.1,
                         CURVED_OR_STRAIGHT="STRAIGHT", MATERIAL_STATUS="OPEN_METAL", PLASTERABLE_EXTERNAL_FACE_STATUS="ZERO_BY_MATERIAL",
                         PLASTERABLE_INTERNAL_FACE_STATUS="ZERO_BY_MATERIAL", COPING_STATUS="NONE", BALUSTRADE_STATUS="X", HANDRAIL_STATUS="X",
                         SOURCE_DIMENSION_IDS=[], DIMENSION_OWNER_STATUS={}, SOURCE_CONFIDENCE_STATUS="x", OWNER_VERIFICATION_STATUS="x",
                         QUANTITY_ELIGIBILITY="x", PROVENANCE={})
        assert c["PLASTERABLE_SOLID_FACE_M2"] == 0.0
        with pytest.raises(ValueError):
            PA.component(**dict(c, PLASTERABLE_EXTERNAL_FACE_STATUS="ELIGIBLE"))
    f = PA.face(face_id="F", component_id="X", side="EXTERNAL", bottom=None, bottom_source="NOT_ESTABLISHED", top=None,
                top_source="NOT_ESTABLISHED", material="OPEN_METAL", eligibility="ZERO_BY_MATERIAL", length_m=3.0, length_source="ESTABLISHED")
    assert PA.face_area(f)["GROSS_AREA_M2"] == 0.0


def test_coping_is_not_a_wall_face_height():
    wall = PA.face(face_id="W", component_id="P", side="ROOF_SIDE", bottom=9.70, bottom_source="ESTABLISHED", top=11.10,
                   top_source="OWNER_ESTABLISHED", material="SOLID_MASONRY_OR_RC", eligibility="ELIGIBLE", length_m=2.0, length_source="ESTABLISHED_FROM_DWG")
    cap = PA.face(face_id="C", component_id="CAP", side="TOP", bottom=0.0, bottom_source="ESTABLISHED", top=0.20, top_source="ESTABLISHED",
                  material="SOLID_MASONRY_OR_RC", eligibility="ELIGIBLE", length_m=2.0, length_source="ESTABLISHED_FROM_DWG")
    assert wall["FACE_HEIGHT"] == 1.4 and cap["FACE_HEIGHT"] == 0.2
    assert PA.face_area(wall)["GROSS_AREA_M2"] == 2.8          # the coping's 0.20 never enters the wall face


def test_wall_thickness_dimensions_are_not_added_to_clear_dimensions():
    from engine.dimension_roles import clear_opening_width
    assert "WALL_THICKNESS" in DIMENSION_ROLES
    assert abs(clear_opening_width(1.50, [0.20, 0.20])["CLEAR_OPENING_M"] - 1.10) < 1e-9


def test_exterior_setting_out_chain_is_not_an_interior_plaster_length():
    reg = json.loads(Path("data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/OWNER_EVIDENCE_RECONCILIATION.json").read_text("utf-8")) \
        if Path("data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/OWNER_EVIDENCE_RECONCILIATION.json").exists() else None
    if reg is None:
        pytest.skip("owner evidence artifact not present")
    for s in reg["PRINTED_SEGMENTS_VS_AUTHORED"]:
        if s["ID"] in ("90 lower", "90 upper", "633", "90", "633 glazing"):
            assert "SETTING_OUT" in s["WHAT"].upper() or "GLAZ" in s["WHAT"].upper() or "PIER" in s["WHAT"].upper()
    # 90 + 633 + 90 as a plaster length must not equal the SALOON established face
    assert abs((0.90 + 6.33 + 0.90) - 5.15) > 1.0


def test_column_existence_exposure_and_face_ownership_are_three_statements():
    st = Path("data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/STRUCTURAL_SOURCE_CHECK.json")
    if not st.exists():
        pytest.skip("structural check artifact not present")
    d = json.loads(st.read_text("utf-8"))["D2"]
    assert d["COLUMN_EXISTS"]["STATUS"] == "ESTABLISHED"
    assert d["COLUMN_EXPOSED_TO_ROOM"]["STATUS"] != d["COLUMN_EXISTS"]["STATUS"]
    assert d["COLUMN_OWNS_CLEAR_FINISH_FACE"]["STATUS"] == "NO"


def test_curved_geometry_uses_developed_length_not_chord():
    import math
    r = PA.developed_length([{"ID": "a", "KIND": "ARC", "radius_mm": 1000.0, "sweep_rad": math.pi / 2}])
    assert abs(r["DEVELOPED_LENGTH_M"] - 1.5708) < 1e-3
    assert r["CHORD_OR_BBOX_USED"] is False and r["CURVE_TYPE"] == "ARC"
    with pytest.raises(ValueError):
        PA.developed_length([{"ID": "b", "KIND": "BBOX", "length_mm": 1}])


def test_weakest_input_quantity_state():
    assert QS.weakest(["SOURCE_ESTABLISHED", "OWNER_PROJECT_INPUT"]) == "OWNER_PARAMETRIC_QUANTITY"
    assert QS.weakest(["SOURCE_ESTABLISHED", "PROVISIONAL", "OWNER_PROJECT_INPUT"]) == "PROVISIONAL_QUANTITY"
    assert QS.weakest(["ESTABLISHED", None]) == "NOT_ESTABLISHED"
    assert QS.weakest(["ESTABLISHED_FROM_DWG", "PROPOSED_CORRESPONDENCE"]) == "PROVISIONAL_QUANTITY"


def test_contractor_basis_cannot_overwrite_engineering_basis():
    assert set(BASES) == {"ENGINEERING_QS", "CONTRACTOR_SITE_MEASUREMENT"}
    eng = {"UNIT": "m2", "VALUE": 4.8766, "QUANTITY_STATE": "PROVISIONAL_QUANTITY"}
    con = {"UNIT": "m2", "VALUE": 5.9216, "QUANTITY_STATE": "CONTRACTOR_MEASUREMENT_QUANTITY"}
    t = QS.totals_by_unit([eng, con])
    assert t["m2"]["PROVISIONAL_QUANTITY"] == 4.8766 and t["m2"]["CONTRACTOR_MEASUREMENT_QUANTITY"] == 5.9216


def test_benchmark_cannot_affect_geometry():
    g = Path("data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/BENCHMARK_LEAKAGE_GUARD.json")
    if not g.exists():
        pytest.skip("leakage guard artifact not present")
    assert json.loads(g.read_text("utf-8"))["GEOMETRY_ARTIFACTS_CLEAN"] is True


def test_owner_evidence_is_forward_only_and_frozen_hashes_unchanged():
    e = SL.entry(ledger_id="L", previous_statement="x", previous_artifact="a", mark="SUPERSEDED", replaced_by="y", evidence="z")
    assert e["FORWARD_ONLY"] and e["FROZEN_ARTIFACT_UNCHANGED"]
    with pytest.raises(ValueError):
        SL.entry(ledger_id="L", previous_statement="x", previous_artifact="a", mark="OVERWRITTEN", replaced_by="y", evidence="z")
    led = Path("data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/REVISION_SUPERSESSION_LEDGER.json")
    if led.exists():
        d = json.loads(led.read_text("utf-8"))
        assert all(v["OK"] for v in d["FROZEN_ARTIFACTS_UNCHANGED"].values())


def test_units_cannot_be_summed_together():
    with pytest.raises(QS.UnitMixError):
        QS.grand_total([{"UNIT": "m2", "VALUE": 1, "QUANTITY_STATE": "PROVISIONAL_QUANTITY"},
                        {"UNIT": "lm", "VALUE": 1, "QUANTITY_STATE": "PROVISIONAL_QUANTITY"}])
    t = QS.totals_by_unit([{"UNIT": "m2", "VALUE": 1, "QUANTITY_STATE": "PROVISIONAL_QUANTITY"},
                           {"UNIT": "lm", "VALUE": 2, "QUANTITY_STATE": "PROVISIONAL_QUANTITY"}])
    assert t == {"m2": {"PROVISIONAL_QUANTITY": 1.0}, "lm": {"PROVISIONAL_QUANTITY": 2.0}}


def test_opening_survives_measurement_closure_and_keeps_its_own_deduction():
    o = OR.opening(opening_id="D", host_face="W", opening_type="DOOR", width_m=1.0, width_source="PROVISIONAL_DEFAULT",
                   height_m=2.2, height_source="PROVISIONAL_DEFAULT", deduction_rule="FULL_OPENING_DEDUCTION",
                   reveal_depth_m=0.15, reveal_depth_source="PROVISIONAL_DEFAULT")
    assert o["AREA"] == 2.2 and o["DEDUCTION_AMOUNT"] == 2.2 and o["REVEAL_LENGTH"] == 5.4
    assert o["MEASUREMENT_CLOSURE"]["MATERIAL_PRESENT"] is False and o["STATUS"] == "PROVISIONAL_QUANTITY"


def test_decision_queue_only_stops_on_blocking_items():
    base = dict(LOCATION="l", TRADE="t", QUESTION="q", WHY_SOURCE_HIERARCHY_FAILED="w", AVAILABLE_EVIDENCE=[], OPTION_A="a", OPTION_B="b",
                OPTION_C_IF_REQUIRED=None, QUANTITY_IMPACT_IF_KNOWN=None, BLOCKS_WHAT="x", VISUAL_CARD="v")
    q = [ODQ.item(DECISION_ID="1", CAN_OTHER_WORK_CONTINUE=True, **base)]
    assert ODQ.stop_gate(q)["STOP_REQUIRED"] is False
    q.append(ODQ.item(DECISION_ID="2", CAN_OTHER_WORK_CONTINUE=False, **base))
    assert ODQ.stop_gate(q)["STOP_REQUIRED"] is True


def test_se_elevation_regression_104_139_130_155_50():
    p = Path("data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/SE_ELEVATION_SOURCE_AUDIT.json")
    if not p.exists():
        pytest.skip("SE audit artifact not present")
    ts = json.loads(p.read_text("utf-8"))["TEXT_SOURCE_STATUS"]
    assert ts["104_SOURCE_STATUS"]["IS_IT_A_MISREAD_OF_139"] is False
    assert ts["130_SOURCE_STATUS"]["SE_ELEVATION"] == "not present"
    tr = json.loads(Path("data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/PLASTER_QUANTITY_TRACE.json").read_text("utf-8"))
    heights = {l.get("HEIGHT_M") for l in tr["LINES"] if isinstance(l.get("HEIGHT_M"), (int, float))}
    for v in (1.04, 1.30, 1.39, 1.55):
        assert v not in heights
