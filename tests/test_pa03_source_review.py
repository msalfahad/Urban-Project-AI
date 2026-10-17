"""PA03 source-review regressions (directive §28, ten invariants)."""

import pytest

from engine import source_review as SR


def _edge(eid, cont, void=True, ev=None, **over):
    base = dict(EDGE_ID=eid, PLAN_AXIS="x", LENGTH_M=1.0, GROUND_FLOOR_PHYSICAL_FACE="?", FIRST_FLOOR_PHYSICAL_FACE="?", VOID_FLOOR_OPENING=void,
                WALL_CONTINUES_VERTICALLY=cont, RAILING_AT_FIRST_FLOOR=False, OPEN_EDGE=False, STAIR_EDGE=False, COLUMN=False, GLAZING=False, OTHER=None,
                EVIDENCE=ev or [], STATUS="s")
    base.update(over)
    return SR.edge_record(**base)


# 1. a void opening never implies "no double-height wall"
def test_void_opening_does_not_imply_no_double_height_wall():
    edges = [_edge("N", False, True), _edge("S", True, True, ev=["same wall plane on both plan copies"])]
    dh = SR.double_height_status(edges)
    assert dh["VOID_IMPLIES_NO_DOUBLE_HEIGHT_WALL"] is False
    assert dh["DOUBLE_HEIGHT_WALL_STATUS"] == "NOT_FULLY_ESTABLISHED" and dh["CANDIDATE_EDGES"] == ["S"]
    only_open = [_edge("N", False, True), _edge("E", False, True)]
    assert SR.double_height_status(only_open)["DOUBLE_HEIGHT_WALL_STATUS"] == "NO_CANDIDATE_FACE_FOUND_IN_PLAN_SOURCES"
    unknown = [_edge("N", "UNKNOWN", True)]
    assert SR.double_height_status(unknown)["DOUBLE_HEIGHT_WALL_STATUS"] == "NOT_FULLY_ESTABLISHED"


# 2. printed 587 x 400 cannot silently become 5.82 x 2.75
def test_printed_void_cannot_be_substituted_or_averaged():
    rec = SR.reconcile_dimension(name="D", printed_value=4.00, printed_source="DWG dim", classification="IDENTITY_MAPPING_DIFFERENCE", explanation="two objects",
                                 cad_candidates=[{"BASIS": "wall face", "VALUE": 4.00, "ENTITY_IDS": ["a"], "OBJECT": "zone"}, {"BASIS": "X", "VALUE": 2.75, "ENTITY_IDS": ["b"], "OBJECT": "slab opening"}])
    assert rec["PRINTED_VALUE"] == 4.00 and rec["PRINTED_VALUE_PRESERVED"] and not rec["AVERAGED"]
    assert SR.assert_not_substituted(rec, [(4.00, 2.75)])
    bad = dict(rec, PRINTED_VALUE=2.75)
    with pytest.raises(SR.SubstitutionError):
        SR.assert_not_substituted(bad, [(4.00, 2.75)])
    with pytest.raises(SR.SubstitutionError):
        SR.reconcile_dimension(name="D", printed_value=4.00, printed_source="s", classification="CAD_GEOMETRY_DIFFERENCE", explanation="e",
                               cad_candidates=[{"BASIS": "a", "VALUE": 2.75, "ENTITY_IDS": [], "OBJECT": "o"}, {"BASIS": "mean", "VALUE": 3.375, "ENTITY_IDS": [], "OBJECT": "o"}])
    with pytest.raises(ValueError):
        SR.reconcile_dimension(name="D", printed_value=4.0, printed_source="s", classification="RESOLVED_SOMEHOW", explanation="e", cad_candidates=[])


# 3. floor opening geometry and wall continuity are different variables
def test_floor_opening_and_wall_continuity_are_independent_fields():
    e = _edge("S", True, True, ev=["plan"])
    assert e["VOID_FLOOR_OPENING"] is True and e["WALL_CONTINUES_VERTICALLY"] is True
    with pytest.raises(ValueError):
        _edge("S", True, True, ev=[])                      # continuity needs evidence
    with pytest.raises(ValueError):
        _edge("S", False, True, DERIVED_FROM_VOID_OPENING=True)
    with pytest.raises(ValueError):
        _edge("S", "maybe", True)


