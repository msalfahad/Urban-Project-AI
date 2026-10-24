"""T-260 hand fixture, Villa C (synthetic, not Alsenan): door class and opening width from drawing evidence.

Villa C by hand (heads not printed -> Q-55 C 2.20 m, ASSUMED - OWNER-APPROVED; the main entrance prints 2.50):
- C-D0 house entrance, label 'ENTRANCE' on the plan, double leaf, jambs 1.80 / 1.80 -> MAIN, 1.80 x 2.50 = 4.500 m2.
- C-D1 kitchen -> service yard (exterior-coded, nothing drawn to the plot line), jambs 0.90 / 0.90, block frame 1.00
  -> ALUMINIUM, 0.90 x 2.20 = 1.980 m2 (the 1.00 frame is a symbol).
- C-D2 majlis -> front court, flagged as a main-entrance candidate by exterior adjacency only, jambs 1.00 / 1.00 ->
  ALUMINIUM 2.200 m2 (no entrance evidence: UP-DOOR-CLS-004 not met).
- C-D3 store -> covered side passage, mouth open on the plan AND on the section -> ALUMINIUM 0.80 x 2.20 = 1.760.
- C-D4 pantry -> passage closed at its mouth by a drawn glazed screen -> enclosed corridor -> PVC 1.760.
- C-D5 laundry -> passage open on the plan, no second sheet read -> class HELD (Q-67 A condition not established).
- C-D6 bedroom -> hall, the hall side not established, no class note -> HELD, never PVC by default.
- C-D7 jambs 0.90 on one face, 0.95 on the other -> CONFLICT 0.90 .. 0.95 (1.980 .. 2.090 m2), never 2.090.
- C-D8 jambs 0.90 / 0.90 on the plan, the elevation prints the opening 1.00 -> CONFLICT 0.90 .. 1.00.
Aluminium line settled: C-D1 1.980 + C-D2 2.200 + C-D3 1.760 = 5.940 m2, 3 pcs; held C-D5, C-D7 (C-D8 conflict).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t260"))
import door_evidence as E  # noqa: E402


def faces(a, b, **kw):
    return [dict({"face": "A", "gap_m": a}, **kw), dict({"face": "B", "gap_m": b}, **kw)]


IN = {"kind": "INTERIOR", "evidence": ["LABEL"]}
YARD = {"kind": "EXTERIOR", "evidence": ["EXTERIOR_CODED", "NOTHING_BEYOND_TO_PLOT"]}


def passage(across_plan, across_second):
    return {"kind": "PASSAGE", "evidence": ["OPEN_MOUTH"],
            "mouths": [{"drawn_across_plan": across_plan, "drawn_across_second_sheet": across_second}]}


DOORS = [
    {"id": "C-D1", "faces": faces(0.90, 0.90), "block_frame_m": 1.00, "sides": [IN, YARD]},
    {"id": "C-D2", "faces": faces(1.00, 1.00), "sides": [IN, YARD], "main_entrance_candidate": True,
     "entrance_evidence": ["ENGINE_CANDIDATE"], "enters_main_building": False},
    {"id": "C-D3", "faces": faces(0.80, 0.80), "sides": [IN, passage([], [])]},
    {"id": "C-D4", "faces": faces(0.80, 0.80), "sides": [IN, passage(["glazed screen"], None)]},
    {"id": "C-D5", "faces": faces(0.80, 0.80), "sides": [IN, passage([], None)]},
    {"id": "C-D6", "faces": faces(0.80, 0.80), "sides": [IN, {"kind": "UNKNOWN", "evidence": []}]},
    {"id": "C-D7", "faces": faces(0.90, 0.95), "sides": [IN, YARD]},
    {"id": "C-D8", "faces": faces(0.90, 0.90) + [{"face": "SE elevation", "gap_m": 1.00,
                                                   "source": "ELEVATION_OPENING"}], "sides": [IN, YARD]},
]
ROWS = {r["id"]: r for r in E.ledger(DOORS)}


def test_main_entrance_needs_entrance_evidence():
    d = {"faces": faces(1.80, 1.80), "sides": [IN, YARD], "entrance_evidence": ["LABEL"], "enters_main_building": True}
    c = E.door_class(d)
    assert c["class"] == E.MAIN and c["rule"] == "UP-DOOR-CLS-004"
    a = E.door_area(E.opening_width(d["faces"]), height_m=2.50, height_printed=True)
    assert a == {"status": E.DC, "m2": 4.5, "range_m2": None, "cause": ""}


def test_exterior_door_is_aluminium_with_the_jamb_opening_not_the_frame():
    r = ROWS["C-D1"]
    assert (r["class"], r["width_m"], r["m2"], r["outcome"]) == (E.ALU, 0.9, 1.98, "SETTLED")
    assert r["status"] == E.AS and "symbol" in r["width_note"]


def test_candidate_by_adjacency_is_not_a_main_entrance():
    r = ROWS["C-D2"]
    assert r["class"] == E.ALU and r["m2"] == 2.2 and "UP-DOOR-CLS-004 not met" in r["class_reason"]


def test_open_passage_confirmed_on_two_sheets_is_exterior():
    assert (ROWS["C-D3"]["class"], ROWS["C-D3"]["m2"]) == (E.ALU, 1.76)


def test_enclosed_corridor_keeps_the_pantry_door_internal():
    assert (ROWS["C-D4"]["class"], ROWS["C-D4"]["class_rule"], ROWS["C-D4"]["m2"]) == (E.PVC, "UP-DOOR-CLS-001", 1.76)


def test_open_mouth_on_one_sheet_only_is_held_never_0():
    r = ROWS["C-D5"]
    assert r["outcome"] == "STILL-HELD" and r["m2"] is None and "second sheet" in r["class_reason"]


def test_door_with_no_class_note_is_held_not_pvc():
    r = ROWS["C-D6"]
    assert r["class"] is None and r["outcome"] == "STILL-HELD" and "never PVC by default" in r["class_reason"]


def test_faces_that_differ_are_a_conflict_range_never_the_larger_end():
    r = ROWS["C-D7"]
    assert r["width_status"] == E.CONFLICT and r["m2"] is None
    w = E.opening_width(faces(0.90, 0.95))
    assert w["range_m"] == [0.9, 0.95]
    assert E.door_area(w)["range_m2"] == [1.98, 2.09]


def test_plan_and_elevation_widths_that_differ_are_a_conflict():
    assert E.opening_width(DOORS[7]["faces"])["range_m"] == [0.9, 1.0]
    assert ROWS["C-D8"]["outcome"] == "STILL-HELD"


def test_line_total_by_hand():
    alu = [r for r in ROWS.values() if r["class"] == E.ALU and r["outcome"] == "SETTLED"]
    assert sorted(r["id"] for r in alu) == ["C-D1", "C-D2", "C-D3"]
    assert round(sum(r["m2"] for r in alu), 3) == 5.94


# ------------------------------------------------------------------------------------------------- adverse ---
def test_class_from_the_freelancer_is_refused():
    with pytest.raises(E.EvidenceRefused):
        E.door_class({"sides": [IN, {"kind": "UNKNOWN"}], "class_sources": ["FREELANCER"]})


def test_freelancer_alone_never_makes_a_side_exterior():
    st, why = E.side_status({"kind": "EXTERIOR", "evidence": ["FREELANCER"]})
    assert st == "UNKNOWN"


def test_width_from_one_wall_face_only_is_held():
    w = E.opening_width([{"face": "A", "gap_m": 0.90}])
    assert w["status"] == E.HELD and w["width_m"] is None
    w2 = E.opening_width([{"face": "A", "gap_m": 0.90}, {"face": "A", "gap_m": 0.90}])
    assert w2["status"] == E.HELD


def test_block_frame_or_leaf_offered_as_the_opening_is_refused():
    for src in ("BLOCK_FRAME", "ELEVATION_FRAME", "LEAF"):
        with pytest.raises(E.EvidenceRefused):
            E.opening_width(faces(1.00, 1.00, source=src))


def test_held_shown_as_0_is_refused():
    with pytest.raises(E.EvidenceRefused):
        E.check_not_zero([{"id": "X", "status": E.HELD, "m2": 0}])
    assert E.check_not_zero([{"id": "X", "status": E.HELD, "m2": None}])


def test_exterior_claim_without_evidence_is_unknown():
    assert E.side_status({"kind": "EXTERIOR", "evidence": []})[0] == "UNKNOWN"


def test_lift_opening_is_excluded():
    c = E.door_class({"sides": [IN, {"kind": "LIFT"}]})
    assert c["class"] == E.EXCL
