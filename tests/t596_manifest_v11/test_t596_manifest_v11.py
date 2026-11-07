"""T-596: WIRING MANIFEST V11 + OVERLAY DRY RUN (R-T596-1).

Synthetic villa K596 (not the training villa; hand values):
  ring R1 (V9 row: HELD low 50.000 kg, high open): side bars drawn on both faces -> 2 more d12 x 6.00 m x 0.888 kg/m
          = 10.656 kg -> restated low 60.656 kg (0.060656 t), high stays open;
  ring R2 (V9 row: HELD blank): stays blank (carried byte-equal);
  footing P1 (candidate HELD 1.800 .. 2.100 m3 from one reading): accepted scenarios pad alone 1.60 x 1.25 x 0.80 =
          1.600, pad + upstand 1.800, drawn outline 1.75 x 1.50 x 0.80 = 2.100 -> 1.600 .. 2.100 (high unchanged);
          family bounded part with a second component 0.500 .. 0.700: 2.300 .. 2.800 -> 2.100 .. 2.800.
  nosing: 4 edges: E1 tread DC 1.000 (step basis), E2 landing HELD -> 1.000 DC, E3 tread HELD -> 1.000 in lane +
          curtail 0.500 (sub-row on the nosing line), E4 winder HELD -> bound 1.000 .. 1.414214, band 0 .. 0.050:
          valued 3.500 lm (step 2.000 + nosing 1.500), held 1.000 .. 1.464214 by name.
Adverse: a row from an unmerged task, a moved high, a low lowered without a scenario set, a blank turned into a bound,
HELD 0 .. 0, superseding a package that is not in the order or on other ids, a footing before that is not the T-572
bound, a T-412 HELD edge with no later reading, a HELD edge with a value or no bound, a valued edge at 0: all refused.
Then the training-villa build must be the rebuild and close by hand on the merged T-595 / T-598 figures."""

import copy
import json
from decimal import Decimal
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t596"))
import manifest_v11 as M          # noqa: E402

M9, OV = M.M9, M.OV
MERGED_K = {"T-K595": {"merge": "k595abcd", "verdict": "K596 verdict line"},
            "T-598": {"merge": "x", "verdict": "v"}, "T-434": {"merge": "y", "verdict": "v"}}


def _v9_ops():
    P = M.V9_REBAR
    a = M9.row(P, "T-583", "ADD", "NEW:STR.REBAR:K:R1", None, M9.held(50.0, None), "PARTIALLY VERIFIED", "old line",
               "STR.REBAR", "kg", "K:R1", beside={"concrete_line": "K-C1", "bounded_part_high_kg": 80.0})
    b = M9.row(P, "T-583", "ADD", "NEW:STR.REBAR:K:R2", None, M9.held(), "HELD", "old line", "STR.REBAR", "kg",
               "K:R2", beside={"concrete_line": "K-C2"})
    return [a, b]


def _t595(r1_low="0.060656"):
    return {"rebar": {"rows": [
        {"row_id": "K:R1", "unit": "t", "concrete_line": "K-C1", "status": "HELD_RANGE_HIGH_OPEN", "t_low": r1_low,
         "t_high_bounded_part": 0.08, "version": "K V2"},
        {"row_id": "K:R2", "unit": "t", "concrete_line": "K-C2", "status": "HELD_BLANK", "version": "K V1"}]},
        "footing": {"version": "K V2", "beside_his": {"his_m3": "1.600", "t572_class": "BELOW", "class": "WITHIN"},
                    "component": {"line_id": "K-F1", "element_id": "K:FTG:P1", "unit": "m3", "t572_low": "1.800",
                                  "t572_high": "2.100", "low": "1.600", "high": "2.100", "low_basis": "min",
                                  "high_basis": "outline", "status_label": "ESTIMATED",
                                  "scenarios": {"pad": "1.600", "pad+upstand": "1.800", "outline": "2.100"}}}}


def _idx():
    return {"K-F1": {"line_id": "K-F1", "item_code": "STR.CONC.FOOTING", "unit": "m3", "element_id": "K:FTG:P1",
                     "class": "HELD", "measured_net": None, "held_low": 1.8, "held_high": 2.1},
            "K-F2": {"line_id": "K-F2", "item_code": "STR.CONC.FOOTING", "unit": "m3", "element_id": "K:FTG:P2",
                     "class": "HELD", "measured_net": None, "held_low": 0.5, "held_high": 0.7}}


# ---- normal -----------------------------------------------------------------------------------------------------