# 4. a QA overlay cannot promote its annotation to source evidence
def test_qa_overlay_is_never_source_authority():
    r = SR.render_validity(image="visual_qa/x.png", kind="DERIVED_QA_OVERLAY", ink_fraction=0.05, target_object="void", target_visible=True)
    assert r["IS_SOURCE_AUTHORITY"] is False and r["OVERLAY_ANNOTATION_IS_EVIDENCE"] is False
    s = SR.claim_support(r, "void is 5.82 x 2.75")
    assert s["SUPPORT"] == "QA_CHECK_ONLY" and s["SOURCE_AUTHORITY"] is False
    src = SR.render_validity(image="crop.png", kind="SOURCE_IMAGE", ink_fraction=0.05, target_object="dims", target_visible=True)
    assert SR.claim_support(src, "587 printed")["SOURCE_AUTHORITY"] is False
    with pytest.raises(ValueError):
        SR.render_validity(image="x", kind="SOURCE_OF_TRUTH", ink_fraction=0.1, target_object="t", target_visible=True)


# 5. a QA render without the visible target (or grid only) cannot pass
def test_render_without_visible_target_is_not_informative():
    grid = SR.render_validity(image="grid.png", kind="SOURCE_IMAGE", ink_fraction=0.002, target_object="band", target_visible=True)
    assert grid["VALIDITY"] == "NOT_INFORMATIVE" and grid["CAN_SUPPORT_CLAIM"] is False
    no_target = SR.render_validity(image="line.png", kind="SOURCE_IMAGE", ink_fraction=0.05, target_object="band line", target_visible=False)
    assert no_target["VALIDITY"] == "NOT_INFORMATIVE"
    with pytest.raises(ValueError):
        SR.claim_support(no_target, "a band exists")
    partial = SR.render_validity(image="p.png", kind="SOURCE_IMAGE", ink_fraction=0.05, target_object="t", target_visible="PARTIAL")
    assert partial["VALIDITY"] == "PARTIALLY_INFORMATIVE"


# 6. NE elevation existence cannot coexist with a "no NE elevation" queue reason
def test_elevation_exists_rejects_no_elevation_queue_reason():
    st = {"STATUS": "PROVISIONAL"}
    with pytest.raises(ValueError):
        SR.elevation_finish_eligibility(face_id="NE", elevation_source_exists=True, elevation_page=7, finish_system_established=False,
                                        solid_face_top=st, band_exists=st, band_height=st, band_trade_role=st, queue_reason="no elevation of the neighbour side exists")
    rec = SR.elevation_finish_eligibility(face_id="NE", elevation_source_exists=True, elevation_page=7, finish_system_established=False,
                                          solid_face_top=st, band_exists={"STATUS": "NOT_ESTABLISHED"}, band_height={"STATUS": "DERIVED"}, band_trade_role={"STATUS": "UNKNOWN"},
                                          queue_reason="finish note absent on page 7")
    assert rec["ELEVATION_SOURCE_EXISTS"] and not rec["FINISH_SYSTEM_ESTABLISHED"] and rec["QUANTITY_STATE"] == "GEOMETRIC_REFERENCE_ONLY"
    assert rec["BAND_EXISTS_STATUS"]["STATUS"] != rec["SOLID_FACE_TOP_STATUS"]["STATUS"]


