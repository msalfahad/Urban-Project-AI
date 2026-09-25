"""URBAN_PROJECTS_BOQ_SCHEMA_LIBRARY: the rules that keep a reference project's structure from leaking its numbers.

Learning a house's pricing structure from its old workbooks is useful and safe.  Carrying that project's quantities, rates or
room dimensions into a new one is neither.  These tests hold that line, and check that every item recorded here was really
read from the sheet it names.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba.boq import compare_schema as CS, schema_library as SL

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_boq"
PRC = Path(PR.OUT_DIR) / "pa08_qortuba_pricing"
QS = Path(PR.OUT_DIR) / "pa08_qortuba_qs01"


def reg(name, folder=OUT):
    return json.loads((folder / f"{name}.json").read_text("utf-8"))


def lib():
    return reg("URBAN_PROJECTS_BOQ_SCHEMA_LIBRARY")


def test_every_item_was_verified_in_the_sheet_it_names():
    L = lib()
    assert L["PROVENANCE_UNVERIFIED"] == [], L["PROVENANCE_UNVERIFIED"]
    for r in L["ROWS"]:
        assert r["PROVENANCE_VERIFIED_IN_SHEET"] is True, r["ITEM_ID"]
        assert r["SOURCE_WORKBOOK"] and r["SOURCE_SHEET"] and r["RAW_ARABIC_ITEM"]


def test_every_source_workbook_hash_matches():
    for w in lib()["WORKBOOKS"]:
        assert w["SHA_VERIFIED"] is True, w["FILE"]


def test_the_originals_were_not_modified():
    """Reading a reference file must leave it byte-for-byte as it was."""
    for key, w in SL.WORKBOOKS.items():
        assert SL._sha16(w["FILE"]) == w["SHA16"], key
    assert reg("FREEZE_URBAN_PROJECTS_BOQ_SCHEMA_LIBRARY")["ORIGINALS_MODIFIED"] == 0


def test_no_historical_quantity_rate_or_total_is_stored():
    """The register is structure.  A number in it would be a reference project's data in a new project's file."""
    L = lib()
    text = json.dumps(L, ensure_ascii=False)
    for r in L["ROWS"]:
        for field in ("QUANTITY_BASIS", "FORMULA_PATTERN", "NOTES", "RAW_ARABIC_ITEM"):
            v = r.get(field) or ""
            assert "409.58" not in v and "1209.385" not in v and "1260.6895" not in v, (r["ITEM_ID"], field)
        assert "QUANTITY" not in r and "RATE" not in r and "AMOUNT" not in r and "TOTAL" not in r
    for banned in ("409.58", "282.85", "433.83", "1209.385", "1151.1375", "1260.6895", "128.9", "295.44"):
        assert banned not in text, f"a historical quantity leaked into the register: {banned}"
    fr = reg("FREEZE_URBAN_PROJECTS_BOQ_SCHEMA_LIBRARY")
    assert fr["HISTORICAL_QUANTITIES_STORED"] == 0 and fr["HISTORICAL_RATES_STORED"] == 0
    assert fr["STRUCTURE_ONLY"] is True


def test_every_item_has_a_unit_the_house_actually_uses():
    for r in lib()["ROWS"]:
        assert r["PRICING_UNIT"] in SL.UNITS.values(), (r["ITEM_ID"], r["PRICING_UNIT"])
        assert SL.UNITS[r["PRICING_UNIT_AR"]] == r["PRICING_UNIT"]


def test_the_explicit_deduction_rules_are_quoted_not_paraphrased():
    """A rule the sheet writes in its own words must survive as those words."""
    rules = [r["DEDUCTION_RULE_IF_EXPLICIT"] for r in lib()["ROWS"] if r["DEDUCTION_RULE_IF_EXPLICIT"]]
    assert rules, "the house workbooks do state deduction rules"
    assert any("2م=1م" in x or "2م =1م" in x for x in rules), "the halving rule for corners must be quoted"
    assert any("خصم بالنصف" in x for x in rules), "the half deduction for openings must be quoted"


def test_the_house_conventions_each_name_the_items_they_govern():
    for c in lib()["HOUSE_CONVENTIONS"]:
        assert c["CONVENTION"] and c["WHERE"] and c["APPLIES_TO"]
        canon = {r["CANONICAL_ITEM"] for r in lib()["ROWS"]}
        for item in c["APPLIES_TO"]:
            assert item in canon, item


# ------------------------------------------------------------------ the comparison
def cmp_():
    return reg("QORTUBA_VERSUS_HOUSE_BOQ_SCHEMA")


def test_every_mapped_row_has_a_verdict_from_the_list():
    for r in cmp_()["ROWS"]:
        assert r["VERDICT"] in CS.VERDICTS, (r["QORTUBA_ITEM_NO"], r["VERDICT"])
        assert r["WHY"] and len(r["WHY"]) > 20


def test_a_confirmed_unit_really_matches_the_house_unit():
    for r in cmp_()["ROWS"]:
        if r["VERDICT"] == "UNIT_CONFIRMED_BY_HOUSE_BOQ":
            assert r["QORTUBA_ASSUMED_UNIT"] == r["HOUSE_PRICING_UNIT"], r["QORTUBA_ITEM_NO"]
        if r["VERDICT"] == "UNIT_WRONG_HOUSE_USES_ANOTHER":
            assert r["QORTUBA_ASSUMED_UNIT"] != r["HOUSE_PRICING_UNIT"], r["QORTUBA_ITEM_NO"]


def test_the_named_unit_corrections_are_present():
    """The five the house overturned, checked one by one."""
    wrong = {r["ITEM_NO"]: r for r in cmp_()["ANSWER_2_UNITS_WRONG"]}
    assert wrong["WP-02"]["ASSUMED"] == "M2" and wrong["WP-02"]["HOUSE_UNIT"] == "LM"
    assert wrong["MR-05"]["ASSUMED"] == "LM" and wrong["MR-05"]["HOUSE_UNIT"] == "NR"
    assert wrong["IP-04"]["ASSUMED"] == "LM" and wrong["IP-04"]["HOUSE_UNIT"] == "M2"
    assert wrong["AL-08"]["HOUSE_UNIT"] == "M2" and wrong["OT-01"]["HOUSE_UNIT"] == "M2"


def test_a_clean_map_really_has_a_measured_input_in_the_house_unit():
    clean = cmp_()["ANSWER_5_MAPS_CLEANLY_NOW"]
    assert clean, "the waterproofing rows should map without further input"
    for r in clean:
        mi = r["QORTUBA_MEASURED_INPUT"]
        assert mi and mi["VALUE"] is not None
        assert mi["UNIT"] == r["UNIT"], (r["ITEM_NO"], mi["UNIT"], r["UNIT"])


def test_no_qortuba_quantity_was_changed_by_the_comparison():
    fr = reg("FREEZE_QORTUBA_VERSUS_HOUSE_BOQ_SCHEMA")
    assert fr["QORTUBA_GEOMETRY_CHANGED"] == "NONE"
    assert fr["QORTUBA_QUANTITIES_RECOMPUTED"] == 0
    assert fr["HISTORICAL_QUANTITIES_USED_AS_QORTUBA_INPUTS"] == 0
    aud = json.loads((PRC / "FREEZE_QORTUBA_FINAL_PRICING_AUDIT.json").read_text("utf-8"))
    for n, h in aud["CONTENTS"].items():
        assert SL.hashlib.sha256((PRC / f"{n}.json").read_bytes()).hexdigest() == h, f"{n} changed"
    wp = json.loads((QS / "FREEZE_PA08_QORTUBA_ROOM_BY_ROOM_QS_01.json").read_text("utf-8"))
    for n, h in wp["CONTENTS"].items():
        assert SL.hashlib.sha256((QS / f"{n}.json").read_bytes()).hexdigest() == h, f"{n} changed"


def test_every_missing_house_item_says_where_qortuba_stands():
    miss = cmp_()["ANSWER_4_HOUSE_ITEMS_MISSING_FROM_QORTUBA"]
    assert len(miss) >= 8
    canon = {r["CANONICAL_ITEM"] for r in lib()["ROWS"]}
    for m in miss:
        assert m["HOUSE_BOQ_ITEM"] in canon, m["HOUSE_BOQ_ITEM"]
        assert m["PRICING_UNIT"] in SL.UNITS.values()
        assert m["QORTUBA_POSITION"] and len(m["QORTUBA_POSITION"]) > 15


def test_an_item_with_no_house_precedent_is_not_quietly_given_one():
    """The black profile has no historical counterpart, and inventing one would be the whole failure mode."""
    nh = {r["ITEM_NO"]: r for r in cmp_()["NO_HOUSE_PRECEDENT"]}
    assert "C-06" in nh
    assert "no profile-above-skirting item exists" in nh["C-06"]["WHY"]
    assert nh["C-06"]["NEEDS"]
    for r in cmp_()["ROWS"]:
        if r["VERDICT"] == "NO_HOUSE_PRECEDENT":
            assert r["HOUSE_BOQ_ITEM"] is None and r["HOUSE_RAW_ARABIC"] is None
