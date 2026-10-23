"""T-188 on the development villa inventory (research/agents_t188/alsenan_t188.py; no Drive file needed): the four
known cases of the task row are reproduced, and the correct end of the round stair is not flagged."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("alsenan_t188", ROOT / "research/agents_t188/alsenan_t188.py")
T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T)
RES = T.run()


def rows(state, code=None, el=None):
    return [f for f in RES[state]["findings"] if (code is None or f["code"] == code) and (el is None or f["element"] == el)]


def test_case1_st01_upper_storey_folded_away_until_v306():
    for s in ("A", "V305"):
        f = rows(s, "STOREY_WITHOUT_LINE", "ST-01")
        assert [(x["storey"], x["status"]) for x in f] == [("1F", "HELD")]
    assert rows("V306", "STOREY_WITHOUT_LINE", "ST-01") == []
    st01 = next(r for r in RES["V306"]["elements"] if r["element"] == "ST-01")
    assert st01["storeys"][1]["lines"] == sorted(f"HL:STAIR_CONCRETE:ST-01:{k}" for k in
                                                 ("MS2_L", "MS2_U", "MS2_LD", "MS2_TR"))


def test_case2_third_dome_without_structural_drawing_in_every_state():
    for s in RES:
        assert {x["code"] for x in rows(s, el="DOME-TOWER")} >= {"NO_STRUCTURAL_COUNTERPART", "NO_STRUCTURAL_DETAIL"}
    assert [x["code"] for x in rows("A", "NO_BOQ_LINE", "DOME-TOWER")] == ["NO_BOQ_LINE"]
    assert rows("V306", "NO_BOQ_LINE", "DOME-TOWER") == []          # the placeholder line holds it (UNKNOWN)


def test_case3_pump_room_listed_not_drawn_never_zero():
    for s in RES:
        f = rows(s, "NOT_DRAWN")
        assert sorted(x["lines"][0] for x in f) == ["RC:S17:13", "RC:S17:15"]
        assert all(x["status"] == "NOT_DRAWN" and "never 0" in x["why"] for x in f)


def test_case4_round_stair_ends_at_1f_and_is_not_flagged():
    for s in RES:
        assert [x["code"] for x in rows(s, el="ST-02")] == ["TYPICAL_DETAIL_ONLY"]


def test_misread_dome_outline_on_the_candidates_only():
    assert rows("A", "KIND_MISMATCH") == []
    for s in ("V305", "V306"):
        f = rows(s, "KIND_MISMATCH")
        assert [(x["element"], x["lines"]) for x in f] == [("DOME-A", ["P-C:STAIRS:1F:SITE-b845e1e78b1f74a8"])]


@pytest.mark.parametrize("state", ["A", "V305", "V306"])
def test_lift_tank_and_lobby_flight(state):
    assert {x["code"] for x in rows(state, el="LIFT-01")} == {"COMPONENT_HELD", "NO_BOQ_LINE", "END_NOT_EVIDENCED"}
    assert {x["code"] for x in rows(state, el="TANK-01")} == {"NO_BOQ_LINE", "NO_STRUCTURAL_DETAIL"}
    lobby = rows(state, "STOREY_WITHOUT_LINE", "ST-01b")
    assert len(lobby) == (0 if state == "V306" else 1)


def test_committed_csv_is_current():
    assert (ROOT / "research/agents_t188/FINDINGS_T188.csv").read_text(encoding="utf-8") == T.findings_csv(RES)
