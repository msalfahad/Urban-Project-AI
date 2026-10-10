"""Synthetic traces for the material-role overlap audit. No P7757 value."""

from __future__ import annotations

from engine import material_role_audit as A


def _t(tid, ct, sheet="ELEV", poly=None, line=None, hosted=None):
    d = {"TRACE_ID": tid, "CLAIM_TYPE": ct, "EFFECTIVE_CLAIM_TYPE": ct,
         "SHEET_ID": sheet, "VISUAL_TRACE_STATUS": "TRACE_ESTABLISHED"}
    if poly:
        d["PIXEL_POLYGON"] = poly
    if line:
        d["PIXEL_POLYLINE"] = line
    if hosted:
        d["HOSTED_IN"] = hosted
    return d


def _rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def test_open_balustrade_has_no_plasterable_face_and_is_exclusive_with_solid():
    bal = _t("BAL-1", "BALUSTRADE", poly=_rect(0, 0, 100, 40))
    par = _t("PAR-1", "PARAPET", poly=_rect(0, 20, 100, 60))   # overlaps 20 px
    out = A.overlap_audit([bal, par])
    objs = {o["TRACE_ID"]: o for o in out["PHYSICAL_OBJECTS"]}
    assert objs["BAL-1"]["PLASTERABLE_SOLID_FACE"] is False
    assert objs["BAL-1"]["TRADE_CONTRIBUTION_ROLE"] == "NONE"
    assert objs["PAR-1"]["PLASTERABLE_SOLID_FACE"] is True
    rel = out["OVERLAP_RELATIONS"][0]
    assert rel["OVERLAP_RELATION"] == "MUTUALLY_EXCLUSIVE_MATERIAL_ROLES"
    assert rel["CONTRIBUTION_PRIORITY"] == "EXCLUDE_BOTH_UNTIL_RESOLVED"
    assert out["MATERIAL_CONTRADICTIONS"]


def test_same_object_declared_is_semantic_views_not_contradiction():
    body = _t("PAR-1", "PARAPET", poly=_rect(0, 0, 100, 60))
    face = _t("SEG-1", "WALL_SEGMENT", line=[[0, 0], [100, 0]])
    without = A.overlap_audit([body, face])
    assert without["OVERLAP_RELATIONS"][0]["OVERLAP_RELATION"] == \
        "MUTUALLY_EXCLUSIVE_MATERIAL_ROLES"    # WALL vs PARAPET undeclared
    with_map = A.overlap_audit([body, face],
                               object_map={"PO-1": ["PAR-1", "SEG-1"]})
    assert with_map["OVERLAP_RELATIONS"][0]["OVERLAP_RELATION"] == \
        "SAME_OBJECT_MULTIPLE_SEMANTIC_VIEWS"
    assert not with_map["MATERIAL_CONTRADICTIONS"]


def test_capping_on_parapet_is_an_allowed_layer_with_host_and_child():
    par = _t("PAR-1", "PARAPET", poly=_rect(0, 20, 100, 60))
    cap = _t("PAR-2", "PARAPET", poly=_rect(0, 15, 100, 25))
    out = A.overlap_audit([par, cap], role_overrides={
        "PAR-2": {"MATERIAL_ROLE": "CAPPING_BAND", "REASON": "band on top"}})
    rel = out["OVERLAP_RELATIONS"][0]
    assert rel["OVERLAP_RELATION"] == "ALLOWED_LAYER_OVERLAP"
    objs = {o["TRACE_ID"]: o for o in out["PHYSICAL_OBJECTS"]}
    assert objs["PAR-2"]["TRADE_CONTRIBUTION_ROLE"] == "PARAPET_CAPPING"
    assert objs["PAR-2"]["ROLE_ASSIGNED_BY"] == "CONTROLLER_DECLARATION"


def test_door_hosted_in_wall_is_allowed_layer_and_annotations_are_not_audited():
    wall = _t("SEG-1", "WALL_SEGMENT", poly=_rect(0, 0, 200, 20))
    door = _t("D-1", "DOOR", poly=_rect(50, 0, 100, 20), hosted="SEG-1")
    dim = _t("DIM-1", "PRINTED_DIMENSION", poly=_rect(0, 0, 200, 20))
    out = A.overlap_audit([wall, door, dim])
    assert "DIM-1" in out["TRACES_EXCLUDED_AS_ANNOTATION_OR_NO_AREA"]
    assert len(out["OVERLAP_RELATIONS"]) == 1
    rel = out["OVERLAP_RELATIONS"][0]
    assert rel["OVERLAP_RELATION"] == "ALLOWED_LAYER_OVERLAP"
    objs = {o["TRACE_ID"]: o for o in out["PHYSICAL_OBJECTS"]}
    assert objs["D-1"]["HOST_OBJECT"] == "PO:SEG-1"
    assert objs["SEG-1"]["CHILD_OBJECT"] == ["PO:D-1"]


