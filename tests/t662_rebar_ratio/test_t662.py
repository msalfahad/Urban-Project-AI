"""T-662: rebar by owner-approved ratio (R-T662-1). Synthetic villa "V662" (not the training villa) by hand with adverse
cases (type with no counted member, blank concrete, member with partial detail, HELD concrete in the calibration, a
missing m3, a concrete line in the wrong unit, high below low); then the development villa from repository files only:
every HELD STR.REBAR line once, no member both ways, released detailed subtotal unchanged, outputs current."""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t662"))
import t662_rules as R  # noqa: E402
import t662_alsenan as A  # noqa: E402

D = Decimal


def rel(v, lid="x", unit="kg"):
    return {"line_id": lid, "class": "RELEASED", "measured_net": v, "held_low": None, "held_high": None, "unit": unit}


def bnd(lo, hi, lid="x", unit="kg"):
    return {"line_id": lid, "class": "HELD", "measured_net": None, "held_low": lo, "held_high": hi, "unit": unit}


def blank(lid="x", unit="kg"):
    return {"line_id": lid, "class": "HELD", "measured_net": None, "held_low": None, "held_high": None, "unit": unit}


# ---- villa "V662" (hand) ----------------------------------------------------------------------------------------------
# BEAM calibration:
#   B1 FULL    bars 30 + 20 = 50 kg released, concrete 0.25 m3 released            -> 200 kg/m3
#   B2 BOUNDED bars 40 released + 10 .. 20 bounded = 50 .. 60 kg, concrete 0.50 m3  -> 100 .. 120 kg/m3
#   aggregate: 100 .. 110 kg / 0.75 m3 = 133.333333 .. 146.666667 kg/m3 (NOT the mean of 200 and 100)
#   B9 BOUNDED on HELD concrete 0.1 .. 0.2 m3: never calibrates
# Ratio members:
#   B3 NONE, concrete 0.30 released: 0.30 x 133.333333 x 1.03 = 41.200000 .. 0.30 x 146.666667 x 1.05 = 46.200000 kg
#   B4 NONE, concrete HELD 0.20 .. 0.40: 0.20 x 133.333333 x 1.03 = 27.466667 .. 0.40 x 146.666667 x 1.05 = 61.600000
#   B5 NONE, concrete HELD blank -> HELD blank by name
#   B6 PARTIAL (15 kg released + a blank group) -> no ratio (second way), detail kept
# COLUMN C1 NONE on 0.5 m3 released, no counted column -> HELD, no borrowed beam ratio.
def v662():
    rows = []

    def row(member, typ, lines, conc):
        st = R.member_state(lines)
        cs = R.concrete_state(conc)
        r = {"member": member, "type": typ, "state": st, "concrete_state": cs[0],
             "m3_low": None if cs[1] is None else str(cs[1]), "_cs": cs}
        if st in ("FULL", "BOUNDED"):
            lo, hi = R.detailed_kg(lines)
            r["detailed_kg"] = [str(lo), str(hi)]
        rows.append(r)
    row("B1", "BEAM", [rel(30), rel(20)], [rel("0.25", unit="m3")])
    row("B2", "BEAM", [rel(40), bnd(10, 20)], [rel("0.50", unit="m3")])
    row("B9", "BEAM", [rel(40)], [bnd("0.1", "0.2", unit="m3")])
    row("B3", "BEAM", [blank(), blank()], [rel("0.30", unit="m3")])
    row("B4", "BEAM", [blank()], [bnd("0.20", "0.40", unit="m3")])
    row("B5", "BEAM", [blank()], [blank(unit="m3")])
    row("B6", "BEAM", [rel(15), blank()], [rel("0.30", unit="m3")])
    row("C1", "COLUMN", [blank()], [rel("0.5", unit="m3")])
    cal = {t: R.calibrate(R.calibration_set(rows, t)) for t in ("BEAM", "COLUMN")}
    routed = {r["member"]: R.assign(r["state"], cal[r["type"]], r["_cs"]) for r in rows}
    return rows, cal, routed


def test_v662_calibration_by_hand():
    rows, cal, _ = v662()
    c = cal["BEAM"]
    assert c["n"] == 2 and [m["member"] for m in c["members"]] == ["B1", "B2"]       # B9 on HELD concrete excluded
    assert D(c["m3"]) == D("0.75") and D(c["kg_low"]) == 100 and D(c["kg_high"]) == 110
    assert c["ratio_low"] == "133.333333" and c["ratio_high"] == "146.666667"
    assert c["spread_low"] == ["100.000000", "200.000000"] and c["outliers"] == []
    assert cal["COLUMN"] is None


