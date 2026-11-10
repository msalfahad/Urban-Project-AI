"""T-683 R-T683-1 (stale census class), R-T683-2 (scope bridge), R-T683-3 (reference arithmetic). Villa V683 is
hand-made (not the development villa); the last tests rebuild the development-villa statement on V3.0.66 from committed
files only and check it against the line index and the master census to the last digit."""
from __future__ import annotations

import json
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t679"))
sys.path.insert(0, str(ROOT / "research" / "agents_t683"))
import t679_rules as R  # noqa: E402
import t683_rules as S  # noqa: E402

FAMS = [{"code": "F-LIN", "item_codes": ["STR.CONC.LINTEL"]},
        {"code": "F-COL", "item_codes": ["STR.CONC.COLUMN", "STR.CONC.NECK", "STR.CONC.LIFT"]}]


def ln(lid, code, cls, net=None, lo=None, hi=None, el=None):
    return {"line_id": lid, "item_code": code, "class": cls, "measured_net": net, "held_low": lo, "held_high": hi,
            "unit": "m3", "binding": None, "element_id": el or lid}


# V683 by hand. Lintel L1 over a 1.00 m opening, section 0.20 x 0.20: low (1.00 + 2 x 0.40) x 0.04 = 0.072, high to the
# drawn jamb ceilings 1.00 + 0.50 + 0.60 = 2.10 x 0.04 = 0.084; census V1.0.1 said MEASURABLE NOW (blank), package P
# (base V1.0.2) wired it. Lintel L2 over a 0.80 m opening: blank, OPEN BOUND (host wall held), unwired. Stair-like line
# L3: package wired a floor beside (LOWER_ONLY, at least 0.3) and left it blank. Line L4 added by the package
# (pier remainder 0.04 x (0.85 - 0.80) = 0.002).
def villa():
    lines = {"L1": ln("L1", "STR.CONC.LINTEL", "HELD", lo=0.072, hi=0.084),
             "L2": ln("L2", "STR.CONC.LINTEL", "HELD"),
             "L3": ln("L3", "STR.CONC.LINTEL", "HELD"),
             "L4": ln("L4", "STR.CONC.LINTEL", "HELD", lo=0.0, hi=0.002)}
    causes = {"L1": {"cause_class": "MEASURABLE NOW", "named": "wire the bound", "source": "C census"},
              "L2": {"cause_class": "OPEN BOUND", "named": "host wall held", "source": "C census"},
              "L3": {"cause_class": "MEASURABLE NOW", "named": "split steps", "source": "C census"}}
    cver = {"L1": "V1.0.1", "L2": "V1.0.1", "L3": "V1.0.1"}
    pk = [{"task": "P", "base_version": "V1.0.2", "rows": [
        {"line_id": "L1", "action": "BOUND", "after": {"low": 0.072, "high": 0.084}},
        {"line_id": "L3", "action": "LOWER_ONLY", "after": {"low": None, "high": None},
         "beside": {"kind": "AT_LEAST_M3", "value": 0.3, "basis": "steps"}},
        {"line_id": "L4", "action": "ADD_SHARED", "after": {"low": 0.0, "high": 0.002}}]}]
    rs = {k: {"cause_class": "DESIGNER ITEM", "named": f"{k} residual", "source": "V683 hand"} for k in ("L1", "L3", "L4")}
    return lines, causes, cver, pk, rs


def test_restate_normal_and_totals():
    lines, causes, cver, pk, rs = villa()
    cz, rows, floors = S.restate(causes, cver, lines, pk, rs)
    assert {r["line_id"] for r in rows} == {"L1", "L3", "L4"}
    assert cz["L1"]["cause_class"] == "DESIGNER ITEM" and cz["L2"]["cause_class"] == "OPEN BOUND"
    assert floors == [{"line_id": "L3", "at_least": "0.3", "source": "P LOWER_ONLY", "basis": "steps"}]
    agg = R.aggregate(list(lines.values()), FAMS, cz, prefix="STR.CONC", unit="m3")
    t = R.scope_view(agg["total"])
    # bounded L1 + L4 = 0.072 .. 0.086; blank L2, L3 (never 0); the floor 0.3 is NOT in the low
    assert t["held_bounded"]["low"] == "0.072" and t["held_bounded"]["high"] == "0.086"
    assert t["held_blank"]["lines"] == 2 and t["engine_range"] == ["0.072", R.OPEN]
    assert t["held_bounded"]["by_cause"]["MEASURABLE NOW"] == 0


