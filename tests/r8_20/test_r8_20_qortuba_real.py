"""R8.20 on the committed registers: owner closure reviews bound to digests, the I1471 rationale (no geometry change,
H716 by geometry), release levels, zero quantity change, the corrected BOQ statuses, the XLSX view, plans and gates."""

from __future__ import annotations

import json
from pathlib import Path

from engine.source import boq_report as BR, closure_release as CR

REG = Path(__file__).parent / "registers"


def _r(n):
    return json.loads((REG / f"{n}.json").read_text())


def test_the_three_owner_reviews_are_accepted_for_the_exact_closure_records():
    h = _r("HUMAN_REVIEW_REGISTER")
    assert set(h["states"]) == {"H2430", "H2431", "I1471"} and h["self_approved"] is False
    assert all(v["state"] == "ACCEPTED" and v["digest_match"] and v["satisfies_human_review"] is True
               for v in h["states"].values())
    assert all(r["reviewer_role"] == "PROJECT_OWNER" for r in h["reviews"])


def test_no_closure_reaches_the_reviewed_level_and_nothing_is_released():
    c = _r("CLOSURE_RELEASE_STATUS")
    assert c["released_level_exists"] is False and c["production"] == "NO"
    for v in c["closures"].values():
        assert v["maximum_justified_level"] == "AUTHORISED_FOR_SHADOW" != CR.REVIEWED
        assert v["missing_for_next_level"] == ["CROSS_ROUTE_AGREEMENT", "SOURCE_ANCHOR"]
        assert v["evidence"]["HUMAN_REVIEW"] is True and v["releases_anything"] is False


def test_the_i1471_rationale_changes_no_geometry_and_the_column_is_found_by_geometry():
    i = _r("I1471_COLUMN_CONCEALMENT_REGISTER")
    g = i["geometry_evidence"]
    assert sorted(v["width_mm"] for v in g["bands"].values()) == [150.0, 200.0] and g["stagger_mm"] == 50.0
    assert g["column"]["deterministic"] and g["column"]["column"] == "QORTUBA_REV_NEW|H716||SEGMENT"
    assert i["geometry_changed"] is False and i["normalised_to_150mm"] is False and i["quantity_effect"] == "NONE"
    f = _r("OWNER_PHYSICAL_FACT_REGISTER")
    assert f["allowed_domains"] == [] and f["binding"]["binding"] == "APPLIES" and f["urban_rule_created"] is False


def test_every_published_quantity_and_digest_is_unchanged():
    q = _r("QUANTITY_REGRESSION")
    assert q["all_unchanged"] and q["all_digests_same"] and len(q["rows"]) == 17
    assert all(q["reproduces_r8_19_blind"].values())


def test_boq_statuses_follow_quantity_affecting_blockers_and_the_xlsx_view_validates():
    b = _r("BOQ_REPORT_SHADOW")
    assert b["status_changes_vs_r8_19"] == {"Q-03P": {"R8.19": BR.COMPLETE, "R8.20": BR.SUBTOTAL},
                                            "Q-12": {"R8.19": BR.COMPLETE, "R8.20": BR.SUBTOTAL}}
    assert BR.validate(b["report"], b["evidence_rows"], _r("BOQ_REPORT_SCHEMA")["items"])["state"] == "PASS"
    assert b["approved_for_boq"] == 0
    x = _r("BOQ_XLSX_STATUS")
    assert x["readback_validation"]["state"] == "PASS" and not x["formulas"] and x["statuses_visible"]
    assert x["rows_exported"]["traceability"] == len(b["report"]["rows"])
    assert x["rows_exported"]["summary"] + x["rows_exported"]["breakdown"] == len(b["report"]["rows"])


def test_plans_gates_and_owner_actions():
    assert _r("SOURCE_ANCHOR_STATUS")["state"] == "NOT_ESTABLISHED"
    assert _r("SOURCE_ANCHOR_PLAN")["recommended"] == "A" and _r("SOURCE_ANCHOR_PLAN")["downloads"] == "NONE"
    sp = _r("SECOND_PROJECT_PLAN")
    assert not sp["candidates"]["P7757"]["blind_eligible"] and sp["candidates"]["unseen Kuwait villa"]["recommended"]
    assert _r("MCP_DONOR_REVIEW")["duplicating_full_engines"] is False
    g = _r("PRODUCTION_GATE_STATUS")
    assert g["production_migration"] == "NO" and g["firestore_approved_writes"] == "NONE"
    d = _r("R8_20_DECISION_REGISTER")
    assert d["gates"]["PRODUCTION_MIGRATION"] == "NO" and len(d["answers"]) == 31
    assert _r("OWNER_ACTION_REGISTER")["required_now"] == []
