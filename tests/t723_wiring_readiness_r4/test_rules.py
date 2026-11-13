"""R-T723-1 on a hand-made villa W723 (not the development villa): one-sided figures beside, text-only restatements,
exclusions, one live row per line, one line per row, a previous map restated on a new candidate, package sizes. Every
expected figure is written by hand below; adverse cases cover 0, negative, a range, an unknown side, a one-sided figure
on a bounded or released line, a conflict with no supersession, a row mapped to two lines, a stale host and mirror
(reversed) input order."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t723"))
import t723_rules as R  # noqa: E402

R705, R698 = R.R705, R.R698
E = R.ReadinessError


def ln(lid, code="STR.CONC.NECK", cls="HELD", v=None, lo=None, hi=None, unit="m3"):
    return {"line_id": lid, "item_code": code, "element_id": f"W723:{lid}", "unit": unit, "class": cls,
            "measured_net": v, "held_low": lo, "held_high": hi}


BLANK = ln("L-aaaa0001")
BOUNDED = ln("L-aaaa0002", lo=0.40, hi=0.60)
RELEASED = ln("L-aaaa0003", cls="RELEASED", v=0.55)
EXCL = ln("L-aaaa0004", cls="EXCLUDED")


# ------------------------------------------------------------------ rule 1: one-sided beside
def test_one_sided_beside_on_blank_line():
    a = R.after(R.ONE_SIDED, side="AT_LEAST", value=0.1730004)
    assert a["value"] == 0.173 and a["low"] is None and a["high"] is None
    assert R.wire_action(a, BLANK)[0] == R.BESIDE
    assert R.wire_action(a, BLANK, {"side": "AT_LEAST", "value": 0.173})[0] == R.KEEP
    act, why = R.wire_action(a, BLANK, {"side": "AT_LEAST", "value": 0.172999})
    assert act == R.RESTATE_BESIDE and "0.172999 -> AT_LEAST 0.173" in why
    assert R.wire_action(a, BLANK, {"side": "AT_MOST", "value": 0.173})[0] == R.RESTATE_BESIDE


def test_one_sided_on_bounded_or_released_is_form_conflict():
    a = R.after(R.ONE_SIDED, side="AT_MOST", value=0.425)
    assert R.wire_action(a, BOUNDED)[0] == R.FORM_CONFLICT
    assert R.wire_action(a, RELEASED)[0] == R.FORM_CONFLICT
    half = ln("L-aaaa0005", lo=0.30)                       # an open-ended held line still takes a figure beside
    assert R.wire_action(a, half)[0] == R.BESIDE


@pytest.mark.parametrize("kw", [dict(side="AT_LEAST", value=0), dict(side="AT_MOST", value=0),
                                dict(side="AT_MOST", value=-0.1), dict(side="AT_LEAST", value=None),
                                dict(side="BOTH", value=0.2), dict(side="AT_LEAST", value=0.2, lo=0.1),
                                dict(side="AT_MOST", value=0.2, hi=0.3)])
def test_one_sided_adverse(kw):
    with pytest.raises(E):
        R.after(R.ONE_SIDED, **kw)


def test_conditional_side_keeps_its_figure_beside():
    a = R.after(R.ONE_SIDED, side="CONDITIONAL", value=1.140175)
    assert R.after_text(a) == "ONE_SIDED CONDITIONAL 1.140175"
    assert R.wire_action(a, BLANK)[0] == R.BESIDE


# ------------------------------------------------------------------ rule 2: text only
def test_blank_with_cause_on_blank_line_is_text_not_keep():
    a = R.after(R705.BLANK, note="named: D-26")
    assert R.wire_action(a, BLANK)[0] == R.TEXT
    assert R.wire_action(a, BOUNDED)[0] == R.CHANGE          # a downgrade moves a number: never TEXT
    assert R.wire_action(a, RELEASED)[0] == R.CHANGE


# ------------------------------------------------------------------ rule 3: excluded
def test_excluded():
    a = R.after(R.EXCLUDED, note="owned by the landing line")
    assert R.wire_action(a, BOUNDED)[0] == R.CHANGE
    assert R.wire_action(a, EXCL)[0] == R.KEEP
    for kw in (dict(value=0), dict(lo=0, hi=2.9225)):
        with pytest.raises(E):
            R.after(R.EXCLUDED, **kw)


def test_inherited_r705_states_unchanged():
    assert R.wire_action(R.after(R705.BOUND, lo=0.40, hi=0.60), BOUNDED)[0] == R.KEEP
    assert R.wire_action(R.after(R705.BOUND, lo=0.45, hi=0.60), BOUNDED)[0] == R.CHANGE
    assert R.wire_action(R.after(R705.VALUE, value=0.55), RELEASED)[0] == R.KEEP
    with pytest.raises(E):
        R.after(R705.VALUE, value=0)


def test_check_after_refuses_zero_states():
    good = [{"row": "x", "after": R.after(R.ONE_SIDED, side="AT_LEAST", value=0.2)}]
    assert R.check_after(good)
    bad = dict(good[0], after=dict(good[0]["after"], value=0.0))
    with pytest.raises(E):
        R.check_after([bad])
    with pytest.raises(E):
        R.check_after([{"row": "y", "after": {"kind": R.EXCLUDED, "value": 0.0, "low": None, "high": None}}])


# ------------------------------------------------------------------ rule 4: one live row per line
def _row(piece, key, host, a, action=R.CHANGE):
    return {"piece": piece, "row": f"{piece}:{key}", "host_line_id": host, "new_line_key": None, "after": a,
            "action": action}


def test_duplicate_and_supersession_and_statement():
    a1 = R.after(R705.BOUND, lo=1.0, hi=2.0)
    rows = [_row("P1", "a", "L-1", a1), _row("P2", "a", "L-1", dict(a1)),                     # same statement
            _row("P1", "b", "L-2", R.after(R.ONE_SIDED, side="AT_LEAST", value=0.3), R.BESIDE),
            _row("P3", "b", "L-2", R.after(R705.BOUND, lo=0.3, hi=0.5)),                       # declared restatement
            _row("P2", "c", "L-3", R.after(R705.NOPROP)), _row("P3", "c", "L-3", R.after(R.EXCLUDED), R.CHANGE)]
    R.resolve_live(rows, ["P1", "P2", "P3"], {("P3", "P1"): {"L-2"}})
    live = {r["row"]: r["live"] for r in rows}
    assert live == {"P1:a": R.LIVE, "P2:a": R.DUPLICATE, "P1:b": R.SUPERSEDED, "P3:b": R.LIVE,
                    "P2:c": R.STATEMENT, "P3:c": R.LIVE}
    rev = [dict(r) for r in reversed(rows)]                                                 # mirror order
    R.resolve_live(rev, ["P1", "P2", "P3"], {("P3", "P1"): {"L-2"}})
    assert {r["row"]: r["live"] for r in rev} == live


def test_conflict_without_supersession_fails():
    rows = [_row("P1", "a", "L-1", R.after(R705.BOUND, lo=1.0, hi=2.0)),
            _row("P2", "a", "L-1", R.after(R705.BOUND, lo=1.0, hi=2.1))]
    with pytest.raises(E, match="CONFLICT on L-1"):
        R.resolve_live(rows, ["P1", "P2"], {})
    with pytest.raises(E):                                  # a declaration for another line does not help
        R.resolve_live(rows, ["P1", "P2"], {("P2", "P1"): {"L-9"}})


# ------------------------------------------------------------------ rule 5: one line per row (acceptance)
def test_row_mapped_to_two_lines_fails():
    a = R.after(R705.BOUND, lo=1.0, hi=2.0)
    ok = [_row("P1", "a", "L-1", a), _row("P1", "b", "L-2", a)]
    assert R.check_one_line_per_row(ok)
    with pytest.raises(E, match="mapped to two lines"):
        R.check_one_line_per_row(ok + [_row("P1", "a", "L-2", a)])


# ------------------------------------------------------------------ rule 6: restated map
def test_restate_class():
    old = {"L-1": ln("L-1", lo=1.0, hi=2.0), "L-2": ln("L-2"), "L-3": ln("L-3"), "L-4": ln("L-4")}
    new = {"L-1": ln("L-1", lo=1.0, hi=2.1), "L-2": ln("L-2"), "L-3": ln("L-3"), "L-4": ln("L-4")}
    b_old, b_new = {"L-3": {"side": "AT_LEAST", "value": 0.1}}, {"L-3": {"side": "AT_MOST", "value": 0.2}}
    pend = {"L-4": "PKG-9"}
    assert R.restate_class("L-1", old, new, b_old, b_new, pend)[0] == R.HOST_CHANGED
    assert R.restate_class("L-2", old, new, b_old, b_new, pend)[0] == R698.MAPPED
    assert R.restate_class("L-3", old, new, b_old, b_new, pend)[0] == R.HOST_CHANGED
    assert R.restate_class("L-4", old, new, b_old, b_new, pend) == (R.PENDING, "PKG-9 changes L-4")
    assert R.restate_class("L-5", old, new, b_old, b_new, pend)[0] == R698.STALE
    extra = dict(new["L-2"], unbound_records=["x"])          # a field outside the state key does not move a host
    assert R.restate_class("L-2", old, dict(new, **{"L-2": extra}), b_old, b_new, pend)[0] == R698.MAPPED


# ------------------------------------------------------------------ rule 8: package size
def test_package_size():
    a = R.after(R705.BOUND, lo=1.0, hi=2.0)
    rows = [dict(_row("P1", "a", "L-1", a), live=R.LIVE),
            dict(_row("P1", "b", "L-2", a, R.BESIDE), live=R.LIVE),
            dict(_row("P1", "c", "L-3", a, R.TEXT), live=R.LIVE),
            dict(_row("P1", "d", "L-1", a, R.TEXT), live=R.LIVE),              # L-1 already changed: not text-only
            dict(_row("P2", "e", "L-4", a), live=R.DUPLICATE),
            dict(_row("P2", "f", "L-5", a), live=R.SUPERSEDED),
            dict(_row("P1", "g", None, a, R.ADD), new_line_key="NEW-1", live=R.LIVE),
            dict(_row("P1", "h", "L-6", a, R.KEEP), live=R.STATEMENT)]
    s = R.package_size(rows)
    assert (s["changed"], s["text_only"], s["added"]) == (2, 1, 1)
    assert s["changed_ids"] == ["L-1", "L-2"] and s["text_ids"] == ["L-3"] and s["added_keys"] == ["NEW-1"]
