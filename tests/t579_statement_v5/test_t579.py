"""T-579: reconciled-quantities statement V5 adapters for T-560 (B11 rebar, t, TYPED_LUMP), T-568 (doors / windows,
nr and m2 apart), T-569 (manifest V8 rows beside), T-572 (HELD bounds, measured set) and T-573 (ceilings by face
class). Synthetic villa "S579" (not the training villa) by hand per adapter, adverse cases, then the merged
training-villa sources (committed research outputs only; no private input)."""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t579"))
import t579_adapters as Z  # noqa: E402
import t579_build as B  # noqa: E402

Dd = Decimal
E = Z.StatementError


@pytest.fixture(scope="module")
def st():
    return B.build()


@pytest.fixture(scope="module")
def v4():
    return Z.load(Z.V4_JSON)


def sec_of(st, sid):
    return [c for c in st["sections_v5"] if c["section_id"] == sid][0]


# ------------------------------------------------------------------------------------------- T-560 (t) ---------
# S579 rebar by hand: pad 1.80 x 1.80, T12 @ 150 both ways, cover 0.075: N = 1 + floor(1.65 / 0.15) = 12 each way,
# bar 1.65 m, 12^2 / 162 = 0.888889 kg/m -> 2 x 12 x 1.65 x 144 / 162 = 35.200 kg VALUED (engine). Columns group:
# valued 1,200.0 kg, held 300 .. 450 kg, 4 blank lines. His typed lumps: footings 0.10 t, columns 2.00 t (total 2.10 t,
# no bar row). Tank: engine 1 blank line, his NO_ROW. Gaps (his - valued): 0.10 - 0.035200 = 0.064800 t;
# 2.00 - 1.200000 = 0.800000 t; section 2.10 - 1.235200 = 0.864800 t, no %.
def s579_rebar():
    def grp(fams, efams, valued, lo, hi, blank, his, gap, rlo, rhi, cls="RULE_DIFF", items=()):
        return {"bench_families": fams, "cls": cls, "engine_families": efams, "his_t": his, "gap_valued_t": gap,
                "residual_low_t": rlo, "residual_high_t": rhi, "residual_carried_by": ["HELD_BLANK"],
                "scope_items": list(items),
                "engine_kg": {"valued_kg": valued, "held_low_kg": lo, "held_high_kg": hi, "held_blank": blank,
                              "excluded": 0, "n_range": 1, "n_valued": 1}}
    return {"bench": {"basis": "TYPED_LUMP", "bar_rows_in_workbook": 0, "total_t": "2.10",
                      "families": {"FOOTINGS": {"t": "0.10"}, "COLUMNS": {"t": "2.00"}}},
            "engine_lines": 9,
            "engine_totals_kg": {"valued_kg": "1235.200", "held_low_kg": "300", "held_high_kg": "450",
                                 "held_blank": 5, "excluded": 0},
            "groups": {"G1": grp(["FOOTINGS"], ["FRP:FTG"], "35.200", None, None, 0, "0.10", "0.064800", "0.064800",
                                 "0.064800"),
                       "G2": grp(["COLUMNS"], ["HL:COLUMN_STEEL"], "1200.0", "300", "450", 4, "2.00", "0.800000",
                                 "0.350000", "0.500000", items=["LIFT_PIT:WALLS: no STR.REBAR line"]),
                       "G7": grp([], ["STAIR:TANK"], None, None, None, 1, None, None, None, None, cls="NO_ROW",
                                 items=["TANK: blank"])}}


def test_t560_by_hand():
    secs, nc = Z.t560_sections(s579_rebar())
    c = secs[0]
    assert (c["unit"], c["reference_total"], c["engine_valued"], c["difference"]) == ("t", "2.10", "1.235200",
                                                                                       "0.864800")
    assert c["difference_pct_of_reference"] is None and c["benchmark_basis"] == "TYPED_LUMP"
    assert [r["delta"] for r in c["rows"]] == ["0.064800", "0.800000"] and c["closure_residual"] == "0.000000"
    assert c["engine_held"]["held_range_t"] == ["0.300000", "0.450000"] and c["engine_held"]["held_blank_lines"] == 5
    assert c["rows"][1]["engine_omission_of_a_line"][0]["element"] == "lift-pit walls"
    assert c["rows"][1]["engine_omission_of_a_line"][0]["bound"] is None
    assert nc["reference_total"] == "NO_ROW" and nc["difference"] is None and nc["engine_held_blank_lines"] == 1
    assert Z.kg_to_t("35.2") == "0.035200"


