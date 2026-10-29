"""T-334: tools/t334_line_state_check.py on a hand-made synthetic villa VG-334 (not the development villa).

Hand calculation (written before running the tool; every figure below is the line's own, nothing recomputed):
  F1 STR.CONC.FOOTING MEASURED 1.5 x 1.0 x 0.8 = 1.2 m3, source S-01 + sha            -> OK
  R1 STR.REBAR SOURCE_DERIVED 6 bars x 3.10 m x 0.888 kg/m = 16.5168 -> printed 16.517 kg (3 decimals, |d| 0.0002)
                                                                                        -> OK
  S1 STR.CONC.SLAB BOUNDED_EXPOSURE 25.0 m2 x 0.20 .. 0.24 = 5.0 .. 6.0 m3, basis + question  -> OK
  B1 STR.CONC.STAIR BLOCKED_RFI (waist not printed; the formula names a plan reading 1.30 x 1.15 = 1.495 m2, another
     unit than the m3 line)                                                             -> OK
  N1 STR.CONC.LINTEL NOT_APPLICABLE_WITH_EVIDENCE (arches only)                         -> OK
  P1 FIN.CEILING SOURCE_DERIVED 4.0 x 3.5 = 14.0 m2 with an rfi on the finish material  -> OK + NOTE (never refused)
  W0 MAS.BLOCK MEASURED 4.0 m2 - opening D1 4.0 m2 = 0.0 m2 (a measured nil, not a hold)  -> OK
  -> 7 lines, 7 OK, 1 note, exit 0.
Adverse (each alone on the clean villa): the Verifier's case (a released 16.517 kg printing 'held: '), held as 0
(valued 0 under 'held:'; a held range 0 .. 0), a figure on a line without quantity (gross on NOT_APPLICABLE,
measured_net on BLOCKED_RFI, a range on BLOCKED_RFI, a valued state without a number), a range without its cause
(no basis; BOUNDED without a question; BOUNDED without a range; low > high), a range excluding its net, SOURCE_DERIVED
without a source (no document; a document without sha256), the formula concluding the gross 44.0 m2 on a 40.0 m2 net,
a held range 48.94 .. 52.29 m2 whose formula concludes 54.27 m2, a figure on a blocked line, an unknown state word.
"""

from __future__ import annotations

import copy
import json
import random

import pytest

from engine.source import boq_line as BL
from tools import t334_line_state_check as C

PID, REV = "VG-334", "e" * 64
CVER = "ARCH_TAKEOFF_V3.0.TEST"
DOC = {"file": "S-01", "sha256": "a" * 64}


def ln(code, eid, ev="MEASURED", q=None, unit="m3", **kw):
    base = dict(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                measured_net=q, element_id=eid, formula=kw.pop("formula", "L x B x H"), rule_id="R-SYN",
                rule_version="1", floor=kw.pop("floor", "GF"), documents=kw.pop("documents", [DOC]))
    base.update(kw)
    return BL.make_line(**base)


def villa():
    return [
        ln("STR.CONC.FOOTING", "F1", q=1.2, formula="1.5 x 1.0 x 0.8 = 1.2 m3", floor="FDN"),
        ln("STR.REBAR", "R1", ev="SOURCE_DERIVED", q=16.5168, unit="kg",
           formula="6 bars x 3.10 m x 0.888 kg/m = 16.517 kg"),
        ln("STR.CONC.SLAB", "S1", ev="BOUNDED_EXPOSURE", bounded_range={"low": 5.0, "high": 6.0, "basis": "depth"},
           rfi={"question": "slab depth 0.20 or 0.24 (not printed)"},
           formula="held: depth not printed; 25.0 m2 x 0.20 .. 0.24 = 5.0 .. 6.0 m3"),
        ln("STR.CONC.STAIR", "B1", ev="BLOCKED_RFI", rfi={"question": "waist not printed"},
           formula="held: waist not printed; landing plan 1.30 x 1.15 = 1.495 m2", floor="1F"),
        ln("STR.CONC.LINTEL", "N1", ev="NOT_APPLICABLE_WITH_EVIDENCE", notes="no lintel: arches only",
           formula="NOT_APPLICABLE: arches only"),
        ln("FIN.CEILING", "P1", ev="SOURCE_DERIVED", q=14.0, unit="m2", formula="4.0 x 3.5 = 14.0 m2",
           rfi={"question": "finish material not scheduled"}),
        ln("MAS.BLOCK", "W0", q=0.0, unit="m2", gross=4.0, deductions=[{"opening": "D1", "area": 4.0}],
           formula="4.0 m2 - opening D1 4.0 m2 = 0.0 m2"),
    ]