def test_v662_ratio_members_by_hand():
    _, _, routed = v662()
    assert routed["B3"]["route"] == "RATIO" and routed["B3"]["status"] == R.LABEL
    assert (routed["B3"]["kg_low"], routed["B3"]["kg_high"]) == ("41.200000", "46.200000")
    assert (routed["B4"]["kg_low"], routed["B4"]["kg_high"]) == ("27.466667", "61.600000")
    assert routed["B4"]["concrete_state"] == "HELD_BOUNDED"


def test_v662_adverse_holds_never_zero():
    _, _, routed = v662()
    assert routed["B5"]["route"] == "RATIO_HELD" and "HELD blank" in routed["B5"]["cause"]
    assert "kg_low" not in routed["B5"]
    assert routed["B6"]["route"] == "PARTIAL_HELD" and "second way" in routed["B6"]["status"]
    assert routed["C1"]["route"] == "RATIO_HELD" and "no borrowed ratio" in routed["C1"]["cause"]
    assert routed["B1"]["route"] == routed["B2"]["route"] == "DETAILED"


def test_adverse_inputs_refused():
    with pytest.raises(R.RuleError):
        R.calibrate([{"member": "X", "m3": None, "kg_low": 1, "kg_high": 1}])             # missing m3, never 0
    with pytest.raises(R.RuleError):
        R.concrete_state([rel("300", unit="kg")])                                         # a kg line as concrete
    with pytest.raises(R.RuleError):
        R.member_state([rel("0.3", unit="m3")])                                           # an m3 line as bars
    with pytest.raises(R.RuleError):
        R.member_state([bnd(20, 10)])                                                     # high below low
    with pytest.raises(R.RuleError):
        R.detailed_kg([rel(10), blank()])                                                 # detail sum over a blank
    assert R.concrete_state([{**rel("1", unit="m3"), "class": "EXCLUDED"}])[0] == "NOT_BOUND"
    assert R.member_state([rel(5), bnd(1, None) | {"held_high": None}]) == "PARTIAL"     # open-high = partial


def test_lap_range_is_carried_not_picked():
    cal = R.calibrate([{"member": "M", "m3": D("1"), "kg_low": D("100"), "kg_high": D("100")}])
    r = R.ratio_kg(cal, ("RELEASED", D("2"), D("2")))
    assert (r["kg_low"], r["kg_high"]) == ("206.000000", "210.000000")


def test_outlier_named_not_removed():
    cal = R.calibrate([{"member": "A", "m3": D("1"), "kg_low": D("100"), "kg_high": D("100")},
                       {"member": "B", "m3": D("1"), "kg_low": D("100"), "kg_high": D("100")},
                       {"member": "C", "m3": D("0.1"), "kg_low": D("40"), "kg_high": D("40")}])
    assert cal["n"] == 3 and cal["outliers"] == ["C"]                                    # 400 > 2 x 133.3


# ---- development villa (repository files only) ------------------------------------------------------------------------
@pytest.fixture(scope="module")
def built():
    return A.build()


def test_villa_every_held_line_once_and_released_unchanged(built):
    c = built["counts"]
    assert c["held_lines"] == len(built["per_held_line"]) == 1699
    assert len({x["line_id"] for x in built["per_held_line"]}) == 1699
    assert built["subtotals"]["released_detailed_kg"] == "9628.462205"                 # trial BOQ r4 B11 released


def test_villa_no_member_both_ways(built):
    lines = {x["line_id"]: x for x in A.load()["per"]}
    for r in built["members"]:
        if r["route"] == "RATIO":
            assert r["state"] == "NONE"
            assert all(lines[lid]["class"] == "HELD" and lines[lid]["held_low"] is None for lid in r["lines"])
            assert r["concrete_state"] in ("RELEASED", "HELD_BOUNDED")
            assert D(r["kg_low"]) > 0 and D(r["kg_high"]) >= D(r["kg_low"])
        if r["route"] in ("DETAILED", "PARTIAL_HELD"):
            assert "kg_low" not in r


def test_villa_calibration_rechecked(built):
    cal = built["calibration"]
    for t, c in cal.items():
        if c:
            m3 = sum(D(m["m3"]) for m in c["members"])
            lo = sum(D(m["kg_low"]) for m in c["members"])
            assert R.q(lo / m3) == D(c["ratio_low"])
    assert cal["COLUMN"] is None and cal["NECK"] is None and cal["SLAB"] is None    # no counted member: no ratio
    held = [x for x in built["per_held_line"] if x["type"] in ("COLUMN", "NECK", "SLAB")]
    assert held and all(x["member_ratio_kg"] is None for x in held)


def test_outputs_current(built):
    assert json.loads(A.OUT_JSON.read_text("utf-8")) == json.loads(json.dumps(built))
    assert A.OUT_MD.read_text("utf-8") == A.md(built)


@pytest.mark.skipif(os.environ.get("URBAN_T662_WRITE") != "1", reason="writer: URBAN_T662_WRITE=1 only")
def test_write_outputs():
    A.write()
