"""Step 1 of the villa blind validation: what arrived, and what was deliberately not read.

The inventory's job is not to find drawings.  It is to establish, checkably, that the seal held while it looked:
that no spreadsheet was opened, that the two projects this repository already knows were recognised as ineligible,
and that when no villa set is present the remaining steps stop rather than proceed on whatever is lying around.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa09 import source_inventory as SI
from research.qs_wall_treatment_01.pa09 import villa_blind_protocol as VP

VILLA = Path(PR.OUT_DIR) / "pa09_villa_blind"


def inv():
    return json.loads((VILLA / "FULL_VILLA_BLIND_SOURCE_INVENTORY.json").read_text("utf-8"))


# ------------------------------------------------------------------ the seal held
def test_no_commercial_file_was_opened_to_find_out_what_it_was():
    r = inv()
    assert r["NOTHING_IN_THE_COMMERCIAL_CLASS_WAS_OPENED"] is True
    assert all(row["OPENED_BY_THIS_INVENTORY"] is False for row in r["ROWS"])


def test_every_spreadsheet_is_sealed_whatever_its_name_suggests():
    """A name is not evidence.  Anything that could hold a priced bill is classified without being read."""
    for ext in SI.COMMERCIAL_EXT:
        proj, why = SI.classify("some_innocent_looking_file" + ext, ext)
        assert proj == "SEALED_NOT_OPENED", ext
        assert "not opened" in why
    r = inv()
    for row in r["ROWS"]:
        if row["EXT"] in SI.COMMERCIAL_EXT:
            assert row["PROJECT"] == "SEALED_NOT_OPENED", row["SOURCE"]


def test_the_sealed_class_is_one_the_protocol_actually_seals():
    kinds = " ".join(VP.SEALED_UNTIL_FREEZE).lower()
    assert "boq" in kinds or "bill" in kinds


# ------------------------------------------------------------------ the two ineligible projects
def test_qortuba_and_p7757_are_recognised_rather_than_measured_again():
    assert SI.classify("BLOCK__1__PLOT_449-rfa1.pdf", ".pdf")[0] == "QORTUBA"
    assert SI.classify("P7757-ARCH-01.dwg", ".dwg")[0] == "P7757"
    assert SI.classify("ST7757_structural.dxf", ".dxf")[0] == "P7757"
    for k in ("P7757", "QORTUBA"):
        assert k in SI.KNOWN


def test_a_drawing_that_names_no_project_is_flagged_not_guessed():
    proj, why = SI.classify("plan_final_rev3.pdf", ".pdf")
    assert proj == "DRAWING_UNATTRIBUTED"
    assert "could not be read" in why


# ------------------------------------------------------------------ the stop
def test_the_workflow_stops_when_no_villa_set_is_present():
    r = inv()
    assert r["VILLA_SOURCE_SET_PRESENT"] is False
    assert r["STEPS_4_TO_15_BLOCKED"] is True
    assert r["DISCIPLINES_RECEIVED_FOR_THE_VILLA"] == []
    assert r["WHY_NOT"] and r["WHAT_IS_NEEDED"]


def test_the_inventory_is_reproducible_and_hashed():
    a = inv()
    b = SI.finish()
    assert b["DIGEST"] == a["DIGEST"]
    assert len(b["DIGEST"]) == 16
    assert b["COUNT"] == len(b["ROWS"]) > 0