def one(line):
    return C.check_line(line)


def mutate(line, **changes):
    x = copy.deepcopy(line)
    for k, v in changes.items():
        if k == "formula":
            x["calculation"]["formula"] = v
        elif k == "documents":
            x["source"]["documents"] = v
        else:
            x[k] = v
    return x


# ---- normal --------------------------------------------------------------------------------------------------------

def test_clean_villa_passes_with_the_material_note():
    rep = C.check_lines(villa())
    assert rep["lines"] == 7 and rep["categories"] == {"OK": 7}
    assert (rep["flagged"], rep["refused"], C.exit_code(rep)) == (0, 0, 0)
    assert rep["notes"] == {C.NOTE_OPEN_RFI: 1}
    assert len(rep["note_lines"]) == 1
    assert C.assert_exportable(villa())["findings"] == []


def test_formula_figure_reader():
    assert C.formula_figure("6 bars x 3.10 m x 0.888 kg/m = 16.517 kg", "kg") == (16.517, 3)
    assert C.formula_figure("21.5 m face x 3.65 m = 78.6101 m2, less 3 openings (net 66.1 m2)", "m2") == (66.1, 1)
    # a figure in another unit is a reading, not the line's quantity
    assert C.formula_figure("0.22 x 2.85 + 0.6 = 1.227 m", "kg") == (None, None)
    assert C.formula_figure("1.30 x 1.15 = 1.495 m2", "m3") == (None, None)
    # unit boundary: 'm' does not match 'm2' / 'm3'
    assert C.formula_figure("2.0 x 1.5 = 3.0 m2", "m") == (None, None)
    assert C.formula_figure("2.0 + 1.5 = 3.5 m", "m") == (3.5, 1)


def test_printed_decimals_set_the_tolerance():
    r = villa()[1]
    assert one(mutate(r, formula="6 x 3.10 x 0.888 = 16.5 kg"))["category"] == "OK"        # 1 decimal: +- 0.05
    bad = one(mutate(r, formula="6 x 3.10 x 0.888 = 16.6 kg"))
    assert bad["category"] == "FORMULA_FIGURE_DISAGREES" and bad["severity"] == "FLAG"


# ---- adverse --------------------------------------------------------------------------------------------------------

def test_valued_line_printing_held_is_refused():
    r = mutate(villa()[1], formula="held: ")                     # the Verifier's case: a released kg under 'held: '
    res = one(r)
    assert (res["category"], res["severity"]) == ("VALUED_WITH_HELD_TEXT", "REFUSED")
    assert res["measured_net"] == 16.5168
    for w in ("HELD remainder: x", "Unresolved: y", "blocked by Q-1", "CONFLICT: two readings"):
        assert one(mutate(r, formula=w))["category"] == "VALUED_WITH_HELD_TEXT"
    # a hold word inside the text (not opening it) is context, not the line's state
    assert one(mutate(r, formula="6 x 3.10 x 0.888 = 16.517 kg; the lap stays held on its own line"))["category"] == "OK"


def test_held_as_zero_is_refused():
    z = mutate(villa()[0], measured_net=0.0, formula="held: lap length not printed")
    assert one(z)["category"] == "HELD_AS_ZERO"
    b = mutate(villa()[2], bounded_range={"low": 0.0, "high": 0.0, "basis": "depth"})
    assert one(b)["category"] == "HELD_AS_ZERO"
    # a measured nil with its arithmetic stays OK (W0)
    assert one(villa()[6])["category"] == "OK"


