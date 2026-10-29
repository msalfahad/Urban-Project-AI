"""T-338: ARCH_TAKEOFF_V3.0.24 (the T-334 line-state findings fixed in the lines' TEXT only: released rebar kg print
their arithmetic, a NOT_APPLICABLE line drops its gross, a formula ends on the line's own figure) on a hand-calculated
NON-Alsenan villa (VG-338), normal and adverse. The independent judge is the merged T-334 check
(tools/t334_line_state_check.py), never the module's own scan.

Villa VG-338, by hand (unit mass d^2/162):
  R12  beam B1 bottom, 6 bars 12 mm x 3.40 m: 144/162 = 0.888889 kg/m; 6 x 3.40 x 0.888889 = 18.133333 -> 18.133 kg
  R20  column C1 main, 3 bars 20 mm x 5.15 m: 400/162 = 2.469136 kg/m; 3 x 5.15 x 2.469136 = 38.148148 -> 38.148 kg
  (both RELEASED ledger records printing 'held: ' as their formula: VALUED_WITH_HELD_TEXT)
  SK   skirting NOT_APPLICABLE (base on full-height tile) keeping gross 4.25 lm: HELD_WITH_FIGURE
  PL1  plaster PROVISIONAL: 4.00 m x 3.00 m = 12.0 m2 less W1 1.20 x 1.40 = 1.68 -> net 10.32 m2; formula concludes
       '= 12.0 m2' (the gross): FORMULA_FIGURE_DISAGREES
  PL2  plaster BOUNDED (no gross field: a held line carries none): faces 8.00 m x 3.00 m = 24.0 m2, held net
       20.5 .. 22.1 m2 (openings HELD); formula concludes '= 24.0 m2' outside the range: FORMULA_FIGURE_DISAGREES
  plus four clean lines (a released rebar line with its own formula, a held rebar line, a measured slab, a blocked
  block wall) that must stay byte-identical.
"""
from __future__ import annotations

import copy
import json
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v3024 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402
from tools import t334_line_state_check as LS  # noqa: E402

PID, REV = "villa-vg338", "a" * 64
DOCS = [{"file": "vg338_st.dxf", "sha256": "d" * 64}]
UMS = {"method": "D2_OVER_162", "source": "project unit-mass method d^2/162 (the hand ledgers' method)"}


def _bar(eid, n, L, d, net, state="RELEASED", ev="SOURCE_DERIVED", formula="held: ", sub=True):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code="STR.REBAR", unit="kg", evidence_state=ev,
                        measured_net=net if ev == "SOURCE_DERIVED" else None, element_id=eid, floor="GF",
                        physical_element="beam", formula=formula, documents=DOCS, rule_id="R-HL", rule_version="v1",
                        inputs={"count": n, "length_m": L, "ledger_state": state, "reasons": []},
                        subtrade=f"beam / {d:g} mm" if sub else "beam", material_state="SOURCE",
                        rfi=None if ev == "SOURCE_DERIVED" else {"question": "bar count not printed"},
                        notes="vg338 ledger")


def _fin(code, eid, ev, unit="m2", net=None, gross=None, rng=None, formula="", floor="1F"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, gross=gross, bounded_range=rng, element_id=eid, floor=floor,
                        physical_element="wall_face", formula=formula, documents=DOCS, rule_id="R-F", rule_version="1",
                        rfi={"question": "openings of the face not printed"} if ev in ("BOUNDED_EXPOSURE",
                                                                                       "BLOCKED_RFI") else None,
                        notes="vg338")


