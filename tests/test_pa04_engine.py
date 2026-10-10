"""PA04 engine regressions: plan regions, height parameters, self-checks, cold challenge."""

import math

import numpy as np
import pytest

from engine import cold_challenge as CC
from engine import height_parameters as HP
from engine import plan_regions as PR
from engine import self_checks as SC


def _box_room(with_door=True):
    # a 4 x 3 m room of 200 walls; a 0.9 door on the south wall drawn as a swing arc + leaf
    L = lambda oid, lay, a, b: ("SEGMENT", oid, lay, a[0], a[1], b[0], b[1], None, None, None, None, None)
    prims = [L("w1", "1", (0, 0), (4000, 0)), L("w2", "1", (4000, 0), (4000, 3000)), L("w3", "1", (4000, 3000), (0, 3000)), L("w4", "1", (0, 3000), (0, 0))]
    # door opening in w1 between x 1500 and 2400: split the wall
    prims[0] = L("w1a", "1", (0, 0), (1500, 0)); prims.append(L("w1b", "1", (2400, 0), (4000, 0)))
    if with_door:
        prims.append(("ARC", "door", "D", None, None, None, None, 1500, 0, 900, 0.0, math.pi / 2))
    return prims


def test_plan_regions_room_faces_and_open_edge():
    wall, door, meta = PR.rasterise(_box_room(True), (-500, -500, 4500, 3500), 50)
    label, sl = PR.flood(wall, door, {"in": (2000, 1500), "out": (2000, -300)}, meta)
    assert sl["in"] != sl["out"]
    faces = PR.merge_collinear(PR.boundary_faces(label, wall, door, sl["in"], meta))
    by = {}
    for f in faces:
        by[f["CLASS"]] = round(by.get(f["CLASS"], 0) + f["LENGTH_M"], 2)
    assert abs(by["WALL"] - (4 + 3 + 4 + 3 - 0.9)) < 0.3 and abs(by.get("DOOR", 0) - 0.9) < 0.2
    assert abs(PR.region_area_m2(label, sl["in"], 50) - 12.0) < 0.6
    # without the door leaf the opening leaks: one region (open edge), never a wall
    wall2, door2, meta2 = PR.rasterise(_box_room(False), (-500, -500, 4500, 3500), 50)
    label2, sl2 = PR.flood(wall2, door2, {"in": (2000, 1500), "out": (2000, -300)}, meta2)
    assert sl2["in"] == sl2["out"]


def test_height_parameter_table_never_hardcodes_a_global_height():
    p = HP.parameter(scope="FIRST_NORMAL_INTERNAL", value=None, source="none", status="NOT_ESTABLISHED", effective_scope="FF")
    a = HP.area_from(12.5, p)
    assert a["LM"] == 12.5 and a["M2"] is None and a["STATE"] == "NOT_ESTABLISHED"
    with pytest.raises(ValueError):
        HP.parameter(scope="GROUND_NORMAL_INTERNAL", value=3.2, source="o", status="OWNER_AUTHORISED", effective_scope="GF")   # needs the owner record
    g = HP.parameter(scope="GROUND_NORMAL_INTERNAL", value=3.2, source="o", status="OWNER_AUTHORISED", effective_scope="GF", owner_override="P7757_OWNER_PARAMETERS")
    assert HP.area_from(2.0, g)["STATE"] == "OWNER_PARAMETRIC_QUANTITY"
    t = HP.table([g, p])
    assert t["GLOBAL_HEIGHT_HARDCODED"] is False and "WET_ROOM_TILE_PREP" in t["MISSING_SCOPES"]
    with pytest.raises(ValueError):
        HP.table([g, g])


def test_self_checks_flag_units_trade_and_leakage():
    lines = [{"ID": "a", "UNIT": "m2", "VALUE": 1.0, "QUANTITY_STATE": "OWNER_PARAMETRIC_QUANTITY", "TREATMENT_STATUS": "UNKNOWN", "SOURCE": "s", "SOURCE_ENTITY_IDS": ["x"]},
             {"ID": "b", "UNIT": "ft2", "VALUE": 1.0, "QUANTITY_STATE": "PROVISIONAL_QUANTITY", "SOURCE": None}]
    r = SC.run_all({"LINES": lines, "X": 12.9}, lines)
    assert set(r["FAILED"]) >= {"TRADE_ELIGIBILITY_CHECK", "UNIT_CHECK", "SOURCE_COMPLETENESS_CHECK", "BENCHMARK_LEAKAGE_CHECK"}
    c = SC.cross_sheet_contradiction([{"ITEM": "void depth", "A": 4.0, "A_SOURCE": "printed", "B": 2.75, "B_SOURCE": "X"}])
    assert not c["PASS"] and c["FINDINGS"][0]["RESOLVED_HERE"] is False


def test_cold_challenge_no_vote_and_agree_on_number_only():
    f1 = CC.compare_field("WIDTH", 5.87, 5.87, primary_basis="DWG dim", challenger_basis="scaled")
    assert f1["VERDICT"] == "AGREE_ON_NUMBER_ONLY"
    f2 = CC.compare_field("CONT", True, False)
    with pytest.raises(ValueError):
        CC.reconcile("x", [f1, f2])                     # open fields need an authority
    r = CC.reconcile("x", [f1, f2], decided_by="NONE", decision="no section")
    assert r["STATUS"] == "UNRESOLVED" and r["MAJORITY_VOTE"] is False and r["AVERAGED"] is False
    assert CC.challenge_required(kind="FACADE_OR_PARAPET_M2", quantity_impact_m2=6.0) and not CC.challenge_required(kind="CURVE_M2", quantity_impact_m2=1.0)
    assert CC.challenge_required(kind="DOUBLE_HEIGHT_INTERPRETATION")
