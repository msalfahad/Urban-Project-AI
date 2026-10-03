"""Crops that can be pointed at, and a physical area that is not allowed to masquerade as a price.

Two separate claims are tested here.  The first is that a question the owner cannot locate is not a question: each
unresolved opening gets its own image, drawn large, with the neighbouring rooms named, the measured clear width on the
face of it, and no engine identifier anywhere a person would read.  The second is that a measured opening area and a
payable quantity are different things: seven PVC doors and 16.665 m2 of hole are established facts, and neither of them
says what the doors cost per unit of anything.
"""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_boq"
CHOICES = "Door  /  Open passage  /  Window  /  Sliding door  /  Not an opening  /  Other?"
PASSAGE_CHOICES = "Open to the ceiling  /  Wall above it - what is the opening height?"
OPAQUE = ("OS-", "BE-", "CAD-", "WALL-", "SITE-")


def reg(name):
    return json.loads((OUT / f"{name}.json").read_text("utf-8"))


def crops():
    return reg("QORTUBA_OWNER_QUESTION_CROPS")


def by_id():
    return {x["QUANTITY_ID"]: x for x in reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"]}


# ------------------------------------------------------------------ one crop per unresolved opening
def test_every_open_gap_question_has_its_own_image():
    asked = [q["#"] for q in reg("QORTUBA_OWNER_QUESTIONS")["ROWS"]
             if q["ASKS_FOR"] in ("TYPE", "PASSAGE_HEIGHT")]
    numbered = [x["#"] for x in crops()["ROWS"]]
    assert sorted(numbered) == sorted(asked), "a question about a gap without a crop cannot be pointed at"
    assert len(set(numbered)) == len(numbered), "two questions must not share a number"


def test_the_numbers_the_owner_already_has_do_not_move():
    """Every gap is answered, so every gap crop is retired - and its number stays out of circulation for good."""
    c = crops()
    assert c["ROWS"] == [] and c["COUNT"] == 0
    assert c["RETIRED_NUMBERS"] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    folder = Path(PR.OUT_DIR) / "pa08_qortuba_boq" / "owner_question_crops"
    for n in c["RETIRED_NUMBERS"]:
        assert not (folder / f"QORTUBA_OPENING_{n}.png").exists(), "an answered question is not pictured as open"


def test_each_image_exists_and_is_a_real_drawing():
    for x in crops()["ROWS"]:
        p = Path(x["IMAGE"])
        assert p.is_file(), f"#{x['#']} has no image"
        # a blank or near-blank PNG compresses to almost nothing: 40 kB is far below any drawn crop and far above an
        # empty canvas, so it separates the two without pinning a file size
        assert p.stat().st_size > 40_000, f"#{x['#']} is too small to contain a drawing"


def test_a_crop_names_its_rooms_and_its_width_and_asks_one_settled_question():
    want = {"TYPE": CHOICES, "PASSAGE_HEIGHT": PASSAGE_CHOICES}
    for x in crops()["ROWS"]:
        assert x["ADJACENT_ROOMS"], f"#{x['#']} names no room"
        assert isinstance(x["WIDTH_M"], (int, float)) and x["WIDTH_M"] > 0
        assert x["QUESTION"] == want[x["ASKS_FOR"]], f"#{x['#']} asks the wrong question for its state"


def test_an_answered_opening_has_no_crop_at_all():
    """Both passages are settled as to type and height, so neither is pictured as an open question."""
    assert not [x for x in crops()["ROWS"] if x["ASKS_FOR"] == "PASSAGE_HEIGHT"]
    assert all(x["ASKS_FOR"] == "TYPE" and x["QUESTION"] == CHOICES for x in crops()["ROWS"])


def test_no_engine_identifier_appears_where_the_owner_reads():
    """The opaque id stays in the audit column and nowhere else: not in the room, the location, or the question."""
    for x in crops()["ROWS"]:
        visible = " | ".join(str(x[k]) for k in ("ROOM", "LOCATION", "QUESTION", "ADJACENT_ROOMS"))
        for tok in OPAQUE:
            assert tok not in visible, f"#{x['#']} shows {tok} to the owner: {visible}"
        assert x["AUDIT_OPENING_ID"], "the audit trail still needs the id"


def test_the_crops_neither_guess_a_type_nor_move_the_geometry():
    c = crops()
    assert c["NO_TYPE_INFERRED"] is True
    assert c["GEOMETRY_MODIFIED"] == "NONE"
    for x in c["ROWS"]:
        # the marker is placed from a frozen register, not fitted or estimated
        assert "jamb" in x["MARKER_BASIS"] or "band" in x["MARKER_BASIS"], x["MARKER_BASIS"]


# ------------------------------------------------------------------ a physical area is not a pricing quantity
def test_the_pvc_doors_are_physically_established_but_not_yet_priceable():
    x = by_id()["Q-16"]
    assert x["COUNT"] == 7
    assert abs(x["PHYSICAL_OPENING_AREA_M2"]["VALUE"] - 16.665) < 1e-9
    assert x["PHYSICAL_OPENING_AREA_M2"]["STATE"] == "ESTABLISHED"
    assert x["FINAL_PRICING_QUANTITY"]["VALUE"] is None
    assert x["FINAL_PRICING_QUANTITY"]["STATE"] == "PROJECT_RULE_REQUIRED"
    assert x["FINAL_PRICING_QUANTITY"]["OPTIONS"] == ["per door", "per set", "by m2"]
    assert x["STATUS"] == "PRICING_BASIS_REQUIRED", "the measurement is done; only the pricing unit is not"


def test_the_internal_glazed_opening_has_its_area_but_not_its_trade():
    x = by_id()["Q-17"]
    assert abs(x["PHYSICAL_OPENING_AREA_M2"]["VALUE"] - 6.05) < 1e-9
    assert x["PHYSICAL_OPENING_AREA_M2"]["STATE"] == "ESTABLISHED"
    assert x["FINAL_PRICING_QUANTITY"]["VALUE"] is None
    assert x["STATUS"] == "TRADE_CLASSIFICATION_PENDING"
    # the deduction it caused elsewhere stands: the wall really does have that hole in it
    rooms = reg("QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC")["ROWS"]
    charged = [o for r in rooms for o in r["OPENINGS_DEDUCTED"] if o["OPENING_ID"] == "OS-b5a0fbb335d4"]
    assert len(charged) == 2 and all(abs(o["AREA_M2"] - 6.05) < 1e-9 for o in charged)


def test_neither_pending_row_is_reported_as_a_final_quantity():
    fin = {x["QUANTITY_ID"] for x in reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"]
           if x["STATUS"] == "FINAL_QUANTITY_AVAILABLE"}
    assert "Q-16" not in fin and "Q-17" not in fin


def test_both_pricing_questions_are_open_in_the_ledger():
    ledger = reg("QORTUBA_QUESTION_LEDGER")
    open_q = {x["ID"]: x for x in ledger["STILL_OPEN"]}
    assert "O-09" in open_q and "O-10" in open_q
    assert "per door" in open_q["O-09"]["QUESTION"]
    assert open_q["O-09"]["KIND"] == "PROJECT_RULE"
    assert open_q["O-10"]["KIND"] == "PROJECT_RULE"
    # and the question that IS answered stays answered: US-13 already settled that they are PVC, not aluminium
    closed = {x["DECISION_ID"] for x in ledger["CLOSED"]}
    assert "V2-03" in closed