# 7. column exposed girth is not an exposed height of 3.20
def test_column_girth_height_and_area_are_separate():
    c = SR.column_vertical_exposure(column_id="C", exposed_girth_lm=0.75, girth_state="PROVISIONAL", exposed_height_m=None, height_state="NOT_ESTABLISHED",
                                    height_evidence=["beam soffit unknown"], parametric_height_m=3.20, parametric_source="owner")
    assert c["COLUMN_BONDING_AREA_M2"]["VALUE"] is None and c["COLUMN_BONDING_AREA_M2"]["STATE"] == "NOT_ESTABLISHED"
    assert c["OWNER_PARAMETRIC_AREA_M2"]["VALUE"] == 2.4 and c["OWNER_PARAMETRIC_AREA_M2"]["IS_PHYSICAL_AREA"] is False
    assert c["AUTO_CONVERTED_GIRTH_X_PARAMETRIC_HEIGHT"] is False
    d = SR.column_vertical_exposure(column_id="C", exposed_girth_lm=1.80, girth_state="PROVISIONAL", exposed_height_m=4.2, height_state="PROVISIONAL", height_evidence=["section"])
    assert d["COLUMN_BONDING_AREA_M2"]["VALUE"] == 7.56 and d["COLUMN_BONDING_AREA_M2"]["STATE"] == "PROVISIONAL_QUANTITY"


# 8. an open lattice has zero plaster
def test_open_lattice_zero_plaster():
    l = SR.lattice_component(component_id="NW-LATTICE", kind="OPEN_LATTICE_BALUSTRADE", height_m=1.30, length_m=5.79, kerb_component_id="NW-KERB")
    assert l["BALUSTRADE_PLASTERABLE_SOLID_FACE_M2"] == 0.0 and l["ZERO_BY_MATERIAL"] and l["WALL_AREA_FROM_THICKNESS_X_HEIGHT"] is None
    with pytest.raises(ValueError):
        SR.lattice_component(component_id="x", kind="SOLID_PARAPET", height_m=1.0, length_m=1.0)


# 9. the curved kerb is a separate component from the lattice
def test_kerb_is_separate_from_lattice():
    l = SR.lattice_component(component_id="NW-LATTICE", kind="OPEN_LATTICE_BALUSTRADE", height_m=1.30, length_m=5.79, kerb_component_id="NW-KERB")
    assert l["KERB_COMPONENT_ID"] == "NW-KERB" and l["KERB_HEIGHT_INHERITED_FROM_LATTICE"] is False
    assert l["HEIGHT_M"] == 1.30 and "KERB_HEIGHT_M" not in l


# 10. the 10 cm stair element cannot become a plaster wall without role evidence
def test_stair_element_needs_role_evidence_to_be_a_wall():
    e = SR.stair_element(element_id="E", printed_thickness_cm=10, length_m=3.35, role="UNRESOLVED", role_evidence=["separates the flights in plan"])
    assert e["PLASTER_WALL_ELIGIBILITY"] == "NOT_ESTABLISHED" and e["PLASTER_AREA_M2"] is None and e["SEPARATES_FLIGHTS_IN_PLAN_IS_NOT_ROLE_EVIDENCE"]
    with pytest.raises(ValueError):
        SR.stair_element(element_id="E", printed_thickness_cm=10, length_m=3.35, role="PARTITION", role_evidence=[])
    b = SR.stair_element(element_id="E", printed_thickness_cm=10, length_m=3.35, role="BALUSTRADE_BASE", role_evidence=["A-A"])
    assert b["PLASTER_WALL_ELIGIBILITY"] == "NOT_A_WALL"
    with pytest.raises(ValueError):
        SR.stair_element(element_id="E", printed_thickness_cm=10, length_m=3.35, role="WALL", role_evidence=["x"])


def test_dimension_ownership_requires_witness_for_printed_owned():
    with pytest.raises(ValueError):
        SR.dimension_ownership(dim_id="d", printed_value=200, chain="c", owner="OPENING_HEIGHT", witness_from="sill", witness_to=None, status="PRINTED_OWNED", evidence="e")
    d = SR.dimension_ownership(dim_id="d", printed_value=250, chain="c", owner="SPANDREL", witness_from="head", witness_to="sill", status="PRINTED_OWNED", evidence="e")
    assert d["SOURCE_IS_NATIVE_PAGE_NOT_PROSE"]
