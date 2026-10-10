"""R8.19 §29-§30: EXPOSED_OBJECT_FINISH_POLICY_V1 - column / duct faces get a finish only where they are physically
exposed to a certified room site, following the room's wall treatment; skirting stays on the frozen V4 path; the
physical class is never merged into WALL_FACE. Synthetic only: written and frozen BEFORE any Qortuba R8.19 run."""

from __future__ import annotations

from engine.source import exposed_finish as EF, wall_contact_path as WC, wall_faces_v2 as WF
from tests.r8_17.test_r8_17_skirting_v4 import M, WALL_E

U, AUTH = 0.001, "TEST HEIGHT"
DRY_T, WET_T = ["PLASTER", "PAINT"], ["WALL_TILE", "WET_WALL_TILE_PREP"]
COL_RULE = {"rule_id": "URBAN-EXPOSED-COLUMN-FINISH-METHOD@v1", "face_class": EF.COLUMN_FACE,
            "requires": ["PHYSICAL_EXPOSURE"], "room_classes": ["DRY_INTERNAL_ROOM", "WET_SERVICE_ROOM",
                                                               "SERVICE_ROOM"], "follows": "ROOM_WALL_TRADES"}
DUCT_RULE = {"rule_id": "URBAN-EXPOSED-INTERIOR-DUCT-FINISH-METHOD@v1", "face_class": EF.OBSTACLE_FACE,
             "requires": ["PHYSICAL_EXPOSURE", "OWNER_PHYSICAL_AUTHORITY"], "room_classes": ["DRY_INTERNAL_ROOM"],
             "follows": "ROOM_WALL_TRADES"}
DUCT_AUTH = {"W|H77||SEGMENT": WC.OWNER_PHYSICAL_OBSTACLE}


def col_edge(seg, length):
    return {"sources": [f"W|H70||SEGMENT|{seg}"], "roles": ["STRUCTURAL_OBSTACLE"], "length": length, "hole": False}


def duct_edge(seg, length, part="H77"):
    return {"sources": [f"W|{part}||SEGMENT|{seg}"], "roles": ["TOPOLOGY_BOUNDARY"], "length": length, "hole": True}


def segs(part, lengths_native):
    return {f"W|{part}||SEGMENT|{i}": {"object": f"W|{part}", "length_m": L * U} for i, L in enumerate(lengths_native)}


def spans(edges, height=3.0, **kw):
    f = WF.site_faces([dict(WALL_E)] + [dict(e) for e in edges], u=U, height_m=height, height_authority=AUTH, **kw)
    assert f["state"] == WF.COMPUTED and f["reconciliation"]["state"] == "PASS"
    return f


def finish(f, segments, cls, room_class, trades, rule, auth=True, site="S1", height=3.0):
    x = EF.exposure(segments, {site: f["spans"]}, cls)
    a = EF.assign(cls, room_class, trades, rule, owner_physical_authority=auth)
    return x, a, EF.surfaces(x["faces"], site=site, height_m=height, height_authority=AUTH, assignment=a)


COLUMN = segs("H70", [500, 500, 500, 500])          # a 0.5 x 0.5 column, four faces


# ------------------------------------------------------------------------------- columns (§29)
def test_c1_dry_room_exposed_column_gets_plaster_and_paint():
    f = spans([col_edge(1, 500), col_edge(2, 500)])
    x, a, s = finish(f, COLUMN, EF.COLUMN_FACE, "DRY_INTERNAL_ROOM", DRY_T, COL_RULE)
    assert x["state"] == "PASS" and a["state"] == EF.INCLUDED and a["trades"] == ["PAINT", "PLASTER"]
    assert len(s) == 2 and all(abs(r["area_m2"] - 1.5) < 1e-9 and r["class"] == EF.COLUMN_FACE for r in s)


def test_c2_dry_column_skirting_is_the_existing_path_never_a_duplicate():
    edges = [col_edge(1, 500), col_edge(2, 500)]
    v4 = WC.measure_v4([WALL_E] + edges, M)
    x, _a, s = finish(spans(edges), COLUMN, EF.COLUMN_FACE, "DRY_INTERNAL_ROOM", DRY_T, COL_RULE)
    assert v4["components"][WC.COLUMN_FACE] == 1000.0                       # already on the V4 path
    assert abs(sum(r["length_m"] for r in s) - v4["components"][WC.COLUMN_FACE] * U) < 1e-9   # the SAME faces
    assert all("SKIRTING" not in r["trades"] for r in s) and "new skirting" in EF.policy_record()["never"]