def test_stale_without_restatement_refused():
    lines, causes, cver, pk, rs = villa()
    del rs["L1"]
    with pytest.raises(R.Refused, match=r"R-T683-1 \(a\).*L1"):
        S.restate(causes, cver, lines, pk, rs)


def test_added_line_needs_restatement():
    lines, causes, cver, pk, rs = villa()
    del rs["L4"]
    with pytest.raises(R.Refused, match="L4"):
        S.restate(causes, cver, lines, pk, rs)


def test_restating_unwired_line_refused():
    lines, causes, cver, pk, rs = villa()
    rs["L2"] = {"cause_class": "DESIGNER ITEM", "named": "x", "source": "y"}
    with pytest.raises(R.Refused, match="no package wired it"):
        S.restate(causes, cver, lines, pk, rs)


def test_restating_to_measurable_now_refused():
    lines, causes, cver, pk, rs = villa()
    rs["L1"]["cause_class"] = "MEASURABLE NOW"
    with pytest.raises(R.Refused, match="residual cause"):
        S.restate(causes, cver, lines, pk, rs)


def test_index_not_package_after_refused():
    lines, causes, cver, pk, rs = villa()
    lines["L1"]["held_high"] = 0.085  # candidate not built from that package
    with pytest.raises(R.Refused, match=r"\(c\).*L1"):
        S.restate(causes, cver, lines, pk, rs)


def test_lower_only_must_stay_blank():
    lines, causes, cver, pk, rs = villa()
    lines["L3"]["held_low"], lines["L3"]["held_high"] = 0.3, 0.5  # a floor turned into a bound: refused
    with pytest.raises(R.Refused, match="LOWER_ONLY must leave the index blank"):
        S.restate(causes, cver, lines, pk, rs)


def test_census_newer_than_package_not_stale():
    lines, causes, cver, pk, rs = villa()
    cver["L1"] = "V1.0.3"  # a census that read the wired candidate: its class stands (a re-census, not stale)
    cver["L3"] = "V1.0.3"
    for k in ("L1", "L3"):
        del rs[k]
    cz, rows, _ = S.restate(causes, cver, lines, pk, rs)
    assert [r["line_id"] for r in rows] == ["L4"] and cz["L1"]["cause_class"] == "MEASURABLE NOW"


def test_package_order_invariant():
    lines, causes, cver, pk, rs = villa()
    early = {"task": "P0", "base_version": "V1.0.0", "rows": [{"line_id": "L1", "action": "BOUND",
                                                               "after": {"low": 0.01, "high": 0.02}}]}
    a = S.restate(causes, cver, lines, pk + [early], rs)
    b = S.restate(causes, cver, lines, [early] + pk, rs)
    assert a == b  # the latest package (by base version) governs, not the list order


# ------------------------------------------------------------------------------------------------ R-T683-2
def bridge_lines():
    # cover 3.40 = walls 1.50 + necks 0.40 + columns 1.50. Pit walls HELD blank; tie beam in the same item code; column
    # C1 0.20 x 0.50 x 3.00 = 0.30 released x 5 = 1.50; neck N1 0.40 released.
    return [ln("W", "STR.CONC.LIFT", "HELD", el="LIFT_PIT:WALLS"), ln("T", "STR.CONC.LIFT", "HELD", el="LIFT_TIE"),
            ln("N1", "STR.CONC.NECK", "RELEASED", 0.4)] + [ln(f"C{i}", "STR.CONC.COLUMN", "RELEASED", 0.3)
                                                           for i in range(5)]