def test_t560_adverse():
    c = Z.t560_sections(s579_rebar())[0][0]
    bad = copy.deepcopy(c)
    bad["difference_pct_of_reference"] = Z.pct_of(bad["reference_total"], bad["engine_valued"])
    with pytest.raises(E, match="TYPED_LUMP"):                    # TYPED_LUMP given a %
        Z.refuse_pct(bad)
    bad = copy.deepcopy(c)
    bad["rows"][0]["unit"] = "kg"                                 # t mixed with kg
    with pytest.raises(E, match="in kg, section in t"):
        Z.close_section(bad)
    d = s579_rebar()
    d["bench"]["total_t"] = "2.20"
    with pytest.raises(E, match="re-add"):
        Z.t560_sections(d)
    d = s579_rebar()
    d["groups"]["G2"]["gap_valued_t"] = "0.700000"
    with pytest.raises(E, match="gap"):
        Z.t560_sections(d)
    d = s579_rebar()
    d["bench"]["basis"] = "COUNTED"
    with pytest.raises(E, match="TYPED_LUMP"):
        Z.t560_sections(d)
    d = s579_rebar()
    d["engine_totals_kg"]["held_blank"] = 4                       # a blank line lost on the way
    with pytest.raises(E, match="candidate totals"):
        Z.t560_sections(d)


# ------------------------------------------------------------------------------------------- generic section -----
def test_section_closure_and_pct():
    rows = [Z.row("a", "1.50", "ENGINE_RIGHT", "m2", "s", "WORKER_PROPOSED"),
            Z.row("b", "-0.50", "RULE_DIFFERENCE", "m2", "s", "WORKER_PROPOSED")]
    c = Z.section("S/x", "T-0", "trade", "m2", "10.00", "9.00", rows, basis="b", verification="v", pct=True)
    assert c["difference"] == "1.00" and c["difference_pct_of_reference"] == "10.00"
    assert c["by_class_gross_abs"]["ENGINE_RIGHT"] == "1.50" and c["closure_residual"] == "0.00"
    with pytest.raises(E, match="rows"):
        Z.section("S/x", "T-0", "t", "m2", "10.00", "8.00", rows, basis="b", verification="v")
    with pytest.raises(E, match="not a statement class"):
        Z.row("c", "1", "NOT_IN_HIS_ROWS", "m2", "s", "v")
    held = [Z.row("h", "0", "HELD", "m2", "s", "v")]             # HELD printed as 0 with no bound
    with pytest.raises(E, match="printed as 0"):
        Z.section("S/h", "T-0", "t", "m2", "5", "5", held, basis="b", verification="v")
    with pytest.raises(E, match="HELD"):                         # % on a section with a HELD row
        Z.section("S/h", "T-0", "t", "m2", "5", "4", [Z.row("h", "1", "HELD", "m2", "s", "v", bound=["0", "1"])],
                  basis="b", verification="v", pct=True)


