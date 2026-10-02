"""R8.15 §35 + §23: a FULL-HEIGHT passage and a passage WITH HEAD side by side; reveal depth basis (US-07)."""

from __future__ import annotations

import json
from pathlib import Path

from engine.source import opening_reveals as OR, owner_facts as OF, trade_strips as TS
from tests.r8_8 import helpers as H

ROOT = Path(__file__).resolve().parents[2]
MBD = next(f for f in json.loads((ROOT / "data/registry/OWNER_PHYSICAL_FACTS.json").read_text())["facts"]
           if f["fact_id"] == "QORTUBA-NEW-MB-DRESS-PASSAGE-FULL-HEIGHT-OWNER-001")
HALL = {"passage_id": "P-HALL", "width": 120.0, "wall_thickness": 20.0,
        "polygon": [(0, 0), (120, 0), (120, 20), (0, 20)]}
MB = {"passage_id": "P-MB", "width": 120.0, "wall_thickness": 15.0,
      "polygon": [(0, 0), (15, 0), (15, 120), (0, 120)]}
FIN = {"LEFT_JAMB": "PLASTER", "RIGHT_JAMB": "PLASTER", "TOP_SOFFIT": "PLASTER"}


def reveals(p, head, **kw):
    return OR.passage_reveals(p, head=head, finish=FIN, unit_to_m=0.01, **kw)


def test_the_full_height_owner_fact_is_recorded_for_the_new_revision_only():
    f = OF.from_record(MBD)
    assert f.kind == "PASSAGE_HEAD_CONDITION" and f.statement["head_condition"] == "FULL_HEIGHT"
    assert OF.PASSAGE_ATTRIBUTES in f.allowed_domains and OF.TOPOLOGY_ROLE not in f.allowed_domains
    assert OF.bind(f, H.inp([H.seg(1, 0, 0, 10, 0)]))["binding"] == OF.REJECTED_SCOPE


def test_a_full_height_passage_has_no_top_soffit_and_the_ceiling_continues():
    r = reveals(MB, OR.FULL_HEIGHT, clear_height=None, jamb_authority={OR.LEFT_JAMB: "cap"},
                jamb_absent={OR.RIGHT_JAMB: "ABUTS_CONTINUOUS_WALL_FACE"}, height_basis="FULL_HEIGHT")
    assert not [s for s in r["surfaces"] if s["surface"] == OR.TOP_SOFFIT]
    assert {"surface": OR.TOP_SOFFIT, "state": "NO_HEAD_FULL_HEIGHT"} in r["missing"]
    assert r["ownership"]["CEILING_EXCLUDES_M2"] == 0.0 and r["ownership"]["CEILING_STATE"] == "CEILING_CONTINUES"


def test_side_jamb_records_remain_on_a_full_height_passage():
    r = reveals(MB, OR.FULL_HEIGHT, clear_height=None, jamb_authority={OR.LEFT_JAMB: "cap"},
                jamb_absent={OR.RIGHT_JAMB: "ABUTS_CONTINUOUS_WALL_FACE"}, height_basis="FULL_HEIGHT")
    j = [s for s in r["surfaces"] if s["surface"] == OR.LEFT_JAMB]
    assert len(j) == 1 and abs(j[0]["depth_m"] - 0.15) < 1e-12 and j[0]["area_m2"] is None   # height not set here
    assert {"surface": OR.RIGHT_JAMB, "state": "ABUTS_CONTINUOUS_WALL_FACE"} in r["missing"]


def test_the_ceiling_row_includes_the_full_height_footprint_and_excludes_the_hall_soffit():
    strips = [{"id": "P-HALL", "kind": "OPEN_PASSAGE", "location": TS.INSIDE_SITE, "site": "S1", "sides": ["S1"],
               "area_m2": 0.24}, {"id": "P-MB", "kind": "OPEN_PASSAGE", "location": TS.INSIDE_SITE, "site": "S2",
                                  "sides": ["S2"], "area_m2": 0.18}]
    tr = {"S1": "CEILING_BY_AREA", "S2": "CEILING_BY_AREA"}
    heads = {"P-HALL": OR.WITH_HEAD, "P-MB": OR.FULL_HEIGHT}
    aud = [TS.audit_v2(s, {"S1", "S2"}, tr, "CEILING_BY_AREA", trade=TS.CEILING, head=heads[s["id"]]) for s in strips]
    assert [a["state"] for a in aud] == [TS.SOFFIT_EXCLUDED, TS.INCLUDED]
    eff = TS.row_effect_v2(aud)
    assert eff["soffit_exclusion_m2"] == 0.24 and eff["passages_included"] == ["P-MB"] and eff["release"] == []


def test_the_old_qp18_is_not_the_authority():
    assert any("QP-18" in x for x in MBD["does_not_use"])
    assert MBD["scope"]["source_revision_id"] == "QORTUBA_REV_NEW"
    assert any(x.startswith("the old Qortuba revision") for x in MBD["transfer_forbidden"])


def test_the_hall_passage_keeps_its_top_soffit():
    r = reveals(HALL, OR.WITH_HEAD, clear_height=2.2, jamb_authority={OR.LEFT_JAMB: "a", OR.RIGHT_JAMB: "b"})
    s = [x for x in r["surfaces"] if x["surface"] == OR.TOP_SOFFIT]
    assert len(s) == 1 and abs(s[0]["area_m2"] - 1.2 * 0.2) < 1e-12
    assert r["ownership"]["CEILING_STATE"] == "SOFFIT_FOOTPRINT_REMOVED"


def test_two_passages_with_different_heads_coexist_and_no_footprint_has_two_owners():
    hall = reveals(HALL, OR.WITH_HEAD, clear_height=2.2, jamb_authority={OR.LEFT_JAMB: "a", OR.RIGHT_JAMB: "b"})
    mb = reveals(MB, OR.FULL_HEIGHT, clear_height=None, jamb_authority={OR.LEFT_JAMB: "cap"})
    claims = [("P-HALL", "TOP_SOFFIT")] + [("P-MB", "CEILING")]
    assert OR.ownership_guard(claims) == []
    assert OR.ownership_guard(claims + [("P-HALL", "CEILING")]) == [["P-HALL", ["CEILING", "TOP_SOFFIT"]]]
    assert hall["ownership"]["CEILING_EXCLUDES_M2"] > 0 and mb["ownership"]["CEILING_EXCLUDES_M2"] == 0.0


def test_source_reveal_depth_wins_and_us07_is_fallback_only():
    d = OR.reveal_depth(0.20, 0.25, "US-07")
    assert d["basis"] == OR.SOURCE_DEPTH and d["depth_m"] == 0.20 and not d["default_used"]
    f = OR.reveal_depth(None, 0.25, "US-07")
    assert f["basis"] == OR.DEFAULT_DEPTH and f["depth_m"] == 0.25 and f["default_used"]
    assert OR.reveal_depth(None)["basis"] == OR.DEPTH_UNRESOLVED
    r = reveals(HALL, OR.WITH_HEAD, clear_height=2.2, jamb_authority={OR.LEFT_JAMB: "a"}, default_depth_m=0.25,
                default_ref="US-07")
    j = next(s for s in r["surfaces"] if s["surface"] == OR.LEFT_JAMB)
    assert abs(j["area_m2"] - 0.2 * 2.2) < 1e-12 and abs(j["area_at_default_depth_m2"] - 0.25 * 2.2) < 1e-12
    assert j["depth_basis"] == OR.SOURCE_DEPTH
