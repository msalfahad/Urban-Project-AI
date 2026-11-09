"""T-588: WIRING MANIFEST V9 + OVERLAY DRY RUN (R-T588-1).

Synthetic villa K588 (not the training villa; hand values): a 5-line index (one owned flight step line 9 x 1.10 =
9.90 lm, its second reading HELD 0 .. 9.90, a blank railing, a dome concrete line, a tread area) and 3 rows (a NEW
entrance step line 3 x 2.40 = 7.20 lm, the second reading to EXCLUDED, the railing to AT_LEAST 0.75 lm) with the
after totals and the edge census computed by hand; adverse: a row on a line another package writes, a HELD row with a
value, VERIFIED on a HELD row, HELD 0 .. 0, an unknown evidence status, an edge claimed twice, a claim on an unknown
edge, t booked as kg. Then the training-villa build (out/WIRING_MANIFEST_V9.json) must be the rebuild and close by
hand on the merged T-578 / T-583 / T-584 figures."""

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t588"))
import manifest_v9 as M          # noqa: E402

OV = M.OV
V = "synthetic verdict line"


def _l(lid, code, el, cls="RELEASED", net=None, unit="lm", lo=None, hi=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "element_id": el, "class": cls, "measured_net": net,
            "held_low": lo, "held_high": hi}


@pytest.fixture
def villa():
    return {l["line_id"]: l for l in [
        _l("L-1", "FIN.STAIR.STEP_LM", "K-STAIR:flight 1", net=9.9),                     # 9 treads x 1.10
        _l("L-2", "FIN.STAIR.STEP_LM", "K-UPPER:flight 1", cls="HELD", lo=0.0, hi=9.9),  # same flight read again
        _l("L-3", "FIN.RAILING", "RAIL:K-R1", cls="HELD"),
        _l("L-4", "STR.CONC.DOME", "K-DOME:SHELL", net=1.2, unit="m3"),
        _l("L-5", "FIN.MARBLE.TREAD", "K-COURT#E-TREADS", net=2.16, unit="m2"),           # 3 x 2.40 x 0.30
    ]}


def _rows(idx):
    P = "K588"
    return [
        M.row(P, "FR-E", "ADD", "NEW:FIN.STAIR.STEP_LM:K-COURT#E-STEPS", None, M.released(7.2), "VERIFIED", V,
              "FIN.STAIR.STEP_LM", "lm", "K-COURT#E-STEPS", beside={"nr": 3}),
        M.row(P, "FR-2ND", "SET", "L-2", OV.state(idx["L-2"]), M.excluded(), "PARTIALLY VERIFIED", V),
        M.row(P, "FR-RAIL", "SET", "L-3", OV.state(idx["L-3"]), M.held(0.75, None), "HELD", V),
    ]


def _edges():
    e = [{"eid": f"A-N{i:02d}", "stair": "K-1", "flight": "A", "kind": "TREAD", "status": "DRAWING-CONFIRMED",
          "in_step_basis": True, "qty_lm": "1.10"} for i in range(1, 10)]
    e.append({"eid": "A-N10", "stair": "K-1", "flight": "A", "kind": "LANDING_EDGE", "status": "DRAWING-CONFIRMED",
              "in_step_basis": False, "qty_lm": "1.10"})
    e += [{"eid": f"E-N{i}", "stair": "K-2", "flight": "E", "kind": "TREAD", "status": "DRAWING-CONFIRMED",
           "in_step_basis": True, "qty_lm": "2.40"} for i in range(1, 4)]
    e.append({"eid": "E-N4", "stair": "K-2", "flight": "E", "kind": "LANDING_EDGE", "status": "DRAWING-CONFIRMED",
              "in_step_basis": False, "qty_lm": "2.40"})
    return e


FLIGHTS = {"L-1": ("K-1", "A"), "L-2": ("K-1", "A")}
E_LINE = {"NEW:FIN.STAIR.STEP_LM:K-COURT#E-STEPS": ("K-2", "E")}


def _census(idx, extra=None):
    f = dict(FLIGHTS, **(extra or {}))
    live = {k for k, l in idx.items() if l["class"] != "EXCLUDED" and l["item_code"] == "FIN.STAIR.STEP_LM"}
    return M.census(_edges(), M.step_claims(_edges(), f, live))


# ---- synthetic: normal ----------------------------------------------------------------------------------------------