def test_figure_on_a_line_without_quantity_is_refused():
    n = mutate(villa()[4], gross=7.6)                            # taken off, old gross kept
    assert one(n)["category"] == "HELD_WITH_FIGURE" and "gross 7.6" in one(n)["detail"]
    b = mutate(villa()[3], measured_net=0.0)
    assert one(b)["category"] == "HELD_WITH_FIGURE"
    br = mutate(villa()[3], bounded_range={"low": 1.0, "high": 2.0, "basis": "x"})
    assert one(br)["category"] == "HELD_WITH_FIGURE"
    v = mutate(villa()[0], measured_net=None)                    # a valued word with no number
    assert one(v)["category"] == "HELD_WITH_FIGURE"


def test_range_needs_its_cause_and_its_net():
    s = villa()[2]
    assert one(mutate(s, bounded_range={"low": 5.0, "high": 6.0, "basis": ""}))["category"] == "RANGE_WITHOUT_CAUSE"
    assert one(mutate(s, rfi=None))["category"] == "RANGE_WITHOUT_CAUSE"
    assert one(mutate(s, bounded_range=None))["category"] == "RANGE_WITHOUT_CAUSE"
    assert one(mutate(s, bounded_range={"low": 6.0, "high": 5.0, "basis": "d"}))["category"] == "RANGE_WITHOUT_CAUSE"
    f = mutate(villa()[0], bounded_range={"low": 1.3, "high": 1.5, "basis": "convention"})
    res = one(f)
    assert res["category"] == "RANGE_EXCLUDES_NET" and res["severity"] == "REFUSED"
    assert one(mutate(villa()[0], bounded_range={"low": 1.2, "high": 1.5, "basis": "convention"}))["category"] == "OK"


def test_source_derived_names_its_source():
    r = villa()[1]
    assert one(mutate(r, documents=[]))["category"] == "SOURCE_NOT_NAMED"
    assert one(mutate(r, documents=[{"file": "S-01"}]))["category"] == "SOURCE_NOT_NAMED"
    # a PROVISIONAL line is not required to name a document
    assert one(mutate(r, evidence_state="PROVISIONAL", documents=[]))["category"] == "OK"


def test_formula_concluding_the_gross_is_flagged():
    p = ln("FIN.PAINT", "PX", ev="PROVISIONAL", q=40.0, unit="m2", gross=44.0,
           formula="11.0 m face x 4.0 m = 44.0 m2, less 1 opening(s) by their own area")
    res = one(p)
    assert (res["category"], res["severity"]) == ("FORMULA_FIGURE_DISAGREES", "FLAG")
    assert "(= gross 44.0)" in res["detail"]
    ok = mutate(p, formula="11.0 m face x 4.0 m = 44.0 m2, less 1 opening(s) (net 40.0 m2)")
    assert one(ok)["category"] == "OK"
    h = ln("FIN.PAINT", "PH", ev="BOUNDED_EXPOSURE", unit="m2", bounded_range={"low": 48.94, "high": 52.29,
           "basis": "held openings bounded"}, rfi={"question": "door D3 width not printed"},
           formula="16.2 m face x 3.35 m = 54.27 m2, less 2 opening(s)")
    assert one(h)["category"] == "FORMULA_FIGURE_DISAGREES"
    blk = mutate(villa()[3], formula="held: waist not printed; 1.2 x 1.0 x 0.15 = 0.18 m3")
    assert one(blk)["category"] == "FORMULA_FIGURE_DISAGREES"


def test_unknown_state_and_severity_order():
    u = mutate(villa()[0], evidence_state="HELD")
    assert one(u)["category"] == "UNKNOWN_STATE"
    both = mutate(villa()[1], formula="held: ", documents=[])
    res = one(both)
    assert res["category"] == "VALUED_WITH_HELD_TEXT" and res["issues"] == "VALUED_WITH_HELD_TEXT SOURCE_NOT_NAMED"