def lines_3023():
    return [
        _bar("R12", 6, 3.40, 12, 18.133),
        _bar("R20", 3, 5.15, 20, 38.148),
        _bar("R16ok", 4, 2.65, 16, 16.751, formula="4 x 2.65 m x 1.580247 kg/m = 16.751 kg"),
        _bar("R16held", 4, 2.65, 16, None, state="HELD_DEFINED", ev="BLOCKED_RFI", formula="held: bar count"),
        _fin("FIN.SKIRTING", "SK", "NOT_APPLICABLE_WITH_EVIDENCE", unit="lm", gross=4.25,
             formula="NOT_APPLICABLE: base on full-height tile; was 4.25"),
        _fin("FIN.PLASTER", "PL1", "PROVISIONAL", net=10.32, gross=12.0,
             formula="4.00 m face x 3.00 m owner height = 12.0 m2, less 1 opening(s) by their own records"),
        _fin("FIN.PLASTER", "PL2", "BOUNDED_EXPOSURE",
             rng={"low": 20.5, "high": 22.1, "basis": "openings of the face HELD"},
             formula="8.00 m face x 3.00 m owner height = 24.0 m2, less the held openings"),
        _fin("STR.CONC.SLAB", "S1", "MEASURED", unit="m3", net=12.5, formula="50.0 m2 x 0.25 m = 12.5 m3",
             floor="GF"),
        _fin("MAS.BLOCK", "W1", "BLOCKED_RFI", formula="held: block type not read", floor="GF"),
    ]


def _id(ls, eid):
    return next(ln["line_id"] for ln in ls if ln["location"]["element_id"] == eid)


def doc(ls=None, **kw):
    ls = ls or lines_3023()
    fixes = [{"line_id": _id(ls, "R12"), "kind": "REBAR_FORMULA", "task": "T-P334"},
             {"line_id": _id(ls, "R20"), "kind": "REBAR_FORMULA", "task": "T-P334"},
             {"line_id": _id(ls, "SK"), "kind": "NA_GROSS", "task": "T-P334"},
             {"line_id": _id(ls, "PL1"), "kind": "FORMULA_END", "task": "T-P334"},
             {"line_id": _id(ls, "PL2"), "kind": "FORMULA_END", "task": "T-P334"}]
    d = {"schema": A.INPUTS_SCHEMA, "project": PID,
         "sources": [{"file": "vg338_findings.csv", "sha256": "c" * 64, "task": "T-P334", "merge_commit": "m334",
                      "checker_run": "checker c334"}],
         "unit_mass": dict(UMS), "fixes": fixes, "for_lead": [],
         "declared": {"REBAR_FORMULA": {"lines": 2, "kg": 56.281}, "NA_GROSS": {"lines": 1, "gross": 4.25},
                      "FORMULA_END": {"lines": 2}}}
    d.update(kw)
    return d


def run(d=None, ls=None):
    ls = ls or lines_3023()
    d = A.load_inputs(d or doc(ls))
    ch, logs = A.changes_for(d, ls)
    out, ident = A.integrate(ls, ch, d)
    return ls, ch, logs, out, ident


def _by(out):
    return {ln["location"]["element_id"]: ln for ln in out}


# ------------------------------------------------------------------------------------------------ normal
def test_the_t334_check_finds_the_five_findings_before():
    rep = LS.check_lines(lines_3023())
    kinds = {r["element_id"]: r["category"] for r in rep["findings"]}
    assert kinds == {"R12": "VALUED_WITH_HELD_TEXT", "R20": "VALUED_WITH_HELD_TEXT", "SK": "HELD_WITH_FIGURE",
                     "PL1": "FORMULA_FIGURE_DISAGREES", "PL2": "FORMULA_FIGURE_DISAGREES"}


def test_hand_fixture_after_v3024_the_t334_check_is_clean():
    ls, ch, logs, out, ident = run()
    rep = LS.check_lines(out)
    assert rep["refused"] == 0 and rep["flagged"] == 0, rep["findings"]
    assert ident["replaced"] == 5 and ident["added"] == 0 and ident["outside_rows"] == 4
    assert ident["by_kind"] == {"FORMULA_END": 2, "NA_GROSS": 1, "REBAR_FORMULA": 2}
    assert logs[0]["rebar_kg"] == pytest.approx(56.281, abs=1e-9) and logs[0]["na_gross"] == 4.25