def test_fixture_after_values_by_hand(villa):
    before = copy.deepcopy(villa)
    after, rep = OV.apply(villa, [("K588", _rows(villa))])
    assert villa == before                                                   # a COPY is overlaid
    assert [r["status"] for r in rep["rows"]] == ["APPLIED"] * 3
    t = OV.totals(after)
    s = t["FIN.STAIR.STEP_LM|lm"]
    assert Decimal(s["released"]) == Decimal("9.9") + Decimal("7.2") == Decimal("17.1")
    assert s["held_n"] == 0 and s["excluded_n"] == 1 and s["released_n"] == 2
    r = t["FIN.RAILING|lm"]
    assert r["held_low"] == "0.75" and r["held_high_open_n"] == 1 and r["held_high"] == "0"   # open, never 0
    assert after["L-4"] == villa["L-4"] and after["L-5"] == villa["L-5"]    # every other line byte-identical
    assert set(rep["steps"][0]["totals_changed"]) == {"FIN.STAIR.STEP_LM|lm", "FIN.RAILING|lm"}


def test_fixture_edge_census_before_and_after(villa):
    c0 = _census(villa)
    assert sorted(c0["doubles"]) == [f"A-N{i:02d}" for i in range(1, 10)]   # second reading claims the 9 treads
    assert c0["orphans"] == ["E-N1", "E-N2", "E-N3"]                          # entrance treads: no step line
    after, _ = OV.apply(villa, [("K588", _rows(villa))])
    c1 = _census(after, E_LINE)
    assert c1["doubles"] == {} and c1["orphans"] == []
    assert c1["by_stair"]["K-2"] == {"edges": 4, "step_basis": 3, "nosing_line": 1, "held": 0}
    # the platform edge stays a nosing edge, never inside the step line: 3 x 2.40 = 7.20 lm, not 4 x 2.40
    claims = M.step_claims(_edges(), E_LINE, set(E_LINE))
    assert sum(Decimal(e["qty_lm"]) for e in _edges() if e["eid"] in claims[next(iter(E_LINE))]) == Decimal("7.20")


def test_class_map():
    assert M.class_of(M.released(1.0)) == "RELEASED"
    assert M.class_of(M.held()) == "HELD"
    assert M.class_of(M.held(0.5, None)) == "AT_LEAST"
    assert M.class_of(M.held(0.0, 2.0)) == "HELD_RANGE"
    assert M.class_of(M.excluded()) == "EXCLUDED"


def test_t_to_kg_exact():
    assert M.kg("0.290684") == 290.684 and M.kg("0.767783") == 767.783 and M.kg(None) is None


# ---- synthetic: adverse -----------------------------------------------------------------------------------------

def test_row_on_a_line_another_package_writes_refused(villa):
    a = _rows(villa)
    b = [M.row("OTHER", "X", "SET", "L-3", OV.state(villa["L-3"]), M.held(0.5, 1.0), "HELD", V)]
    with pytest.raises(OV.OverlayError, match="R1 TWO_ROWS_ONE_LINE"):
        M.validate_rows(a + b)
    with pytest.raises(OV.OverlayError, match="R1"):
        OV.apply(villa, [("K588", a), ("OTHER", b)])


def test_held_row_with_a_value_refused(villa):
    bad = {"class": "HELD", "measured_net": 7.2, "held_low": None, "held_high": None}
    with pytest.raises(M.ManifestError, match="HELD_AS_VALUE"):
        M.row("K", "X", "SET", "L-3", OV.state(villa["L-3"]), bad, "HELD", V)


def test_verified_on_a_held_row_and_unknown_status_refused(villa):
    with pytest.raises(M.ManifestError, match="labelled VERIFIED"):
        M.row("K", "X", "SET", "L-3", OV.state(villa["L-3"]), M.held(0.75, None), "VERIFIED", V)
    with pytest.raises(M.ManifestError, match="not a WORKFLOW_CONTROLS"):
        M.row("K", "X", "TEXT_ONLY", "L-1", OV.state(villa["L-1"]), None, "PROBABLY", V)


def test_held_zero_zero_refused(villa):
    r = M.row("K", "X", "SET", "L-3", OV.state(villa["L-3"]), M.held(0.0, 0.0), "HELD", V)
    with pytest.raises(OV.OverlayError, match="HELD_AS_0"):
        M.validate_rows([r])


def test_stale_before_is_flagged_not_applied(villa):
    r = M.row("K", "X", "SET", "L-2", M.held(0.0, 9.0), M.excluded(), "PARTIALLY VERIFIED", V)
    after, rep = OV.apply(villa, [("K", [r])])
    assert rep["rows"][0]["status"] == "STALE" and after["L-2"] == villa["L-2"]


def test_edge_claimed_twice_and_unknown_edge():
    claims = {"L-1": ["A-N01"], "L-9": ["A-N01"]}
    assert M.census(_edges(), claims)["doubles"]["A-N01"] == ["L-1", "L-9"]
    with pytest.raises(M.ManifestError, match="not in the census"):
        M.census(_edges(), {"L-1": ["Z-N99"]})


