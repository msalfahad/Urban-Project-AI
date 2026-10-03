"""R8.13 §31: the owner floor object-footprint fact as a scoped TradeObjectFootprintPolicy, the wet / service finish
scope and the skirting unit - synthetic and on the committed data file; never a topology input."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from engine.source import owner_facts as OF, owner_method_facts as MF, room_topology as RT, run_manifest as RM
from engine.source import topology_closures as TC, trade_regions as TR, trade_strips as TS
from tests.r8_8 import helpers as H

ROOT = Path(__file__).resolve().parents[2]
DATA = json.loads((ROOT / "data/registry/OWNER_FINISH_FACTS.json").read_text())


def fact(**over):
    rec = {"fact_id": "F-FLOOR", "version": 1, "kind": "TRADE_OBJECT_FOOTPRINT", "authority": ["PROJECT_OWNER"],
           "scope": {"source_revision_id": H.REV, "source_anchor_sha256": "a" * 64, "region_id": H.REGION,
                     "frame_id": "MF:" + H.REGION, "trade": "FLOOR_FINISH", "space_classes": ["DRY_INTERNAL_ROOM"],
                     "finish": "PORCELAIN_DRY_FLOOR"},
           "statement": {"trade": "FLOOR_FINISH", "object_class": TR.ANY_NON_PARTITION_OBJECT,
                         "treatment": TR.FOOTPRINT_INCLUDED}, "unit": "m2"}
    rec.update(over)
    return MF.from_record(rec)


RULE = TR.TradeTreatmentRule("R", 1, "FLOOR_FINISH", "TEST", (), otherwise="PORCELAIN_DRY_FLOOR")
SOFA = {"effect": "CHANGES_AREA", "sources": ["REV_A|H40||SEGMENT|0"]}            # a non-partition object in the room


def room_with(obj_layer):
    walls = [H.seg(1, 0, 0, 500, 0), H.seg(2, 500, 0, 500, 400), H.seg(3, 500, 400, 0, 400), H.seg(4, 0, 400, 0, 0)]
    pts = [(100, 100), (300, 100), (300, 160), (100, 160)]
    obj = [H.part(40, "SEGMENT", (*pts[i], *pts[(i + 1) % 4]), layer=obj_layer, idx=i) for i in range(4)]
    return H.inp(walls + obj, texts=[H.text(5, "BED", 400, 300)])


# ------------------------------------------------------------------------------- the policy
def test_whole_room_with_a_sofa_or_a_built_in_wardrobe_takes_no_deduction():
    f = fact()
    pol = MF.footprint_policy(f)
    assert (pol.trade, pol.object_class, pol.treatment) == ("FLOOR_FINISH", TR.ANY_NON_PARTITION_OBJECT,
                                                            TR.FOOTPRINT_INCLUDED)
    for obj in (SOFA, dict(SOFA, sources=["REV_A|H41||SEGMENT|0"])):                  # sofa / built-in wardrobe
        m = TR.object_materiality(obj, RULE, (pol,))
        assert m["state"] == TR.NON_MATERIAL and m["footprint_policy"] == "F-FLOOR@v1"
    assert MF.footprint_area(20.0, [1.2, 0.6], pol.treatment) == 20.0


def test_footprint_deducted_is_a_deterministic_deduction_synthetic_only():
    d = fact(statement={"trade": "FLOOR_FINISH", "object_class": TR.ANY_NON_PARTITION_OBJECT,
                        "treatment": TR.FOOTPRINT_DEDUCTED})
    pol = MF.footprint_policy(d)
    assert MF.footprint_area(20.0, [1.2, 0.6, 0.3], pol.treatment) == MF.footprint_area(20.0, [0.3, 1.2, 0.6],
                                                                                         pol.treatment) == 17.9
    assert TR.object_materiality(SOFA, RULE, (pol,))["state"] == TR.MATERIAL           # the role now matters


def test_no_policy_is_blocked_trade_rule():
    m = TR.object_materiality(SOFA, RULE, ())
    assert m["state"] == TR.MATERIAL and "no authority says how this trade treats an object footprint" in m["why"]
    assert MF.footprint_area(20.0, [1.2], None) is None


def test_scope_selected_plan_only_no_revision_or_project_transfer():
    f = fact()
    inp = H.inp([H.seg(1, 0, 0, 10, 0)])
    assert MF.bind(f, inp)["binding"] == "APPLIES"
    for other in (replace(inp, revision=H.rev("REV_B")), replace(inp, revision=H.rev(sha="b" * 64)),
                  replace(inp, region_id="R2"), replace(inp, frame_id="MF:R2")):
        assert MF.bind(f, other)["binding"] == OF.REJECTED_SCOPE
    b = MF.bind(f, inp)
    assert MF.policies_for([(f, b)], trade="FLOOR_FINISH", space_classes=["DRY_INTERNAL_ROOM"],
                           finish="PORCELAIN_DRY_FLOOR")
    for trade, cls, fin in (("CEILING", ["DRY_INTERNAL_ROOM"], None), ("FLOOR_FINISH", ["WET_SERVICE_ROOM"], None),
                            ("FLOOR_FINISH", ["DRY_INTERNAL_ROOM", "WET_SERVICE_ROOM"], None),
                            ("FLOOR_FINISH", ["DRY_INTERNAL_ROOM"], "CERAMIC_WET_FLOOR")):
        assert MF.policies_for([(f, b)], trade=trade, space_classes=cls, finish=fin) == ()
        assert MF.row_outcome(f, b, trade=trade, space_classes=cls, finish=fin, used=False) == OF.REJECTED_SCOPE
    assert MF.row_outcome(f, b, trade="FLOOR_FINISH", space_classes=["DRY_INTERNAL_ROOM"], used=True) == OF.APPLIED


def test_a_method_fact_never_reaches_topology():
    with pytest.raises(ValueError):
        fact(allowed_domains=[OF.TOPOLOGY_ROLE])
    with pytest.raises(ValueError):
        fact(allowed_domains=["PASSAGE_DETECTION"])
    assert set(fact().allowed_domains) == {MF.TRADE_FOOTPRINT}


def test_the_policy_does_not_alter_the_topology_digest_but_alters_the_q13_row_digest_only():
    inp = room_with("FURNITURE")
    a = RT.run(inp, frame_insert=None, closure_policy=TC.POLICY_ID)
    b = RT.run(inp, frame_insert=None, closure_policy=TC.POLICY_ID)                      # the fact is no RT input
    top = a["run_manifest"]["RUN_INPUT_DIGEST"]
    assert top == b["run_manifest"]["RUN_INPUT_DIGEST"]
    pol = MF.footprint_policy(fact())
    k = lambda pols, facts=(): RM.row_authority_digest(top, row_id="Q-13", row_method="m", trade_rules=["R@v1"],
                                                       footprint_policies=pols, owner_facts_applied=facts)["digest"]
    with_fact = k([f"{pol.policy_id}@v{pol.version}:{pol.trade}:{pol.treatment}"], ["F-FLOOR@v1"])
    assert with_fact != k([])
    q14 = lambda: RM.row_authority_digest(top, row_id="Q-14", row_method="m", trade_rules=["C@v1"],
                                          footprint_policies=["CEIL@v1:CEILING:FOOTPRINT_INCLUDED"])["digest"]
    assert q14() == q14()                                  # Q-14 never lists the floor policy, so it cannot move


def test_floor_is_m2_and_skirting_is_lm():
    dry = MF.from_record(next(f for f in DATA["facts"] if f["kind"] == "MEASUREMENT_UNIT"))
    assert dry.statement["floor_unit"] == "m2" and dry.statement["skirting_unit"] == "lm" and dry.unit == "lm"
    floor = MF.from_record(next(f for f in DATA["facts"] if f["kind"] == "TRADE_OBJECT_FOOTPRINT"))
    assert floor.unit == "m2"


def test_3_20_m_has_its_exact_scope_and_does_not_transfer():
    wet = MF.from_record(next(f for f in DATA["facts"] if f["kind"] == "FINISH_SCOPE"))
    assert wet.statement["wall_finish_height_m"] == 3.20
    assert wet.scope["source_revision_id"] == "QORTUBA_REV_NEW" and wet.scope["plan"] == "PLAN_VARIANT_4_SELECTED"
    assert set(wet.scope["space_classes"]) == {"WET_SERVICE_ROOM", "SERVICE_ROOM"}
    for p in ("P7757", "Al Rashed", "the old Qortuba revision", "an Urban default", "any future villa or project"):
        assert p in wet.transfer_forbidden
    assert MF.bind(wet, H.inp([H.seg(1, 0, 0, 10, 0)]))["binding"] == OF.REJECTED_SCOPE   # any other source


def test_a_change_needs_a_scoped_supersession_and_a_silent_duplicate_is_a_conflict():
    wet = next(f for f in DATA["facts"] if f["kind"] == "FINISH_SCOPE")
    rules = [{"ref": "QP-01 QORTUBA_WALL_TILE_HEIGHT = 3.00 m", "trade": "WALL_TILE", "attribute": "HEIGHT_M",
              "value": 3.00}]
    assert MF.conflicts([MF.from_record(wet)], rules) == []
    silent = dict(wet, relations=[r for r in wet["relations"] if r["relation"] != MF.SUPERSEDED_IN_SCOPE])
    (c,) = MF.conflicts([MF.from_record(silent)], rules)
    assert (c["fact_value"], c["rule_value"]) == (3.20, 3.00)
    with pytest.raises(ValueError):
        MF.from_record(dict(wet, relations=[{"rule": "QP-01", "relation": MF.SUPERSEDED_IN_SCOPE}]))   # no scope


def test_the_committed_facts_load_and_relate_only_through_known_relations():
    fs = [MF.from_record(f) for f in DATA["facts"]]
    assert {f.kind for f in fs} == {"TRADE_OBJECT_FOOTPRINT", "MEASUREMENT_UNIT", "FINISH_SCOPE"}
    assert all(r["relation"] in MF.RELATIONS for f in fs for r in f.relations)
    floor = next(f for f in fs if f.kind == "TRADE_OBJECT_FOOTPRINT")
    assert floor.statement["treatment"] == TR.FOOTPRINT_INCLUDED and \
        {"built-in wardrobes", "loose furniture", "sofas"} <= set(floor.statement["includes"])
    assert "'ignore furniture globally'" in floor.statement["is_not"]
    assert MF.policy_record()["digest"] and len(MF.policy_record()["digest"]) == 64


# ------------------------------------------------------------------------------- strips (§19)
def test_strip_audit_separates_thresholds_from_passages():
    th = {"id": "T1", "kind": "THRESHOLD", "location": TS.SEPARATE_SITE, "sides": ["A", "B"], "area_m2": 0.15}
    op = {"id": "P1", "kind": "OPEN_PASSAGE", "location": TS.INSIDE_SITE, "site": "A", "area_m2": 0.24}
    tr = {"A": "PORCELAIN", "B": "CERAMIC"}
    a = TS.audit(th, {"A"}, tr, "PORCELAIN")
    assert a["state"] == TS.EXCLUDED and not a["in_row_total"]
    b = TS.audit(op, {"A"}, tr, "PORCELAIN")
    assert b["state"] == TS.INCLUDED and b["in_row_total"]
    assert TS.audit(op, {"A"}, {"A": "CERAMIC"}, "PORCELAIN")["state"] == TS.SIDES_DIFFER
    assert TS.audit(op, {"A"}, {}, "PORCELAIN")["state"] == TS.SIDE_UNRESOLVED
    assert TS.audit(th, {"C"}, tr, "PORCELAIN")["state"] == TS.NOT_IN_ROW
    assert TS.audit(th, {"A"}, tr, "PORCELAIN", allocation={"ref": "X", "to": "ROW"})["state"] == TS.ALLOCATED
    e = TS.row_effect([a, b])
    assert e == {"blocking": [], "release": ["T1"], "included": ["P1"], "excluded_area_m2": 0.15,
                 "included_area_m2": 0.24}