def test_rebar_formula_is_the_hand_arithmetic_and_the_quantity_is_unchanged():
    _ls, _ch, _logs, out, _i = run()
    b = _by(out)
    f12 = b["R12"]["calculation"]["formula"]
    assert f12.startswith("6 x 3.4 m x 0.888889 kg/m (12 mm, kg/m = d^2 / 162) = 18.133 kg")
    rec = b["R12"]["calculation"]["inputs"]["line_state_v3024"]
    assert rec["product_kg"] == pytest.approx(18.133333, abs=1e-6) and rec["before_formula"] == "held: "
    assert b["R12"]["measured_net"] == 18.133 and b["R12"]["evidence_state"] == "SOURCE_DERIVED"
    assert "= 38.148 kg" in b["R20"]["calculation"]["formula"] and "2.469136 kg/m" in b["R20"]["calculation"]["formula"]
    assert LS.formula_figure(f12, "kg") == (18.133, 3)


def test_na_line_drops_its_gross_and_keeps_it_on_record():
    ls, _ch, _logs, out, _i = run()
    sk = _by(out)["SK"]
    assert sk["gross"] is None and sk["measured_net"] is None and sk["bounded_range"] is None
    assert sk["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE"
    assert sk["calculation"]["inputs"]["line_state_v3024"]["before_gross"] == 4.25
    assert sk["calculation"]["formula"] == _by(ls)["SK"]["calculation"]["formula"]


def test_formula_ends_on_the_lines_own_figure_and_keeps_the_reading():
    _ls, _ch, _logs, out, _i = run()
    b = _by(out)
    f1, f2 = b["PL1"]["calculation"]["formula"], b["PL2"]["calculation"]["formula"]
    assert "= 12.0 m2" in f1 and LS.formula_figure(f1, "m2") == (10.32, 2)
    assert "= 24.0 m2" in f2 and "held net 20.5 m2 .. 22.1 m2" in f2 and LS.formula_figure(f2, "m2") == (20.5, 1)
    assert b["PL1"]["gross"] == 12.0 and b["PL2"]["gross"] is None     # a valued line keeps its gross


def test_every_other_line_is_byte_identical_and_no_quantity_moves():
    ls, _ch, _logs, out, ident = run()
    b0 = {ln["line_id"]: ln for ln in ls}
    for ln in out:
        o = b0[ln["line_id"]]
        assert A30._qty(o) == A30._qty(ln) and o["rfi"] == ln["rfi"] and o["bounded_range"] == ln["bounded_range"]
        if ln["location"]["element_id"] in ("R16ok", "R16held", "S1", "W1"):
            assert A30.line_sha(o) == A30.line_sha(ln)
    d = A.diff_rows(ls, out)
    assert {r["vs_v3_0_23"] for r in d} == {"SAME", "CHANGED_TEXT_ONLY"}
    assert sum(r["vs_v3_0_23"] == "CHANGED_TEXT_ONLY" for r in d) == 5


def test_line_order_does_not_matter():
    ls = lines_3023()
    sh = list(ls)
    random.Random(338).shuffle(sh)
    _l, _c, _g, out1, _i1 = run(doc(ls), ls)
    _l, _c, _g, out2, _i2 = run(doc(ls), sh)
    assert {ln["line_id"]: A30.line_sha(ln) for ln in out1} == {ln["line_id"]: A30.line_sha(ln) for ln in out2}


def test_a_line_listed_for_the_lead_stays_as_it_is():
    ls = lines_3023() + [_bar("R14odd", 2, 1.0, 14, 9.9, state="HELD_RANGE")]   # valued under 'held:' but not RELEASED
    d = doc(ls)
    d["for_lead"] = [{"line_id": _id(ls, "R14odd"), "why": "valued but its record is a held range: state question"}]
    _l, _c, _g, out, ident = run(d, ls)
    o = _by(ls)["R14odd"]
    assert A30.line_sha(_by(out)["R14odd"]) == A30.line_sha(o) and ident["line_state"]["for_lead"] == 1


def test_no_inputs_changes_nothing():
    ls = lines_3023()
    ch, logs = A.changes_for(None, ls)
    assert ch == [] and logs[0]["state"] == "NO_PROJECT_INPUT"


# ------------------------------------------------------------------------------------------------ adverse
def _refused(d, ls=None, exc=A.InputsError, match=None):
    ls = ls or lines_3023()
    with pytest.raises(exc, match=match):
        dd = A.load_inputs(d)
        ch, _ = A.changes_for(dd, ls)
        A.integrate(ls, ch, dd)


def test_adverse_product_not_the_net_is_refused():
    ls = lines_3023()
    ls[0] = _bar("R12", 6, 3.40, 12, 18.5)         # the quantity does not follow from its inputs
    _refused(doc(ls), ls, match="does not follow")


def test_adverse_length_in_mm_is_refused():
    ls = lines_3023()
    ls[0] = _bar("R12", 6, 3400, 12, 18.133)       # a length in mm: the product is 1000 x the net
    _refused(doc(ls), ls, match="does not follow")


def test_adverse_no_diameter_is_refused():
    ls = lines_3023()
    ls[0] = _bar("R12", 6, 3.40, 12, 18.133, sub=False)
    _refused(doc(ls), ls, match="no bar diameter")


def test_adverse_missing_count_is_refused():
    ls = lines_3023()
    ln = copy.deepcopy(ls[0])
    ln["calculation"]["inputs"]["count"] = None
    ls[0] = ln
    _refused(doc(ls), ls, match="count")


def test_adverse_a_valued_non_released_line_under_hold_text_is_not_fixed():
    ls = lines_3023() + [_bar("R14odd", 2, 1.0, 14, 9.9, state="HELD_RANGE")]
    _refused(doc(ls), ls, match="neither fixed nor listed")
    d = doc(ls)
    d["fixes"].append({"line_id": _id(ls, "R14odd"), "kind": "REBAR_FORMULA", "task": "T-P334"})
    d["declared"]["REBAR_FORMULA"] = {"lines": 3, "kg": 66.181}
    _refused(d, ls, match="not a text fix")


def test_adverse_a_held_line_with_a_gross_that_is_not_na_goes_to_the_lead():
    ls = lines_3023() + [_fin("FIN.PAINT", "PB", "BOUNDED_EXPOSURE", gross=9.0,
                              rng={"low": 7.0, "high": 8.0, "basis": "openings HELD"}, formula="faces 9.0 less held")]
    _refused(doc(ls), ls, match="neither fixed nor listed")
    d = doc(ls)
    d["for_lead"] = [{"line_id": _id(ls, "PB"), "why": "bounded line with a gross: which state?"}]
    _l, _c, _g, out, _i = run(d, ls)
    assert _by(out)["PB"]["gross"] == 9.0


def test_adverse_unlisted_finding_is_refused():
    d = doc()
    d["fixes"] = [f for f in d["fixes"] if f["kind"] != "NA_GROSS"]
    d["declared"]["NA_GROSS"] = {"lines": 0}
    _refused(d, match="neither fixed nor listed")


def test_adverse_stale_listing_is_refused():
    ls = lines_3023()
    d = doc(ls)
    d["fixes"].append({"line_id": _id(ls, "S1"), "kind": "FORMULA_END", "task": "T-P334"})
    d["declared"]["FORMULA_END"] = {"lines": 3}
    _refused(d, ls, match="shows no finding")
    d = doc(ls)
    d["fixes"][0]["line_id"] = "L-nosuchline"
    _refused(d, ls, match="no such line")


def test_adverse_wrong_kind_twice_and_both_lists_are_refused():
    ls = lines_3023()
    d = doc(ls)
    d["fixes"][2]["kind"] = "FORMULA_END"
    d["declared"] = {"REBAR_FORMULA": {"lines": 2, "kg": 56.281}, "NA_GROSS": {"lines": 0}, "FORMULA_END": {"lines": 3}}
    _refused(d, ls, match="shows NA_GROSS")
    d = doc(ls)
    d["fixes"].append(dict(d["fixes"][0]))
    _refused(d, ls, match="listed twice")
    d = doc(ls)
    d["for_lead"] = [{"line_id": _id(ls, "R12"), "why": "x"}]
    _refused(d, ls, match="both fixed and listed")


def test_adverse_declared_totals_and_unit_mass_are_checked():
    d = doc()
    d["declared"]["REBAR_FORMULA"]["kg"] = 56.3
    _refused(d, match="declared REBAR_FORMULA.kg")
    d = doc()
    d["declared"]["FORMULA_END"]["lines"] = 1
    _refused(d, match="declared FORMULA_END.lines")
    _refused(doc(unit_mass={"method": "RATIO_80_KG_M3", "source": "x"}), match="unit_mass")
    _refused(doc(unit_mass={"method": "D2_OVER_162"}), match="source")
    # a different (valid) method: the product no longer equals the net -> refused, never a re-computed quantity
    _refused(doc(unit_mass={"method": "EXACT_DENSITY", "density_kg_m3": 7000, "source": "x"}), match="does not follow")


def test_adverse_integrate_refuses_a_quantity_or_field_change():
    ls = lines_3023()
    d = A.load_inputs(doc(ls))
    ch, _ = A.changes_for(d, ls)
    bad = copy.deepcopy(ch)
    bad[0]["after"]["measured_net"] = 18.2
    with pytest.raises(ValueError):
        A.integrate(ls, bad, d)
    bad = copy.deepcopy(ch)
    bad[3]["after"]["rfi"] = {"question": "x"}
    with pytest.raises(ValueError, match="outside its formula"):
        A.integrate(ls, bad, d)
    bad = copy.deepcopy(ch)
    bad[0]["after"]["calculation"]["inputs"]["count"] = 7
    with pytest.raises(ValueError, match="beyond the formula"):
        A.integrate(ls, bad, d)
    bad = copy.deepcopy(ch)
    bad[1]["after"]["calculation"]["formula"] = "held: "        # a fixed line still stating two states
    with pytest.raises(ValueError, match="still state two states"):
        A.integrate(ls, bad, d)


def test_adverse_schema_and_project():
    _refused(doc(schema="URBAN_V3023_INPUTS_V1"), match="schema")
    with pytest.raises(A.InputsError, match="for"):
        A.load_inputs(doc(project="another-villa"), PID)
    d = doc()
    d["sources"][0]["checker_run"] = ""
    _refused(d, match="checker_run")


def test_write_files_and_identity(tmp_path):
    ls = lines_3023()
    d = A.load_inputs(doc(ls))
    ch, logs = A.changes_for(d, ls)
    names, ident, led = A.write(tmp_path, ls, ch, logs, d, released_lines=ls[:2])
    assert names == sorted(["V3_0_24_BOQ_LINES.json", "V3_0_24_BOQ_LINES.csv", "V3_0_24_INTEGRATION_LEDGER.json",
                            "V3_0_24_INTEGRATION_LEDGER.csv", "V3_0_24_DIFF.csv", "V3_0_24_RUN.json"])
    run = json.loads((tmp_path / "V3_0_24_RUN.json").read_text(encoding="utf-8"))
    assert run["totals_moved_by_code"] == {} and run["released_default"] is False
    assert ident["diff"]["vs_v3_0_23"] == {"SAME": 4, "CHANGED_TEXT_ONLY": 5}
    assert len(led["rows"]) == 5 and led["integration_package"] is True
    out = json.loads((tmp_path / "V3_0_24_BOQ_LINES.json").read_text(encoding="utf-8"))
    out = out if isinstance(out, list) else out["lines"]
    assert LS.check_lines(out)["findings"] == []