COMP = [{"name": "walls", "reference": "1.50", "engine": {"item_codes": ["STR.CONC.LIFT"],
                                                          "element_ids": ["LIFT_PIT:WALLS"]}},
        {"name": "necks", "reference": "0.40", "engine": {"item_codes": ["STR.CONC.NECK"], "element_ids": None}},
        {"name": "columns", "reference": "1.50", "engine": {"item_codes": ["STR.CONC.COLUMN"], "element_ids": None}}]


def test_bridge_normal():
    b = S.bridge("K", "3.40", COMP, bridge_lines())
    rows = {r["component"]: r for r in b["components"]}
    assert rows["walls"]["status"] == "HELD inside: not agreement" and rows["walls"]["pct_of_reference"] is None
    assert rows["columns"]["pct_of_reference"] == "0.00" and rows["columns"]["status"] == "RELEASED only"
    nc = S.not_comparable(bridge_lines(), ["STR.CONC.NECK", "STR.CONC.COLUMN"], b, COMP)
    assert [x["line_id"] for x in nc] == ["T"]  # the tie beam is never folded into the walls


def test_bridge_held_equal_reference_is_not_agreement():
    lines = bridge_lines() + [ln("N2", "STR.CONC.NECK", "HELD")]
    b = S.bridge("K", "3.40", COMP, lines)
    necks = next(r for r in b["components"] if r["component"] == "necks")
    assert necks["difference_ref_minus_released"] == "0.00"  # ref = released, but a HELD line is inside
    assert necks["pct_of_reference"] is None and necks["status"].startswith("HELD")


def test_bridge_components_must_readd():
    with pytest.raises(R.Refused, match="re-add"):
        S.bridge("K", "3.41", COMP, bridge_lines())


def test_bridge_no_engine_line_and_double_claim():
    comp = COMP + [{"name": "ghost", "reference": "0", "engine": {"item_codes": ["STR.CONC.NONE"]}}]
    b = S.bridge("K", "3.40", comp, bridge_lines())
    assert b["components"][-1]["status"] == "NO_ENGINE_LINE"
    twice = COMP[:2] + [{"name": "columns", "reference": "1.50",
                         "engine": {"item_codes": ["STR.CONC.COLUMN", "STR.CONC.NECK"], "element_ids": None}}]
    with pytest.raises(R.Refused, match="answers necks and columns"):
        S.bridge("K", "3.40", twice, bridge_lines())


# ------------------------------------------------------------------------------------------------ R-T683-3
def sheet(sub_formula="=SUM(I7:I7)", cover="=I4+I10"):
    # col I = 9, col E = 5. Section 1: rows 2, 3 items; row 4 sub-total. Section 2 (page break): row 6 first item
    # 0.2 x 0.4 x 1.6 = 0.128, row 7 item 1.0 (copy of E7), row 8 carry-forward SUM(I6:I7), row 9 carry-before =I8,
    # row 10 the sub-total; row 12 the cover.
    cells = {(2, 9): 2.0, (3, 9): 0.5, (4, 9): "=SUM(I2:I3)", (6, 9): "=E6", (6, 5): "=B6*C6*D6", (7, 9): "=E7",
             (7, 5): 1.0, (8, 9): "=SUM(I6:I7)", (9, 9): "=I8", (10, 9): sub_formula, (12, 9): cover}
    reach_val = {"=SUM(I7:I7)": 1.0, "=SUM(I9:I9)": 1.128}[sub_formula]
    cov = 2.5 + reach_val if cover == "=I4+I10" else 2.5 * 2 + reach_val
    values = {(2, 9): 2.0, (3, 9): 0.5, (4, 9): 2.5, (6, 9): 0.128, (6, 5): 0.128, (7, 9): 1.0, (7, 5): 1.0,
              (8, 9): 1.128, (9, 9): 1.128, (10, 9): reach_val, (12, 9): cov}
    return cells, values


