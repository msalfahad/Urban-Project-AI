"""T-290 stairs and domes basis ledger on a hand-calculated NON-Alsenan fixture (villa K, synthetic).

Villa K, dog-leg stair GF -> 1F plus one roof dome (every value printed on the villa K sheets S-03 / S-04 / S-07 unless
stated). Owner method (Q-19 / Q-47 A): n step triangles + the waist along the sloped length of the n goings.
  F1 lower flight: 6 risers 0.170 printed, 5 drawn goings 0.300 (the top tread IS the landing: demonstrated on S-04),
     width 1.10, waist 'T 15': steps 5 x 1/2 x 0.17 x 0.30 x 1.10 = 0.140250; waist 0.15 x 1.10 x hypot(1.50, 0.85)
     = 0.15 x 1.10 x 1.724094 = 0.284476 -> 0.424726 m3, VERIFIED (Checker record CHK-K-01).
  L1 half landing: drawn polygon 1.10 x 1.25 less a 0.20 x 0.20 chamfer = 1.355 m2 x 0.15 = 0.203250 m3 (DC, S-04).
  F2 upper flight: risers by the owner rule K-OR-1 (0.170, the section counts only), 6 goings 0.300, width 1.10,
     waist 0.15: steps 6 x 1/2 x 0.17 x 0.30 x 1.10 = 0.168300; waist 0.15 x 1.10 x hypot(1.80, 1.02) = 0.341371
     -> 0.509671 m3 (ASSUMED - OWNER-APPROVED).
  W1 winder turn at the head of F2: three wedge lines drawn, no dimension, no soffit -> HELD blank (RFI K-1).
  E1 entrance steps: 3 risers 0.15, goings 0.30, width 2.00 printed: steps 3 x 1/2 x 0.15 x 0.30 x 2.00 = 0.135000
     (DC); waist / support not printed -> HELD (RFI K-2). The engine released E1 on a convention waist 0.15.
  D1 roof dome shell: spherical cap, mid-surface radius 2.00, rise 1.00, shell 0.10 printed on S-07:
     2 pi x 2.00 x 1.00 x 0.10 = 1.256637 m3, VERIFIED (CHK-K-02). Its ring is a beam-line member (OWNED_ELSEWHERE).
  F2 head inside floor beam B5: 0.031 m3 billed in the beam line (OWNED_ELSEWHERE).
Candidate lines: LK-1 = F1 + L1 (engine 0.650 at a convention waist), LK-2 = F2 + W1 (BLOCKED), LK-3 = E1 (engine
0.4335 at the convention waist), LK-4 = D1 shell (engine 1.256637), LK-5 a retired convention dome (no quantity).
"""
from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t290"))
import stair_dome_basis as B  # noqa: E402

CTX = {"project_id": "VILLA-K", "revision_set_sha256": "cd" * 32, "candidate": "TEST_V1"}
P = "PRINTED"

F1 = B.flight_owner_method(5, 0.170, 0.300, 1.10, 0.15)
F2 = B.flight_owner_method(6, 0.170, 0.300, 1.10, 0.15)
L1 = (1.10 * 1.25 - 0.5 * 0.20 * 0.20) * 0.15
E1 = 3 * 0.5 * 0.15 * 0.30 * 2.00
SHELL = 2 * math.pi * 2.00 * 1.00 * 0.10


def comps():
    return [
        {"id": "F1", "kind": "FLIGHT", "status": B.VERIFIED, "value_m3": F1, "checker": "CHK-K-01",
         "dims": {"riser": P, "going": P, "width": P, "waist": P}, "soffit_rows": ["SOF-F1"], "formwork_rows": ["FW-F1"]},
        {"id": "L1", "kind": "LANDING", "status": B.DC, "value_m3": L1, "sheet": "S-04",
         "dims": {"polygon": P, "thickness": P}, "soffit_rows": ["SOF-L1"]},
        {"id": "F2", "kind": "FLIGHT", "status": B.AOA, "value_m3": F2, "owner_rule": "K-OR-1",
         "dims": {"riser": "OWNER_RULE", "going": P, "width": P, "waist": P}},
        {"id": "W1", "kind": "WINDER", "status": B.HELD, "drawn_dimensioned": False, "held_item": "RFI K-1"},
        {"id": "E1-STEPS", "kind": "STEPS", "status": B.DC, "value_m3": E1, "sheet": "S-03",
         "dims": {"riser": P, "going": P, "width": P}},
        {"id": "E1-WAIST", "kind": "WAIST", "status": B.HELD, "held_item": "RFI K-2"},
        {"id": "D1-SHELL", "kind": "SHELL", "status": B.VERIFIED, "value_m3": SHELL, "checker": "CHK-K-02",
         "dims": {"radius": P, "rise": P, "thickness": P}},
        {"id": "D1-RING", "kind": "RING", "status": B.OWNED_ELSEWHERE, "owner_line": "BEAM"},
        {"id": "F2-HEAD", "kind": "HEAD", "status": B.OWNED_ELSEWHERE, "owner_line": "BEAM", "value_m3": 0.031},
    ]