# ------------------------------------------------------------------------------------------- T-568 (nr / m2) -----
# S579 openings by hand: aluminium doors drawn 3 (1.00 x 2.20 = 2.20 m2 each, 6.60 m2), his 2 x 1.00 x 2.40 = 4.80:
# his - ours: count -1 nr ENGINE_RIGHT; m2 -2.20 ENGINE_RIGHT (the third door) + 2 x 0.20 = +0.40 RULE_DIFFERENCE
# (head 2.20 vs 2.40) = -1.80. Windows: 2 settled 1.50 x 1.20 = 3.60 m2, one HELD count 1 .. 2 with no figure; his 3
# windows 5.40 m2: nr +1 HELD; m2 +1.80 HELD. Internal doors: 4 drawn, 3 of them on a SETTLED line 0.80 x 2.20 x 3 =
# 5.28, 1 on a HELD line (width held 1.518 .. 1.760); his 3 deduction rows 0.80 x 2.40 = 5.76: nr his 3 - settled 3
# = 0 = +1 HELD - 1 ENGINE_RIGHT; m2 +0.48 = 3 x 0.16 RULE_DIFFERENCE.
def s579_openings():
    def r(cls, unit, term, delta, cause, name):
        return {"cls": cls, "unit": unit, "term": term, "delta": delta, "cause": cause, "name": name, "note": ""}
    A, W, P = "DOOR.EXTERNAL.ALUMINIUM", "WINDOW.ALUMINIUM", "DOOR.INTERNAL.PVC"
    return {
        "candidate_closure": [
            {"line": f"{A}|GF|pcs|SETTLED_DRAWING_CONFIRMED", "candidate": [3.0, None, None]},
            {"line": f"{A}|GF|m2|SETTLED_ASSUMED_OWNER_APPROVED", "candidate": [6.6, None, None]},
            {"line": f"{W}|GF|pcs|SETTLED_DRAWING_CONFIRMED", "candidate": [2.0, None, None]},
            {"line": f"{W}|GF|pcs|HELD", "candidate": [None, 1.0, 2.0]},
            {"line": f"{W}|GF|m2|SETTLED_DRAWING_CONFIRMED", "candidate": [3.6, None, None]},
            {"line": f"{W}|GF|m2|HELD_NO_FIGURE", "candidate": [None, None, None]},
            {"line": f"{P}|GF|pcs|SETTLED_DRAWING_CONFIRMED", "candidate": [3.0, None, None]},
            {"line": f"{P}|GF|pcs|HELD", "candidate": [None, 1.0, 1.0]},
            {"line": f"{P}|GF|m2|SETTLED_ASSUMED_OWNER_APPROVED", "candidate": [5.28, None, None]},
            {"line": f"{P}|GF|m2|HELD", "candidate": [None, 1.518, 1.76]}],
        "supply_aluminium": {
            A: {"nr": {"ours_settled": 3, "his": 2, "ours_minus_his": 1},
                "m2": {"ours_settled": "6.60", "his": "4.80", "ours_minus_his": "1.80", "ours_held": []},
                "rows": [r(A, "nr", "ours only", "1", "ENGINE_RIGHT", "D3"), r(A, "m2", "ours only", "2.20",
                                                                               "ENGINE_RIGHT", "D3"),
                         r(A, "m2", "height", "-0.20", "RULE_DIFFERENCE", "D1"),
                         r(A, "m2", "height", "-0.20", "RULE_DIFFERENCE", "D2")]},
            W: {"nr": {"ours_settled": 2, "his": 3, "ours_minus_his": -1, "ours_count_held": ["W3"]},
                "m2": {"ours_settled": "3.60", "his": "5.40", "ours_minus_his": "-1.80", "ours_held": ["W3"],
                       "ours_held_bounds": {"W3": None}},
                "rows": [r(W, "nr", "count HELD", "-1", "HELD", "W3"), r(W, "m2", "ours HELD", "-1.80", "HELD", "W3")]}},
        "masonry_deduction_doors": {
            P: {"nr": {"ours_settled": 4, "his": 3, "ours_minus_his": 1},
                "m2": {"ours_settled": "5.28", "his": "5.76", "ours_minus_his": "-0.48", "ours_held": ["P4"]},
                "rows": [r(P, "nr", "ours only", "1", "ENGINE_RIGHT", "P4")] +
                        [r(P, "m2", "height", "-0.16", "RULE_DIFFERENCE", f"P{i}") for i in (1, 2, 3)]},
            "LIFT.LANDING_OPENING": {"nr": {"ours_settled": 1, "his": 1}, "m2": {"his": "2.4", "ours_held": ["L1"]}}},
        "windows_like_for_like": {"settled_both_sides": {"nr": 2, "ours": "3.60", "his": "3.60", "diff": "0",
                                                         "pct": "0.00"},
                                  "with_Q76A_W17": {"nr": 2, "ours": "3.60", "his": "3.60", "diff": "0", "pct": "0.00"}}}