def test_omitted_first_row_found():
    cells, values = sheet()
    f = S.audit_cover(cells, values, (12, 9), 9)
    assert f == [{"kind": "OMITTED_ROW", "row": 6, "value": 0.128}]
    a = S.arithmetic(values[(12, 9)], S.item_values(cells, values, (12, 9), 9), f)
    assert a["cover_minus_rows"] == "-0.128000" and a["row_sum"] == "3.628000"


def test_carry_chain_reaches_every_row_once():
    cells, values = sheet("=SUM(I9:I9)")  # sub-total through the carry-before cell: no slip
    assert S.audit_cover(cells, values, (12, 9), 9) == []


def test_double_row_found():
    cells, values = sheet(cover="=I4+I4+I10")
    f = S.audit_cover(cells, values, (12, 9), 9)
    assert {x["row"] for x in f if x["kind"] == "DOUBLE_ROW"} == {2, 3}


def test_unexplained_residual_refused():
    cells, values = sheet()
    with pytest.raises(R.Refused, match="not explained"):
        S.arithmetic(3.5, S.item_values(cells, values, (12, 9), 9), [])


# ------------------------------------------------------------------------------------------------ development villa
@pytest.fixture(scope="module")
def st():
    import t683_alsenan as T
    return T, T.build()


def test_committed_outputs_reproduce(st):
    T, s = st
    import t679_alsenan as A
    assert T.OUT_JSON.read_text(encoding="utf-8") == A.dumps(s)
    assert T.OUT_MD.read_text(encoding="utf-8") == T.md(s)


def test_totals_equal_index_to_last_digit(st):
    T, s = st
    idx = json.loads((ROOT / T.INDEX).read_text(encoding="utf-8"))
    rel, lo, hi, nb = X(0), X(0), X(0), 0
    for l_ in idx["lines"]:
        if not l_["item_code"].startswith("STR.CONC"):
            continue
        if l_["class"] == "RELEASED":
            rel += X(repr(l_["measured_net"]))
        elif l_["class"] == "HELD" and l_["held_low"] is not None:
            lo += X(repr(l_["held_low"]))
            hi += X(repr(l_["held_high"]))
        elif l_["class"] == "HELD":
            nb += 1
    t = s["trade_total"]
    assert X(t["released"]["m3"]) == rel == X("291.476251")
    assert (X(t["held_bounded"]["low"]), X(t["held_bounded"]["high"])) == (lo, hi) == (X("42.014281"),
                                                                                     X("66.193191"))
    assert t["held_blank"]["lines"] == nb == 89 and t["lines"] == 597
    assert s["candidate"]["master_census_agrees"] == 14


def test_every_held_line_has_a_current_cause(st):
    T, s = st
    assert len(s["held_lines"]) == 190
    assert all(h["cause_class"] in R.CAUSE_CLASSES for h in s["held_lines"])
    wired = {r["line_id"] for _, rel in T.PACKAGES for r in json.loads((ROOT / rel).read_text())["rows"]}
    assert not [h for h in s["held_lines"] if h["cause_class"] == "MEASURABLE NOW" and h["line_id"] in wired]
    assert len(s["stale_classes_restated"]) == 19 and len(s["measurable_now_still_held"]) == 11


def test_findings_closed(st):
    _, s = st
    ra = s["reference_apart"]
    assert ra["beam_arithmetic"]["cover_minus_rows"] == "-0.128000"
    assert ra["beam_arithmetic"]["his_row_sum"] == "66.093875"
    assert ra["column_bridge"]["reference"] == "39.7515"
    assert [x["element_id"] for x in ra["column_bridge_not_comparable"]] == ["LIFT_TIE_BEAM:GF"]
    assert {r["line_id"] for r in s["f_t679_1_census_rows"]} == {"L-893c3db13b14dc38625e", "L-bef35462630d4b76596f"}
    assert all(r["pct_of_reference"] is None for r in ra["column_bridge"]["components"])
