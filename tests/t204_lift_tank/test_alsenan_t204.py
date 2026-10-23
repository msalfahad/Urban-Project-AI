"""T-204 development-villa regression (Alsenan lift pit and roof tank). Hand values from the printed / drawn geometry
(foundation plan ring 2.20 / 1.80, walls 0.20, columns C1 / C2 / C2 0.20 x 0.50 and C9 0.25 x 1.00, FF 4.60 x 4.50 x
0.55, p.14 typical detail), the freelancer reconciliation in units, and the ELEMENT_CONTINUITY_V1 re-run.  No drawing or
client data is read here: the script's inputs are the committed readings (handles and printed values only)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("t204_alsenan_tests", ROOT / "research/agents_t204/alsenan_t204.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

RES, CONT, SUMM = A.summary()


def rows():
    return {r["component"]: r for r in RES["lift"]["rows"]}


def test_ring_by_hand():
    s = RES["lift"]["summary"]
    assert s["ring_gross_m2"] == pytest.approx(2.20 * 2.20 - 1.80 * 1.80)      # 1.60
    # C1 / C2 / C2 0.20 x 0.50 = 0.10 each, C9 0.20 of its 0.25 width in the band x 1.00 = 0.20
    assert s["column_in_ring_m2"] == pytest.approx(0.50)
    # net 1.10 = 0.20 x (1.20 + 0.70 + 1.80 + 1.80), the four S8.1A wall regions 0.24 / 0.14 / 0.36 / 0.36
    assert s["ring_net_m2"] == pytest.approx(0.24 + 0.14 + 0.36 + 0.36)
    assert s["net_centreline_m"] == pytest.approx(5.50)
    assert s["face_run_inner_m"] == pytest.approx(5.50) and s["face_run_outer_m"] == pytest.approx(5.50)
    # envelope: 2.20 x 2.20 + C9's 0.05 x 1.00 outside the ring; outline 8.80 + 2 x 0.05
    assert s["envelope_m2"] == pytest.approx(4.89) and s["envelope_outline_m"] == pytest.approx(8.90)


def test_height_dependent_rows_held_never_zero():
    r = rows()
    for comp in ("PIT_WALL_CONCRETE", "PIT_WALL_FORMWORK", "BARS_VERTICAL", "BARS_HORIZONTAL",
                 "MEMBRANE_PIT_OUTER_FACES", "PROTECTION_BOARD_WALLS", "TIE_BEAMS_CONCRETE:GF"):
        assert r[comp]["status"] == "HELD" and r[comp]["value"] is None, comp
    assert all(x["value"] is None for x in RES["lift"]["rows"] + RES["tank"]["rows"] if x["status"] != "DRAWING-CONFIRMED")


def test_fixed_parts_by_hand():
    r = rows()
    assert r["MEMBRANE_BASE_SOFFIT"]["value"] == pytest.approx(4.60 * 4.50)                 # 20.70
    assert r["MEMBRANE_BASE_SIDES"]["value"] == pytest.approx(2 * (4.60 + 4.50) * 0.60)    # 10.92
    assert r["MEMBRANE_BASE_TOP_OUTSIDE_PIT"]["value"] == pytest.approx(20.70 - 4.89)      # 15.81
    assert r["SCREED_UNDER_BASE"]["value"] == pytest.approx(20.70 * 0.05)                  # 1.035
    assert r["PIT_BASE"]["value"] == pytest.approx(11.385) and r["PIT_BASE"]["listed_only"]
    assert r["TIE_BEAMS_LENGTH:GF"]["value"] == pytest.approx(5.50)
    assert r["TIE_BEAMS:1F"]["status"] == r["TIE_BEAMS:2F"]["status"] == "NOT_REQUIRED"
    v = r["BARS_VERTICAL"]
    # runs 1.20, 0.70, 1.80, 1.80 at 6/m: C 33.0, A 8 + 5 + 11 + 11 = 35, B 9 + 6 + 12 + 12 = 39 per face
    assert (v["count_inner"]["A"], v["count_inner"]["B"]) == (35, 39)
    assert v["count_inner"]["C"] == pytest.approx(33.0)


def test_freelancer_reconciled_in_units():
    rec = SUMM["freelancer_reconciliation"]
    assert rec["plan_difference_m2"] == pytest.approx(0.0)          # 8.00 x 0.20 = the drawn ring
    assert rec["at_his_height_net_m3"] == pytest.approx(1.65)       # 1.10 x 1.50
    assert rec["at_his_height_column_part_m3"] == pytest.approx(0.75)   # 0.50 x 1.50, also in his neck rows
    assert rec["closes"] is True                                    # 1.65 + 0.75 = 2.40, no residual
    assert "UNRESOLVED" in rec["verdict"]                           # the height itself is not printed


def test_tank_held_with_designer_item():
    t = RES["tank"]
    assert t["missing"] == ["walls", "base", "cover"]
    assert t["designer_item"] and "Q-S8.4-01" in t["designer_item"]
    assert sum(1 for x in t["rows"] if x["status"] == "LISTED") == 2     # the two T&B panels, never re-added


def test_continuity_rerun():
    lt = SUMM["continuity_lift_tank"]
    assert "LIFT-01:NO_BOQ_LINE:HELD" in lt["V306"] and "TANK-01:NO_BOQ_LINE:HELD" in lt["V306"]
    after = lt["V306+T204"]
    assert not any("NO_BOQ_LINE" in x for x in after)                   # a HELD line per element now
    assert "TANK-01:NO_STRUCTURAL_DETAIL:HELD" in after                 # the tank still has no detail
    assert "LIFT-01:COMPONENT_HELD:HELD" in after                       # the pit depth is still not printed
    assert not any("END_NOT_EVIDENCED" in x for x in after)             # the +13.90 slab closes the shaft
    props = A.proposed_lines()
    assert props and all(p["state"] == "HELD" for p in props)


def test_committed_outputs_current():
    here = ROOT / "research/agents_t204"
    assert (here / "LEDGER_T204.csv").read_text(encoding="utf-8") == A.ledger_csv(RES)
    assert (here / "FINDINGS_T204.csv").read_text(encoding="utf-8") == A.findings_csv(CONT)