def lines():
    return [
        {"group": "STAIR", "line_id": "LK-1", "item_code": "STR.CONC.STAIR", "engine_qty_m3": 0.650,
         "engine_state": "SOURCE_DERIVED", "components": ["F1", "L1"]},
        {"group": "STAIR", "line_id": "LK-2", "item_code": "STR.CONC.STAIR", "engine_qty_m3": None,
         "engine_state": "BLOCKED_RFI", "components": ["F2", "W1"]},
        {"group": "STAIR", "line_id": "LK-3", "item_code": "STR.CONC.STAIR", "engine_qty_m3": 0.4335,
         "engine_state": "PROVISIONAL", "components": ["E1-STEPS", "E1-WAIST"]},
        {"group": "DOME", "line_id": "LK-4", "item_code": "STR.CONC.DOME", "engine_qty_m3": SHELL,
         "engine_state": "SOURCE_DERIVED", "components": ["D1-SHELL"]},
        {"group": "DOME", "line_id": "LK-5", "item_code": "STR.CONC.DOME", "engine_qty_m3": None,
         "engine_state": "NOT_APPLICABLE_WITH_EVIDENCE", "components": [], "reason": "retired convention dome"},
    ]


NAMED = {"STAIR": 0.650 + 0.4335, "DOME": SHELL}


def run(ls=None, cs=None, named=NAMED):
    return {r["line_id"]: r for r in B.ledger(ls or lines(), cs or comps(), CTX, named)}


# ---------------------------------------------------------------- NORMAL
def test_hand_values():
    assert round(F1, 6) == 0.424726 and round(F2, 6) == 0.509671
    assert round(L1, 6) == 0.203250 and round(E1, 6) == 0.135 and round(SHELL, 6) == 1.256637


def test_drawn_flight_and_landing_line_is_the_sum_at_the_weakest_status():
    r = run()["LK-1"]
    assert round(r["drawing_qty_m3"], 6) == 0.627976
    assert r["status"] == B.DC                       # VERIFIED F1 + DC L1 -> DC, never VERIFIED
    assert round(r["delta_m3"], 6) == round(0.627976 - 0.650, 6)
    assert r["soffit_rows"] == "SOF-F1 ; SOF-L1" and r["formwork_rows"] == "FW-F1"


def test_line_with_a_held_winder_is_blank_with_its_closable_part_beside_it():
    r = run()["LK-2"]
    assert r["drawing_qty_m3"] is None and r["status"] == B.HELD
    assert r["held_item"] == "RFI K-1"
    assert round(r["closable_component_m3"], 6) == 0.509671 and r["closable_by_status"].startswith(B.AOA)
    assert r["drawing_low_m3"] is None                # the winder has no bound: the line has none


def test_convention_waist_line_is_held_steps_known():
    r = run()["LK-3"]
    assert r["status"] == B.HELD and r["drawing_qty_m3"] is None and r["delta_m3"] is None
    assert round(r["closable_component_m3"], 6) == 0.135


def test_verified_dome_and_retired_line():
    rows = run()
    assert rows["LK-4"]["status"] == B.VERIFIED and round(rows["LK-4"]["delta_m3"], 9) == 0
    assert rows["LK-5"]["status"] == B.NOT_APPLICABLE and rows["LK-5"]["drawing_qty_m3"] is None


def test_owned_elsewhere_pieces_are_not_unbound_omissions():
    rows = B.ledger(lines(), comps(), CTX, NAMED)
    assert B.unbound(rows, comps()) == []
    cs = comps() + [{"id": "F3", "kind": "FLIGHT", "status": B.DC, "value_m3": 0.2, "sheet": "S-04"}]
    assert B.unbound(B.ledger(lines(), cs, CTX, NAMED), cs) == ["F3"]


def test_mirror_order_invariant():
    a = run()
    b = run(list(reversed(lines())), list(reversed(comps())))
    for k in a:
        assert a[k]["status"] == b[k]["status"] and a[k]["drawing_qty_m3"] == b[k]["drawing_qty_m3"]


def test_conflict_line_carries_the_range():
    cs = comps()
    cs[1] = {"id": "L1", "kind": "LANDING", "status": B.CONFLICT, "low_m3": 0.18, "high_m3": 0.21, "held_item": "K-3"}
    r = run(cs=cs)["LK-1"]
    assert r["status"] == B.CONFLICT and r["drawing_qty_m3"] is None
    assert round(r["drawing_low_m3"], 6) == round(F1 + 0.18, 6) and round(r["drawing_high_m3"], 6) == round(F1 + 0.21, 6)


# ---------------------------------------------------------------- ADVERSE
def test_undimensioned_winder_with_a_value_is_refused():
    cs = comps()
    cs[3] = {"id": "W1", "kind": "WINDER", "status": B.DC, "value_m3": 0.12, "sheet": "S-04", "drawn_dimensioned": False}
    with pytest.raises(B.BasisError, match="never generated"):
        run(cs=cs)
    cs[3] = {"id": "W1", "kind": "WINDER", "status": B.HELD, "value_m3": 0.0, "held_item": "RFI K-1"}
    with pytest.raises(B.BasisError):
        run(cs=cs)


