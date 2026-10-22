"""T-182: the five-measures layout of tools/scoreboard_v2.py (owner scoreboard review 2026-10-22) on the T-177
synthetic villa (not the development villa). Hand calculation written before running the tool:

  CONCRETE m3, 4 reference lines (freelancer FOOT 20.0, SLAB 8.0, BEAM 10.0, COL 5.0)
    engine: FOOT 19.0 compared, SLAB HELD, BEAM 10.4 compared, COL HELD
    checker whole re-measures (T-177 verdicts): FOOT 19.1 (engine 19.0, counted), BEAM 10.0 (verdict made on engine
      10.0, this run 10.4: STALE), SLAB 8.0 (line HELD)
    1 Coverage        4 / 4 answered                                   -> "100.00 (4 / 4)"
    2 Verified        FOOT only                                        -> "1 / 4 (25.00 %); 1 partial re-measure ..."
    3 Accuracy lines  FOOT |19.0 - 19.1| = 0.1 (signed -0.1), BEAM |10.4 - 10.0| = 0.4 (signed +0.4, 4.0 % > 1 %,
                      stale: INCLUDED); SLAB checker 8.0 but no engine quantity: listed, not counted
      sizes: FOOT 19.1, BEAM 10.0, SLAB 8.0 (checker); COL none (HELD, no checker quantity) -> size incomplete
      scope at most 29.1 / 37.1 = 78.44 %                            -> NOT YET MEASURED
      + a whole checker re-measure COL 5.0: size 42.1 complete, share 29.1 / 42.1 = 69.12 % >= 50 %
      WAPE (0.1 + 0.4) / 29.1 = 1.72 %; signed (-0.1 + 0.4) / 29.1 = +1.03 %
      with minimum 75 %: 69.12 % is below                             -> NOT YET MEASURED
    4 Freelancer variance (T-177 values) WAPE 4.67 %, signed -2.00 % on 2 / 4 compared
    5 Held or UNKNOWN (T-177 cell, unchanged)
  Candidate (SLAB L3 L4 L5 released at 2.0 each): SLAB 7.5 compared, checker 8.0: |0.5|, signed -0.5
      with COL 5.0: sum checker 19.1 + 10.0 + 8.0 = 37.1, size 42.1, share 88.12 %
      WAPE (0.1 + 0.4 + 0.5) / 37.1 = 2.70 %; signed (-0.1 + 0.4 - 0.5) / 37.1 = -0.54 %
"""

from __future__ import annotations

import copy
import json
import re

import pytest

from tools import scoreboard_v2 as V
from tests.t177_scoreboard_v2 import test_scoreboard_v2 as F

FIVE = V.LAYOUT_FIVE
ACC = "Accuracy vs independent (lines, scope share)"


def side(ls=None, vdoc=None, ref=None, min_scope=V.MIN_ACCURACY_SCOPE, label="BASE"):
    return V.score_side(ls if ls is not None else F.lines(), F.release_report(), ref if ref is not None else F.normalised(),
                        F.key_map(), vdoc if vdoc is not None else F.verdicts(), label, layout=FIVE,
                        min_scope=min_scope)


def with_col(vdoc=None):
    vdoc = vdoc if vdoc is not None else F.verdicts()
    vdoc["verdicts"].append(F.vd("R-COL", "REMEASURE", unit="m3", engine_qty=5.0, checker_qty=5.0))
    return vdoc


def cells(r):
    return dict(zip(V.COLUMNS_FIVE, r["cells"]))


def conc(s):
    return cells(F.row(s, "CONCRETE", "m3"))


def test_five_measure_cells_hand_values():
    c = conc(side())
    assert c["Coverage % (n / d)"] == "100.00 (4 / 4)"
    assert c["Verified n / d"] == "1 / 4 (25.00 %); 1 partial re-measure not counted"
    assert c[ACC] == ("NOT YET MEASURED (2 lines; scope at most 78.44 % = 29.100 / 37.100 m3: 1 ref line without a "
                      "quantity independent of the freelancer; 1 above 1 %; 1 stale; 1 checker-measured line HELD in "
                      "the engine, not counted)")
    assert c["Freelancer variance"] == "WAPE 4.67 %, signed -2.00 % (2 / 4 compared)"
    assert c["Held or UNKNOWN"] == "2 ref lines HELD; 4 engine lines: 2 bounded 6.000 .. 9.500 m3 + 2 UNKNOWN (no bound)"
    assert c["Rule difference share %"] == "25.00 (1 / 4)"


