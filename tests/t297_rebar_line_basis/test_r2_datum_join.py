"""T-297 r2 (Checker F-T297-04): one member, one datum status across trades (rule LB-10), on a hand-calculated
NON-Alsenan villa (K297r2) and adverse cases. Nothing here comes from a client drawing.

Villa K297r2 (invented): top-storey column C7 (0.20 x 0.40) carries '4 ø 12' over the storey interval 3.30 m from the
2F slab top to the ROOF slab top; the roof drawing prints only the finished roof level (no structural roof level, no
build-up), so the candidate HOLDS C7's concrete on the roof datum 'RD-1'. Its links '6 ø 8 / m' over the concrete height
are a BOUND 4.80 .. 5.10 kg (count readings). Column C8 on the same storey has a printed structural roof level: its
datum is not held.

Hand values (kg/m = d^2 / 162 as the fixture's check table):
  C7 main: 4 x 3.30 x 144 / 162 = 4 x 3.30 x 0.888889 = 11.733333 kg  -> HELD (kg kept as audit only), never DC
  C8 main: 4 x 3.30 x 0.888889 = 11.733333 kg                          -> DRAWING_CONFIRMED (datum printed)
  C7 links: BOUND 4.80 .. 5.10 kg whose datum names RD-1, datum status HELD
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t297"
sys.path.insert(0, str(HERE))
import t297_datum_join as J  # noqa: E402
import t297_ledger as L  # noqa: E402

MAIN = 4 * 3.30 * 144 / 162
RD = "RD-1_ROOF_DATUM (concrete line L-K-C7 HELD)"


def c7_main(status="HELD", **kw):
    base = dict(line_kg=MAIN, length_datum=RD, length_datum_status="HELD", flags=("BAR_LENGTH_ON_HELD_DATUM",),
                reason="LB-10: bar length on the held roof datum", evidence="schedule C7 2F 4 ø 12")
    base.update(kw)
    if status != "HELD" and "quantity_kg" not in kw:
        base["quantity_kg"] = MAIN
    return L.Row("L-K-C7-MAIN", "COLUMNS", ("COL-K-C7",), "MAIN BARS net", status, **base)


def c7_links(**kw):
    base = dict(bound_low_kg=4.80, bound_high_kg=5.10, datum="count readings A / B | length datum: " + RD,
                datum_status="HELD", length_datum=RD, length_datum_status="HELD", reason="Q-71 count readings")
    base.update(kw)
    return L.Row("L-K-C7-LINKS", "COLUMNS", ("COL-K-C7",), "LINKS 6 ø 8 / m", "BOUND", **base)


def c8_main():
    return L.Row("L-K-C8-MAIN", "COLUMNS", ("COL-K-C8",), "MAIN BARS net", "DRAWING_CONFIRMED", quantity_kg=MAIN,
                 evidence="schedule C8 2F 4 ø 12; structural roof level printed")


def test_hand_value():
    assert round(MAIN, 6) == 11.733333


def test_normal_held_datum_row_is_held_and_the_printed_one_is_measured():
    s = L.build([c7_main(), c7_links(), c8_main()], ["L-K-C7-MAIN", "L-K-C7-LINKS", "L-K-C8-MAIN"])
    t = s["totals"]
    assert t["COLUMNS|DRAWING_CONFIRMED"] == {"lines": 1, "kg": 11.733333, "t": 0.011733}   # C8 only
    assert t["COLUMNS|HELD"] == {"lines": 1}
    assert t["COLUMNS|BOUND"]["low_kg"] == 4.8 and t["COLUMNS|BOUND"]["high_kg"] == 5.1
    c = {r["line_id"]: r for r in L.consumer([c7_main(), c7_links(), c8_main()])}
    assert c["L-K-C7-MAIN"]["quantity_t"] is None and c["L-K-C7-MAIN"]["length_datum"]["status"] == "HELD"
    assert RD in c["L-K-C7-LINKS"]["bound_t"]["datum"] and c["L-K-C8-MAIN"]["length_datum"] is None


@pytest.mark.parametrize("status", ["DRAWING_CONFIRMED", "VERIFIED", "CONVENTION", "ASSUMED_OWNER_APPROVED"])
def test_adverse_bar_on_a_held_datum_cannot_be_measured(status):
    with pytest.raises(L.LedgerError, match="cannot be"):
        L.check_row(c7_main(status))


def test_adverse_bound_on_a_held_datum_must_name_it():
    with pytest.raises(L.LedgerError, match="names it"):
        L.check_row(c7_links(datum="count readings A / B"))
    with pytest.raises(L.LedgerError, match="names it"):
        L.check_row(c7_links(datum_status="DRAWING_CONFIRMED"))


def test_adverse_bound_on_a_superseded_height_and_absent_member():
    with pytest.raises(L.LedgerError, match="superseded"):
        L.check_row(c7_links(length_datum_status="SUPERSEDED"))
    with pytest.raises(L.LedgerError, match="NOT_APPLICABLE"):
        L.check_row(c7_main(length_datum_status="NOT_PRESENT"))
    with pytest.raises(L.LedgerError, match="named"):
        L.check_row(c7_main(length_datum=""))
    with pytest.raises(L.LedgerError, match="length datum status"):
        L.check_row(c7_main(length_datum_status="PENDING"))


def test_adverse_held_datum_row_never_zero():
    with pytest.raises(L.LedgerError, match="blank, never 0"):
        L.check_row(c7_main(quantity_kg=0.0))


# ---- the join's own checks on invented stacks (plan panels shifted per storey; mirror / rotation-free fixture) ----

def _tie(pairs):
    return {m: (lid, eid, "PROVISIONAL") for m, lid, eid in pairs}


MEM = {"K-GF-1": {"mark": "C2", "storey": "GF", "x": "10.000", "y": "5.000"},
       "K-1F-1": {"mark": "C2", "storey": "1F", "x": "-20.000", "y": "5.000"},
       "K-GF-2": {"mark": "C2", "storey": "GF", "x": "14.000", "y": "5.000"},
       "K-1F-2": {"mark": "C2", "storey": "1F", "x": "-16.000", "y": "5.000"}}


def test_normal_stack_check_on_a_constant_storey_shift():
    tie = _tie([("K-GF-1", "L1", "P-C:COL:SH12:C2@100000,9000|GF"), ("K-1F-1", "L2", "P-C:COL:SH12:C2@100000,9000|1F"),
                ("K-GF-2", "L3", "P-C:COL:SH12:C2@104500,9000|GF"), ("K-1F-2", "L4", "P-C:COL:SH12:C2@104500,9000|1F")])
    shift, n, total, _ = J.storey_shift(tie, MEM)
    assert (shift, n, total) == (30.0, 2, 2)
    rows = J.stack_check([{"member": "K-1F-1"}, {"member": "K-1F-2"}], tie, MEM)
    assert rows[0]["stack_members"] == ["K-1F-1", "K-GF-1"]


def test_adverse_crossed_tie_between_two_columns_of_one_mark_is_refused():
    tie = _tie([("K-GF-1", "L1", "P-C:COL:SH12:C2@100000,9000|GF"), ("K-1F-1", "L4", "P-C:COL:SH12:C2@104500,9000|1F"),
                ("K-GF-2", "L3", "P-C:COL:SH12:C2@104500,9000|GF"), ("K-1F-2", "L2", "P-C:COL:SH12:C2@100000,9000|1F"),
                ("K-GF-3", "L5", "P-C:COL:SH12:C2@108000,9000|GF"), ("K-1F-3", "L6", "P-C:COL:SH12:C2@108000,9000|1F"),
                ("K-GF-4", "L7", "P-C:COL:SH12:C2@112000,9000|GF"), ("K-1F-4", "L8", "P-C:COL:SH12:C2@112000,9000|1F")])
    mem = dict(MEM, **{"K-GF-3": {"mark": "C2", "storey": "GF", "x": "20.000", "y": "5.000"},
                       "K-1F-3": {"mark": "C2", "storey": "1F", "x": "-10.000", "y": "5.000"},
                       "K-GF-4": {"mark": "C2", "storey": "GF", "x": "24.000", "y": "5.000"},
                       "K-1F-4": {"mark": "C2", "storey": "1F", "x": "-6.000", "y": "5.000"}})
    assert J.storey_shift(tie, mem)[:2] == (30.0, 2)      # the two true stacks outvote the crossed pair
    with pytest.raises(J.JoinError, match="not one plan position"):
        J.stack_check([{"member": "K-1F-1"}], tie, mem)


def test_adverse_columns_closer_than_the_tolerance_refuse_the_join():
    mem = dict(MEM, **{"K-GF-9": {"mark": "C2", "storey": "GF", "x": "10.500", "y": "5.300"}})
    tie = _tie([("K-GF-1", "L1", "P-C:COL:SH12:C2@100000,9000|GF"), ("K-1F-1", "L2", "P-C:COL:SH12:C2@100000,9000|1F")])
    with pytest.raises(J.JoinError, match="apart"):
        J.stack_check([{"member": "K-1F-1"}], tie, mem)


# ---- the join on the committed merged inputs: mark / storey and NOT_PRESENT refusals (records invented) ----

def test_adverse_mark_mismatch_and_tied_absent_member_are_refused():
    tie = J.ties()
    lid = next(iter(v[0] for k, v in tie.items() if k.startswith("COL-2F-")))
    with pytest.raises(J.JoinError, match="!="):
        J.build_join([{"line_id": lid, "element_id": "P-C:COL:SH12:C99@1,1|2F", "group": "X", "action": "HOLD",
                       "held_item": "D-39_ROOF_DATUM"}])
    with pytest.raises(J.JoinError, match="NOT_PRESENT"):
        J.build_join([{"line_id": lid, "element_id": "P-C:COL:SH12:C2@1,1|2F", "group": "X",
                       "action": "NOT_PRESENT"}])
    with pytest.raises(J.JoinError, match="no tied"):
        J.build_join([{"line_id": "L-none", "element_id": "P-C:COL:SH12:C2@1,1|2F", "group": "X", "action": "HOLD",
                       "held_item": "D-39_ROOF_DATUM"}])