def test_rebar_restatement_hand_values():
    (P, rows), moved = M.pkg_rebar_v2(_t595(), _v9_ops(), source="T-K595", merged=MERGED_K)
    by = {r["element_id"]: r for r in rows}
    assert by["K:R1"]["after"]["held_low"] == 60.656 and by["K:R1"]["after"]["held_high"] is None
    assert moved == {"K:R1": {"kg_before": 50.0, "kg_after": 60.656, "how": "RAISED"}}
    assert by["K:R2"]["after"] == M9.held() and by["K:R2"]["evidence"]["verdict_line"] == "old line"
    assert by["K:R1"]["evidence"]["verdict_line"] == "K596 verdict line"
    assert all(r["line_id"].startswith("NEW:STR.REBAR:K:") and r["package"] == P for r in rows)


def test_supersede_by_name_keeps_position_and_ids():
    old = _v9_ops()
    order = [("A", []), (M.V9_REBAR, old), ("B", [])]
    pkg, _ = M.pkg_rebar_v2(_t595(), old, source="T-K595", merged=MERGED_K)
    out, found = M.supersede(order, M.V9_REBAR, pkg)
    assert [n for n, _ in out] == ["A", M.P_REBAR, "B"] and found is old


def test_footing_scenario_bound_and_family():
    idx = _idx()
    (P, rows), how = M.pkg_footing(_t595(), idx, line="K-F1", source="T-K595", merged=MERGED_K)
    assert how == "LOWERED" and rows[0]["after"] == M9.held(1.6, 2.1) and rows[0]["evidence"]["status"] == "HELD"
    after, rep = OV.apply(idx, [(P, rows)])
    assert rep["rows"][0]["status"] == "APPLIED"
    t572 = {"components": [
        {"family": "B10 FOOTING LINE", "kind": "BOUNDED", "line_id": "K-F1", "low": "1.800", "high": "2.100"},
        {"family": "B10 FOOTING LINE", "kind": "BOUNDED", "line_id": "K-F2", "low": "0.500", "high": "0.700"}]}
    b, a = M.family_bounded(t572, idx, {"K-F1"}), M.family_bounded(t572, after, {"K-F1"})
    assert (b["low"], b["high"], a["low"], a["high"]) == ("2.3000", "2.8000", "2.1000", "2.8000")
    after["K-F2"]["held_low"] = 0.6                         # candidate differs from the T-572 bound: named, not swapped
    c = M.family_bounded(t572, after, {"K-F1"})
    assert c["low"] == "2.1000" and c["candidate_state_differs"][0]["line"] == "K-F2"


def _t412():
    def e(eid, kind, status, basis, qty="", beside="", handles=""):
        return {"eid": eid, "stair": "KS", "flight": "KF", "kind": kind, "status": status, "in_step_basis": basis,
                "qty_lm": qty, "beside_lm": beside, "handles": handles}
    return [e("K-E1", "TREAD", "DRAWING-CONFIRMED", "yes", "1.000000"),
            e("K-E2", "LANDING_EDGE", "HELD", "no", beside="1.000000"),
            e("K-E3", "TREAD", "HELD", "yes", beside="1.000000"),
            e("K-E4", "WINDER", "HELD", "yes")]


def _t598():
    return {"result": {"edges": [
        {"id": "K-E2", "status": "DRAWING-CONFIRMED", "lm": 1.0, "bound": None, "cause": "LANDING"},
        {"id": "K-E3", "status": "ASSUMED - OWNER-APPROVED", "lm": 1.5, "curtail_m": 0.5, "in_lane_m": 1.0,
         "bound": None, "cause": "CURTAIL"},
        {"id": "K-E4", "status": "HELD", "lm": None, "bound": [1.0, 1.414214], "cause": "WINDER NOT DRAWN"},
        {"id": "K-E3-BAND", "status": "HELD", "lm": None, "bound": [0.0, 0.05], "cause": "BAND"}]}}


def test_nosing_ledger_hand_values():
    rows, subs = M.nosing_ledger(_t412(), _t598(), merged=MERGED_K)
    t = M.ledger_totals(rows, subs)
    assert t["valued_lm"] == "3.5" and t["edges_valued"] == 3 and t["edges_held"] == 1
    assert t["valued_lm_by_owner"] == {M.NOSING_OWNER: "1.5", M.STEP_OWNER: "2"}
    assert t["held_bound_lm"] == ["1", "1.464214"]
    cur = next(s for s in subs if s["eid"] == "K-E3#CURTAIL")
    assert cur["lm"] == "0.5" and cur["owner"] == M.NOSING_OWNER and cur["part_of"] == "K-E3"
    assert next(r for r in rows if r["eid"] == "K-E3")["lm"] == "1"      # in-lane only on the step-basis edge


