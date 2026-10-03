"""QORTUBA_PRICING_INPUT_MATRIX: the rules that stop a measurement becoming a price by accident.

A pricing matrix is where a careful takeoff usually goes wrong: a geometric length is copied into a purchase quantity, a
missing height is filled with a plausible one, and an amount appears beside a rate nobody supplied.  These tests hold the six
layers apart and keep every number tied to the basis that produced it.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba.pricing import matrix as MX

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_pricing"
QS = Path(PR.OUT_DIR) / "pa08_qortuba_qs01"


def reg(name, folder=OUT):
    return json.loads((folder / f"{name}.json").read_text("utf-8"))


def rows():
    return reg("QORTUBA_PRICING_INPUT_MATRIX")["ROWS"]


def test_no_row_carries_a_rate_or_an_amount():
    """No rate was supplied for this project, so nothing may be priced."""
    for r in rows():
        assert r["LAYERS"]["RATE"]["VALUE"] is None, r["ITEM"]
        assert r["LAYERS"]["AMOUNT"]["VALUE"] is None, r["ITEM"]
    assert reg("FREEZE_QORTUBA_PRICING_INPUT_MATRIX")["PRICED"] is False


def test_every_row_keeps_the_six_layers_apart():
    for r in rows():
        L = r["LAYERS"]
        for k in ("MEASURED_GEOMETRY", "COMMERCIAL_SCOPE", "WASTE_PERCENT", "PROCUREMENT_QUANTITY", "RATE", "AMOUNT"):
            assert k in L, (r["ITEM"], k)
        assert L["MEASURED_GEOMETRY"]["VALUE"] == r["QUANTITY"]
        assert L["COMMERCIAL_SCOPE"]["VALUE"] is None, "a geometric quantity was copied into commercial scope"
        assert L["WASTE_PERCENT"]["VALUE"] is None and L["PROCUREMENT_QUANTITY"]["VALUE"] is None


def test_a_quantity_never_appears_without_a_basis():
    for r in rows():
        if r["QUANTITY"] is not None:
            assert r["STATUS"] == "SOURCE_ESTABLISHED", (r["ITEM"], r["STATUS"])
            assert r["SOURCE"] and r["FORMULA"] and len(r["FORMULA"]) > 10, r["ITEM"]


def test_can_price_now_matches_the_quantity_state():
    for r in rows():
        expected = "YES" if (r["STATUS"] == "SOURCE_ESTABLISHED" and r["QUANTITY"] is not None) else "NO"
        assert r["CAN_PRICE_NOW"] == expected, (r["ITEM"], r["CAN_PRICE_NOW"])
        assert "does not mean a rate exists" in r["CAN_PRICE_NOW_MEANS"]


def test_every_blocked_item_names_one_next_input():
    blocked = [r for r in rows() if r["CAN_PRICE_NOW"] == "NO"]
    assert blocked
    for r in blocked:
        assert r["SINGLE_NEXT_INPUT_TO_UNLOCK"], r["ITEM"]
        assert r["STATUS"] in MX.STATUSES and r["STATUS"] != "SOURCE_ESTABLISHED"


def test_no_height_is_invented_for_any_trade():
    for r in rows():
        if r["UNIT"] == "M2" and "height" in (r["MISSING_INPUT"] or ""):
            assert r["QUANTITY"] is None, f"{r['ITEM']} released an area while still missing a height"


def test_every_trade_section_is_present():
    got = {r["TRADE_CODE"] for r in rows()}
    assert got == {c for c, _, _ in MX.TRADES}, sorted(got)
    for r in rows():
        assert r["TRADE_AR"] and r["TRADE"]


def test_the_readiness_summary_has_no_overall_percentage():
    s = reg("QORTUBA_PRICING_READINESS_SUMMARY")
    assert "NO_OVERALL_PERCENTAGE" in s
    scored = [k for k in s if k not in ("ARTIFACT", "NO_OVERALL_PERCENTAGE")
              and ("PERCENT" in k.upper() or "SCORE" in k.upper())]
    assert not scored, scored
    for x in s["ROWS"]:
        assert x["READINESS"] in MX.READINESS
        assert x["WHY"] and (x["READINESS"] == "READY_TO_PRICE" or x["UNLOCKS"])


def test_readiness_follows_the_rows_it_summarises():
    by_code = {}
    for r in rows():
        a, b = by_code.setdefault(r["TRADE_CODE"], [0, 0])
        by_code[r["TRADE_CODE"]] = [a + (r["CAN_PRICE_NOW"] == "YES"), b + 1]
    for x in reg("QORTUBA_PRICING_READINESS_SUMMARY")["ROWS"]:
        ready, total = by_code[x["TRADE_CODE"]]
        assert x["ITEMS_WITH_AN_ESTABLISHED_QUANTITY"] == ready and x["ITEMS"] == total
        expected = "READY_TO_PRICE" if ready == total else "PARTIALLY_READY" if ready else "NOT_READY"
        assert x["READINESS"] == expected, (x["TRADE"], x["READINESS"], expected)


def test_the_unlock_register_groups_identical_asks():
    u = reg("QORTUBA_MINIMUM_INPUTS_TO_UNLOCK")
    assert u["COUNT"] < len([r for r in rows() if r["CAN_PRICE_NOW"] == "NO"]), "identical asks were not grouped"
    seen = set()
    for x in u["ROWS"]:
        assert x["NEXT_INPUT"] not in seen, x["NEXT_INPUT"]
        seen.add(x["NEXT_INPUT"])
        assert x["UNBLOCKS_ITEMS"] == len(x["ITEMS"]) and x["TRADES"]
    biggest = u["ROWS"][0]
    assert biggest["UNBLOCKS_ITEMS"] >= 3, "the register should show which single input frees the most"


def test_the_excel_structure_leaves_price_columns_empty():
    x = reg("QORTUBA_EXCEL_TRADE_STRUCTURE")
    for col in ("البند", "الوصف", "الوحدة", "الكمية", "الهالك %", "كمية الشراء", "سعر الوحدة", "الإجمالي",
                "مصدر الكمية", "حالة الاعتماد", "ملاحظات"):
        assert col in x["COLUMNS"], col
    for sec in x["SECTIONS"]:
        for r in sec["ROWS"]:
            assert r["سعر الوحدة"] is None and r["الإجمالي"] is None
            assert r["الهالك %"] is None and r["كمية الشراء"] is None
            assert r["حالة الاعتماد"] in MX.STATUSES
    assert x["SECTION_COUNT"] == len(MX.TRADES)


def test_the_matrix_left_the_room_workpapers_untouched():
    fr = json.loads((QS / "FREEZE_PA08_QORTUBA_ROOM_BY_ROOM_QS_01.json").read_text("utf-8"))
    for n, h in fr["CONTENTS"].items():
        assert MX._sha(QS / f"{n}.json") == h, f"{n} changed"
    assert reg("FREEZE_QORTUBA_PRICING_INPUT_MATRIX")["GEOMETRY_ENGINE_CHANGED"] == "NONE"


def test_established_quantities_match_the_frozen_workpaper():
    """The matrix re-cuts; it must not re-measure."""
    s = json.loads((QS / "QORTUBA_QS01_SUMMARY_TOTALS.json").read_text("utf-8"))
    by = {(r["ITEM"], r["SUBITEM"]): r for r in rows()}
    assert by[("FLOOR_FINISH", "dry internal floor area")]["QUANTITY"] == s["A_DRY_INTERNAL_FLOOR_AREA_M2"]["VALUE"]
    assert by[("FLOOR_FINISH", "bathroom floor area")]["QUANTITY"] == s["B_WET_INTERNAL_FLOOR_AREA_M2"]["VALUE"]
    assert by[("SKIRTING", "skirting, dry rooms")]["QUANTITY"] == s["D_TOTAL_SKIRTING_LM"]["VALUE"]
    assert by[("PROFILE", "black profile above skirting")]["QUANTITY"] == s["E_TOTAL_BLACK_PROFILE_LM"]["VALUE"]
    assert by[("FLAT_CEILING", "flat ceiling plan geometry")]["QUANTITY"] == s["F_TOTAL_CEILING_GEOMETRY_M2"]["VALUE"]


def test_the_ceiling_perimeter_is_the_gross_line_not_the_skirting_net():
    """A cove runs across a door head; a skirting stops at it.  The two lengths must not be the same row."""
    by = {(r["ITEM"], r["SUBITEM"]): r for r in rows()}
    cove = by[("CEILING_PERIMETER", "perimeter for cove, bulkhead or shadow gap")]
    skirt = by[("SKIRTING", "skirting, dry rooms")]
    assert cove["QUANTITY"] > skirt["QUANTITY"]
    assert "door" in cove["CONFIDENCE"].lower() or "door" in cove["WHY_DIFFERENT_FROM_SKIRTING"].lower()


def test_out_of_apartment_scope_items_say_so():
    for r in rows():
        if r["SUBITEM"] in ("roof waterproofing area", "terrace waterproofing area", "stair plan area on this floor"):
            text = (r.get("SCOPE_NOTE") or "") + " " + (r["MISSING_INPUT"] or "") + " " + (r["SINGLE_NEXT_INPUT_TO_UNLOCK"] or "")
            assert "scope" in text.lower() or "contract" in text.lower(), (r["SUBITEM"], text)