def test_c3_wet_room_exposed_column_gets_wall_tile_at_the_wet_height():
    x, a, s = finish(spans([col_edge(0, 500)], height=3.2), COLUMN, EF.COLUMN_FACE, "WET_SERVICE_ROOM", WET_T,
                     COL_RULE, height=3.2)
    assert a["trades"] == ["WALL_TILE", "WET_WALL_TILE_PREP"] and len(s) == 1
    assert abs(s[0]["area_m2"] - 1.6) < 1e-9 and s[0]["height_m"] == 3.2


def test_c4_wet_room_column_never_gets_paint_or_plaster():
    _x, a, s = finish(spans([col_edge(0, 500)], height=3.2), COLUMN, EF.COLUMN_FACE, "WET_SERVICE_ROOM", WET_T,
                      COL_RULE, height=3.2)
    assert not {"PAINT", "PLASTER"} & set(a["trades"]) and all(not {"PAINT", "PLASTER"} & set(r["trades"]) for r in s)


def test_c5_wet_full_tile_room_column_has_no_normal_skirting():
    edges = [col_edge(0, 500)]
    v4 = WC.measure_v4([WALL_E] + edges, M, full_wall_tile=True)
    _x, _a, s = finish(spans(edges, height=3.2), COLUMN, EF.COLUMN_FACE, "WET_SERVICE_ROOM", WET_T, COL_RULE,
                       height=3.2)
    assert v4["state"] == WC.NO_SKIRTING and v4["length"] == 0.0 and all("SKIRTING" not in r["trades"] for r in s)


def test_c6_an_embedded_column_face_gets_no_room_finish():
    f = spans([])                                                          # the column is buried in the wall
    x, a, s = finish(f, COLUMN, EF.COLUMN_FACE, "DRY_INTERNAL_ROOM", DRY_T, COL_RULE)
    assert s == [] and all(v["state"] == EF.HIDDEN and v["hidden_m"] == 0.5 for v in x["segments"].values())


def test_c7_a_partially_exposed_column_counts_its_exposed_faces_only():
    f1 = spans([col_edge(1, 300), col_edge(2, 500)])                      # seg 1: 0.3 of 0.5 exposed to S1
    f2 = spans([col_edge(1, 200)])                                         # seg 1: the other 0.2 exposed to S2
    x = EF.exposure(COLUMN, {"S1": f1["spans"], "S2": f2["spans"]}, EF.COLUMN_FACE)
    sg = x["segments"]
    assert sg["W|H70||SEGMENT|1"]["exposed_m"] == {"S1": 0.3, "S2": 0.2} and sg["W|H70||SEGMENT|1"]["state"] == EF.EXPOSED
    assert sg["W|H70||SEGMENT|0"]["state"] == EF.HIDDEN and sg["W|H70||SEGMENT|3"]["hidden_m"] == 0.5
    one = EF.exposure(COLUMN, {"S1": f1["spans"]}, EF.COLUMN_FACE)["segments"]["W|H70||SEGMENT|1"]
    assert one["state"] == EF.PARTIAL and abs(one["hidden_m"] - 0.2) < 1e-9
    a = EF.assign(EF.COLUMN_FACE, "DRY_INTERNAL_ROOM", DRY_T, COL_RULE, owner_physical_authority=True)
    s = EF.surfaces(x["faces"], site="S1", height_m=3.0, height_authority=AUTH, assignment=a)
    assert abs(sum(r["area_m2"] for r in s) - (0.3 + 0.5) * 3.0) < 1e-9


def test_c8_column_identity_stays_separate_from_the_wall_and_fails_closed():
    f = spans([col_edge(1, 500)])
    assert abs(f["areas_m2"]["WALL_PLANE_NET"] - 3.0) < 1e-9 and f["areas_m2"]["COLUMN_FACE"] == 1.5
    _x, _a, s = finish(f, COLUMN, EF.COLUMN_FACE, "DRY_INTERNAL_ROOM", DRY_T, COL_RULE)
    assert {r["class"] for r in s} == {EF.COLUMN_FACE}
    stray = {"class": EF.COLUMN_FACE, "length_m": 0.5, "sources": ["W|H99||SEGMENT|0"], "geom": None}
    bad = EF.exposure(COLUMN, {"S1": [stray]}, EF.COLUMN_FACE)
    assert bad["state"] == "FAIL" and bad["errors"][0]["error"] == "OBJECT_IDENTITY_UNRESOLVED"
    over = EF.exposure(COLUMN, {"S1": [dict(stray, sources=["W|H70||SEGMENT|0"], length_m=0.9)]}, EF.COLUMN_FACE)
    assert over["state"] == "FAIL" and over["errors"][0]["error"] == "EXPOSED_LONGER_THAN_SEGMENT"