# ---- adverse ----------------------------------------------------------------------------------------------------

def test_row_from_unmerged_task_refused():
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.require_merged("T-599")
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.pkg_rebar_v2(_t595(), _v9_ops(), source="T-UNMERGED", merged=MERGED_K)
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.pkg_footing(_t595(), _idx(), line="K-F1", source="T-599")
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.nosing_ledger(_t412(), _t598(), merged={"T-434": MERGED_K["T-434"]})


@pytest.mark.parametrize("old,new,ss,msg", [
    (M9.held(50.0, 80.0), M9.held(55.0, 90.0), False, "never moves the high"),
    (M9.held(50.0, None), M9.held(55.0, 90.0), False, "never moves the high"),
    (M9.held(50.0, 80.0), M9.held(45.0, 80.0), False, "without a named accepted scenario set"),
    (M9.held(), M9.held(10.0, None), False, "blank stays blank"),
    (M9.held(50.0, 80.0), M9.held(85.0, 80.0), False, "outside"),
    (M9.held(0.0, 0.0), M9.held(0.0, 0.0), True, "0 .. 0"),
    (M9.held(1.0, 2.0), M9.released(1.5), False, "keeps the class"),
])
def test_bad_restatements_refused(old, new, ss, msg):
    with pytest.raises(M.ManifestError, match=msg):
        M.check_restated(old, new, scenario_set=ss)


def test_lowered_with_scenario_set_allowed_high_kept():
    assert M.check_restated(M9.held(1.8, 2.1), M9.held(1.6, 2.1), scenario_set=True) == "LOWERED"


def test_footing_low_lowered_without_scenarios_refused():
    t = _t595()
    del t["footing"]["component"]["scenarios"]
    with pytest.raises(M.ManifestError, match="scenario set"):
        M.pkg_footing(t, _idx(), line="K-F1", source="T-K595", merged=MERGED_K)


def test_footing_before_not_t572_refused():
    idx = _idx()
    idx["K-F1"]["held_low"] = 1.7
    with pytest.raises(M.ManifestError, match="not the T-572 V1 bound"):
        M.pkg_footing(_t595(), idx, line="K-F1", source="T-K595", merged=MERGED_K)


def test_supersede_missing_or_other_ids_refused():
    old = _v9_ops()
    pkg, _ = M.pkg_rebar_v2(_t595(), old, source="T-K595", merged=MERGED_K)
    with pytest.raises(M.ManifestError, match="nothing to supersede"):
        M.supersede([("A", [])], M.V9_REBAR, pkg)
    with pytest.raises(M.ManifestError, match="exactly the line ids"):
        M.supersede([(M.V9_REBAR, old[:1])], M.V9_REBAR, pkg)


def test_rebar_high_moved_refused():
    t = _t595()
    t["rebar"]["rows"][0]["t_high_bounded_part"] = 0.09
    with pytest.raises(M.ManifestError, match="bounded part high moved"):
        M.pkg_rebar_v2(t, _v9_ops(), source="T-K595", merged=MERGED_K)


def test_held_edge_with_no_reading_refused():
    t = _t598()
    t["result"]["edges"] = [e for e in t["result"]["edges"] if e["id"] != "K-E4"]
    with pytest.raises(M.ManifestError, match="no later reading"):
        M.nosing_ledger(_t412(), t, merged=MERGED_K)


@pytest.mark.parametrize("patch,msg", [
    ({"id": "K-E4", "bound": [0.0, 0.0]}, "never 0"),
    ({"id": "K-E4", "bound": None}, "never 0"),
    ({"id": "K-E2", "lm": 0.0}, "lm > 0"),
    ({"id": "K-E2", "status": "ESTIMATED"}, "not a WORKFLOW_CONTROLS"),
])
def test_bad_edges_refused(patch, msg):
    t = _t598()
    e = next(x for x in t["result"]["edges"] if x["id"] == patch["id"])
    e.update({k: v for k, v in patch.items() if k != "id"})
    with pytest.raises(M.ManifestError, match=msg):
        M.nosing_ledger(_t412(), t, merged=MERGED_K)


def test_held_edge_with_value_refused():
    with pytest.raises(M.ManifestError, match="carries no value"):
        M.ledger_row(_t412()[3], "HELD", "1.0", [1.0, 1.4], "x", M.STEP_OWNER)


# ---- training villa (committed output, hand closure on merged figures) -----------------------------------------

@pytest.fixture(scope="module")
def built():
    return M.build()


def test_alsenan_rebuild_is_committed(built):
    assert M.OUT_JSON.read_text(encoding="utf-8") == M.dumps(built)


