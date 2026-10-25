"""T-301: the waterproofing scope inventory (R-T301-WP-INVENTORY-1) on a hand villa, NOT the development villa.

Villa V-301 (hand calculation; foundation family only):
  footings  FA 1.80 x 1.60 = 2.880 m2, FB 2.20 x 2.00 = 4.400 m2, FC (one outline, two tags: area HELD), FL lift footing
            (owned by the lift system: membrane / screed NOT_APPLICABLE with evidence)
            membrane m2 = 2.880 + 4.400 = 7.280; screed m3 = 7.280 x 0.05 = 0.364
  lift      base 3.00 x 3.00 = 9.000 m2 soffit; board under the base NOT_APPLICABLE (detail: board on sides / top only)
  buried    GB1 side A 4.00 m x (0.80 - 0.10) = 2.800 m2 (drawn, released); GB1 side B HELD (depth not printed);
            GB2 outer face above natural ground NOT_APPLICABLE; GB1 soffit on blinding NOT_APPLICABLE
Lines: L-MEM 7.280 m2 (FA, FB), L-MEM-H held (FC), L-SCR3 0.364 m3 (FA, FB), L-SCR3-H held (FC), L-PIT 9.000 (soffit),
L-LIQ 2.800 (GB1 A), L-LIQ-H held (GB1 B).
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/agents_t301"))

import t301_wp_inventory as W  # noqa: E402
from engine.source import trade_completeness_v1 as TC  # noqa: E402

F = "WP.FOUNDATION"
MEM, SCR, PIT_M, PIT_B, LIQ = ("WP.FOUNDATION.FOOTING_MEMBRANE", "WP.FOUNDATION.FOOTING_SCREED",
                               "WP.FOUNDATION.LIFT_PIT_MEMBRANE", "WP.FOUNDATION.LIFT_PIT_BOARD",
                               "WP.FOUNDATION.BURIED_LIQUID")
EV = {"sheet": "S-05 lift detail", "ref": "handle 2A0: lift footing takes the lift membrane system"}


def el(item, unit, element, face, qty=None, na=None):
    e = {"family": F, "item_code": item, "unit": unit, "element": element, "face": face, "floor": "FDN",
         "applicability": "NOT_APPLICABLE" if na else "APPLICABLE", "qty": qty, "source": "hand census V-301"}
    if na:
        e["evidence"] = na
    return e


def villa():
    els = [el(MEM, "m2", "FTG:FA", "UNDERSIDE", 2.88), el(MEM, "m2", "FTG:FB", "UNDERSIDE", 4.40),
           el(MEM, "m2", "FTG:FC", "UNDERSIDE"), el(MEM, "m2", "FTG:FL", "UNDERSIDE", na=EV),
           el(SCR, "m3", "FTG:FA", "UNDERSIDE", round(2.88 * 0.05, 6)), el(SCR, "m3", "FTG:FB", "UNDERSIDE", 0.22),
           el(SCR, "m3", "FTG:FC", "UNDERSIDE"), el(SCR, "m3", "FTG:FL", "UNDERSIDE", na=EV),
           el(PIT_M, "m2", "LIFT", "BASE_SOFFIT", 9.0),
           el(PIT_B, "m2", "LIFT", "BASE_SOFFIT", na={"sheet": "S-05", "ref": "board on sides and top only"}),
           el(LIQ, "m2", "GB1", "side A", 2.8), el(LIQ, "m2", "GB1", "side B"),
           el(LIQ, "m2", "GB2", "OUTER", na={"sheet": "S-04 section", "ref": "soffit above natural ground"}),
           el(LIQ, "m2", "GB1", "SOFFIT", na={"sheet": "S-04", "ref": "cast on the printed blinding"})]
    lines = [{"line_id": "L-MEM", "item_code": MEM, "unit": "m2", "evidence_state": "SOURCE_DERIVED", "measured_net": 7.28},
             {"line_id": "L-MEM-H", "item_code": MEM, "unit": "m2", "evidence_state": "BLOCKED_RFI", "measured_net": None},
             {"line_id": "L-SCR3", "item_code": SCR, "unit": "m3", "evidence_state": "SOURCE_DERIVED", "measured_net": 0.364},
             {"line_id": "L-SCR3-H", "item_code": SCR, "unit": "m3", "evidence_state": "BLOCKED_RFI", "measured_net": None},
             {"line_id": "L-PIT", "item_code": PIT_M, "unit": "m2", "evidence_state": "SOURCE_DERIVED", "measured_net": 9.0},
             {"line_id": "L-LIQ", "item_code": LIQ, "unit": "m2", "evidence_state": "SOURCE_DERIVED", "measured_net": 2.8},
             {"line_id": "L-LIQ-H", "item_code": LIQ, "unit": "m2", "evidence_state": "BLOCKED_RFI", "measured_net": None}]
    k = lambda item, unit, e, f: f"{item}[{unit}]/{e}/{f}"  # noqa: E731
    links = {"L-MEM": [k(MEM, "m2", "FTG:FA", "UNDERSIDE"), k(MEM, "m2", "FTG:FB", "UNDERSIDE")],
             "L-MEM-H": [k(MEM, "m2", "FTG:FC", "UNDERSIDE")],
             "L-SCR3": [k(SCR, "m3", "FTG:FA", "UNDERSIDE"), k(SCR, "m3", "FTG:FB", "UNDERSIDE")],
             "L-SCR3-H": [k(SCR, "m3", "FTG:FC", "UNDERSIDE")],
             "L-PIT": [k(PIT_M, "m2", "LIFT", "BASE_SOFFIT")],
             "L-LIQ": [k(LIQ, "m2", "GB1", "side A")], "L-LIQ-H": [k(LIQ, "m2", "GB1", "side B")]}
    return els, lines, links


def fam(rep, item, unit):
    return next(f for f in rep["families"] if f["item_code"] == item and f["unit"] == unit)


# ------------------------------------------------------------------------------------------------ normal
def test_normal_every_face_in_line_or_not_applicable_residual_zero():
    els, lines, links = villa()
    rep = W.join(els, lines, links)
    assert rep["counts"] == {"IN_LINE": 9, "NOT_APPLICABLE": 5, "MISSING": 0}
    m = fam(rep, MEM, "m2")
    assert (m["in_line_quantity"], m["in_line_held"], m["not_applicable"], m["missing"]) == (2, 1, 1, 0)
    assert m["inventory_qty_in_line"] == 7.28 and m["line_qty"] == 7.28 and m["residual"] == 0.0 and m["complete"]
    s = fam(rep, SCR, "m3")
    assert s["inventory_qty_in_line"] == 0.364 and s["residual"] == 0.0          # 0.144 + 0.220
    assert fam(rep, LIQ, "m2")["residual"] == 0.0 and fam(rep, PIT_M, "m2")["residual"] == 0.0
    assert all(f["complete"] for f in rep["families"])
    assert rep["register_only"] == [] and rep["unlinked_lines"] == []
    held = [r for r in rep["elements"] if r["line_state"] == "BLOCKED_RFI"]
    assert held and all(r["qty"] is None for r in held)                          # held is blank, never 0


def test_t236_schema_gives_a_complete_waterproofing_trade():
    els, lines, links = villa()
    inv, exc, ll = W.to_t236(els, links, "hand census V-301")
    canon = [{"line_id": x["line_id"], "item_code": x["item_code"], "unit": x["unit"], "trade": "WATERPROOFING",
              "evidence_state": x["evidence_state"], "measured_net": x["measured_net"],
              "rfi": {"question": "held"} if x["measured_net"] is None else None} for x in lines]
    rep = TC.check(inventories=inv, lines=canon, line_links=ll, exclusions=exc)
    row = next(r for r in rep["trades"] if r["trade"] == "WATERPROOFING")
    assert row["status"] == "COMPLETE_AGAINST_INVENTORY"
    assert (row["found"], row["measured"], row["held"], row["missing"], row["excluded"]) == (9, 6, 3, 0, 5)


# ------------------------------------------------------------------------------------------------ adverse
def test_a_face_in_two_lines_is_refused():
    els, lines, links = villa()
    links["L-MEM-H"] = links["L-MEM-H"] + [links["L-MEM"][0]]                 # FA's membrane also in the held line
    with pytest.raises(W.InventoryError, match="double count"):
        W.join(els, lines, links)


def test_not_applicable_without_evidence_is_refused():
    els, lines, links = villa()
    bad = copy.deepcopy(els)
    next(e for e in bad if e["element"] == "GB2")["evidence"] = {"sheet": "S-04"}   # no ref / handle
    with pytest.raises(W.InventoryError, match="without evidence"):
        W.join(bad, lines, links)
    bad2 = copy.deepcopy(els)
    del next(e for e in bad2 if e["element"] == "FTG:FL" and e["item_code"] == MEM)["evidence"]
    with pytest.raises(W.InventoryError, match="without evidence"):
        W.validate_inventory(bad2)


def test_missing_reported_as_zero_is_refused_and_missing_stays_blank():
    els, lines, links = villa()
    bad = copy.deepcopy(els)
    next(e for e in bad if e["face"] == "side B")["qty"] = 0
    with pytest.raises(W.InventoryError, match="never 0"):
        W.join(bad, lines, links)
    del links["L-LIQ-H"]                                                        # the held side B line omitted
    lines = [x for x in lines if x["line_id"] != "L-LIQ-H"]
    rep = W.join(els, lines, links)
    miss = [r for r in rep["elements"] if r["status"] == "MISSING"]
    assert [(r["element"], r["face"], r["qty"]) for r in miss] == [("GB1", "side B", None)]
    assert not fam(rep, LIQ, "m2")["complete"]


def test_not_applicable_face_carried_by_a_line_is_refused():
    els, lines, links = villa()
    links["L-LIQ"] = links["L-LIQ"] + [f"{LIQ}[m2]/GB2/OUTER"]
    with pytest.raises(W.InventoryError, match="NOT_APPLICABLE"):
        W.join(els, lines, links)


def test_a_line_naming_another_item_or_unit_is_refused():
    els, lines, links = villa()
    links["L-SCR3"] = [f"{MEM}[m2]/FTG:FA/UNDERSIDE"]
    with pytest.raises(W.InventoryError, match="another item"):
        W.join(els, lines, links)


def test_a_line_key_in_no_inventory_is_register_only_and_a_residual_is_named():
    els, lines, links = villa()
    links["L-LIQ"] = links["L-LIQ"] + [f"{LIQ}[m2]/GB9/side A"]                # an element no census found
    lines = [dict(x, measured_net=2.95) if x["line_id"] == "L-LIQ" else x for x in lines]
    rep = W.join(els, lines, links)
    assert rep["register_only"] == [{"line_id": "L-LIQ", "key": f"{LIQ}[m2]/GB9/side A"}]
    f = fam(rep, LIQ, "m2")
    assert f["residual"] == pytest.approx(-0.15) and not f["complete"]          # 2.800 inventory vs 2.950 line


def test_t236_gaps_when_an_element_is_missing():
    els, lines, links = villa()
    del links["L-MEM-H"]
    lines = [x for x in lines if x["line_id"] != "L-MEM-H"]
    inv, exc, ll = W.to_t236(els, links, "hand census V-301")
    canon = [{"line_id": x["line_id"], "item_code": x["item_code"], "unit": x["unit"], "trade": "WATERPROOFING",
              "evidence_state": x["evidence_state"], "measured_net": x["measured_net"],
              "rfi": {"question": "held"} if x["measured_net"] is None else None} for x in lines]
    rep = TC.check(inventories=inv, lines=canon, line_links=ll, exclusions=exc)
    row = next(r for r in rep["trades"] if r["trade"] == "WATERPROOFING")
    assert row["status"] == "GAPS" and row["missing"] == 1


def test_inventory_validation_refusals():
    els, _l, _k = villa()
    with pytest.raises(W.InventoryError, match="twice"):
        W.validate_inventory(els + [copy.deepcopy(els[0])])
    bad = copy.deepcopy(els)
    bad[0]["family"] = "WP.GARDEN"
    with pytest.raises(W.InventoryError, match="family"):
        W.validate_inventory(bad)
    bad = copy.deepcopy(els)
    bad[3]["qty"] = 1.0                                                          # NA with a quantity
    with pytest.raises(W.InventoryError, match="no quantity"):
        W.validate_inventory(bad)
