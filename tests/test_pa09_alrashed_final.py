"""The blind freeze: the window standard, the two reconciliations, and the line the system does not cross.

The guide the owner approved is a fallback and the tests hold it there: it supplies a height where the project is
silent and never a width the project can be measured for.  The porcelain and its preparation now take one host,
and the difference that was 155 m2 is zero because the defect that caused it was fixed, not documented away.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa09.alrashed import owner_inputs as OI, window_standard as WS

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"


def rec():
    return json.loads((OUT / "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json").read_text("utf-8"))


# ------------------------------------------------------------------ the guide is a fallback
def test_the_guide_ranks_below_anything_the_project_states_or_yields():
    ranks = {name: n for n, name, _ in WS.PRIORITY}
    assert ranks["SOURCE_STATED_DIMENSION"] == 1
    assert ranks["MEASURED_FROM_PROJECT_GEOMETRY"] == 2
    assert ranks["EXPLICIT_PROJECT_OWNER_OVERRIDE"] == 3
    assert ranks[WS.VERSION] == 4
    assert ranks["ASK_THE_OWNER"] == 5


def test_no_window_takes_its_width_from_the_guide():
    for w in rec()["WINDOW_REGISTER"]:
        assert w["WIDTH_SOURCE"] == "MEASURED_FROM_PROJECT_GEOMETRY"
        assert w["WIDTH_PRIORITY_RANK"] == 2
        assert w["HEIGHT_PRIORITY_RANK"] == 4


def test_the_measured_widths_are_not_the_guides_widths():
    """The guide would have given 1.80 for a master bedroom; the drawing gives 2.001, and the drawing wins."""
    w = next(x for x in rec()["WINDOW_REGISTER"] if x["GUIDE_CATEGORY"] == "MASTER_LARGE_BEDROOM")
    assert abs(w["WIDTH_M"] - 2.001) < 1e-6
    assert w["WIDTH_M"] != WS.TABLE["MASTER_LARGE_BEDROOM"]["W"]
    assert w["HEIGHT_M"] == WS.TABLE["MASTER_LARGE_BEDROOM"]["H"]


def test_the_two_metre_height_is_superseded_and_gone():
    assert WS.SUPERSEDES["BY"] == WS.VERSION
    for w in rec()["WINDOW_REGISTER"]:
        assert w["HEIGHT_M"] != OI.AR03_WINDOW_HEIGHT_M, "no window may keep the illustrative 2.00 m"
    assert {w["HEIGHT_M"] for w in rec()["WINDOW_REGISTER"]} == {1.5, 1.2, 2.2, 0.6}


def test_orientation_and_daylight_advice_never_touches_a_quantity():
    for k, v in WS.NOT_APPLIED_TO_TAKEOFF.items():
        if k != "WHY":
            assert v == "DESIGN_REVIEW_ONLY", k


def test_the_guide_records_that_its_pdf_did_not_arrive():
    assert WS.PROVENANCE["DOCUMENT_RECEIVED"] is False
    assert WS.PROVENANCE["WHAT_WAS_INGESTED"]


# ------------------------------------------------------------------ the reconciliations
def test_porcelain_and_its_preparation_take_one_host_and_agree_exactly():
    r = rec()
    for x in r["WET_ROOM_RECONCILIATION"]:
        assert x["CERAMIC_HOST_LENGTH_M"] == x["TILE_PREP_HOST_LENGTH_M"]
        assert x["NET_WALL_PORCELAIN_M2"] == x["TILE_PREP_AREA_M2"]
        assert x["DIFFERENCE_M2"] == 0.0
    assert r["TOTALS"]["WALL_PORCELAIN_NET_M2"] == r["TOTALS"]["TILE_PREPARATION_M2"]


def test_the_earlier_gap_was_called_an_engine_error_not_a_trade_rule():
    d = next(c for c in rec()["PRE_FREEZE_AUDIT"]["CHECKS"] if c["CHECK"] == "D_PORCELAIN_VS_TILE_PREP")
    assert d["PASS"] and d["DETAIL"]["TOTAL_DIFFERENCE_M2"] < 1e-6
    assert d["DETAIL"]["OUTCOME"].startswith("A - ENGINE ERROR")


def test_only_confirmed_masonry_is_billed():
    r = rec()
    for b in r["BLOCKWORK"]:
        assert b["OBJECT_IDENTITY"] == "MASONRY_WALL" and b["THICKNESS_MM"] in (150, 200)
    for x in r["BLOCKWORK_EXCLUDED_ARTEFACTS"]:
        assert x["BILLED"] is False and x["OBJECT_IDENTITY"] == "NOT_CONFIRMED_MASONRY_WALL"
    assert r["BLOCKWORK_EXCLUDED_ARTEFACTS"], "the artefacts are reported, not silently dropped"


def test_no_wall_deducts_more_than_it_contains():
    for b in rec()["BLOCKWORK"]:
        assert b["DEDUCTION_GUARD_OK"] and 0 < b["NET_AREA_M2"] <= b["GROSS_AREA_M2"]


def test_external_plaster_is_now_net_of_the_windows():
    r = rec()
    gr = next(p for p in r["PLASTER_AND_PAINT"] if p["FLOOR"] == "GROUND")
    assert abs(gr["WINDOW_DEDUCTION_M2"] - r["TOTALS"]["ALUMINIUM_M2"]) < 1e-3, "the deduction is the aluminium area, to the rounding the row carries"
    assert gr["EXTERNAL_PLASTER_NET_M2"] < gr["EXTERNAL_PLASTER_GROSS_M2"]


# ------------------------------------------------------------------ the freeze
def test_every_pre_freeze_check_passes():
    a = rec()["PRE_FREEZE_AUDIT"]
    assert a["ALL_PASS"] is True
    assert {c["CHECK"][0] for c in a["CHECKS"]} == set("ABCDEFGHIJK")


def test_the_freeze_carries_no_rate_and_no_waste():
    r = rec()
    assert r["RATES_SUPPLIED"] == 0 and r["WASTE_APPLIED"] is False
    assert r["WORKBOOK"]["RATES_SUPPLIED"] == 0 and r["WORKBOOK"]["WASTE_APPLIED"] is False
    assert set(r["WORKBOOK"]["PRICING_COLUMNS_LEFT_BLANK"]) == {"الهالك %", "كمية الشراء", "سعر الوحدة", "الإجمالي"}


def test_the_system_does_not_approve_its_own_takeoff():
    ex = json.loads((OUT / "ALRASHED_STRUCTURED_DRAFT_EXPORT.json").read_text("utf-8"))
    assert ex["APPROVAL_STATUS"] == "DRAFT"
    for row in ex["ROWS"]:
        assert row["APPROVAL_STATUS"] == "DRAFT"
        assert row["SOURCE"] and row["MEASURED_UNIT"] and row["PROJECT_ID"]


def test_structural_and_mep_are_scoped_out_and_carry_no_quantity():
    r = rec()
    assert r["SCOPE"]["OUT_STATUS"] == "OUT_OF_SCOPE_FOR_CURRENT_VALIDATION"
    blob = json.dumps(json.loads((OUT / "ALRASHED_STRUCTURED_DRAFT_EXPORT.json").read_text("utf-8")))
    for absent in ("REINFORCEMENT", "SANITARY", "ELECTRICAL", "HVAC"):
        assert f'"TRADE": "{absent}"' not in blob


def test_the_historical_excel_is_untouched():
    r = rec()
    assert "not requested, opened, inspected or compared" in r["SEALED"]
    src = Path("research/qs_wall_treatment_01/pa09/alrashed").rglob("*.py")
    for p in src:
        t = p.read_text("utf-8")
        assert ".xlsx" not in t or "ALRASHED_TRADE_PRICING_WORKBOOK" in t