def test_convention_waist_refused_as_drawing_confirmed():
    cs = comps()
    cs[4] = {"id": "E1-STEPS", "kind": "FLIGHT", "status": B.DC, "value_m3": 0.4335, "sheet": "S-03",
             "dims": {"riser": P, "going": P, "width": P, "waist": "CONVENTION"}}
    with pytest.raises(B.BasisError, match="CONVENTION"):
        run(cs=cs)
    cs[4]["status"], cs[4]["checker"] = B.VERIFIED, "CHK-X"
    with pytest.raises(B.BasisError, match="CONVENTION"):
        run(cs=cs)


def test_same_piece_in_two_lines_refused():
    ls = lines()
    ls[2]["components"] = ["E1-STEPS", "E1-WAIST", "F1"]
    with pytest.raises(B.BasisError, match="two lines"):
        run(ls=ls)


def test_owned_elsewhere_piece_bound_to_a_stair_line_refused():
    ls = lines()
    ls[1]["components"] = ["F2", "W1", "F2-HEAD"]
    with pytest.raises(B.BasisError, match="owned by the BEAM line"):
        run(ls=ls)


def test_held_without_item_zero_value_and_single_end_conflict_refused():
    for bad in ({"id": "E1-WAIST", "kind": "WAIST", "status": B.HELD},
                {"id": "E1-WAIST", "kind": "WAIST", "status": B.HELD, "value_m3": 0, "held_item": "K-2"},
                {"id": "E1-WAIST", "kind": "WAIST", "status": B.CONFLICT, "value_m3": 0.2, "held_item": "K-2"},
                {"id": "E1-WAIST", "kind": "WAIST", "status": B.CONFLICT, "low_m3": 0.2, "high_m3": 0.2, "held_item": "K"},
                {"id": "E1-WAIST", "kind": "WAIST", "status": B.DC, "value_m3": 0.0, "sheet": "S-03"},
                {"id": "E1-WAIST", "kind": "WAIST", "status": B.VERIFIED, "value_m3": 0.1},
                {"id": "E1-WAIST", "kind": "WAIST", "status": B.AOA, "value_m3": 0.1},
                {"id": "E1-WAIST", "kind": "WAIST", "status": "PROBABLE", "value_m3": 0.1}):
        cs = comps()
        cs[5] = bad
        with pytest.raises(B.BasisError):
            run(cs=cs)


def test_soffit_row_given_to_two_pieces_refused():
    cs = comps()
    cs[2]["soffit_rows"] = ["SOF-F1"]
    with pytest.raises(B.BasisError, match="one owner"):
        run(cs=cs)


def test_named_total_residual_and_duplicates_refused():
    with pytest.raises(B.BasisError, match="named total"):
        run(named={"STAIR": 1.0, "DOME": SHELL})
    ls = lines() + [copy.deepcopy(lines()[0])]
    with pytest.raises(B.BasisError, match="line id appears twice"):
        B.ledger(ls, comps(), CTX, None)
    with pytest.raises(B.BasisError, match="appears twice"):
        B.ledger(lines(), comps() + [comps()[0]], CTX, None)
    with pytest.raises(B.BasisError, match="context"):
        B.ledger(lines(), comps(), {"project_id": "VILLA-K", "candidate": "X"}, None)


def test_line_without_pieces_must_be_retired_and_cited_row_books_nothing():
    ls = lines()
    ls[3]["components"] = []
    with pytest.raises(B.BasisError, match="retired"):
        run(ls=ls)
    ls = lines()
    ls[2] = dict(ls[2], components=[], cited="T-OTHER", cited_status=B.HELD, cited_item="RFI K-2", drawing_qty_m3=0.135)
    cs = [c for c in comps() if not c["id"].startswith("E1")]
    with pytest.raises(B.BasisError, match="CITED"):
        run(ls=ls, cs=cs)
    del ls[2]["drawing_qty_m3"]
    r = run(ls=ls, cs=cs)["LK-3"]
    assert r["ledger_owner"] == "T-OTHER" and r["status"] == B.HELD and r["drawing_qty_m3"] is None


def test_flight_formula_has_no_default():
    for args in ((5, 0.17, 0.30, 1.10, None), (5, 0.17, 0.30, 1.10, 0.0), (0, 0.17, 0.30, 1.10, 0.15),
                 (5, None, 0.30, 1.10, 0.15)):
        with pytest.raises(B.BasisError):
            B.flight_owner_method(*args)


def test_unit_slip_mm_value_is_caught_by_the_named_total():
    cs = comps()
    ls = lines()
    ls[0]["engine_qty_m3"] = 650.0                    # mm-scale slip on the engine side
    with pytest.raises(B.BasisError, match="named total"):
        run(ls=ls, cs=cs)