def test_t568_by_hand(v4):
    secs, nc = Z.t568_sections(s579_openings(), v4)
    by = {c["section_id"]: c for c in secs}
    a = by["T-568/alu-doors-nr"]
    assert (a["unit"], a["reference_total"], a["engine_valued"], a["difference"]) == ("nr", "2", "3", "-1")
    assert a["by_class"]["ENGINE_RIGHT"] == "-1" and a["difference_pct_of_reference"] == "-50.00"
    m = by["T-568/alu-doors-m2"]
    assert m["difference"] == "-1.80" and m["by_class"]["ENGINE_RIGHT"] == "-2.20"
    assert Dd(m["by_class"]["RULE_DIFFERENCE"]) == Dd("0.40")
    w = by["T-568/windows-nr"]
    assert w["by_class"]["HELD"] == "1" and w["rows"][0]["bound"] == ["1", "2"] and w["difference_pct_of_reference"] is None
    wm = by["T-568/windows-m2"]
    assert wm["engine_held"]["held_lines_no_figure"] == 1 and wm["difference_pct_of_reference"] is None
    p = by["T-568/internal-doors-nr"]
    assert (p["engine_valued"], p["difference"], p["by_class"]["HELD"], p["by_class"]["ENGINE_RIGHT"]) == \
        ("3", "0", "1", "-1")
    assert p["kind"] == "CROSS_REFERENCE_COUNT_CHECK" and p["reference_counted_in"] == "T-543/blockwork"
    assert Dd(by["T-568/internal-doors-m2"]["by_class"]["RULE_DIFFERENCE"]) == Dd("0.48")
    assert {x["unit"] for x in secs} == {"nr", "m2"} and all(len({r["unit"] for r in x["rows"]}) <= 1 for x in secs)
    assert all(b["difference"] is None for b in nc)


def test_t568_adverse(v4):
    d = s579_openings()
    d["supply_aluminium"]["DOOR.EXTERNAL.ALUMINIUM"]["m2"]["ours_minus_his"] = "1.60"     # causes do not close
    with pytest.raises(E, match="causes"):
        Z.t568_sections(d, v4)
    d = s579_openings()
    d["candidate_closure"][0]["candidate"] = [2.5, None, None]                           # a count of 2.5
    with pytest.raises(E, match="whole number"):
        Z.t568_sections(d, v4)
    d = s579_openings()
    d["supply_aluminium"]["DOOR.EXTERNAL.ALUMINIUM"]["rows"][1]["unit"] = "nr"           # area as nr
    with pytest.raises(E):
        Z.t568_sections(d, v4)


# ------------------------------------------------------------------------------------------- T-543 restatement ---
def test_blockwork_restatement_by_hand_and_adverse(v4):
    bw = [c for c in v4["sections"] if c["section_id"] == "T-543/blockwork"][0]
    new, moves = Z.restate_blockwork_t568(bw)
    assert len(moves) == 8 and sum(Dd(m["delta"]) for m in moves) == Dd("6.30")
    er = sum(Dd(m["delta"]) for m in moves if m["to"] == "ENGINE_RIGHT")
    assert er == Dd("6.54") and [m["delta"] for m in moves if m["to"] == "RULE_DIFFERENCE"] == ["-0.24"]
    for k in ("ENGINE_RIGHT", "RULE_DIFFERENCE", "UNRESOLVED"):
        assert Dd(new["by_class"][k]) - Dd(bw["by_class"][k]) == {"ENGINE_RIGHT": er, "RULE_DIFFERENCE": Dd("-0.24"),
                                                                  "UNRESOLVED": Dd("-6.30")}[k]
    assert new["by_class"]["HELD"] == bw["by_class"]["HELD"] and new["difference"] == bw["difference"]
    bad = copy.deepcopy(bw)
    [r for r in bad["rows"] if r["name"] in Z.T559_ROWS][0]["class"] = "HELD"
    with pytest.raises(E, match="expected UNRESOLVED"):
        Z.restate_blockwork_t568(bad)
    bad = copy.deepcopy(bw)
    bad["rows"] = [r for r in bad["rows"] if "D-1F-02" not in r["name"]]
    with pytest.raises(E, match="missing"):
        Z.restate_blockwork_t568(bad)


