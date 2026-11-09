"""T-577 marble / stone thresholds, sills, lift and entrance stone reconciliation (R-T577-1): a non-Alsenan hand
fixture, adverse cases, and the development-villa build pinned (byte-identical rebuild, closures, units)."""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t577"
sys.path.insert(0, str(HERE))
R = importlib.import_module("t577_rules")
_spec = importlib.util.spec_from_file_location("t577_alsenan", HERE / "t577_alsenan.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

D = Decimal


# ---- hand fixture (not Alsenan): 3 doors 0.90 m in 0.20 m walls; 2 windows 1.20 m with 0.05 printed returns ---------
def _doors():
    return [("D1", "GF", R.threshold("0.90", "0.20")), ("D2", "GF", R.threshold("0.90", "0.20")),
            ("D3", "1F", R.threshold("0.90", "0.20"))]


def test_fixture_three_door_thresholds():
    assert R.threshold("0.90", "0.20") == (D("0.90"), D("0.1800"), 1)
    lm, m2, nr = R.totals(_doors())
    assert (lm, m2, nr) == (D("2.70"), D("0.5400"), 3)


def test_fixture_two_window_sills_with_printed_returns():
    s = R.sill("1.20", "0.10", [("0.05", True), ("0.05", True)])
    assert s[0] == D("1.30") and s[1] == D("0.1300") and s[2] == 1
    lm, m2, nr = R.totals([("W1", "GF", s), ("W2", "GF", s)])
    assert (lm, nr) == (D("2.60"), 2) and m2 == D("0.2600")


def test_fixture_in_millimetres():
    assert R.threshold("900", "200", unit="mm") == (D("0.900"), D("0.180000"), 1)
    assert R.sill("1200", "100", [("50", True), ("50", True)], unit="mm")[0] == D("1.300")


@pytest.mark.parametrize("deg", [0, 37, 90, 180, 211])
@pytest.mark.parametrize("mirror", [False, True])
def test_fixture_jamb_width_rotation_and_mirror(deg, mirror):
    a = math.radians(deg)
    p, q = (0.0, 0.0), (0.90, 0.0)
    if mirror:
        q = (-q[0], q[1])
    rot = lambda x: (x[0] * math.cos(a) - x[1] * math.sin(a) + 5.0, x[0] * math.sin(a) + x[1] * math.cos(a) - 3.0)  # noqa
    w = R.jamb_width(rot(p), rot(q))
    assert w == D("0.900000")
    assert R.threshold(w, "0.20")[1] == D("0.18000000")


def test_fixture_reconcile_closes_and_pct():
    pieces = {"D1": {"unit": "lm", "value": D("0.90"), "status": "DRAWING-CONFIRMED"},
              "D2": {"unit": "lm", "value": D("0.90"), "status": "DRAWING-CONFIRMED"},
              "D3": {"unit": "lm", "value": D("0.90"), "status": "DRAWING-CONFIRMED"}}
    cells = {"X.C1": {"label": "lm", "value": D("2.80"), "class": "LENGTH"}}
    g = [{"id": "doors", "pieces": ["D1", "D2", "D3"], "cells": ["X.C1"],
          "causes": [{"label": "his typed 2.80 vs 3 x 0.90", "amount": D("-0.10"), "verdict": "ENGINE_RIGHT",
                      "kind": "MEASURE", "source": "fixture"}]}]
    t = R.reconcile("lm", g, pieces, cells)
    assert t["groups"][0]["gap"] == D("-0.10") and t["groups"][0]["pct"] == D("-3.57")


# ---- adverse --------------------------------------------------------------------------------------------------------
def test_adverse_m2_row_compared_as_lm_refused():
    with pytest.raises(R.RuleError, match="R-T546-1"):
        R.his_cell("lm", "m2", "7.70")
    cells = {"X.H1": {"label": "m2", "value": D("7.70"), "class": "LENGTH_IN_AREA_COLUMN"}}
    with pytest.raises(R.RuleError, match="refused"):
        R.reconcile("lm", [{"id": "g", "pieces": [], "cells": ["X.H1"], "causes": []}], {}, cells)


def test_adverse_one_opening_on_two_plans_counted_twice_refused():
    with pytest.raises(R.RuleError, match="read twice"):
        R.totals(_doors() + [("D2", "section A-A", R.threshold("0.90", "0.20"))])


def test_length_in_area_column_classified_and_never_read_as_lm():
    assert R.classify_cell("m2", count="1", length="1.30", value="1.30") == "LENGTH_IN_AREA_COLUMN"
    assert R.classify_cell("m2", count="1", length="0", area="5.10", value="5.10") == "AREA"
    with pytest.raises(R.RuleError, match="not established"):
        R.classify_cell("m2", count="1", length="1.30", value="2.00")
    with pytest.raises(R.RuleError, match="not established"):
        R.classify_cell("sqft", value="1")
    assert R.length_of_row("6", "nr", "1.20", "lm") == D("7.20")
    with pytest.raises(R.RuleError):
        R.length_of_row("6", "nr", "7.20", "m2")


def test_adverse_unprinted_sill_return_refused():
    with pytest.raises(R.RuleError, match="not printed"):
        R.sill("1.20", "0.10", [("0.05", False)])


def test_adverse_missing_width_never_zero():
    with pytest.raises(R.RuleError, match="never 0"):
        R.threshold(None, "0.20")
    with pytest.raises(R.RuleError, match="HELD"):
        R.threshold("0", "0.20")
    with pytest.raises(R.RuleError, match="unknown"):
        R.threshold("0.90", "0.20", unit="ft")


def test_adverse_held_with_value_verified_and_unnamed_residual_refused():
    cells = {}
    base = {"id": "g", "pieces": ["P"], "cells": [], "causes": []}
    with pytest.raises(R.RuleError, match="with a value"):
        R.reconcile("m2", [base], {"P": {"unit": "m2", "value": D("1"), "status": "HELD"}}, cells)
    with pytest.raises(R.RuleError, match="Checker"):
        R.reconcile("m2", [base], {"P": {"unit": "m2", "value": D("1"), "status": "VERIFIED"}}, cells)
    with pytest.raises(R.RuleError, match="never becomes 0"):
        R.reconcile("m2", [base], {"P": {"unit": "m2", "value": None, "status": "DRAWING-CONFIRMED"}}, cells)
    with pytest.raises(R.RuleError, match="close exactly"):
        R.reconcile("m2", [base], {"P": {"unit": "m2", "value": D("1"), "status": "DRAWING-CONFIRMED"}}, cells)
    with pytest.raises(R.RuleError, match="unnamed"):
        R.reconcile("m2", [{**base, "causes": [{"label": " ", "amount": D("1"), "verdict": "UNRESOLVED",
                                                 "kind": "MEASURE", "source": "x"}]}],
                    {"P": {"unit": "m2", "value": D("1"), "status": "DRAWING-CONFIRMED"}}, cells)
    with pytest.raises(R.RuleError, match="amount must be 0"):
        R.reconcile("m2", [{**base, "causes": [{"label": "held", "amount": D("1"), "verdict": "HELD",
                                                 "kind": "HELD", "bound": (D(0), None), "source": "x"}]}],
                    {"P": {"unit": "m2", "value": D("1"), "status": "DRAWING-CONFIRMED"}}, cells)


def test_adverse_piece_in_two_groups_or_unused_refused():
    pieces = {"P": {"unit": "nr", "value": 1, "status": "DRAWING-CONFIRMED"}}
    c = [{"label": "x", "amount": D(1), "verdict": "ENGINE_RIGHT", "kind": "SCOPE", "source": "x"}]
    with pytest.raises(R.RuleError, match="two groups"):
        R.reconcile("nr", [{"id": "a", "pieces": ["P"], "cells": [], "causes": c},
                           {"id": "b", "pieces": ["P"], "cells": [], "causes": c}], pieces, {})
    with pytest.raises(R.RuleError, match="used once"):
        R.reconcile("nr", [], pieces, {})
    with pytest.raises(R.RuleError, match="inside the m2 table"):
        R.reconcile("m2", [], pieces, {})


def test_partition_unnamed_remainder_refused():
    assert R.partition("10", [("a", "4"), ("b", "6")]) == D("10")
    with pytest.raises(R.RuleError, match="unnamed remainder"):
        R.partition("10", [("a", "4")])


# ---- development villa (pinned) -------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def built():
    return A.build()


def test_alsenan_rebuild_byte_identical(built):
    assert (HERE / "out" / "T577_MARBLE_RECONCILE.json").read_text(encoding="utf-8") == A.dump(built)


def test_alsenan_totals_close_per_unit(built):
    for unit, t in built["tables"].items():
        gs = t["groups"]
        assert sum(D(g["ours"]) for g in gs) == D(t["totals"]["ours"])
        assert sum(D(g["his"]) for g in gs) == D(t["totals"]["his"])
        for g in gs:
            assert sum(D(c["amount"]) for c in g["causes"]) == D(g["gap"])
        assert t["totals"]["pct"] is None
    m2, lm, nr = (built["tables"][u]["totals"] for u in ("m2", "lm", "nr"))
    assert (m2["ours"], m2["his"]) == ("18.0382", "26.8")
    assert (lm["ours"], lm["his"]) == ("56.83", "21.7")
    assert (nr["ours"], nr["his"]) == ("67", "11")


def test_alsenan_his_marble_total_partition(built):
    p = built["tables"]["m2"]["his_marble_total"]
    assert p["total"] == "295.44"
    assert sum(D(v) for _, v in p["parts"]) == D("295.44")
    assert (p["area_shaped"], p["length_shaped"]) == ("164.54", "130.9")
    assert sum(D(v) for _, v in built["tables"]["lm"]["his_marble_total"]["parts"]) == D("29.87")
    assert sum(D(v) for _, v in built["tables"]["nr"]["his_marble_total"]["parts"]) == D("96")


def test_alsenan_key_groups(built):
    g = {(u, x["id"]): x for u, t in built["tables"].items() for x in t["groups"]}
    assert (g["m2", "WET"]["ours"], len(g["m2", "WET"]["pieces"])) == ("1.82", 14)
    assert g["m2", "EXT"]["held_bound"] == ["1.31", "1.31"] and g["m2", "EXT"]["his"] == "7.7"
    assert [c["kind"] for c in g["m2", "EXT"]["causes"]] == ["UNIT", "HELD"]
    assert g["lm", "EXT"]["held_bound"] == ["6.8", "6.8"] and g["lm", "EXT"]["his"] == "7.7"
    assert g["nr", "EXT"]["gap"] == "0" and g["nr", "EXT"]["pct"] == "0.00"
    assert g["m2", "E1_LANDING"]["gap"] == "0.0794" and g["m2", "E1_LANDING"]["pct"] == "1.56"
    assert g["lm", "E1_STEPS"]["his"] == "14.0" and g["lm", "E1_STEPS"]["ours"] == "0"
    assert g["m2", "LIFT"]["held_bound"] == ["2.75", "13.98"]
    assert g["m2", "SILL"]["ours"] == "2.5614" and g["m2", "SILL"]["held_bound"] == ["0", None]


def test_alsenan_held_pieces_never_zero(built):
    for pid, p in built["pieces"].items():
        for u in ("m2", "lm", "nr"):
            if p[u] and p[u]["status"] == "HELD":
                assert p[u]["value"] is None and "bound" in p[u]


def test_alsenan_codes_closed(built):
    c = built["code_closure"]
    assert c["FIN.MARBLE.THRESHOLD"]["used"] == c["FIN.MARBLE.THRESHOLD"]["lines"] == 14
    assert c["FIN.MARBLE.LIFT_THRESHOLD"]["released_used"] == {"lm": "3.0", "m2": "1.5"}
    assert (c["ARCH.THRESHOLD"]["used"], c["ARCH.THRESHOLD"]["not_this_element"]) == (8, 16)
    assert (c["ARCH.WINDOW_REVEAL"]["used"], c["ARCH.WINDOW_REVEAL"]["not_this_element"]) == (30, 32)


def test_alsenan_edited_input_stops_the_build(monkeypatch):
    monkeypatch.setitem(A.PINS, A.LEDGER, "0" * 16)
    with pytest.raises(R.RuleError, match="changed"):
        A.build()


def test_alsenan_output_has_no_workbook_text():
    s = (HERE / "out" / "T577_MARBLE_RECONCILE.json").read_text(encoding="utf-8")
    assert not any("؀" <= ch <= "ۿ" for ch in s)
    json.loads(s)
