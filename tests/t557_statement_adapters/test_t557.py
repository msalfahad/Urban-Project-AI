"""T-557: statement adapters for T-545 (beams m3), T-547 (wall tile m2), T-552 (plaster internal / external m2) and the
T-550 restatement of the T-543 blockwork section, on the T-548 builder and the T-554 adapters (both read only).
Synthetic villa "S557" (not the training villa) by hand per adapter, adverse cases, then the merged training-villa
sources (committed research outputs only; no private input)."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t557"))
import t557_adapters as X  # noqa: E402
import t557_build as B  # noqa: E402

S = X.S
Dd = Decimal


def close(sec):
    return S.build_statement([X.SA.for_builder(sec)])["sections"][0]


def ln(lid, code, cls, unit, net=None, lo=None, hi=None, el="E"):
    return {"line_id": lid, "item_code": code, "class": cls, "unit": unit, "measured_net": net,
            "held_low": lo, "held_high": hi, "element_id": el}


# ------------------------------------------------------------------------------------------------ R-T557-1 (d) ----
def test_bound_is_a_range():
    assert X.require_range(["6", "9"], "b") == (Dd("6"), Dd("9"))
    for bad in ("9", 9.0, ["6"], ["6", None], [None, "9"], ["9", "6"]):
        with pytest.raises(X.AdapterError):
            X.require_range(bad, "b")


# ------------------------------------------------------------------------------------------------ T-545 format ----
# S557 beams by hand. Engine: R1 6.000 + R2 3.000 = 9.000 m3 valued; H1 HELD bound 0.500 .. 1.000 (his share 0.800);
# excluded X1. His rows 10.000. engine - his = -1.000 = COUNT +1.500 (ENGINE_RIGHT) + HELD -0.800 + THROUGH_SUPPORT
# -1.700 (RULE_DIFFERENCE). Statement (his - engine) = +1.000: ENGINE_RIGHT -1.5, HELD +0.8, RULE_DIFFERENCE +1.7;
# bounded AT_LEAST 9.5 .. 10.0.
def s557_beams():
    index = {x["line_id"]: x for x in [
        ln("R1", "STR.CONC.BEAM", "RELEASED", "m3", 6.0), ln("R2", "STR.CONC.BEAM", "RELEASED", "m3", 3.0),
        ln("H1", "STR.CONC.BEAM", "HELD", "m3", None, 0.5, 1.0), ln("X1", "STR.CONC.BEAM", "EXCLUDED", "m3")]}
    d = {"engine": {"released_m3": "9.000", "released_lines": 2, "held_lines": 1},
         "total": {"his_m3": "10.000", "his_printed_total_m3": "10.000", "held_rollup": {},
                   "his_printed_minus_rows_m3 (BM-ARITH, his 1F sub-total leaves his first 1F row out)": "0"},
         "floors": {"GF": {"engine_m3": "9.000", "his_m3": "10.000", "components": {
             "COUNT": {"m3": "1.500", "verdict": "ENGINE_RIGHT"}, "SECTION": {"m3": "0", "verdict": "UNRESOLVED"},
             "HELD": {"m3": "-0.800", "verdict": "HELD"},
             "THROUGH_SUPPORT": {"m3": "-1.700", "verdict": "RULE_DIFFERENCE"}}}},
         "held_beside_his": [{"line_id": "H1", "floor": "GF", "mark": "B9", "engine_low_m3": "0.5",
                              "engine_high_m3": "1.0", "his_share_m3": "0.800", "class": "INSIDE", "reason": "x"}]}
    return d, index


def test_t545_by_hand():
    d, index = s557_beams()
    sec = X.t545_from(d, index)
    c = close(sec)
    assert c["unit"] == "m3" and c["difference"] == "1"
    assert c["by_class"]["ENGINE_RIGHT"] == "-1.5" and c["by_class"]["HELD"] == "0.8"
    assert c["by_class"]["RULE_DIFFERENCE"] == "1.7"
    assert c["engine_bounded"] == {"low_at_least": "9.5", "high": "10", "high_open": False}
    v = {r["source_cause"]: r["verification"] for r in sec["rows"]}
    assert v == {"COUNT": "CHECKER_CONFIRMED", "HELD": "WORKER_PROPOSED", "THROUGH_SUPPORT": "WORKER_PROPOSED"}
    assert [r for r in sec["rows"] if r["class"] == "HELD"][0]["held_line_ids"] == ["H1"]
    assert sec["beside"]["zero_components_not_listed"] == ["GF SECTION"]


def test_t545_adverse_held_share_and_index():
    d, index = s557_beams()
    d2 = copy.deepcopy(d)
    d2["held_beside_his"][0]["his_share_m3"] = "0.700"            # his share no longer the HELD component
    with pytest.raises(X.AdapterError):
        X.t545_from(d2, index)
    i2 = copy.deepcopy(index)
    i2["H1"]["held_high"] = 2.0                                   # report bound differs from the index
    with pytest.raises(X.AdapterError):
        X.t545_from(d, i2)


# ------------------------------------------------------------------------------------------------ T-547 format ----
# S557 wall tile by hand: room A valued 20.0 (his 18.0: height +2.5 RULE_DIFFERENCE, doors -0.5 ENGINE_RIGHT); room B
# HELD (his 10.0; drawing bound 6 .. 9). engine 20, his 28: statement +8 = -2.5 + 0.5 + 10 (HELD).
def s557_tile():
    d = {"engine_total": "20.0", "freelancer_total": "28.0", "held_bound_total": {"lo": "6", "hi": "9"},
         "engine_with_held_bounds": {"lo": "26", "hi": "29", "lo_pct": "-7.14", "hi_pct": "3.57"},
         "rows": [{"room": "A", "line_id": "TA", "state": "VALUED", "engine": "20.0", "freelancer": "18.0",
                   "delta": "2.0", "components": [
                       {"name": "height", "delta": "2.5", "cause": "RULE_DIFFERENCE", "basis": "Q-48 A"},
                       {"name": "doors", "delta": "-0.5", "cause": "ENGINE_RIGHT", "basis": "Q-73"}]},
                  {"room": "B", "line_id": "TB", "state": "HELD", "engine": None, "freelancer": "10.0",
                   "delta": "-10.0", "held_fact": "datum", "bound": {"lo": "6", "hi": "9"},
                   "components": [{"name": "held", "delta": "-10.0", "cause": "HELD"}]}]}
    index = {"TA": ln("TA", "FIN.WALL.TILE", "RELEASED", "m2", 20.0), "TB": ln("TB", "FIN.WALL.TILE", "HELD", "m2")}
    return d, index


def test_t547_by_hand_bounds_beside_not_in_range():
    d, index = s557_tile()
    sec = X.t547_from(d, index)
    c = close(sec)
    assert c["difference"] == "8" and c["by_class"]["HELD"] == "10"
    assert c["by_class"]["RULE_DIFFERENCE"] == "-2.5" and c["by_class"]["ENGINE_RIGHT"] == "0.5"
    assert c["engine_bounded"]["high_open"] is True                # drawing bound is never an engine bound
    assert sec["beside"]["held_drawing_derived_total_m2"] == ["6", "9"]


def test_t547_adverse_held_bound_as_point_value_refused():
    d, index = s557_tile()
    d["rows"][1]["bound"] = {"lo": "7.5", "hi": None}               # a HELD bound supplied as one value
    with pytest.raises(X.AdapterError, match="missing end"):
        X.t547_from(d, index)
    d, index = s557_tile()
    d["rows"][1]["engine"] = "0"                                    # HELD given a quantity
    with pytest.raises(X.AdapterError):
        X.t547_from(d, index)


# ------------------------------------------------------------------------------------------------ T-552 format ----
# S557 plaster by hand. Internal: dry V1 RELEASED 30.0 (room R1), dry H1 HELD 20 .. 25 (room R2), shaft S1 HELD (no
# bound), return T1 RELEASED 2.0. Rows (his - engine): R1 openings +4 RULE_DIFFERENCE, R1 height +1 (-> ENGINE_WRONG,
# fix FIX-1), R1 length -0.5 ENGINE_RIGHT, R2 HELD gross +28, R2 height +2 (-> HELD, on the HELD line), WS wet space +5
# RULE_DIFFERENCE (no line), shaft HELD +40, shaft box +3 ENGINE_RIGHT (-> HELD), shaft residual +6 UNRESOLVED, return
# residual -1 UNRESOLVED. Engine 32, his 119.5, difference 87.5 = ENGINE_RIGHT -0.5 + ENGINE_WRONG 1 + RULE 9 + HELD 73
# + UNRESOLVED 5. External: facade F1 HELD, fence G1 HELD; row 1 drawn faces 10 .. 11 + his vs drawn 2 .. 1 (total 12
# in both bridges) -> HELD; boundary 5 HELD (fence); frame 1.5 (no line) -> UNRESOLVED; residual 0.5. 19 = 17 + 2.
def s557_plaster():
    lines = [ln("V1", "FIN.PLASTER", "RELEASED", "m2", 30.0, el="HL:WALL_FINISH:R1:PLASTER"),
             ln("H1", "FIN.PLASTER", "HELD", "m2", None, 20.0, 25.0, el="HL:WALL_FINISH:R2:PLASTER"),
             ln("S1", "FIN.PLASTER", "HELD", "m2", el="HL:WALL_FINISH:ST_GF:PLASTER"),
             ln("T1", "FIN.PLASTER", "RELEASED", "m2", 2.0, el="GF-OPENING-OP-1:door jambs and head"),
             ln("F1", "FIN.EXT.FINISH", "HELD", "m2", el="GF-FACADE:facade"),
             ln("G1", "EXT.FENCE.PLASTER", "HELD", "m2", el="FENCE:F:PLASTER")]
    index = {x["line_id"]: x for x in lines}
    P = {"all": lines[:4], "dry": {"R1": index["V1"], "R2": index["H1"]}, "shaft": {"ST_GF": index["S1"]},
         "return": [index["T1"]]}

    def r(cause, delta, name, **k):
        return {"cause": cause, "delta": delta, "name": name, "source": "s557", **k}
    d = {"internal": {
        "freelancer_gross": "119.5", "freelancer_net": "110", "his_half_deduction": "9.5", "gap_net": "78",
        "engine_valued_dry_plus_returns": "32", "WET": {"valued_m2": "0"},
        "pairs": {"DRY": {"rooms": [{"room": "R1", "line_id": "V1"}, {"room": "R2", "line_id": "H1"}], "rows": [
            r("RULE_DIFFERENCE", "4", "R1 opening deductions"), r("RULE_DIFFERENCE", "1", "R1 height: his 3.6 vs 3.5"),
            r("ENGINE_RIGHT", "-0.5", "R1 length: his rows"), r("HELD", "28", "R2 HELD line at its engine-basis gross"),
            r("RULE_DIFFERENCE", "2", "R2 height: his 3.6 vs 3.15"), r("RULE_DIFFERENCE", "5", "WS wet space")]},
            "SHAFT": {"rows": [r("HELD", "40", "shaft faces"), r("ENGINE_RIGHT", "3", "south side"),
                               r("UNRESOLVED", "6", "SHAFT RESIDUAL")]},
            "RETURN": {"rows": [r("UNRESOLVED", "-1", "RETURN RESIDUAL")]}}},
        "q72_dry_plaster_height": {"verdict": "ENGINE_WRONG", "rule": "Q-72", "missing_total": ["6", "8.5"], "rows": [
            {"line_id": "V1", "room": "R1", "corrected_net": ["33.0", "34.0"], "missing_m2": ["3.0", "4.0"],
             "plaster_height": ["4.0", "4.1"], "status": "HELD (BOUNDED)", "beam_end_sections_held": []},
            {"line_id": "H1", "room": "R2", "corrected_net": ["24", "30"], "missing_m2": ["3", "4.5"],
             "plaster_height": ["4.0", "4.1"], "status": "HELD (BOUNDED)", "beam_end_sections_held": []}]},
        "external": {"freelancer_gross": "19", "freelancer_net": "18", "his_half_deduction": "1",
                     "bridge_lo": {"rows": []}, "bridge_hi": {"rows": []}}}
    ext = [("HELD", "10", "11", "his row 1: drawn faces (GF storey)"), ("ENGINE_RIGHT", "2", "1",
                                                                        "his row 1 vs the drawn faces"),
           ("HELD", "5", "5", "his row 2 (HELD_Q-65): no wall face drawn"),
           ("HELD", "1.5", "1.5", "his row 3 (NOT_IN_T159): no wall face drawn"),
           ("UNRESOLVED", "0.5", "0.5", "EXTERNAL RESIDUAL")]
    for c, lo, hi, nm in ext:
        d["external"]["bridge_lo"]["rows"].append(r(c, lo, nm))
        d["external"]["bridge_hi"]["rows"].append(r(c, hi, nm))
    ew = {("T-552/plaster-internal", "R1 height:"): "FIX-1"}
    return d, index, P, ew


def test_t552_by_hand_internal_and_external():
    d, index, P, ew = s557_plaster()
    internal, external = X.t552_from(d, index, P, ew)
    c = close(internal)
    assert c["difference"] == "87.5"
    assert c["by_class"] == {"ENGINE_RIGHT": "-0.5", "ENGINE_WRONG": "1", "RULE_DIFFERENCE": "9", "HELD": "73",
                             "TOLERANCE": "0", "UNRESOLVED": "5"}
    assert c["engine_bounded"] == {"low_at_least": "52", "high": None, "high_open": True}
    ew_row = [r for r in internal["rows"] if r["class"] == "ENGINE_WRONG"][0]
    assert ew_row["fix_row"] == "FIX-1" and ew_row["reclass"]["tag"] == "F-T557-2"
    rs = internal["beside"]["engine_wrong_restated"]
    assert rs["released_lines_now_m2"] == "30" and rs["released_lines_restated_HELD_BOUNDED_m2"] == ["33", "34"]
    assert rs["all_11_dry_lines_missing_m2"] == ["6", "8.5"]
    e = close(external)
    assert e["difference"] == "19" and e["by_class"]["HELD"] == "17" and e["by_class"]["UNRESOLVED"] == "2"
    assert e["by_class"]["ENGINE_RIGHT"] == "0"                     # his-vs-drawing is never engine agreement
    m = [r for r in external["rows"] if r["name"].startswith("his row 1")][0]
    assert m["delta"] == "12" and "10 .. 11" in m["note"]
    assert [r for r in external["rows"] if "HELD_Q-65" in r["name"]][0]["held_line_ids"] == ["G1"]


def test_engine_wrong_never_in_an_agreement_column():
    d, index, P, ew = s557_plaster()
    internal, _ = X.t552_from(d, index, P, ew)
    st = {"sections": [close(internal)]}
    for r, r0 in zip(st["sections"][0]["rows"], internal["rows"]):
        if "fix_row" in r0:
            r["fix_row"] = r0["fix_row"]
    X.verify_engine_wrong(st, ew)
    for cls in ("ENGINE_RIGHT", "TOLERANCE", "RULE_DIFFERENCE"):
        bad = copy.deepcopy(st)
        [r for r in bad["sections"][0]["rows"] if r["name"].startswith("R1 height:")][0]["class"] = cls
        with pytest.raises(X.AdapterError, match="never lands in an agreement column"):
            X.verify_engine_wrong(bad, ew)
    gone = copy.deepcopy(st)
    gone["sections"][0]["rows"] = [r for r in gone["sections"][0]["rows"] if not r["name"].startswith("R1 height")]
    with pytest.raises(X.AdapterError):
        X.verify_engine_wrong(gone, ew)


def test_t552_adverse():
    d, index, P, ew = s557_plaster()
    d2 = copy.deepcopy(d)
    d2["q72_dry_plaster_height"]["rows"][0]["corrected_net"] = "33.5"   # restated HELD bound as a point value
    with pytest.raises(X.AdapterError, match="not a \\[low, high\\] pair"):
        X.t552_from(d2, index, P, ew)
    d3 = copy.deepcopy(d)
    d3["external"]["bridge_hi"]["rows"][1]["delta"] = "1.5"           # bridges disagree on the row total
    with pytest.raises(X.AdapterError, match="bridges differ"):
        X.t552_from(d3, index, P, ew)
    i2 = copy.deepcopy(index)
    i2["F1"]["class"], i2["F1"]["measured_net"] = "RELEASED", 3.0     # a valued external line: report says 0
    with pytest.raises(X.AdapterError):
        X.t552_from(d, i2, P, ew)


# ------------------------------------------------------------------------------------------------ T-550 restate ---
# S557 blockwork: rows HELD 50 (H), upstand 9 ENGINE_RIGHT, residual 9 UNRESOLVED. T-550 splits the 9: length +1
# UNRESOLVED, below finish +6 ENGINE_RIGHT (no masonry, NONE), per-run height +1.5 ENGINE_RIGHT (on the HELD parapet
# face -> HELD, F-T557-6), held runs +0.5 HELD. After: ENGINE_RIGHT 15, HELD 52, UNRESOLVED 1.
def s557_blockwork():
    sec = {"section_id": "S557/blockwork", "report": "S", "trade": "B9", "unit": "m2",
           "reference": {"kind": "FREELANCER", "total": "100", "unit": "m2", "basis": "b"},
           "engine": {"valued_total": "32", "valued_lines": [{"line_id": "V", "qty": "32"}],
                      "held_lines": [{"line_id": "H", "low": None, "high": None},
                                     {"line_id": "P", "low": None, "high": None}], "excluded_lines": []},
           "rows": [{"name": "GF: HELD walls", "delta": "50", "class": "HELD", "engine_status": "HELD",
                     "held_line_ids": ["H"]},
                    {"name": "parapets: RC upstand 0.30 m above the slab", "delta": "9", "class": "ENGINE_RIGHT",
                     "engine_status": "NONE", "held_line_ids": []},
                    {"name": "parapets: RESIDUAL: parapet height below the finished roof (b_edge)", "delta": "9",
                     "class": "UNRESOLVED", "engine_status": "HELD", "held_line_ids": []},
                    {"name": "1F 'projections' row", "delta": "0", "class": "UNRESOLVED", "engine_status": "NONE",
                     "held_line_ids": []}]}
    d = {"parapet_residual_t543": "9", "projections_note": "not found", "openings_note": "o",
         "parapet_split": [{"chain": "C", "difference_m2": "9", "rows": [
             {"name": "C: length census", "cause": "UNRESOLVED", "delta": "1", "basis": "b"},
             {"name": "C: his height below the finished roof x centreline", "cause": "ENGINE_RIGHT", "delta": "6",
              "basis": "hatch"},
             {"name": "C: his flat printed height vs each run's printed height", "cause": "ENGINE_RIGHT",
              "delta": "1.5", "basis": "b"},
             {"name": "C: zero", "cause": "ENGINE_RIGHT", "delta": "0E-7", "basis": "b"},
             {"name": "C: held runs", "cause": "HELD", "delta": "0.5", "basis": "b"}]}],
         "restated_by_cause": {"ENGINE_RIGHT": "16.5", "HELD": "50.5", "UNRESOLVED": "1"},
         "t543_by_cause": {"ENGINE_RIGHT": "9", "HELD": "50", "UNRESOLVED": "9"}}
    return sec, d


def test_t550_restate_by_hand():
    sec, d = s557_blockwork()
    before = close(sec)
    new = X.t550_restate(sec, d, ["P"])
    c = close(new)
    assert c["by_class"]["ENGINE_RIGHT"] == "15" and c["by_class"]["HELD"] == "52"
    assert c["by_class"]["UNRESOLVED"] == "1" and c["difference"] == before["difference"]
    assert X.t550_expected_by_class(before["by_class"], d, new["rows"]) == c["by_class"]
    below = [r for r in new["rows"] if "below the finished roof x" in r["name"]][0]
    assert below["engine_status"] == "NONE" and "GEOMETRY, not the hatch" in below["note"]
    assert [r for r in new["rows"] if "each run's" in r["name"]][0]["reclass"]["tag"] == "F-T557-6"
    assert new["rows"][0] == sec["rows"][0]                         # untouched rows byte-identical
    assert new["rows"][-1]["note"].startswith("T-550:")


def test_t550_adverse():
    sec, d = s557_blockwork()
    d2 = copy.deepcopy(d)
    d2["parapet_split"][0]["rows"][0]["delta"] = "0.5"               # parts no longer close to the chain
    with pytest.raises(X.AdapterError):
        X.t550_restate(sec, d2, ["P"])
    s2 = copy.deepcopy(sec)
    s2["rows"][2]["delta"] = "8"                                      # target row changed since T-550
    with pytest.raises(X.AdapterError, match="re|restates"):
        X.t550_restate(s2, d, ["P"])


# ------------------------------------------------------------------------------------------------ training villa --
@pytest.fixture(scope="module")
def st():
    return B.build()


def test_reproduces_out():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t557/t557_build.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_every_section_closes_and_units_apart(st):
    for c in st["sections"]:
        assert sum((Dd(v) for v in c["by_class"].values()), Dd(0)) == Dd(c["difference"])
        assert Dd(c["reference_total"]) - Dd(c["engine_valued"]) == Dd(c["difference"])
    keys = [(t["trade"], t["unit"], t["reference_kind"]) for t in st["totals"]]
    assert len(keys) == len(set(keys))
    assert {c["unit"] for c in st["sections"]} == {"m2", "lm", "m3"}


def test_blockwork_restated_by_t550(st):
    c = [x for x in st["sections"] if x["section_id"] == "T-543/blockwork"][0]
    assert c["by_class"]["UNRESOLVED"] == "25.922437" and c["difference"] == "792.897"
    proj = [r for r in c["rows"] if r["name"].startswith("1F 'projections' row")]
    assert len(proj) == 1 and proj[0]["delta"] == "41.25" and proj[0]["class"] == "UNRESOLVED"
    assert not [r for r in c["rows"] if r["name"].startswith(X.T543_PARAPET_RESIDUAL)]
    below = [r for r in c["rows"] if "below the finished roof (delta" in r["name"]]
    assert sum(Dd(r["delta"]) for r in below) == Dd("68.4188") and all(r["class"] == "ENGINE_RIGHT" for r in below)
    assert all("GEOMETRY, not the hatch" in r["note"] for r in below)


def test_plaster_engine_wrong_and_restated_bound(st):
    c = [x for x in st["sections"] if x["section_id"] == "T-552/plaster-internal"][0]
    ew = [r for r in c["rows"] if r["class"] == "ENGINE_WRONG"]
    assert len(ew) == 4 and all(r["fix_row"] == "T-556" for r in ew)
    assert c["by_class"]["ENGINE_WRONG"] == "1.62315"
    rs = c["beside"]["engine_wrong_restated"]
    assert rs["released_lines_now_m2"] == "217.2081"
    assert rs["released_lines_restated_HELD_BOUNDED_m2"] == ["261.77493", "269.32863"]
    assert rs["all_11_dry_lines_missing_m2"] == ["146.4144", "171.2304"]
    assert c["engine_valued"] == "240.2781"                         # the restated bound never enters the engine column
    X.verify_engine_wrong(st)


def test_beams_and_tile_figures(st):
    b = [x for x in st["sections"] if x["section_id"] == "T-545/beams"][0]
    assert (b["reference_total"], b["engine_valued"], b["difference"]) == ("66.093875", "66.321054", "-0.227179")
    assert b["engine_bounded"]["low_at_least"] == "74.693883" and b["engine_bounded"]["high_open"]
    assert {r["verification"] for r in b["rows"] if r["source_cause"] == "COUNT"} == {"CHECKER_CONFIRMED"}
    assert {r["verification"] for r in b["rows"] if r["source_cause"] != "COUNT"} == {"WORKER_PROPOSED"}
    t = [x for x in st["sections"] if x["section_id"] == "T-547/wall-tile"][0]
    assert (t["difference"], t["by_class"]["HELD"]) == ("93.5262", "138.39")
    assert t["beside"]["held_drawing_derived_total_m2"] == ["102.2085", "144.1735"]


def test_held_never_agreement_or_zero(st):
    for c in st["sections"]:
        for r in c["rows"]:
            if r["engine_status"] == "HELD":
                assert r["class"] in ("HELD", "UNRESOLVED")
            if r["class"] == "HELD":
                assert Dd(r["delta"]) != 0 and r["held_line_ids"]


def test_t554_sections_unchanged(st):
    old = json.loads((ROOT / "research/agents_t554/out/RECONCILED_STATEMENT_T554.json").read_text())
    new = {c["section_id"]: c for c in st["sections"]}
    for c in old["sections"]:
        if c["section_id"] != "T-543/blockwork":
            assert new[c["section_id"]]["by_class"] == c["by_class"]
            assert [(r["name"], r["delta"], r["class"]) for r in new[c["section_id"]]["rows"]] == \
                   [(r["name"], r["delta"], r["class"]) for r in c["rows"]]