def test_t_as_kg_refused():
    t583 = {"rows": [{"row_id": "K:REBAR", "unit": "kg", "concrete_line": "L-4", "status": "HELD_BLANK"}]}
    v8 = {"rebar_omission": {"rows": [{"concrete_line": "L-4", "expected_after": {
        "element_id": "K:REBAR", "item_code": "STR.REBAR", "unit": "kg"}}]}}
    with pytest.raises(M.ManifestError, match="unit pair"):
        M.pkg_rebar(t583, v8)


# ---- training villa (development, regression only) --------------------------------------------------------------

@pytest.fixture(scope="module")
def built():
    return M.build()


def test_committed_output_is_the_rebuild(built):
    assert M.OUT_JSON.read_text(encoding="utf-8") == M.dumps(built)


def test_overlay_clean(built):
    o = built["overlay"]
    assert o["stale"] == 0 and o["unexplained_conflicts"] == 0 and o["other_lines_changed_vs_v8_overlay"] == []
    assert o["lines"] == {"base": 4999, "after_v8": 5123, "after_v9": 5124}            # + the E1 step line only
    assert [r["op_id"].split("|")[1] for r in o["flagged_rows"]] == ["HOST_FACES_V5"]   # T-580's NO_BEFORE, not V9's
    names = [x["package"] for x in o["order"]]
    assert "REBAR_OMISSION" not in names and names[-2:] == ["RAILS_GUARDS (T-578)",
                                                            "STAIR_STEPS (T-584 FR-T584-1 / FR-T584-3)"]
    v9 = [x for x in o["order"] if x["package"].startswith(("REBAR_COMPONENTS", "RAILS", "STAIR"))]
    assert all(x["status"] == {"APPLIED": x["ops"]} for x in v9)


def test_totals_by_hand(built):
    t = built["overlay"]["v9_vs_v8_totals"]
    s = t["FIN.STAIR.STEP_LM|lm"]
    assert Decimal(s["after"]["released"]) - Decimal(s["before"]["released"]) == 4 * Decimal("2.80")
    assert Decimal(s["before"]["held_high"]) == Decimal("13.7964") + Decimal("11.5") + Decimal("4.6")   # 3 second readings
    assert Decimal(s["after"]["held_low"]) == Decimal("13.7964") + Decimal("4.14365")
    assert s["after"]["held_high"] == "13.85" and s["after"]["held_high_open_n"] == 1
    r = t["STR.REBAR|kg"]
    assert r["after"]["released"] == r["before"]["released"] == "9375.30576"
    assert Decimal(r["after"]["held_low"]) - Decimal(r["before"]["held_low"]) == 2 * Decimal("290.684") + \
        Decimal("122.518") + Decimal("63.897") == Decimal("767.783")
    assert r["after"]["held_high_open_n"] - r["before"]["held_high_open_n"] == 4
    rail = t["FIN.RAILING|lm"]["after"]
    assert Decimal(rail["held_low"]) == Decimal("0.856999") + Decimal("0.261197") and rail["held_high"] == "1.875"
    assert rail["released"] == "33.319174"
    assert t["MET.RAILING.GUARD|lm"]["after"]["held_high"] == "7.5"


def test_edge_census_and_one_source(built):
    c = built["edge_census"]
    assert c["after_v9"]["doubles"] == {} and c["after_v9"]["orphans"] == [] and c["after_v9"]["edges"] == 89
    assert len(c["before_v9"]["doubles"]) == 12 + 10 + 4                        # RS-C, RS-S, RS-A second readings
    assert c["before_v9"]["orphans"] == ["ST03-E1-N01", "ST03-E1-N02", "ST03-E1-N03", "ST03-E1-N04"]
    assert c["after_v9"]["by_stair"]["ST-03"] == {"edges": 5, "step_basis": 4, "nosing_line": 1, "held": 0}
    assert c["t578_one_source"]["same"] is True


def test_rows_classes_and_evidence(built):
    rows = {r["line_id"]: r for r in built["rows"]}
    e1 = rows[M.E1_LINE]
    assert e1["class_after"] == "RELEASED" and e1["after"]["measured_net"] == 11.2 and e1["beside"]["nr"] == 4
    assert e1["evidence"]["status"] == "VERIFIED" and "30A" in e1["beside"]["not_a_step"]
    reb = [r for r in built["rows"] if r["line_id"].startswith("NEW:STR.REBAR:")]
    assert len(reb) == 6 and all(r["after"]["measured_net"] is None for r in reb)        # valued 0 kg: none released
    assert sorted(r["class_after"] for r in reb) == ["AT_LEAST"] * 4 + ["HELD"] * 2
    assert all(r["evidence"]["status"] != "VERIFIED" for r in built["rows"] if r["class_after"] != "RELEASED")
    assert all(r["evidence"]["verdict_line"] for r in built["rows"])
