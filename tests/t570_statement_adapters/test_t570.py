"""T-570: statement adapters V4 for T-561 (B6 paint m2), T-564 (floor tile expected after fix), T-565 (B1 earthworks
NO_ROW), T-566 (B10 column CONFLICT readings, beam UNTRACED marks) and T-567 (B5 external plaster gross vs gross), on
the T-548 builder and the T-554 / T-557 / T-562 adapters (all read only). Synthetic villa "S570" (not the training
villa) by hand per adapter, adverse cases, then the merged training-villa sources (committed research outputs only)."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t570"))
import t570_adapters as Z  # noqa: E402
import t570_build as B  # noqa: E402

S = Z.S
Dd = Decimal


def close(sec):
    return S.build_statement([Z.SA.for_builder(sec)])["sections"][0]


def ln(lid, code, cls, unit, net=None, lo=None, hi=None, el="E"):
    return {"line_id": lid, "item_code": code, "class": cls, "unit": unit, "measured_net": net,
            "held_low": lo, "held_high": hi, "element_id": el}


# ------------------------------------------------------------------------------------------------ T-561 format ----
# S570 paint by hand (his - engine): room A released 4.00 x 5.00 at h 3.00 = 18 x 3 - door 0.90 x 2.20 = 52.02 m2
# (line PA); his A at 3.20 flat = 57.60 gross -> height 18 x 0.20 = 3.60 RD + door 1.98 RD = 5.58. Room B on HELD
# line PB: his 30.00, engine-basis gross 28.00 HELD + length +2.00 ER (moved to HELD). Shaft line PS HELD: his 40 =
# 35 HELD + 3 ER (moved) + 2 UNRESOLVED. Returns: no paint line; plastered return faces 1.50 (omission) - his 1.00
# fewer -> 1.50 ENGINE_WRONG + (-0.50) UNRESOLVED. Soffit line SO HELD: his 6.00 = 5.00 HELD + 1.00 UNRESOLVED.
def s570_paint():
    index = {x["line_id"]: x for x in [
        ln("PA", "FIN.PAINT", "RELEASED", "m2", 52.02, el="A"), ln("PB", "FIN.PAINT", "HELD", "m2", el="B"),
        ln("PS", "FIN.PAINT", "HELD", "m2", el="SHAFT"), ln("PX", "FIN.PAINT", "EXCLUDED", "m2", el="WET"),
        ln("SO", "FIN.STAIR.SOFFIT", "HELD", "m2", el="STAIR:S1:soffit")]}

    def pair(gross, eng, rows, **kw):
        bc = {}
        for r in rows:
            bc[r["cause"]] = str(Dd(bc.get(r["cause"], "0")) + Dd(r["delta"]))
        return {"freelancer_gross": gross, "engine_valued": eng, "gap": str(Dd(gross) - Dd(eng)), "rows": rows,
                "by_cause": bc, **kw}
    dry = pair("87.60", "52.02", [
        {"name": "A height: his 3.20 vs 3.00", "delta": "3.60", "cause": "RULE_DIFFERENCE", "source": "s"},
        {"name": "A opening deductions", "delta": "1.98", "cause": "RULE_DIFFERENCE", "source": "s"},
        {"name": "B HELD paint line", "delta": "28.00", "cause": "HELD", "source": "s"},
        {"name": "B length: his vs drawn", "delta": "2.00", "cause": "ENGINE_RIGHT", "source": "s"}],
        rooms=[{"room": "A", "paint_line_id": "PA"}, {"room": "B", "paint_line_id": "PB"}],
        two_methods={"owner_G1_gross_11_lines": "x", "drawing_derived_gross_11_lines": ["y", "z"], "released_lines": []})
    shaft = pair("40", "0", [{"name": "shaft HELD", "delta": "35", "cause": "HELD", "source": "s"},
                             {"name": "south side", "delta": "3", "cause": "ENGINE_RIGHT", "source": "s"},
                             {"name": "RESIDUAL", "delta": "2", "cause": "UNRESOLVED", "source": "s"}],
                 candidate_lines=[{"line_id": "PS"}])
    ret = pair("1.00", "0", [{"name": "return faces of 3 doors", "delta": "1.50", "cause": "HELD", "source": "s"},
                             {"name": "RETURN RESIDUAL", "delta": "-0.50", "cause": "UNRESOLVED", "source": "s"}],
               engine_omission="no FIN.PAINT return line", outside=[])
    soff = pair("6.00", "0", [{"name": "his row 1: S1 soffit", "delta": "5.00", "cause": "HELD", "source": "SO (HELD)"},
                              {"name": "SOFFIT RESIDUAL", "delta": "1.00", "cause": "UNRESOLVED", "source": "n"}],
                candidate_lines=[{"candidate_line": "SO"}], why_not_wall_paint="CEILING class")
    d = {"internal": {"pairs": {"DRY": dry, "SHAFT": shaft, "RETURN": ret, Z.SOFFIT_PAIR: soff},
                      "engine_valued": "52.02", "freelancer_gross": "134.60", "freelancer_net": "133",
                      "his_half_deduction": "1.6", "gap_gross": str(Dd("134.60") - Dd("52.02")), "gap_net": "1"},
         "external": {"engine_valued_m2": "0"}, "ceiling_paint_beside": {}, "coats": "a rate"}
    return d, index


def test_t561_by_hand():
    d, index = s570_paint()
    p, so = Z.t561_from(d, index, fix_row="T-X")
    c = close(p)
    assert (c["reference_total"], c["engine_valued"], c["difference"]) == ("128.6", "52.02", "76.58")
    assert c["by_class"] == {"ENGINE_RIGHT": "0", "ENGINE_WRONG": "1.5", "RULE_DIFFERENCE": "5.58", "HELD": "68",
                             "TOLERANCE": "0", "UNRESOLVED": "1.5"}
    om = [r for r in p["rows"] if r["source_cause"] == "ENGINE_OMISSION"][0]
    assert om["fix_row"] == "T-X" and om["omission_bound_m2"] == ["0", "1.5"] and om["engine_status"] == "NONE"
    assert om["expected_after_fix"]["class"] == "HELD" and om["reclass"]["tag"] == "F-T570-1"
    bl = [r for r in p["rows"] if r["name"].startswith("DRY B length")][0]
    assert bl["class"] == "HELD" and bl["held_line_ids"] == ["PB"] and bl["reclass"]["tag"] == "F-T570-2"
    assert Z.Y.expected_by_class(p["source_by_class"], p["rows"]) == c["by_class"]
    s = close(so)
    assert s["by_class"]["HELD"] == "5" and s["by_class"]["UNRESOLVED"] == "1" and so["trade"] != p["trade"]
    assert Dd(c["difference"]) + Dd(s["difference"]) == Dd(d["internal"]["gap_gross"])


def test_t561_fixture_area_and_coats():
    # 18 m perimeter x 3.00 - one 0.90 x 2.20 door = 52.02 m2 painted face; two coats is a rate, never 104.04 m2
    assert Dd("18") * Dd("3.00") - Dd("0.90") * Dd("2.20") == Dd("52.02")
    d, index = s570_paint()
    p, _ = Z.t561_from(d, index)
    assert close(p)["engine_valued"] == "52.02"


def test_t561_adverse():
    d, index = s570_paint()
    bad = copy.deepcopy(index)
    bad["PR"] = ln("PR", "FIN.PAINT", "HELD", "m2", el="X-OPENING:RETURN_PAINT")
    with pytest.raises(Z.AdapterError, match="omission is wired"):
        Z.t561_from(d, bad)
    d2 = copy.deepcopy(d)
    d2["internal"]["pairs"]["DRY"]["rows"][0]["delta"] = "3.70"            # a pair that does not close
    with pytest.raises(Z.AdapterError, match="!= gap"):
        Z.t561_from(d2, index)
    d3 = copy.deepcopy(d)
    del d3["internal"]["pairs"]["RETURN"]["engine_omission"]
    with pytest.raises(Z.AdapterError, match="no longer names"):
        Z.t561_from(d3, index)
    p, _ = Z.t561_from(d, index)
    p2 = copy.deepcopy(p)
    om = [r for r in p2["rows"] if r["source_cause"] == "ENGINE_OMISSION"][0]
    om.update({"class": "HELD", "engine_status": "HELD", "held_line_ids": []})   # HELD without a line
    with pytest.raises(S.StatementError, match="names no held line"):
        close(p2)
    p3 = copy.deepcopy(p)
    [r for r in p3["rows"] if r["name"].startswith("DRY B length")][0].update(
        {"class": "ENGINE_RIGHT"})                                          # HELD engine side as agreement
    with pytest.raises(S.StatementError, match="HELD is never agreement"):
        close(p3)
    p4 = copy.deepcopy(p)
    p4["engine"]["held_lines"][0]["qty"] = "0"
    with pytest.raises(Z.SA.AdapterError, match="never 0"):
        Z.SA.refuse_held_as_zero(p4)


# ------------------------------------------------------------------------------------------------ T-565 format ----
def s570_earth():
    index = {x["line_id"]: x for x in [
        ln("E1", "STR.EARTH.EXCAVATION", "RELEASED", "m3", 5.2), ln("E2", "STR.EARTH.EXCAVATION", "HELD", "m3"),
        ln("F1", "STR.EARTH.BACKFILL", "HELD", "m3", None, 2.3, 2.4)]}
    comp = lambda lid, st, basis, **e: {"line_id": lid, "component": lid, "his": "NO_ROW", "class": "NOT_COMPARABLE",
                                        "difference": None, "pct": None, "engine": {"basis": basis, "state": st, **e}}
    d = {"components": [comp("E1", "VALUED", "IN_SITU", value="5.200000"), comp("E2", "HELD_BLANK", "IN_SITU"),
                        comp("F1", "HELD_RANGE", "COMPACTED", low="2.3", high="2.4"),
                        {"line_id": None, "component": "layers", "his": "NO_ROW", "class": "NOT_COMPARABLE",
                         "difference": None, "pct": None, "engine": {"basis": "COUNT", "state": "VALUED", "value": "9"}}],
         "family_totals": {"STR.EARTH.EXCAVATION": {"valued": "5.2", "held_low": None, "held_high": None, "lines": 2,
                                                    "held_blank_lines": 1},
                           "STR.EARTH.BACKFILL": {"valued": None, "held_low": "2.3", "held_high": "2.4", "lines": 1,
                                                  "held_blank_lines": 0}},
         "level_basis": "x", "pits_backfill_closure": {}, "sensitivity_S01_pits_excavation_m3": {},
         "printed_minimum_bound_pits_m3": "1"}
    return d, index


def test_t565_by_hand():
    # pad 2.00 x 2.00 dug 1.30 deep: 5.200 m3 IN_SITU; backfill COMPACTED 2.3 .. 2.4 held; never added together
    d, index = s570_earth()
    b = Z.t565_from(d, index)
    fam = {f["item_code"]: f for f in b["families"]}
    assert fam["STR.EARTH.EXCAVATION"]["engine_valued"] == "5.2" and fam["STR.EARTH.EXCAVATION"]["basis"] == "IN_SITU"
    assert fam["STR.EARTH.BACKFILL"]["engine_valued"] is None and fam["STR.EARTH.BACKFILL"]["engine_held_range"] == \
        ["2.3", "2.4"]
    assert all(f["his"] == "NO_ROW" and f["difference"] is None and f["pct"] is None for f in b["families"])
    assert b["reference_total"] is None and b["difference_pct_of_reference"] is None


def test_t565_adverse():
    d, index = s570_earth()
    b = Z.t565_from(d, index)
    for k, v in (("his", "0"), ("difference", "-5.2"), ("pct", "-100")):
        b2 = copy.deepcopy(b)
        b2["families"][0][k] = v
        with pytest.raises(Z.AdapterError, match="NO_ROW written"):
            Z.refuse_no_row_as_number(b2)
    b3 = copy.deepcopy(b)
    b3["difference_pct_of_reference"] = "0"
    with pytest.raises(Z.AdapterError, match="carries a reference total"):
        Z.refuse_no_row_as_number(b3)
    d2 = copy.deepcopy(d)
    d2["components"][0]["his"] = 0
    with pytest.raises(Z.AdapterError, match="not NO_ROW"):
        Z.t565_from(d2, index)
    d3 = copy.deepcopy(d)
    d3["components"][2]["engine"]["basis"] = "IN_SITU"                     # compacted read as in-situ
    with pytest.raises(Z.AdapterError, match="COMPACTED"):
        Z.t565_from(d3, index)
    i2 = copy.deepcopy(index)
    i2["E3"] = ln("E3", "STR.EARTH.DISPOSAL", "HELD", "m3")                # a line the report does not carry
    with pytest.raises(Z.AdapterError, match="differ from the index"):
        Z.t565_from(d, i2)


# ------------------------------------------------------------------------------------------------ T-566 format ----
def test_t566_classes_by_hand():
    # one storey: his 3 x CA (0.25 each), engine draws 4: one more CA on HELD line H (count +0.25), HELD -0.50
    # (his share on held lines), JOINT_HEAD +0.10 RD. Reading X binds the conflict member as CA, reading Y as CB.
    t_x = {"G": {"residual_m3": "-0.15", "components": {"COUNT": "0.25", "HELD": "-0.50", "JOINT_HEAD": "0.10"},
                 "by_mark": {"CA": {"COUNT": "0.25"}}}}
    t_y = {"G": {"residual_m3": "-0.15", "components": {"COUNT": "-0.25", "HELD": "-0.25", "JOINT_HEAD": "0.35"},
                 "by_mark": {"CA": {"COUNT": "-0.50"}, "CB": {"COUNT": "0.25"}}}}
    two = {"residual_m3": "0", "components": {}}
    conf = [{"position": "P", "storey": "G"}]
    ohx = Z.on_held_for({"P": "CA"}, t_x, set(), conf)
    ohy = Z.on_held_for({"P": "CB"}, t_y, set(), conf)
    assert ohx == {("G", "CA")} and ohy == {("G", "CB")}
    cx, cy = Z.column_classes(t_x, two, ohx), Z.column_classes(t_y, two, ohy)
    assert (cx["HELD"], cx["ENGINE_RIGHT"], cx["RULE_DIFFERENCE"]) == ("0.25", "0", "-0.1")
    assert (cy["HELD"], cy["ENGINE_RIGHT"], cy["RULE_DIFFERENCE"]) == ("0", "0.5", "-0.35")
    assert sum(Dd(v) for v in cx.values()) == sum(Dd(v) for v in cy.values()) == Dd("0.15")   # residual never moves
    bad = copy.deepcopy(t_x)
    bad["G"]["by_mark"]["CA"]["COUNT"] = "0.20"
    with pytest.raises(Z.AdapterError, match="COUNT by mark"):
        Z.column_classes(bad, two, ohx)


@pytest.fixture(scope="module")
def st():
    return B.build()


def _sec(st, sid):
    return [c for c in st["sections"] if c["section_id"] == sid][0]


def test_conflict_never_resolved(st):
    Z.verify_conflict(st)
    for mut in ("resolved", "one", "label"):
        s2 = copy.deepcopy(st)
        cf = _sec(s2, "T-551/columns")["beside"]["conflict_t566"]
        if mut == "resolved":
            cf["resolved_reading"] = cf["reading_of_record"]
        elif mut == "one":
            cf["readings"] = {cf["reading_of_record"]: cf["readings"][cf["reading_of_record"]]}
        else:
            r = [x for x in _sec(s2, "T-551/columns")["rows"] if x.get("conflict")][0]
            r["note"] = r["note"].replace("NOT a resolution", "resolved")
        with pytest.raises(Z.AdapterError):
            Z.verify_conflict(s2)


def test_t566_missing_reading_refused():
    index = Z.SA.load_index()
    d566, d551 = json.loads(Z.T566_JSON.read_text()), json.loads(Z.T551_JSON.read_text())
    secs, _, _ = B.B562.assemble(index)
    col = [x for x in secs if x["section_id"] == "T-551/columns"][0]
    bad = copy.deepcopy(d566)
    bad["t551_resplit"] = bad["t551_resplit"][:3]
    with pytest.raises(Z.AdapterError, match="every reading"):
        Z.t566_columns(col, bad, d551, index)
    bad2 = copy.deepcopy(d566)
    bad2["t551_resplit"][0]["tables"]["GF"]["residual_m3"] = "-1.9"
    with pytest.raises(Z.AdapterError, match="residual moved"):
        Z.t566_columns(col, bad2, d551, index)
    bm = [x for x in secs if x["section_id"] == "T-545/beams"][0]
    bad3 = copy.deepcopy(d566)
    bad3["beam_untraced"]["named"][0]["m3"] = "0.005"
    with pytest.raises(Z.AdapterError, match="re-add"):
        Z.t566_beams(bm, bad3)


# ------------------------------------------------------------------------------------------------ T-567 format ----
def s570_facade():
    index = {x["line_id"]: x for x in [
        ln("FA", "FIN.EXT.FINISH", "HELD", "m2"), ln("FN", "EXT.FENCE.PLASTER", "HELD", "m2")]}
    sec = {"section_id": "T-552/plaster-external", "report": "T-552", "trade": "B5 wall plaster external",
           "item_codes": ["FIN.EXT.FINISH", "EXT.FENCE.PLASTER"], "unit": "m2",
           "reference": {"kind": "FREELANCER", "total": "100", "unit": "m2", "basis": "his J93"},
           "engine": {"valued_total": "0", "valued_lines": [], "held_lines": [{"line_id": "FA", "low": None, "high": None},
                                                                              {"line_id": "FN", "low": None, "high": None}],
                      "excluded_lines": []},
           "rows": [{"name": "old", "delta": "100", "class": "UNRESOLVED"}], "beside": {}}
    # his 100 = our gross 80 / 84 + domes 10 RD + boundary 5 HELD + plinth -2 RD + his widths 4 / 3 ER + unprinted 3 / 0
    rows = []
    for p, og, er, un in (("lo", "80", "4", "3"), ("hi", "84", "3", "0")):
        rows += [{"pass": p, "row": "72", "group": "NW", "kind": "HIS_ONLY", "cause": "RULE_DIFFERENCE", "m2": "10",
                  "name": "domes"},
                 {"pass": p, "row": "87", "group": "BOUNDARY", "kind": "HIS_ONLY", "cause": "HELD", "m2": "5",
                  "name": "boundary EXT.FENCE.PLASTER"},
                 {"pass": p, "row": "52", "group": "SW", "kind": "TERM", "cause": "RULE_DIFFERENCE", "m2": "-2",
                  "name": "plinth"},
                 {"pass": p, "row": "51", "group": "SW", "kind": "TERM", "cause": "ENGINE_RIGHT", "m2": er, "name": "w"},
                 {"pass": p, "row": "77", "group": "ROOF", "kind": "TERM", "cause": "UNRESOLVED", "m2": un, "name": "u"}]
    d = {"his": {"gross_J93": "100"}, "candidate_lines": {"FA": {}},
         "passes": {p: {"residual": "0", "his_gross": "100", "our_gross": og,
                        "by_cause": {"RULE_DIFFERENCE": "8", "HELD": "5", "ENGINE_RIGHT": er, "UNRESOLVED": un}}
                    for p, og, er, un in (("lo", "80", "4", "3"), ("hi", "84", "3", "0"))},
         "net_bound": {"his_net": "98", "our_net_lo": "70", "our_net_hi": "76", "his_minus_ours_lo": "22",
                       "his_minus_ours_hi": "28", "ours_vs_his_pct": ["-28.6", "-22.4"]},
         "like_for_like_gross": {"his_comparable_gross": "85", "our_gross_lo": "80", "our_gross_hi": "84",
                                 "ours_vs_his_pct": ["-5.9", "-1.2"], "his_comparable_net": "83", "our_net_lo": "70",
                                 "our_net_hi": "76", "net_ours_vs_his_pct": ["-15.7", "-8.4"], "his_excluded_m2": "15",
                                 "note": "n"}}
    return sec, d, rows, index


def test_t567_by_hand():
    sec, d, rows, index = s570_facade()
    s2 = Z.t567_restate(sec, d, rows, index)
    c = close(s2)
    assert c["by_class"] == {"ENGINE_RIGHT": "0", "ENGINE_WRONG": "0", "RULE_DIFFERENCE": "10", "HELD": "90",
                             "TOLERANCE": "0", "UNRESOLVED": "0"}
    big = [r for r in s2["rows"] if r["name"].startswith("drawn render faces")][0]
    assert big["delta"] == "87" and big["split_range_m2"]["OUR_GROSS HELD"] == ["80", "84"]
    assert big["split_range_m2"]["TERM UNRESOLVED"] == ["0", "3"]
    assert s2["beside"]["rows_superseded_T552"]["status"] == "SUPERSEDED"
    assert s2["beside"]["net_vs_net"]["basis"] == "NET" and s2["beside"]["like_for_like"]["gross"]["basis"] == "GROSS"


def test_t567_adverse():
    sec, d, rows, index = s570_facade()
    with pytest.raises(Z.AdapterError, match="never set against a gross"):
        Z.pair({"basis": "NET", "v": "98"}, {"basis": "GROSS", "v": "84"})
    r2 = copy.deepcopy(rows)
    r2[5]["m2"] = "11"                                                     # his-only row differs by pass
    with pytest.raises(Z.AdapterError, match="between the passes"):
        Z.t567_restate(sec, d, r2, index)
    d2 = copy.deepcopy(d)
    d2["passes"]["hi"]["our_gross"] = "85"                                  # a pass that does not close
    with pytest.raises(Z.AdapterError, match="differs between the passes"):
        Z.t567_restate(sec, d2, rows, index)
    i2 = copy.deepcopy(index)
    i2["FA"]["class"] = "RELEASED"
    i2["FA"]["measured_net"] = 80
    with pytest.raises(Z.AdapterError):
        Z.t567_restate(sec, d, rows, i2)


# ------------------------------------------------------------------------------------------------ T-564 format ----
def test_t564_by_hand_and_adverse():
    sec = {"engine": {"valued_total": "95"}, "reference": {"total": "100"},
           "beside": {"engine_wrong_restated": {"finding": "F-1", "corrected_area_m2": "2", "engine_with_correction_m2":
                                                "97"}}}
    d = {"fix_rows": {"rows": [{"closes": "F-1", "expected_after": {"add": [
        {"item_code": "FIN.FLOOR.FINISH_HELD", "unit": "m2", "value": 2, "element_id": "R:floor"},
        {"item_code": "FIN.FLOOR.BED.DRY", "unit": "m2", "value": 2, "element_id": "R:bed"}]}}]}}
    e = Z.t564_expected(sec, d, {})["beside"]["expected_after_fix_T564"]
    assert (e["engine_vs_reference_pct_as_valued"], e["engine_vs_reference_pct_expected"]) == ("-5", "-3")
    assert e["status"].startswith("EXPECTED") and "ESTIMATED" in e["added"][0]["finish_status"]
    d2 = copy.deepcopy(d)
    d2["fix_rows"]["rows"][0]["expected_after"]["add"][0]["value"] = 3
    with pytest.raises(Z.AdapterError, match="restated area"):
        Z.t564_expected(sec, d2, {})


def test_expected_never_valued(st):
    Z.verify_expected_apart(st)
    s2 = copy.deepcopy(st)
    f = _sec(s2, "T-553/floor-tile")
    f["engine_valued"] = f["beside"]["expected_after_fix_T564"]["engine_expected_m2"]
    with pytest.raises(Z.AdapterError, match="EXPECTED figure"):
        Z.verify_expected_apart(s2)
    s3 = copy.deepcopy(st)
    _sec(s3, "T-553/floor-tile")["beside"]["expected_after_fix_T564"]["added"][0]["finish_status"] = "VERIFIED"
    with pytest.raises(Z.AdapterError, match="ESTIMATED"):
        Z.verify_expected_apart(s3)


# ------------------------------------------------------------------------------------------------ training villa --
def test_reproduces_committed():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t570/t570_build.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "reproduces" in r.stdout


def test_acceptance_numbers(st):
    p, so = _sec(st, "T-561/paint-internal"), _sec(st, "T-561/stair-soffit")
    assert (p["reference_total"], p["engine_valued"], p["difference"]) == ("1209.385", "217.2081", "992.1769")
    assert Dd(p["difference"]) + Dd(so["difference"]) == Dd("1032.1669")          # T-561 internal gross gap
    assert p["by_class"]["ENGINE_WRONG"] == "23.07" and Dd(p["by_class"]["UNRESOLVED"]) + \
        Dd(so["by_class"]["UNRESOLVED"]) == Dd("64.730966")                          # Checker: 64.73 by name
    f = _sec(st, "T-553/floor-tile")["beside"]["expected_after_fix_T564"]
    assert (f["engine_vs_reference_pct_as_valued"], f["engine_vs_reference_pct_expected"]) == ("-5.49", "-4.765")
    assert f["engine_expected_m2"] == "390.06405"
    cf = _sec(st, "T-551/columns")["beside"]["conflict_t566"]
    assert len(cf["readings"]) == 4 and cf["gf_c3_count_bound_m3"] == ["0", "0.46875"]
    assert cf["by_class_range_over_readings"]["ENGINE_RIGHT"] == ["1.522", "1.81375"]
    bm = _sec(st, "T-545/beams")
    assert bm["by_class"]["UNRESOLVED"] == "0.120452" and bm["difference"] == "-0.227179"
    ex = _sec(st, "T-552/plaster-external")
    assert ex["difference"] == "1502.84" and ex["by_class"]["HELD"] == "1160.366924"
    ew = st["not_comparable"][0]
    assert [f["engine_valued"] for f in ew["families"]] == ["225.941333", None, None]
    assert all(f["pct"] is None and f["his"] == "NO_ROW" for f in ew["families"])


def test_other_sections_untouched(st):
    prev = json.loads(B.B562.JSON_OUT.read_text(encoding="utf-8"))
    old = {c["section_id"]: c for c in prev["sections"]}
    for c in st["sections"]:
        if c["section_id"] in old and c["section_id"] not in B.TOUCHED:
            assert c == old[c["section_id"]], c["section_id"]
    tot0 = {(t["trade"], t["unit"]): t for t in prev["totals"]}
    for t in st["totals"]:
        if t["sections"][0] not in B.TOUCHED + B.NEW_SECTIONS:
            assert t == tot0[(t["trade"], t["unit"])]


def test_untouched_section_change_refused(st):
    index = Z.SA.load_index()
    secs, prov, ctx = B.assemble(index)
    blk = [x for x in secs if x["section_id"] == "T-546/floor"][0]
    blk["rows"][0]["note"] = (blk["rows"][0].get("note") or "") + " edited"
    with pytest.raises(Z.AdapterError, match="changed outside"):
        B.build_from(secs, prov, index, ctx)


def test_every_row_labelled_and_engine_wrong_has_fix(st):
    for sid in B.NEW_SECTIONS + B.TOUCHED:
        for r in _sec(st, sid)["rows"]:
            assert r.get("verification") in ("CHECKER_CONFIRMED", "WORKER_PROPOSED"), (sid, r["name"])
            if r["class"] == "ENGINE_WRONG":
                assert r["fix_row"]


def test_no_unit_mixing_and_no_private_text(st):
    for t in st["totals"]:
        assert len({_sec(st, s)["unit"] for s in t["sections"]}) == 1
    txt = (ROOT / "research/agents_t570/out/RECONCILED_STATEMENT_T570.md").read_text(encoding="utf-8")
    assert not any("؀" <= ch <= "ۿ" for ch in txt)                      # no workbook (Arabic) text
