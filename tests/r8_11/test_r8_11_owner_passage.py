"""R8.11 owner clarification (Hall / Lobby open passage): a part-bound physical fact that reviews the H2431
closure and reclassifies the H2430 blocker - and changes no TS01 input, no site, no area, no frozen rule."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from engine.source import owner_claims as OC, topology_closures as TC, wall_bands as WB
from tests.r8_8 import helpers as H

ROOT = Path(__file__).resolve().parents[2]
REG = Path(__file__).parent / "registers"
sys.path.insert(0, str(ROOT / "research/external_engine_lab"))


def _r(name):
    return json.loads((REG / f"{name}.json").read_text())


@pytest.fixture(scope="module")
def OF():
    import r8_11_owner_facts as m
    return m


def synthetic(dx=0.0, rid="REV_A", region="R1"):
    g = {"470": (0, 0, 300, 0), "471": (300, 0, 465.7, 0), "477": (0, 20, 465.7, 20), "2430": (465.7, 0, 465.7, 20),
         "2431": (585.4, 0.9, 585.4, 20), "2296": (585.4, 0, 910, 0), "2297": (585.4, 20, 910, 20)}
    parts = [H.seg(int(h), *(v + dx if i == 0 and h == "2430" else v for i, v in enumerate(c)),
                   layer="DIM" if h in ("2430", "2431") else "WALL") for h, c in g.items()]
    return H.inp(parts, revision=H.rev(rid=rid), region_id=region)


# ------------------------------------------------------------------------------- binding
def test_the_fact_applies_to_its_own_source(OF):
    i = synthetic()
    fact = OF.build(i)["facts"][0]
    b = OF.bind(fact, i)
    assert b["state"] == OC.APPLIES and OF.readings([b])["2430"][0] == OF.REAL_WALL_END


def test_a_moved_part_makes_the_fact_stale_and_it_classifies_nothing(OF):
    fact = OF.build(synthetic())["facts"][0]
    b = OF.bind(fact, synthetic(dx=1.0))
    assert b["state"] != OC.APPLIES and OF.readings([b]) == {}
    assert {x["state"] for x in b["parts"] if x["handle"] == "2430"} == {OC.STALE_PART_FINGERPRINT}


def test_the_fact_never_transfers_to_another_revision_or_region(OF):
    fact = OF.build(synthetic())["facts"][0]
    assert OF.bind(fact, synthetic(rid="REV_B"))["state"] == OC.SOURCE_SCOPE_MISMATCH
    assert OF.bind(fact, synthetic(region="R2"))["state"] == OC.REGION_SCOPE_MISMATCH


def test_the_committed_fact_carries_no_quantity_and_defers_the_role_claim():
    raw = json.loads((ROOT / "data/registry/OWNER_PHYSICAL_FACTS.json").read_text())
    (f,) = raw["facts"]
    assert {p["handle"] for p in f["parts"]} == {"470", "471", "477", "2430", "2431", "2296", "2297"}
    assert all(len(p["fingerprint"]) == 64 for p in f["parts"])
    assert not {"value", "quantity", "area", "area_m2", "width_mm"} & set(f)
    assert any("part-role claim" in x for x in f["not_applied_in_r8_11"])
    assert "a wall or block quantity across the opening" in f["never"]


# ------------------------------------------------------------------------------- registers
def test_the_h2431_closure_is_owner_reviewed_still_zero_material_and_not_released():
    reg = _r("TOPOLOGY_CLOSURE_REGISTER")
    (cid, rv), = reg["owner_review"].items()
    assert reg["applied"]["NEW_K2"] == [cid]
    assert rv["state"] == "REVIEWED_BY_OWNER" and rv["fact_binding"] == OC.APPLIES
    assert rv["release_level"].startswith(TC.AUTHORISED_FOR_SHADOW) and rv["authorised_for_release"].startswith("NO")
    assert rv["material"].startswith("NONE") and rv["geometry_unchanged"]
    c = next(x for x in reg["NEW_K2"] if x["closure_id"] == cid)
    assert c["physical_material"] == "NONE" and c["geometry"] == [109893.4, 15029.72, 109893.4, 15049.72]


def test_nothing_crosses_the_open_passage():
    for c in _r("TOPOLOGY_CLOSURE_REGISTER")["NEW_K2"]:
        ev = set(c["source_evidence"])
        assert not (ev & {"470", "471", "477", "2430"} and ev & {"2296", "2297", "2431"})
    op = _r("OWNER_PHYSICAL_FACT_REGISTER")["owner_passage"]
    assert op["topology"]["across_the_opening"].startswith("NOTHING") and op["physically_connected"]
    assert op["material_on_any_closure"] == "NONE" and op["trade_allocation"] == "NOT_ALLOCATED"


def test_the_passage_width_is_measured_not_the_owners_approximation():
    op = _r("OWNER_PHYSICAL_FACT_REGISTER")["owner_passage"]
    assert op["clear_width_mm_measured"] == 1196.45 and op["owner_approx_clear_width_m"] == 1.0
    assert op["wall_thickness_mm"] == 200.0 and op["clear_height_m"] == 2.2 and op["door"] == "NONE"
    assert op["side_construction"] == "BLOCK + PLASTER" and op["width_discrepancy_mm"] == 196.4
    s = op["trade_surfaces_record_only"]
    assert {"floor_strip", "left_reveal_west_jamb", "right_reveal_east_jamb", "top_reveal_soffit",
            "wall_faces_around"} <= set(s)
    assert s["right_reveal_east_jamb"]["same_plan_segment_as"] == "TC-aea10821cffe20ff"


def test_the_fact_changed_no_ts01_input_and_no_frozen_rule():
    F = _r("OWNER_PHYSICAL_FACT_REGISTER")
    u = F["unchanged"]
    assert u["RUN_INPUT_DIGEST_same_as_before_the_fact"] and u["wall_band_policy"] == WB.POLICY_ID
    assert _r("WALL_BAND_REGISTER")["policy"]["digest"] == WB.policy_record()["digest"]
    assert F["binding"]["OLD_K1"][0]["state"] == OC.SOURCE_SCOPE_MISMATCH
    assert {r: v[1] for r, v in u["rows"].items() if v[1] is not None} == {
        "Q-03": 17.7425, "Q-03P": 11.685, "Q-11": 17.7425, "Q-12": 11.685}


def test_h2430_physical_role_resolved_but_generic_classification_untouched():
    c = _r("WALL_BAND_REGISTER")["cap_analysis"]["2430"]
    assert c["classification"] == WB.CAP_UNRESOLVED                       # the blind generic result stands
    assert c["physical_role"]["state"] == "RESOLVED: REAL_WALL_END"
    assert c["physical_role"]["engine_representation"].startswith("NONE")


def test_q14_is_an_engine_limitation_with_no_value_and_no_owner_action():
    q = _r("Q14_STATUS")
    assert q["state"] == "BLOCKED_ENGINE_LIMITATION" and q["value"] is None
    r = q["reclassification"]
    assert r["owner_action"] == "NONE" and r["value_computed"] is False and r["physical_fact"].startswith("RESOLVED")
    assert any(b.startswith("PASSAGE_SOFFIT_ALLOCATION") for b in q["release_blockers"])


def test_q13_still_has_more_than_the_wardrobe_fact_so_no_owner_question():
    t = _r("Q13_STATUS")["sole_blocker_test"]
    assert t["answer"] == "NO" and "ENGINE_LIMITATION:WALL_END_REPRESENTATION_PENDING:2430" in t["other_blockers"]
    oa = _r("OWNER_ACTION_REGISTER")
    assert oa["required_now"] == [] and oa["answered_in_r8_11"][0]["never_ask_again"]


def test_the_decision_register_answers_the_six_clarification_questions():
    a = _r("R8_11_DECISION_REGISTER")["owner_clarification_addendum"]
    assert {k.split("_")[0] for k in a if k[0].isdigit()} == {"1", "2", "3", "4", "5", "6"}
