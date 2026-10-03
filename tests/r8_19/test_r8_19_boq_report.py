"""R8.19 §23-§25: BOQ_REPORT_LAYER_V1 - presentation only: quantities copied verbatim from evidence rows, statuses
derived (never typed), traceability on every row, no calculation, no pricing. Synthetic only."""

from __future__ import annotations

import copy

from engine.source import boq_report as BR

TRACE = {"run_id": "RUN-1", "source_revision": "REV", "trade_row": "T", "sites": ["S1", "S2"],
         "surface_ids": ["s1"], "authority_digest": "abc", "rule_ids": ["R@v1"], "owner_facts": ["F@v1"],
         "release_state": "SHADOW"}
ITEMS = {r: {"item_code": f"IT-{r}", "trade": "PAINT", "description_ar": "دهانات", "description_en": "Paint"}
         for r in ("COMPLETE", "SUB", "BLOCK", "REL")}


def ev(row_id, complete, sub, unresolved=(), release="SHADOW"):
    return dict(TRACE, row_id=row_id, unit="m2", complete=complete, authorised_subtotal=sub,
                unresolved=list(unresolved), release_state=release, floor="F2", source="DXF", blockers=["SHADOW"],
                per_room={"S1": {"zones": ["BED"], "qty": 10.25}, "S2": {"zones": ["HALL"], "qty": 20.5}})


EVS = [ev("COMPLETE", 30.75, 30.75), ev("SUB", None, 28.0, ["COLUMN"]), ev("BLOCK", None, None, ["X"]),
       ev("REL", 30.75, 30.75, release=BR.RELEASED)]


def rep():
    return BR.build(EVS, ITEMS, run={"run_id": "RUN-1"})


def total(r, rid):
    return next(x for x in r["rows"] if x["evidence_row"] == rid and x["ROW_KIND"] == "TOTAL")


def test_b1_a_complete_row_is_copied_verbatim():
    r = rep()
    t = total(r, "COMPLETE")
    assert t["STATUS"] == BR.COMPLETE and t["QTY"] == 30.75 and t["approved_for_boq"] is False
    assert BR.validate(r, EVS, ITEMS)["state"] == "PASS"


def test_b2_a_subtotal_is_shown_as_a_subtotal_never_as_approved():
    t = total(rep(), "SUB")
    assert t["STATUS"] == BR.SUBTOTAL and t["QTY"] == 28.0 and t["approved_for_boq"] is False


def test_b3_a_blocked_row_has_no_quantity():
    r = rep()
    assert all(x["QTY"] is None and x["STATUS"] == BR.BLOCKED for x in r["rows"] if x["evidence_row"] == "BLOCK")


def test_b4_released_needs_a_release_record():
    r = rep()
    assert total(r, "REL")["STATUS"] == BR.RELEASED and total(r, "REL")["approved_for_boq"] is True
    assert sum(1 for x in r["rows"] if x["STATUS"] == BR.RELEASED) == 3


def test_b5_a_manual_edit_or_a_status_tamper_is_refused():
    r = rep()
    edited = copy.deepcopy(r)
    total(edited, "COMPLETE")["QTY"] = 30.76
    assert BR.validate(edited, EVS, ITEMS)["state"] == "FAIL"
    tampered = copy.deepcopy(r)
    total(tampered, "SUB")["approved_for_boq"] = True
    v = BR.validate(tampered, EVS, ITEMS)
    assert v["state"] == "FAIL" and v["status_violations"] == ["IT-SUB"]


def test_b6_every_row_keeps_its_trace():
    r = rep()
    assert all(set(BR.TRACE) <= set(x["trace"]) for x in r["rows"])
    assert [x["trace"]["sites"] for x in r["rows"] if x["evidence_row"] == "COMPLETE"] == [["S1", "S2"], ["S1"], ["S2"]]
    broken = copy.deepcopy(r)
    del broken["rows"][0]["trace"]["authority_digest"]
    assert BR.validate(broken, EVS, ITEMS)["untraced"] == ["IT-COMPLETE"]


def test_b7_the_report_never_calculates():
    odd = [dict(EVS[0], complete=31.0, authorised_subtotal=31.0)]          # rooms sum to 30.75, the row says 31.0
    r = BR.build(odd, ITEMS, run={})
    assert total(r, "COMPLETE")["QTY"] == 31.0 and r["calculates"] is False and r["pricing"] is None
    assert "a calculation, sum or rounding in the report" in BR.policy_record()["never"]