def test_report_by_family_order_and_counts():
    v = villa()
    bad = v + [mutate(v[1], line_id="L-x1", formula="held: "),
               mutate(v[1], line_id="L-x2", formula="held: ", measured_net=10.0, location=dict(v[1]["location"],
                      element_id="R2", floor="1F")),
               mutate(v[4], line_id="L-x3", gross=7.6)]
    rep = C.check_lines(bad)
    assert (rep["refused"], rep["flagged"], C.exit_code(rep)) == (3, 0, 2)
    assert rep["by_kind"] == {"HELD_WITH_FIGURE": 1, "VALUED_WITH_HELD_TEXT": 2}
    fam = {(f["item_code"], f["evidence_state"]): f for f in rep["families"]}
    rb = fam[("STR.REBAR", "SOURCE_DERIVED")]
    assert (rb["lines"], rb["ok"], rb["refused"], rb["findings_net"]) == (3, 1, 2, 26.5168)
    shuffled = list(bad)
    random.Random(7).shuffle(shuffled)
    assert C.check_lines(shuffled)["findings"] == rep["findings"]
    with pytest.raises(C.LineStateError):
        C.check_lines(v + [v[0]])
    with pytest.raises(C.LineStateError):
        C.assert_exportable(bad)


# ---- command line and the guarded export ------------------------------------------------------------------------------

def _write(tmp_path, lines, name="lines.json"):
    p = tmp_path / name
    p.write_text(json.dumps(lines, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def test_cli_check_writes_report_and_csv(tmp_path):
    p = _write(tmp_path, villa() + [mutate(villa()[1], line_id="L-x1", formula="held: ")])
    j, c = tmp_path / "r.json", tmp_path / "r.csv"
    assert C.main(["check", "--lines", str(p), "--json", str(j), "--csv", str(c)]) == 2
    rep = json.loads(j.read_text(encoding="utf-8"))
    assert rep["schema"] == C.SCHEMA and rep["refused"] == 1 and rep["findings"][0]["line_id"] == "L-x1"
    rows = c.read_text(encoding="utf-8").splitlines()
    assert rows[0].split(",")[:8] == ["line_id", "trade", "item_code", "floor", "element_id", "unit", "evidence_state",
                                      "category"]
    assert len(rows) == 2 and ",VALUED_WITH_HELD_TEXT,REFUSED," in rows[1]
    flag = villa() + [ln("FIN.PAINT", "PX", ev="PROVISIONAL", q=40.0, unit="m2", gross=44.0,
                         formula="11.0 m x 4.0 m = 44.0 m2, less 1 opening")]
    assert C.main(["check", "--lines", str(_write(tmp_path, flag, "f.json"))]) == 1
    assert C.main(["check", "--lines", str(_write(tmp_path, villa(), "ok.json"))]) == 0


def test_guarded_export_refuses_and_writes_nothing(tmp_path, capsys):
    p = _write(tmp_path, villa() + [mutate(villa()[1], line_id="L-x1", formula="held: ")])
    out = tmp_path / "export"
    assert C.main(["export", "--lines", str(p), "--candidate-version", CVER, "--out", str(out),
                   "--code-commit", "abc1234"]) == 2
    assert not out.exists()
    assert "VALUED_WITH_HELD_TEXT" in capsys.readouterr().err


def test_guarded_export_delegates_unchanged_when_clean(tmp_path):
    from tools import boq_export_v1 as X
    p = _write(tmp_path, villa())
    a, b = tmp_path / "guarded", tmp_path / "plain"
    common = ["--lines", str(p), "--candidate-version", CVER, "--code-commit", "abc1234"]
    assert C.main(["export", *common, "--out", str(a)]) == 0
    assert X.main([*common, "--out", str(b)]) == 0
    for name in ("BOQ.csv", "BOQ_ENGINE_UNITS.csv"):
        assert (a / name).read_bytes() == (b / name).read_bytes()


def test_usage_without_subcommand():
    assert C.main([]) == 64
