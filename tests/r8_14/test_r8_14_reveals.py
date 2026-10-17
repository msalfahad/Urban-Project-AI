"""R8.14 §38: open-passage reveal surfaces and the soffit / ceiling double-count guard."""

from __future__ import annotations

import json
from pathlib import Path

from engine.source import opening_reveals as OR, owner_facts as OF, owner_method_facts as MF, room_topology as RT
from engine.source import topology_closures as TC, trade_strips as TS
from tests.r8_8 import helpers as H
from tests.r8_13.test_r8_13_wall_band_v4 import box, wall

ROOT = Path(__file__).resolve().parents[2]
FACTS = {f["fact_id"]: f for f in json.loads((ROOT / "data/registry/OWNER_METHOD_FACTS.json").read_text())["facts"]}
P = {"passage_id": "OP-1", "polygon": [(600, 400), (600, 420), (720, 420), (720, 400)], "width": 120.0,
     "wall_thickness": 20.0}
U = 0.01                                                                     # native unit -> m (10 mm units)
FIN = {OR.LEFT_JAMB: "PLASTER", OR.RIGHT_JAMB: "PLASTER", OR.TOP_SOFFIT: "PLASTER"}


def passage_run():
    p = box() + wall(lower=((0, 300), (300, 600))) + \
        [H.seg(20, 720, 400, 1000, 400), H.seg(21, 720, 420, 1000, 420), H.seg(91, 720, 400, 720, 420, layer="DIM")]
    return RT.run(H.inp(p, texts=[H.text(5, "HALL", 500, 100), H.text(6, "LOBBY", 500, 700)]), frame_insert=None,
                  closure_policy=TC.POLICY_ID)


def test_an_open_passage_with_a_head_has_a_separate_soffit_from_source_geometry():
    r = OR.passage_reveals(P, head=OR.WITH_HEAD, clear_height=2.2, jamb_authority={OR.LEFT_JAMB: "W", OR.RIGHT_JAMB: "E"},
                           finish=FIN, unit_to_m=U)
    (s,) = [x for x in r["surfaces"] if x["surface"] == OR.TOP_SOFFIT]
    assert abs(s["footprint_m2"] - 1.2 * 0.2) < 1e-12 and s["finish"] == "PLASTER"
    assert abs(r["ownership"]["CEILING_EXCLUDES_M2"] - s["footprint_m2"]) < 1e-12


def test_the_normal_ceiling_excludes_the_soffit_footprint_exactly_once():
    a = TS.audit_v2({"id": "OP-1", "kind": "OPEN_PASSAGE", "location": TS.INSIDE_SITE, "site": "S", "area_m2": 0.24},
                    {"S"}, {"S": "CEILING_BY_AREA"}, "CEILING_BY_AREA", trade=TS.CEILING, head=OR.WITH_HEAD)
    assert a["state"] == TS.SOFFIT_EXCLUDED and a["contribution_m2"] == -0.24
    assert OR.ownership_guard([("OP-1", "TOP_SOFFIT"), ("S", "CEILING")]) == []
    assert OR.ownership_guard([("OP-1", "TOP_SOFFIT"), ("OP-1", "CEILING")]) == [["OP-1", ["CEILING", "TOP_SOFFIT"]]]


def test_left_and_right_jambs_are_separate_reveal_surfaces_and_paint_is_never_assumed():
    r = OR.passage_reveals(P, head=OR.WITH_HEAD, clear_height=2.2, jamb_authority={OR.LEFT_JAMB: "W", OR.RIGHT_JAMB: "E"},
                           finish=FIN, unit_to_m=U)
    jambs = {x["surface"]: x for x in r["surfaces"] if x["surface"] != OR.TOP_SOFFIT}
    assert set(jambs) == {OR.LEFT_JAMB, OR.RIGHT_JAMB}
    assert all(abs(j["area_m2"] - 0.2 * 2.2) < 1e-12 and j["trade"] == "PLASTER" for j in jambs.values())
    assert r["ownership"]["PAINT"].startswith("NOT_AUTHORISED")
    assert abs(r["ownership"]["ROOM_WALL_FACE_LOSES"]["per_side_m2"] - 1.2 * 2.2) < 1e-12


def test_nothing_closes_the_passage_and_a_closure_alone_creates_no_plaster():
    run = passage_run()
    assert any(round(p["width"]) == 120 for p in run["passages"])
    assert len([s for s in run["sites"] if s["labels"]]) == 1                      # still one connected site
    r = OR.passage_reveals(P, head=OR.WITH_HEAD, clear_height=2.2, jamb_authority={OR.LEFT_JAMB: None,
                           OR.RIGHT_JAMB: "E"}, finish=FIN, unit_to_m=U)
    assert [m["surface"] for m in r["missing"]] == [OR.LEFT_JAMB]                   # a TCLOSURE-only jamb
    assert {x["surface"] for x in r["surfaces"]} == {OR.RIGHT_JAMB, OR.TOP_SOFFIT}


def test_a_full_height_passage_has_no_soffit_and_the_ceiling_continues():
    r = OR.passage_reveals(P, head=OR.FULL_HEIGHT, clear_height=None, jamb_authority={OR.LEFT_JAMB: "W",
                           OR.RIGHT_JAMB: "E"}, finish=FIN, unit_to_m=U)
    assert not [x for x in r["surfaces"] if x["surface"] == OR.TOP_SOFFIT]
    assert r["ownership"]["CEILING_EXCLUDES_M2"] == 0.0 and r["ownership"]["CEILING_STATE"] == "CEILING_CONTINUES"
    a = TS.audit_v2({"id": "OP-1", "kind": "OPEN_PASSAGE", "location": TS.INSIDE_SITE, "site": "S", "area_m2": 0.24},
                    {"S"}, {"S": "CEILING_BY_AREA"}, "CEILING_BY_AREA", trade=TS.CEILING, head=OR.FULL_HEIGHT)
    assert a["state"] == TS.INCLUDED


def test_an_unknown_head_is_a_release_blocker_never_a_silent_ceiling():
    a = TS.audit_v2({"id": "OP-2", "kind": "OPEN_PASSAGE", "location": TS.INSIDE_SITE, "site": "S", "area_m2": 0.18},
                    {"S"}, {"S": "CEILING_BY_AREA"}, "CEILING_BY_AREA", trade=TS.CEILING, head=None)
    assert a["state"] == TS.HEAD_UNRESOLVED and TS.row_effect_v2([a])["release"] == ["OP-2"]


def test_the_2_20_m_and_soffit_facts_are_scoped_to_the_selected_revision_and_qp18_never_transfers():
    for fid in ("QORTUBA-NEW-OPEN-PASSAGE-REVEALS-PLASTERED-OWNER-001", "QORTUBA-NEW-OPEN-PASSAGE-SOFFIT-NOT-CEILING-OWNER-001"):
        f = MF.from_record(FACTS[fid])
        assert MF.bind(f, H.inp([H.seg(1, 0, 0, 10, 0)]))["binding"] == OF.REJECTED_SCOPE
        assert f.scope["source_revision_id"] == "QORTUBA_REV_NEW" and f.scope["passage_fact"].startswith(
            "QORTUBA-NEW-HALL-LOBBY")
        assert any("QP-18" in t for t in f.transfer_forbidden)
    assert FACTS["QORTUBA-NEW-OPEN-PASSAGE-REVEALS-PLASTERED-OWNER-001"]["statement"]["paint"].startswith("NOT stated")