def test_near_total_undeclared_overlap_stays_unresolved_until_declared():
    a = _t("COL-1", "COLUMN", poly=_rect(0, 0, 50, 50))
    b = _t("STR-1", "STAIR", poly=_rect(0, 0, 50, 50))
    out = A.overlap_audit([a, b])
    assert out["OVERLAP_RELATIONS"][0]["OVERLAP_RELATION"] == "UNRESOLVED_OVERLAP"
    out2 = A.overlap_audit([a, b], same_projection_pairs=[("COL-1", "STR-1")])
    assert out2["OVERLAP_RELATIONS"][0]["OVERLAP_RELATION"] == \
        "DIFFERENT_OBJECTS_SAME_PROJECTION"


def test_unresolved_feature_overlap_is_unresolved_and_touching_is_adjacency():
    a = _t("SEG-1", "WALL_SEGMENT", poly=_rect(0, 0, 50, 50))
    u = _t("UNK-1", "UNRESOLVED_FEATURE", poly=_rect(40, 40, 90, 90))
    c = _t("COL-1", "COLUMN", poly=_rect(50, 0, 80, 50))   # touches SEG-1
    out = A.overlap_audit([a, u, c])
    rels = {(r["A"], r["B"]): r["OVERLAP_RELATION"] for r in out["OVERLAP_RELATIONS"]}
    assert rels[("SEG-1", "UNK-1")] == "UNRESOLVED_OVERLAP"
    assert any(x["A"] == "SEG-1" and x["B"] == "COL-1" for x in out["ADJACENCIES"])


def test_guard_refuses_duplicates_parent_child_and_balustrade_faces():
    cid = A.trade_contribution_id
    good = [
        {"TRADE_CONTRIBUTION_ID": cid("PL", "PO-1", "EXT", "FACE"), "TRADE": "PL",
         "PHYSICAL_OBJECT_ID": "PO-1", "FACE_ID": "EXT", "ITEM": "FACE",
         "MATERIAL_ROLE": "PARAPET_SOLID_FACE", "VALUE": 3.0},
        {"TRADE_CONTRIBUTION_ID": cid("PL", "PO-1", "TOP", "CAPPING"), "TRADE": "PL",
         "PHYSICAL_OBJECT_ID": "PO-1", "FACE_ID": "TOP", "ITEM": "CAPPING",
         "MATERIAL_ROLE": "CAPPING_BAND", "VALUE": 0.5},
    ]
    assert A.guard_contributions(good)["GUARD_STATUS"] == "CLEAN"
    bad = good + [
        dict(good[0]),                                            # duplicate id
        {"TRADE_CONTRIBUTION_ID": cid("PL", "PO-B", "EXT", "FACE"), "TRADE": "PL",
         "PHYSICAL_OBJECT_ID": "PO-B", "FACE_ID": "EXT", "ITEM": "FACE",
         "MATERIAL_ROLE": "OPEN_BALUSTRADE", "VALUE": 2.0},        # §4 breach
        {"TRADE_CONTRIBUTION_ID": cid("PL", "PO-D", "EXT", "FACE"), "TRADE": "PL",
         "PHYSICAL_OBJECT_ID": "PO-D", "FACE_ID": "EXT", "ITEM": "FACE",
         "MATERIAL_ROLE": "DOOR_OPENING", "HOST_OBJECT": "PO-1", "VALUE": 2.2},
    ]
    g = A.guard_contributions(bad)
    kinds = {c["CONFLICT"] for c in g["CONFLICTS"]}
    assert {"DUPLICATE_PHYSICAL_CONTRIBUTION", "BALUSTRADE_PARAPET_CONFLICT",
            "PARENT_CHILD_DOUBLE_COUNT"} <= kinds
    assert g["GUARD_STATUS"] == "CONFLICTS_FOUND"
    assert g["A_CONFLICT_BLOCKS_THE_TOTAL"] is True


def test_audit_is_deterministic_by_hash():
    a = _t("SEG-1", "WALL_SEGMENT", poly=_rect(0, 0, 50, 50))
    b = _t("COL-1", "COLUMN", poly=_rect(40, 0, 80, 50))
    h1 = A.overlap_audit([a, b])["AUDIT_SHA256"]
    h2 = A.overlap_audit([a, b])["AUDIT_SHA256"]
    assert h1 == h2