# ------------------------------------------------------------------------------------------- T-572 (m3) ----------
# S579 necks by hand: neck 0.40 x 0.40 between printed -1.20 .. -0.30: 0.16 x 0.90 = 0.144 BOTH ENDS (0.144 .. 0.144);
# neck on a printed minimum only: 0.33 x 0.90 = 0.297 LOWER_ONLY; a third with no founding note UNBOUNDED.
def s579_bounds():
    def comp(kind, lo, hi, item=None):
        return {"element_id": f"N{kind}", "family": "B10 NECK", "unit": "m3", "kind": kind, "low": lo, "high": hi,
                "low_item": item, "high_item": item}
    fam = {"valued": "0", "held_components": 3, "not_present_proposed": 0, "bounded_part_low": "0.441",
           "bounded_part_high": "0.144", "family_low": None}
    return {"families": {"B10 NECK": fam},
            "components": [comp("BOUNDED", "0.144", "0.144"), comp("LOWER_ONLY", "0.297", None),
                           comp("UNBOUNDED", None, None, "D-00 founding level not printed")],
            "beside_his": {"B10 NECK": {"candidate_generic_range_m3": ["0.1", "0.5"]}}}


def test_t572_bounds_by_hand(v4):
    c = Z.t572_bounds(s579_bounds(), v4)
    f = c["families"][0]
    assert f["both_ends_drawn"]["range"] == ["0.144", "0.144"]
    assert f["lower_end_only"] == {"n": 1, "at_least": "0.297", "high": "OPEN"}
    assert f["family_total"]["family_held"] is None and "D-00" in f["family_total"]["stated"]
    Z.refuse_one_sided_as_point(c)
    d = s579_bounds()                        # all held carry a lower end -> AT_LEAST, never a range
    d["components"] = d["components"][:2]
    d["families"]["B10 NECK"]["held_components"] = 2
    f2 = Z.t572_bounds(d, v4)["families"][0]
    assert f2["family_total"]["family_held"] == {"at_least": "0.441", "high": "OPEN"}


def test_t572_adverse(v4):
    d = s579_bounds()
    d["components"][1]["high"] = "0.400"                  # LOWER_ONLY with a high
    with pytest.raises(E, match="LOWER_ONLY"):
        Z.t572_bounds(d, v4)
    c = Z.t572_bounds(s579_bounds(), v4)
    bad = copy.deepcopy(c)
    bad["families"][0]["lower_end_only"]["high"] = "0.400"           # one-sided printed as a point / range
    with pytest.raises(E, match="LOWER_ONLY printed with a high"):
        Z.refuse_one_sided_as_point(bad)
    bad = copy.deepcopy(c)
    bad["families"][0]["family_total"]["family_held"] = ["0.441", "0.600"]
    with pytest.raises(E, match="range"):
        Z.refuse_one_sided_as_point(bad)
    one = {"section_id": "S/n", "kind": "ONE_SIDED", "engine": Z.at_least("8.0"), "difference": "0.5",
           "difference_pct_of_reference": None}
    with pytest.raises(E, match="point"):
        Z.refuse_one_sided_as_point(one)
    d = s579_bounds()
    d["components"][0]["unit"] = "m2"                     # m3 vs m2
    with pytest.raises(E, match="not in m3"):
        Z.t572_bounds(d, v4)
    d = s579_bounds()
    d["families"]["B10 NECK"]["bounded_part_low"] = "0.500"
    with pytest.raises(E, match="bounded low"):
        Z.t572_bounds(d, v4)


# ------------------------------------------------------------------------------------------- T-569 / T-573 -------
def test_manifest_row_never_a_candidate_line(st, v4):
    idx = Z.load_index()
    d = Z.load(Z.T569_JSON)
    eid = d["rebar_omission"]["rows"][0]["expected_after"]["element_id"]
    fake = dict(idx)
    fake["L-fake"] = {"line_id": "L-fake", "element_id": eid}             # manifest row shown as a candidate line
    with pytest.raises(E, match="already candidate lines"):
        Z.t569_manifest(d, fake, v4)
    bad = copy.deepcopy(st)
    bad["manifest_beside"][0]["rows"][0]["candidate_line"] = True
    with pytest.raises(E, match="candidate line"):
        Z.refuse_manifest_as_line(bad)
    bad = copy.deepcopy(st)
    bad["sections_v5"][0]["rows"][0]["manifest_row"] = "W17_Q76A"
    with pytest.raises(E, match="manifest row inside"):
        Z.refuse_manifest_as_line(bad)