def test_accuracy_reported_when_scope_complete_and_above_minimum():
    s = side(vdoc=with_col())
    assert conc(s)[ACC] == ("WAPE 1.72 %, signed 1.03 % (2 lines; scope 69.12 % = 29.100 / 42.100 m3, minimum 50 %; "
                            "1 above 1 %; 1 stale; 2 checker-measured lines HELD in the engine, not counted)")
    a = F.row(s, "CONCRETE", "m3")["accuracy"]
    assert abs(a["wape"] - 0.5 / 29.1) < 1e-12 and abs(a["signed"] - 0.3 / 29.1) < 1e-12


def test_accuracy_below_minimum_is_not_yet_measured():
    c = conc(side(vdoc=with_col(), min_scope=0.75))
    assert c[ACC].startswith("NOT YET MEASURED (2 lines; scope 69.12 % = 29.100 / 42.100 m3, below the 75 % minimum")


def test_adverse_dropping_discrepant_line_would_change_accuracy():
    # the discrepant / stale BEAM re-measure stays in the accuracy figure: without it WAPE would be 0.1 / 19.1
    a = F.row(side(vdoc=with_col()), "CONCRETE", "m3")["accuracy"]
    assert a["lines"] == 2 and a["discrepant_lines"] == 1 and abs(a["sum_abs"] - 0.5) < 1e-12
    assert abs(a["wape"] - 0.1 / 19.1) > 1e-3


def test_unrelated_passed_checks_leave_verified_share_unchanged():
    before = conc(side())["Verified n / d"]
    vdoc = F.verdicts()
    vdoc["verdicts"] += [
        F.vd("R-BEAM", "NO_RULE_DIFFERENCE"),                                            # a passed rule check
        F.vd("R-BEAM", "REMEASURE", "PARTIAL", unit="m3", checker_qty=10.4),             # agrees, but partial
        F.vd("R-FLR", "REMEASURE", unit="m2", engine_qty=30.0, checker_qty=30.0),        # another trade's line
        F.vd("R-WALL", "RULE_DIFFERENCE")]                                               # another trade, rule kind
    s = side(vdoc=vdoc)
    assert conc(s)["Verified n / d"] == before.replace("1 partial re-measure", "2 partial re-measures")
    assert conc(s)["Verified n / d"].startswith("1 / 4 (25.00 %)")
    assert cells(F.row(s, "FLOOR_AREA", "m2"))["Verified n / d"].startswith("0 / 1 (0.00 %)")


def test_held_line_stays_held_with_a_checker_quantity():
    s = side(vdoc=with_col())
    c = conc(s)
    assert c["Held or UNKNOWN"] == conc(side())["Held or UNKNOWN"]
    au = {a["ref_id"]: a for a in s["accuracy_audit"]}
    assert au["R-SLAB"]["counted"] is False and au["R-SLAB"]["reason"].startswith("NO_RELEASED_ENGINE_QTY (HELD)")
    assert au["R-SLAB"]["engine_qty"] is None
    assert au["R-COL"]["counted"] is False
    assert au["R-FOOT"]["counted"] and au["R-BEAM"]["counted"] and "stale" in au["R-BEAM"]["reason"]


def test_smaller_freelancer_variance_does_not_change_accuracy():
    ref = F.normalised()
    for r in ref["records"]:
        if r["id"] == "R-FOOT":
            r["qty"] = 19.0                 # freelancer now equals the engine
        if r["id"] == "R-BEAM":
            r["qty"] = 10.4
    for vdoc in (F.verdicts(), with_col()):
        a, b = conc(side(vdoc=copy.deepcopy(vdoc))), conc(side(vdoc=copy.deepcopy(vdoc), ref=ref))
        assert b["Freelancer variance"] == "WAPE 0.00 %, signed 0.00 % (2 / 4 compared)"
        assert a["Freelancer variance"] != b["Freelancer variance"]
        assert a[ACC] == b[ACC]


def test_accuracy_needs_no_freelancer_quantity():
    ref = F.normalised()
    next(r for r in ref["records"] if r["id"] == "R-BEAM")["qty"] = None
    s = side(vdoc=with_col(), ref=ref)
    assert conc(s)[ACC].startswith("WAPE 1.72 %, signed 1.03 % (2 lines;")
    assert conc(s)["Freelancer variance"] == "WAPE 5.00 %, signed -5.00 % (1 / 4 compared)"


def test_no_independent_quantity_is_not_yet_measured():
    c = cells(F.row(side(), "PAINT", "m2"))
    assert c[ACC] == "NOT YET MEASURED (0 lines with an independent checker quantity)"
    assert c["Freelancer variance"] == "NOT YET MEASURED (0 / 1 compared)"
    w = cells(F.row(side(), "WINDOWS", "m2"))
    assert w["Coverage % (n / d)"] == "0.00 (0 / 1)"


