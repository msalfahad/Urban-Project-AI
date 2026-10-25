"""T-291 R-T291-1 on a hand-calculated villa N (not Alsenan): normal and adverse cases.

Villa N, ground storey 4.16 m, slab 0.16 -> normal panel 4.00 m (hand):
  N-W1 0.20 BLACK  3.000 m x 4.000 = 12.000 - door D1 1.000 x 2.000 = 10.000 m2  VERIFIED (Checker run 'C-1')
  N-W2 0.20 BLACK  2.000 m x 3.000 (under a beam soffit 3.00) = 6.000 m2          DRAWING-CONFIRMED
  N-W3 0.20 WHITE  4.000 m, beam over it not printed                             HELD 'beam depth (RFI-7)'
  N-W4 0.20 BLACK  2.000 m x 4.000 = 8.000 at d = 0, 1.500 m under a sunken panel -> 8.000 - 1.500 x d m2
  N-W5 0.15 BLACK  1.250 m x 4.000 = 5.000 m2 ASSUMED - OWNER-APPROVED, the engine books 3/4 of it in the 0.15 line
                   and 1/4 in the mixed-thickness junction line (one wall in two line ids)
  N-W6 0.20 WHITE  2.500 m: established part 1.500 x 4.000 = 6.000 m2 (DRAWING-CONFIRMED) + held piece 1.000 m
Lines: L-020 (ARCH.WALL_PANEL GF 0.2, engine 33.000), L-015 (ARCH.WALL_PANEL GF 0.15), L-JN (ARCH.WALL_PANEL GF
junction), L-1F (ARCH.WALL_PANEL 1F 0.2, no register wall on 1F -> unmatched line).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t291"))

import wall_line_ledger as R  # noqa: E402

PANEL = "ARCH.WALL_PANEL"


def walls():
    return [
        {"wall_id": "N-W1", "floor": "GF", "t_m": 0.2, "block_type": "BLACK", "state": "ESTABLISHED",
         "class": "VERIFIED", "net_m2": 3.0 * 4.0 - 1.0 * 2.0, "verified_by": "C-1", "deductions_m2": 2.0},
        {"wall_id": "N-W2", "floor": "GF", "t_m": 0.2, "block_type": "BLACK", "state": "ESTABLISHED",
         "class": "SOURCE-SUPPORTED PENDING INDEPENDENT CHECK", "net_m2": 2.0 * 3.0},
        {"wall_id": "N-W3", "floor": "GF", "t_m": 0.2, "block_type": "WHITE", "state": "HELD", "class": "HELD",
         "held_items": "beam depth (RFI-7)"},
        {"wall_id": "N-W4", "floor": "GF", "t_m": 0.2, "block_type": "BLACK", "state": "HELD ON DROP",
         "class": "SOURCE-SUPPORTED PENDING INDEPENDENT CHECK", "upper_m2": 2.0 * 4.0, "drop_length_m": 1.5,
         "held_items": "drop d (RFI-8)"},
        {"wall_id": "N-W5", "floor": "GF", "t_m": 0.15, "block_type": "BLACK", "state": "ESTABLISHED",
         "class": "PROJECT-SPECIFIC", "net_m2": 1.25 * 4.0},
        {"wall_id": "N-W6", "floor": "GF", "t_m": 0.2, "block_type": "WHITE", "state": "ESTABLISHED_PART_PLUS_HELD",
         "class": "SOURCE-SUPPORTED PENDING INDEPENDENT CHECK", "net_m2": 1.5 * 4.0, "held_items": "1.000 m piece"},
    ]


def lines():
    return [
        {"line_id": "L-020", "item_code": PANEL, "floor": "GF", "family": "0.2", "unit": "m2"},
        {"line_id": "L-015", "item_code": PANEL, "floor": "GF", "family": "0.15", "unit": "m2"},
        {"line_id": "L-JN", "item_code": PANEL, "floor": "GF", "family": "junction", "unit": "m2"},
        {"line_id": "L-1F", "item_code": PANEL, "floor": "1F", "family": "0.2", "unit": "m2"},
    ]


SHARES = {("N-W5", PANEL): {"L-015": 0.75, "L-JN": 0.25}}


def build(ws=None, ls=None, shares=SHARES):
    ws, ls = ws or walls(), ls or lines()
    b, uw, ul = R.bind(ws, ls, shares)
    return ws, R.ledger_rows(ws, ls, b), uw, ul


def test_normal_binding_and_hand_values():
    ws, rows, uw, ul = build()
    by = {(r["wall_id"], r["line_id"]): r for r in rows}
    assert by[("N-W1", "L-020")]["carried"] == pytest.approx(10.000)
    assert by[("N-W1", "L-020")]["status"] == R.VERIFIED and by[("N-W1", "L-020")]["verified_by"] == "C-1"
    assert by[("N-W2", "L-020")]["carried"] == pytest.approx(6.000)
    assert by[("N-W3", "L-020")]["carried"] is None and by[("N-W3", "L-020")]["held_item"] == "beam depth (RFI-7)"
    d = by[("N-W4", "L-020")]
    assert d["carried"] is None and d["upper"] == pytest.approx(8.000) and d["drop_length_m"] == pytest.approx(1.5)
    # one wall in two line ids: 5.000 = 3.750 + 1.250
    assert by[("N-W5", "L-015")]["carried"] == pytest.approx(3.750)
    assert by[("N-W5", "L-JN")]["carried"] == pytest.approx(1.250)
    p = by[("N-W6", "L-020")]
    assert p["status"] == R.PART_PLUS_HELD and p["carried"] == pytest.approx(6.000) and p["part_status"] == R.DC
    # one line holding several walls
    assert sorted(r["wall_id"] for r in rows if r["line_id"] == "L-020") == ["N-W1", "N-W2", "N-W3", "N-W4", "N-W6"]
    assert uw == [] and ul == [("L-1F", "no register wall of storey 1F family 0.2")]


def test_closure_per_status_is_zero():
    ws, rows, _, _ = build()
    res = R.closure(ws, rows, PANEL, "m2")
    assert all(abs(v) <= R.TOL for v in res.values())
    t = R.ledger_totals(rows, PANEL)
    assert t[R.VERIFIED] == pytest.approx(10.0) and t[R.DC] == pytest.approx(6.0) and t[R.AOA] == pytest.approx(5.0)
    assert t["upper"] == pytest.approx(8.0) and t["drop_length_m"] == pytest.approx(1.5)
    assert t[R.PART_PLUS_HELD] == pytest.approx(6.0)


def test_m3_rows_are_m2_times_thickness():
    ws = walls()
    ls = [dict(ln, item_code="ARCH.WALL_VOLUME", unit="m3") for ln in lines()]
    b, _, _ = R.bind(ws, ls, {("N-W5", "ARCH.WALL_VOLUME"): {"L-015": 0.75, "L-JN": 0.25}})
    rows = R.ledger_rows(ws, ls, b)
    by = {(r["wall_id"], r["line_id"]): r for r in rows}
    assert by[("N-W1", "L-020")]["carried"] == pytest.approx(2.000)          # 10.000 x 0.20
    assert by[("N-W5", "L-015")]["carried"] == pytest.approx(0.5625)         # 3.750 x 0.15
    assert by[("N-W4", "L-020")]["drop_coefficient"] == pytest.approx(0.300)  # 1.500 x 0.20 m3 per m of d
    R.closure(ws, rows, "ARCH.WALL_VOLUME", "m3")


def test_mirror_and_order_do_not_change_the_ledger():
    a = build()[1]
    b = build(ws=list(reversed(walls())), ls=list(reversed(lines())))[1]
    key = lambda r: (r["wall_id"], r["line_id"])  # noqa: E731
    assert sorted(map(str, sorted(a, key=key))) == sorted(map(str, sorted(b, key=key)))


# --- adverse ------------------------------------------------------------------------------------------------

def test_wall_in_no_line_is_listed_not_dropped():
    ws = walls() + [{"wall_id": "N-W7", "floor": "2F", "t_m": 0.2, "state": "ESTABLISHED",
                     "class": "PROJECT-SPECIFIC", "net_m2": 3.0}]
    b, uw, _ = R.bind(ws, lines(), SHARES)
    assert ("N-W7", PANEL, "no ARCH.WALL_PANEL line for storey 2F thickness 0.2 m") in uw
    rows = R.ledger_rows(ws, lines(), b)
    with pytest.raises(R.LedgerError, match="^NOT_CLOSED"):
        R.closure(ws, rows, PANEL, "m2")          # the register keeps the wall: the gap shows, never silently closes


def test_held_wall_summed_as_zero_is_refused():
    ws, rows, _, _ = build()
    r = next(x for x in rows if x["wall_id"] == "N-W3")
    with pytest.raises(R.LedgerError, match="^HELD_AS_ZERO"):
        R.check_row(dict(r, carried=0.0))
    with pytest.raises(R.LedgerError, match="^HELD_UNNAMED"):
        R.check_row(dict(r, held_item=None))


def test_opening_deducted_twice_is_refused():
    ops = [{"opening_id": "D1", "host": "N-W1", "deduction_m2": 2.0, "state": "DEDUCTED"},
           {"opening_id": "D1", "host": "N-W2", "deduction_m2": 2.0, "state": "DEDUCTED"}]
    with pytest.raises(R.LedgerError, match="^OPENING_TWICE"):
        R.opening_ledger(ops, walls())
    assert R.opening_ledger(ops[:1], walls()) == {"N-W1": 2.0}
    with pytest.raises(R.LedgerError, match="^OPENING_SUM"):
        R.opening_ledger([dict(ops[0], deduction_m2=1.8)], walls())
    with pytest.raises(R.LedgerError, match="^HELD_AS_ZERO"):
        R.opening_ledger([{"opening_id": "W9", "host": "N-W3", "deduction_m2": 0.0, "state": "HELD"}], [])


def test_drop_term_evaluated_at_zero_is_refused():
    ws, rows, _, _ = build()
    r = next(x for x in rows if x["wall_id"] == "N-W4")
    with pytest.raises(R.LedgerError, match="^DROP_EVALUATED"):
        R.check_row(dict(r, carried=8.0))           # d = 0 booked as a quantity
    with pytest.raises(R.LedgerError, match="^DROP_EVALUATED"):
        R.evaluate_drop(r, 0.0)
    with pytest.raises(R.LedgerError, match="^HELD_AS_ZERO"):
        R.check_row(dict(r, upper=None))


def test_wall_carried_twice_is_refused():
    ws, rows, _, _ = build()
    dup = rows + [dict(next(x for x in rows if x["wall_id"] == "N-W2"), line_id="L-1F")]
    with pytest.raises(R.LedgerError, match="^WALL_TWICE"):
        R.ledger_totals(dup, PANEL)
    with pytest.raises(R.LedgerError, match="^WALL_TWICE"):
        R.bind(walls() + [walls()[0]], lines(), SHARES)


def test_verified_without_checker_run_and_bad_units_refused():
    w = walls()
    w[0] = dict(w[0], verified_by=None)
    with pytest.raises(R.LedgerError, match="^NO_CHECKER_RUN"):
        build(ws=w)
    w = walls()
    w[1] = dict(w[1], t_m=200)          # millimetres
    with pytest.raises(R.LedgerError, match="^BAD_UNITS"):
        build(ws=w)


def test_conflict_increment_stays_outside_totals():
    w = walls()
    w[1] = dict(w[1], conflict="beam width CONFLICT", conflict_increment_m2=0.017)
    ws, rows, _, _ = build(ws=w)
    r = next(x for x in rows if x["wall_id"] == "N-W2")
    assert r["carried"] == pytest.approx(6.0) and r["conflict_increment"] == pytest.approx(0.017)
    assert R.ledger_totals(rows, PANEL)[R.DC] == pytest.approx(6.0)
    with pytest.raises(R.LedgerError, match="^CONFLICT_IN_TOTAL"):
        R.check_row(dict(r, conflict_in_total=True))


def test_ambiguous_lines_need_declared_shares():
    ls = lines() + [{"line_id": "L-020b", "item_code": PANEL, "floor": "GF", "family": "0.2", "unit": "m2"}]
    with pytest.raises(R.LedgerError, match="^AMBIGUOUS_LINE"):
        R.bind(walls(), ls, SHARES)
    with pytest.raises(R.LedgerError, match="^SHARES_NOT_CLOSED"):
        R.bind(walls(), lines(), {("N-W5", PANEL): {"L-015": 0.7, "L-JN": 0.25}})


def test_engine_vs_register_named_parts():
    ws, rows, _, _ = build()
    r020 = [r for r in rows if r["line_id"] == "L-020"]
    ops = [{"opening_id": "D1", "host": "N-W1", "deduction_m2": 2.0, "state": "DEDUCTED"}]
    blank = R.engine_vs_register({"line_id": "L-020", "quantity": None}, r020, ws, ops)
    assert blank["engine"] is None                               # a BLOCKED engine line: nothing to reconcile
    p = R.engine_vs_register({"line_id": "L-020", "quantity": 33.0}, r020, ws, ops,
                             [{"opening_id": "D1", "deduction_m2": 2.2}])
    # carried 10.000 + 6.000 + 6.000 (part) = 22.000; engine 33.000 -> 11.000 m2 to the named parts
    assert p["carried_determinate_and_parts"] == pytest.approx(22.0) and p["engine_minus_carried"] == pytest.approx(11.0)
    assert p["a_held_walls"] == ["N-W3"] and p["b_drop_upper_at_d0"] == pytest.approx(8.0)
    assert p["c_openings_register_m2"] == pytest.approx(2.0) and p["c_openings_engine_m2"] == pytest.approx(2.2)
