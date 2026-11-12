"""R-T730-1 on a hand-made villa W730 (not the development villa): rows a merged package wired, a carried conflict
between merged pieces, the capped-blank form, caps (incl. 0), an arris-by-arris restatement, blockers and buildable
hubs, and id resolution that never re-maps a missing id to a neighbour. Every expected figure is written by hand
below; adverse cases cover 0 / negative caps, a form rule on a non-zero low, an unlisted or untrue conflict, a lost /
added / moved / doubled arris, a malformed blocker, absent / short / ambiguous ids and mirror (reversed) input order."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t730"))
import t730_rules as R  # noqa: E402

R723, R705, R698 = R.R723, R.R705, R.R698
E = R.ReadinessError


def ln(lid, code="STR.FORMWORK", cls="HELD", v=None, lo=None, hi=None, unit="m2", el=None):
    return {"line_id": lid, "item_code": code, "element_id": el or f"W730:{lid}", "unit": unit, "class": cls,
            "measured_net": v, "held_low": lo, "held_high": hi}


BLANK = ln("L-bbbb00010000")
BOUNDED = ln("L-bbbb00020000", lo=1.20, hi=1.50)
RELEASED = ln("L-bbbb00030000", cls="RELEASED", v=2.40)
EXCL = ln("L-bbbb00040000", cls="EXCLUDED")
ZERO_RANGE = ln("L-bbbb00050000", code="STR.CONC.GROUND_BEAM", lo=0.0, hi=3.00, unit="m3")
LOW_RANGE = ln("L-bbbb00060000", code="STR.CONC.GROUND_BEAM", lo=0.10, hi=3.00, unit="m3")
TGT = {x["line_id"]: x for x in (BLANK, BOUNDED, RELEASED, EXCL, ZERO_RANGE, LOW_RANGE)}


def one(side, v):
    return R.after(R723.ONE_SIDED, side=side, value=v)


# ------------------------------------------------------------------------------------------------- rule 1 WIRED
def test_wired_one_sided_beside_equal():
    a = one("AT_LEAST", 0.75)
    assert R.wire_action(a, BLANK, {"side": "AT_LEAST", "value": 0.75}, was=R.BESIDE)[0] == R.WIRED


def test_restate_when_beside_differs_even_if_was_beside():
    a = one("AT_LEAST", 0.75)
    assert R.wire_action(a, BLANK, {"side": "AT_LEAST", "value": 0.750001}, was=R.BESIDE)[0] == R.RESTATE_BESIDE


def test_side_must_match_for_wired():
    a = one("AT_LEAST", 0.75)
    assert R.wire_action(a, BLANK, {"side": "AT_MOST", "value": 0.75}, was=R.BESIDE)[0] == R.RESTATE_BESIDE


def test_wired_bound_and_value_from_index():
    assert R.wire_action(R.after(R705.BOUND, lo=1.2, hi=1.5), BOUNDED, was=R.CHANGE)[0] == R.WIRED
    assert R.wire_action(R.after(R705.VALUE, value=2.4), RELEASED, was=R.CHANGE)[0] == R.WIRED
    assert R.wire_action(R.after(R705.BOUND, lo=1.2, hi=1.51), BOUNDED, was=R.CHANGE)[0] == R.CHANGE


def test_wired_excluded():
    assert R.wire_action(R.after(R723.EXCLUDED), EXCL, was=R.CHANGE)[0] == R.WIRED


def test_text_wired_only_with_named_record():
    a = R.after(R705.BLANK, note="named cause")
    assert R.wire_action(a, BLANK, was=R.TEXT, named=True)[0] == R.WIRED
    assert R.wire_action(a, BLANK, was=R.TEXT, named=False)[0] == R.TEXT


def test_keep_and_statement_never_wired():
    a = one("AT_LEAST", 0.75)
    assert R.wire_action(a, BLANK, {"side": "AT_LEAST", "value": 0.75}, was=R.KEEP)[0] == R.KEEP
    assert R.wire_action(R.after(R705.NOPROP), BLANK, was=R.KEEP)[0] == R.KEEP
    assert R.wire_action(R.after(R705.NOPROP), BLANK, was=R.CHANGE)[0] == R.KEEP


def test_wired_one_sided_never_on_a_ranged_line():
    a = one("AT_LEAST", 1.2)
    assert not R.carried(a, BOUNDED, {"side": "AT_LEAST", "value": 1.2}, False)


# ------------------------------------------------------------------------------------------ rule 3 FORM RESTATE
def test_form_restate_with_rule():
    act, why = R.wire_action(one("AT_MOST", 3.0), ZERO_RANGE, form_rule="R-X-3")
    assert act == R.CHANGE and R.FORM_RESTATE in why and "cap 3.0" in why


def test_form_conflict_without_rule():
    assert R.wire_action(one("AT_MOST", 3.0), ZERO_RANGE)[0] == R.FORM_CONFLICT


def test_adverse_form_rule_never_applies_to_a_real_floor():
    # a low of 0.10 is a floor: the range narrows nothing by a cap, rule or no rule
    assert R.wire_action(one("AT_MOST", 3.0), LOW_RANGE, form_rule="R-X-3")[0] == R.FORM_CONFLICT


# --------------------------------------------------------------------------------------------------- rule 4 CAP
def test_cap_forms():
    assert R.cap_after(None)["kind"] == R705.BLANK
    a = R.cap_after(0.873917, note="SEQ")
    assert (a["kind"], a["side"], a["value"]) == (R723.ONE_SIDED, "AT_MOST", 0.873917)
    z = R.cap_after(0.0, note="face 0 .. 0")
    assert z["kind"] == R705.BLANK and z["value"] is None and "CAP_ZERO" in z["note"]


def test_adverse_negative_cap_refused():
    with pytest.raises(E):
        R.cap_after(-0.1)


def test_adverse_one_sided_never_a_range_or_zero():
    with pytest.raises(E):
        R.after(R723.ONE_SIDED, side="AT_MOST", value=1.0, lo=0.0)
    with pytest.raises(E):
        R.after(R723.ONE_SIDED, side="AT_LEAST", value=0)


# ------------------------------------------------------------------------------------------------- rule 7 IDS
def test_resolve_full_and_unique_prefix():
    assert R.resolve("L-bbbb00030000", TGT) == "L-bbbb00030000"
    assert R.resolve("L-bbbb0003", TGT) == "L-bbbb00030000"


def test_adverse_missing_id_never_maps_to_a_neighbour():
    # a neighbour carries the same element id and the next id in sequence: still refused
    tgt = dict(TGT)
    tgt["L-bbbb00070000"] = ln("L-bbbb00070000", el=f"W730:L-bbbb00080000")
    with pytest.raises(E):
        R.resolve("L-bbbb00080000", tgt)
    with pytest.raises(E):
        R.resolve("L-bbbb0008", tgt)


def test_adverse_short_and_ambiguous_ids():
    with pytest.raises(E):
        R.resolve("L-bbbb000", TGT)            # 7 hex digits
    with pytest.raises(E):
        R.resolve("L-bbbb0000", TGT)           # matches nothing ...
    tgt = {"L-cccc00010001": ln("L-cccc00010001"), "L-cccc00010002": ln("L-cccc00010002")}
    with pytest.raises(E):
        R.resolve("L-cccc0001", tgt)           # ... or two lines


# ------------------------------------------------------------------------------------- rule 2 CONFLICT CARRIED
def row(piece, key, host, a, action=R.CHANGE):
    return {"piece": piece, "row": f"{piece}:{key}", "host_line_id": host, "new_line_key": None, "after": a,
            "action": action, "action_reason": "", "blockers": []}


def test_conflict_listed_is_carried_and_blocks():
    h = BLANK["line_id"]
    rs = [row("P1", "a", h, R.after(R705.BOUND, lo=5.5926, hi=7.362)), row("P2", "a", h, R.after(R705.BLANK), R.TEXT)]
    R.resolve_live(rs, ["P1", "P2"], {}, {h: "T-999 (decider)"})
    assert {r["live"] for r in rs} == {R.CONFLICT}
    assert all("CONFLICT T-999 (decider)" in r["blockers"] for r in rs)
    assert R.package_size(rs)["changed"] == 0


def test_adverse_unlisted_conflict_fails():
    h = BLANK["line_id"]
    rs = [row("P1", "a", h, R.after(R705.BOUND, lo=1, hi=2)), row("P2", "a", h, R.after(R705.BLANK), R.TEXT)]
    with pytest.raises(E):
        R.resolve_live(rs, ["P1", "P2"], {}, {})


def test_adverse_listed_line_that_does_not_conflict_fails():
    h = BLANK["line_id"]
    rs = [row("P1", "a", h, R.after(R705.BOUND, lo=1, hi=2)), row("P2", "a", h, R.after(R705.BOUND, lo=1, hi=2))]
    with pytest.raises(E):
        R.resolve_live(rs, ["P1", "P2"], {}, {h: "T-999"})


def test_declared_supersession_still_works_and_mirror_order():
    h = BLANK["line_id"]
    for flip in (False, True):
        rs = [row("P1", "a", h, R.after(R705.BOUND, lo=0.679193, hi=0.854426)),
              row("P2", "a", h, R.after(R705.BOUND, lo=0.679193, hi=0.843465))]
        if flip:
            rs.reverse()
        R.resolve_live(rs, ["P1", "P2"], {("P2", "P1"): {h}}, {})
        live = {r["piece"]: r["live"] for r in rs}
        assert live == {"P1": R.SUPERSEDED, "P2": R.LIVE}


# -------------------------------------------------------------------------------------------- rule 5 ARRIS
def arr(piece, edge, host):
    return {"piece": piece, "row": f"{piece}:{edge}", "element": edge, "host_line_id": host}


def test_arris_supersede_one_to_one_and_mirror():
    e = [arr("A", "1F-01#V06", "L-h1"), arr("A", "GF-02#C1", "L-h2")]
    n = [arr("B", "GF-02#C1", "L-h2"), arr("B", "1F-01#V06", "L-h1")]
    assert R.arris_supersede(e, n) == {"A:1F-01#V06": "B:1F-01#V06", "A:GF-02#C1": "B:GF-02#C1"}
    assert R.arris_supersede(list(reversed(e)), list(reversed(n))) == R.arris_supersede(e, n)


@pytest.mark.parametrize("later", [
    [arr("B", "1F-01#V06", "L-h1")],                                                  # arris lost
    [arr("B", "1F-01#V06", "L-h1"), arr("B", "GF-02#C1", "L-h2"), arr("B", "X#1", "L-h2")],  # arris added
    [arr("B", "1F-01#V06", "L-h1"), arr("B", "GF-02#C1", "L-h1")],                    # arris moved host
    [arr("B", "1F-01#V06", "L-h1"), arr("B", "1F-01#V06", "L-h1"), arr("B", "GF-02#C1", "L-h2")],  # twice
])
def test_adverse_arris_restatement(later):
    e = [arr("A", "1F-01#V06", "L-h1"), arr("A", "GF-02#C1", "L-h2")]
    with pytest.raises(E):
        R.arris_supersede(e, later)


# ------------------------------------------------------------------------------------------- rule 6 BLOCKERS
def test_blockers_kinds():
    assert R.check_blockers([{"row": "x", "blockers": ["WAITS T-732", "PENDING_ON T-717", "RULING ORR-007"]}])
    for bad in (["LATER"], ["WAITS"], ["WAITS  "]):
        with pytest.raises(E):
            R.check_blockers([{"row": "x", "blockers": bad}])


def test_buildable_own_and_earlier_hubs_only():
    rs = [{"row": "a", "live": R.LIVE, "action": R.CHANGE, "blockers": ["PENDING_ON T-717"]},
          {"row": "b", "live": R.LIVE, "action": R.KEEP, "blockers": ["WAITS T-999"]},       # KEEP moves nothing
          {"row": "c", "live": R.SUPERSEDED, "action": R.CHANGE, "blockers": ["WAITS T-999"]}]  # not live
    assert R.buildable(rs, earlier_hubs=["T-717"]) == (True, [])
    ok, open_ = R.buildable(rs, earlier_hubs=[])
    assert not ok and open_ == ["PENDING_ON T-717"]
    rs.append({"row": "d", "live": R.CONFLICT, "action": R.TEXT, "blockers": ["CONFLICT T-732"]})
    assert R.buildable(rs, earlier_hubs=["T-717"])[1] == ["CONFLICT T-732"]


def test_package_size_skips_wired():
    rs = [{"row": "a", "live": R.LIVE, "action": R.WIRED, "host_line_id": "L-1", "new_line_key": None},
          {"row": "b", "live": R.LIVE, "action": R.BESIDE, "host_line_id": "L-2", "new_line_key": None},
          {"row": "c", "live": None, "action": R.TEXT, "host_line_id": "L-3", "new_line_key": None},
          {"row": "d", "live": None, "action": R.ADD, "host_line_id": "L-3", "new_line_key": "K-1"}]
    s = R.package_size(rs)
    assert (s["changed"], s["text_only"], s["added"]) == (1, 1, 1)