def test_candidate_and_released_are_separate_rows(tmp_path):
    run = F.write_run(tmp_path)
    cand = copy.deepcopy(F.lines())
    for ln in cand:
        if ln["line_id"] in ("L3", "L4", "L5"):
            ln.update(evidence_state="SOURCE_DERIVED", measured_net=2.0, bounded_range=None)
    cp = tmp_path / "V3_0_9_BOQ_LINES.json"
    cp.write_text(json.dumps(cand), encoding="utf-8")
    res = V.build(run, "BASE", F.normalised(), F.key_map(), with_col(), cp, "CAND", layout=FIVE)
    assert res["columns"] == list(V.COLUMNS_FIVE) and res["layout"] == FIVE and res["min_accuracy_scope"] == 0.5
    base_c, cand_c = conc(res["sides"][0]), conc(res["sides"][1])
    assert base_c[ACC].startswith("WAPE 1.72 %, signed 1.03 % (2 lines; scope 69.12 %")
    assert cand_c[ACC].startswith("WAPE 2.70 %, signed -0.54 % (3 lines; scope 88.12 % = 37.100 / 42.100 m3")
    md = V.markdown(res, "2026-01-01 00:00 UTC")
    lines = md.splitlines()
    assert lines[0] == "## SCOREBOARD v2.1 2026-01-01 00:00 UTC"
    assert lines[2] == "| " + " | ".join(V.COLUMNS_FIVE) + " |"
    rows = [m for m in lines if m.startswith("| CONCRETE | m3 |")]
    assert len(rows) == 2 and rows[0].split(" | ")[2] == "BASE" and rows[1].split(" | ")[2].startswith("CAND")
    # the T-132 dashboard parser looks for '## SCOREBOARD v2 ' and must not read this table as the old format
    assert not re.search(r"^## SCOREBOARD v2 ", md, re.M)
    with pytest.raises(ValueError, match="never combined"):
        V.build(run, "BASE", F.normalised(), F.key_map(), F.verdicts(), cp, "BASE", layout=FIVE)


def test_default_layout_unchanged(tmp_path):
    run = F.write_run(tmp_path)
    res = V.build(run, "BASE", F.normalised(), F.key_map(), F.verdicts())
    assert "layout" not in res and res["columns"] == list(V.COLUMNS)
    assert all("accuracy" not in r for r in res["sides"][0]["rows"]) and "accuracy_audit" not in res["sides"][0]
    assert V.markdown(res, "X").splitlines()[0] == "## SCOREBOARD v2 X"


@pytest.mark.parametrize("bad", [0.0, -0.1, 1.5])
def test_bad_minimum_refused(bad):
    with pytest.raises(ValueError, match="minimum accuracy scope"):
        side(min_scope=bad)


def test_bad_layout_refused():
    with pytest.raises(ValueError, match="layout"):
        V.score_side(F.lines(), F.release_report(), F.normalised(), F.key_map(), F.verdicts(), "B", layout="X")


def test_keymap_five_measures_options(tmp_path):
    run = F.write_run(tmp_path)
    plain = F._keymap_cli(tmp_path, run, [], "v1a.json")
    five = F._keymap_cli(tmp_path, run, ["--v2-out", "@T/v2.json", "--v2-markdown", "@T/v2.md", "--v2-label", "BASE",
                                         "--v2-verdicts", "@V", "--v2-five-measures",
                                         "--v2-min-accuracy-scope", "0.6"], "v1b.json")
    assert plain == five
    v2 = json.loads((tmp_path / "v2.json").read_text(encoding="utf-8"))
    assert v2["columns"] == list(V.COLUMNS_FIVE) and v2["min_accuracy_scope"] == 0.6
    assert (tmp_path / "v2.md").read_text(encoding="utf-8") == V.markdown(v2)
    with pytest.raises(SystemExit):
        F._keymap_cli(tmp_path, run, ["--v2-out", "@T/x.json", "--v2-label", "B", "--v2-verdicts", "@V",
                                      "--v2-min-accuracy-scope", "0.6"], "y.json")
    with pytest.raises(SystemExit):
        F._keymap_cli(tmp_path, run, ["--v2-five-measures"], "z.json")


def test_scoreboard_cli_five(tmp_path):
    run = F.write_run(tmp_path)
    d = tmp_path / "in"
    d.mkdir()
    for n, doc in (("ref.json", F.normalised()), ("km.json", F.key_map()), ("v.json", with_col())):
        (d / n).write_text(json.dumps(doc), encoding="utf-8")
    base = ["--run", str(run), "--label", "BASE", "--reference", str(d / "ref.json"), "--key-map", str(d / "km.json"),
            "--verdicts", str(d / "v.json"), "--out", str(tmp_path / "o.json")]
    assert V.main(base + ["--layout", "five", "--heading", "H"]) == 0
    o = json.loads((tmp_path / "o.json").read_text(encoding="utf-8"))
    assert o["layout"] == FIVE
    with pytest.raises(SystemExit):
        V.main(base + ["--min-accuracy-scope", "0.6"])