def test_alsenan_overlay_clean(built):
    o = built["overlay"]
    assert o["lines"] == {"base": 4999, "after_v10": 5124, "after_v11": 5124}
    assert o["stale"] == 0 and o["unexplained_conflicts"] == 0 and o["other_lines_changed_vs_v10_overlay"] == []
    assert [r["package"] for r in o["flagged_rows"]] == ["T-498"]          # T-580's own NO_BEFORE, not a V11 row
    assert sorted(o["v11_vs_v10_totals"]) == ["STR.CONC.FOOTING|m3", "STR.REBAR|kg"]
    for k, v in o["v11_vs_v10_totals"].items():                            # HELD highs unchanged, nothing released
        assert v["before"]["held_high"] == v["after"]["held_high"]
        assert v["before"]["released"] == v["after"]["released"]
        assert v["before"]["held_high_open_n"] == v["after"]["held_high_open_n"]
    assert built["candidate_files_touched"] == 0 and built["released_quantities_changed"] == 0


def test_alsenan_rebar_by_hand(built):
    r = built["rebar"]
    # 4 x d14 side bars: (4 - 2) x 8.99725 m x 1.209877 kg/m = 21.7713 kg on 122.518 -> T-595 row 144.29 kg
    assert abs(Decimal(2) * Decimal("8.99725") * Decimal("1.209877") - Decimal("21.7713")) < Decimal("0.0005")   # 8.99725 printed to 5 dp
    assert list(r["moved"]) == [M.EAST_RING] and r["moved"][M.EAST_RING]["kg_after"] == 144.29
    assert r["bounded_low_kg"] == {"v10": "767.783", "v11": "789.555", "delta": "21.772"}
    assert len(r["carried_byte_equal"]) == 5
    sup = built["supersedes"][M.V9_REBAR]
    assert sup["by"] == M.P_REBAR and len(sup["same_line_ids"]) == 6


def test_alsenan_footing_by_hand(built):
    f = built["footing"]
    assert Decimal("2.80") * Decimal("1.40") * Decimal("0.50") == Decimal("1.960000")       # S02-1 F10 alone
    assert Decimal("3.25") * Decimal("1.40") * Decimal("0.50") == Decimal("2.275000")       # S02-3 outline
    assert (f["before"]["held_low"], f["before"]["held_high"]) == (2.176, 2.275)
    assert (f["after"]["held_low"], f["after"]["held_high"]) == (1.96, 2.275)
    fam = f["family_bounded_part_m3"]
    assert (fam["v10"]["low"], fam["v11"]["low"], fam["v11"]["high"]) == ("7.8445", "7.6285", "13.9613")
    assert fam["v11"]["candidate_state_differs"][0]["t572_flags"] == ["LINE_POINT_7.2204_IS_Q-28A_READING"]


def test_alsenan_nosing_by_hand(built):
    n = built["nosing"]
    t = n["totals"]
    # 88.500 + 3.450 + 15.421440 = 107.371440 lm; held 4 x 1.150 .. 4 x 1.735655 + band 0 .. 0.050
    assert Decimal("88.500") + Decimal("3.450") + Decimal("15.421440") == Decimal(t["valued_lm"])
    assert (t["edges"], t["edges_valued"], t["edges_held"]) == (89, 85, 4)
    assert t["held_bound_lm"] == ["4.6", "6.99262"] and len(t["held_by_name"]) == 5
    assert t["valued_lm_by_status"] == {"ASSUMED - OWNER-APPROVED": "16.57144", "DRAWING-CONFIRMED": "90.8"}
    assert sum(Decimal(v) for v in t["valued_lm_by_owner"].values()) == Decimal("107.37144")
    assert t["valued_lm_by_owner"][M.NOSING_OWNER] == "13.62144"           # 12.000 off-step + curtail 1.621440
    ms2u = next(r for r in n["ledger"] if r["eid"] == "ST01-MS2U-N12")
    assert ms2u["status"] == "ASSUMED - OWNER-APPROVED" and ms2u["lm"] == "1.15"       # F-C-T598-1
    assert all(r["lm"] != "0" for r in n["ledger"] + n["sub_rows"])
    assert n["census_after_v11"]["doubles"] == 0 and n["census_after_v11"]["orphans"] == 0
    assert n["his"]["his_minus_ours"] == "15.82856" and n["his"]["residual"] == "0"
    assert n["candidate_lines"].startswith("none")


def test_alsenan_sources_merged(built):
    assert built["sources_merged"] == {"T-434": "a6b325b3", "T-595": "568ce15e", "T-598": "78196c45"}