# ------------------------------------------------------------------------------- ducts (§30)
DUCT = segs("H77", [400, 200, 400, 200])
LINING = segs("H78", [380, 180, 380, 180])
FOUR = [duct_edge(0, 400), duct_edge(1, 200), duct_edge(2, 400), duct_edge(3, 200)]


def test_d1_an_authorised_exposed_dry_duct_gets_plaster_and_paint():
    f = spans(FOUR, obstacle_authority=DUCT_AUTH)
    _x, a, s = finish(f, DUCT, EF.OBSTACLE_FACE, "DRY_INTERNAL_ROOM", DRY_T, DUCT_RULE)
    assert a["state"] == EF.INCLUDED and a["trades"] == ["PAINT", "PLASTER"]
    assert abs(sum(r["area_m2"] for r in s) - 1.2 * 3.0) < 1e-9 and {r["class"] for r in s} == {EF.OBSTACLE_FACE}


def test_d2_duct_skirting_is_the_existing_authorised_path():
    v4 = WC.measure_v4([WALL_E] + FOUR, M, obstacle_authority=DUCT_AUTH)
    _x, _a, s = finish(spans(FOUR, obstacle_authority=DUCT_AUTH), DUCT, EF.OBSTACLE_FACE, "DRY_INTERNAL_ROOM", DRY_T,
                       DUCT_RULE)
    assert v4["components"][WC.AUTHORISED_OBSTACLE_FACE] == 1200.0
    assert abs(sum(r["length_m"] for r in s) - 1.2) < 1e-9 and all("SKIRTING" not in r["trades"] for r in s)


def test_d3_hidden_duct_sides_and_the_internal_lining_get_no_finish():
    f = spans(FOUR[:3], obstacle_authority=DUCT_AUTH)                       # side 3 sits against an existing wall
    x, _a, s = finish(f, {**DUCT, **LINING}, EF.OBSTACLE_FACE, "DRY_INTERNAL_ROOM", DRY_T, DUCT_RULE)
    sg = x["segments"]
    assert sg["W|H77||SEGMENT|3"]["state"] == EF.HIDDEN and all(sg[k]["state"] == EF.HIDDEN for k in LINING)
    assert abs(sum(r["length_m"] for r in s) - 1.0) < 1e-9


def test_d4_a_duct_never_becomes_wall_identity():
    f = spans(FOUR, obstacle_authority=DUCT_AUTH)
    assert abs(f["areas_m2"]["WALL_PLANE_NET"] - 3.0) < 1e-9 and abs(f["areas_m2"]["OBSTACLE_FACE"] - 3.6) < 1e-9
    _x, _a, s = finish(f, DUCT, EF.OBSTACLE_FACE, "DRY_INTERNAL_ROOM", DRY_T, DUCT_RULE)
    assert not [r for r in s if r["class"] == "WALL_FACE"]


def test_d5_an_unauthorised_generic_obstacle_gets_no_inferred_finish():
    up = WF.site_faces([dict(WALL_E)] + FOUR, u=U, height_m=3.0, height_authority=AUTH,
                       obstacle_authority={"W|H77||SEGMENT": "UNPROVEN_OBSTACLE"})
    assert up["state"] == WF.BLOCKED                                       # the wall-face engine fails closed too
    f = spans(FOUR, obstacle_authority=DUCT_AUTH)
    _x, a, s = finish(f, DUCT, EF.OBSTACLE_FACE, "DRY_INTERNAL_ROOM", DRY_T, DUCT_RULE, auth=False)
    assert a["state"] == EF.UNRESOLVED and s == [] and "owner physical authority" in a["why"]


def test_d6_owner_duct_authority_and_rule_scope_are_both_required():
    a_wet = EF.assign(EF.OBSTACLE_FACE, "WET_SERVICE_ROOM", WET_T, DUCT_RULE, owner_physical_authority=True)
    a_none = EF.assign(EF.OBSTACLE_FACE, "DRY_INTERNAL_ROOM", DRY_T, None, owner_physical_authority=True)
    a_col = EF.assign(EF.OBSTACLE_FACE, "DRY_INTERNAL_ROOM", DRY_T, COL_RULE, owner_physical_authority=True)
    assert a_wet["state"] == a_none["state"] == a_col["state"] == EF.UNRESOLVED
    assert "WET_SERVICE_ROOM" in a_wet["why"]