def test_t573_cove_and_cross_reference_adverse(v4):
    d = Z.load(Z.T573_JSON)
    bad = copy.deepcopy(d)
    [g for g in bad["classes"]["groups"] if g["id"].startswith("COVE")][0]["unit"] = "m2"   # lm with m2
    with pytest.raises(E, match="cove"):
        Z.t573_sections(bad, v4)
    w = copy.deepcopy(v4)
    sec = [c for c in w["sections"] if c["section_id"] == "T-552/plaster-external"][0]
    sec["rows"] = [r for r in sec["rows"] if not r["name"].startswith("his row 73 ")]    # row 73 lost there
    with pytest.raises(E, match="row 73"):
        Z.t573_sections(d, w)


# ------------------------------------------------------------------------------------------- training villa -----
def test_reproduces_committed(st):
    assert st == json.loads(B.JSON_OUT.read_text(encoding="utf-8"))
    assert B.to_markdown(st) == B.MD_OUT.read_text(encoding="utf-8")


def test_v4_sections_untouched_except_blockwork(st, v4):
    for a, b in zip(st["sections"], v4["sections"]):
        if a["section_id"] != "T-543/blockwork":
            assert a == b
    bw = [c for c in st["sections"] if c["section_id"] == "T-543/blockwork"][0]
    assert bw["by_class"]["UNRESOLVED"] == "52.206437" and bw["by_class"]["ENGINE_RIGHT"] == "113.541080"
    assert bw["difference"] == "792.897"
    bad = copy.deepcopy(st)
    bad["sections"][0]["rows"][0]["delta"] = "1"
    with pytest.raises(E, match="changed outside"):
        B.check_v4_unchanged(bad, v4)


def test_acceptance_numbers(st):
    r = sec_of(st, "T-560/rebar")
    assert (r["reference_total"], r["engine_valued"], r["difference"]) == ("44.190000", "9.375306", "34.814694")
    assert r["engine_held"]["held_range_t"] == ["14.278249", "19.646878"] and r["engine_held"]["held_blank_lines"] == 799
    assert r["difference_pct_of_reference"] is None and set(x["class"] for x in r["rows"]) == {"RULE_DIFFERENCE"}
    w = sec_of(st, "T-568/windows-m2")
    assert (w["difference"], w["by_class"]["HELD"], w["by_class"]["ENGINE_RIGHT"]) == ("40.644", "36.669", "3.975")
    assert w["beside"]["like_for_like_settled_both_sides"]["engine_vs_reference_pct"] == "-4.95"
    assert sec_of(st, "T-568/alu-doors-nr")["difference"] == "-1"
    b = sec_of(st, "T-573/ceiling-board")
    assert b["difference"] == "42.688823" and b["difference_pct_of_reference"] is None
    assert b["beside"]["like_for_like_no_held"]["engine_vs_reference_pct"] == "-0.33"
    p = sec_of(st, "T-573/ceiling-paint")
    assert p["difference"] == "57.499323" and p["by_class"]["RULE_DIFFERENCE"] == "42.745"
    hb = {f["family"]: f for f in sec_of(st, "T-572/held-bounds")["families"]}
    assert hb["B10 NECK"]["family_total"]["family_held"] == {"at_least": "9.723900", "high": "OPEN"}
    assert hb["B1-03 BACKFILL"]["lower_end_only"]["at_least"] == "99.645011"
    assert hb["B1-02 EXCAVATION"]["family_total"]["family_held"] is None
    assert sec_of(st, "T-572/measured-columns_GF")["difference_pct_of_reference"] == "-10.18"


def test_every_section_closes_and_units(st):
    for c in st["sections_v5"]:
        if "by_class" in c:
            assert c["closure_residual"] is None or Dd(c["closure_residual"]) == 0
            assert all(r["unit"] == c["unit"] for r in c["rows"])
            Z.refuse_pct(c)
        Z.refuse_one_sided_as_point(c)
    assert sec_of(st, "T-572/measured-necks")["engine"] == {"at_least": "8.869500", "high": "OPEN"}
    assert st["reports_pending"] == ["T-571", "T-574"] and st["released_quantities_changed"] == 0
    tags = {m["tag"] for m in st["reclasses"] if m["tag"].startswith("F-T579")}
    assert tags == {"F-T579-1", "F-T579-2", "F-T579-3"}


def test_no_private_text(st):
    """The V5 additions carry no workbook text (V4 carries its own reviewed labels unchanged)."""
    txt = json.dumps([st["sections_v5"], st["manifest_beside"], st["not_comparable"][1:]], ensure_ascii=False)
    assert not any("؀" <= ch <= "ۿ" for ch in txt)
