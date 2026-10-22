"""T-177: tools/scoreboard_v2.py (the SCOREBOARD v2 columns by script) on a hand-calculated synthetic villa that is
not the development villa, with held, bounded, conditional, excluded, unit-refused and silent lines.

Hand calculation (written before running the tool):
  CONCRETE m3, 4 reference lines
    FOOT ref 20.0: L1 FOOTING 10.0 (SOURCE_DERIVED) + L2 STRAP 9.0 (PROVISIONAL)       = 19.0 compared, err -1.0
    SLAB ref  8.0: L3 BLOCKED_RFI bounded 2.0 .. 3.0; L4 BOUNDED_EXPOSURE (net 5.0) bounded 4.0 .. 6.5;
                   L5 BLOCKED_RFI no bound; L6 SLAB SOURCE_DERIVED 1.5 (released part)  HELD
    BEAM ref 10.0: L7 BEAM MEASURED 10.4                                                 compared, err +0.4
    COL  ref  5.0: L8 COLUMN PROVISIONAL without measured_net, bound {low 1.0, high None} HELD, UNKNOWN (incomplete)
    coverage 4/4 = 100.00; compared 2; WAPE (1.0 + 0.4) / 30 = 4.67 %; signed (-1.0 + 0.4) / 30 = -2.00 %
    held: 2 ref lines; engine lines L3 L4 L5 L8 = 2 bounded (2.0 + 4.0) .. (3.0 + 6.5) = 6.000 .. 9.500 + 2 UNKNOWN;
          released part L6 1 line 1.5 m3 (JSON only, never compared)
    verdicts: FOOT re-measure WHOLE, engine 19.0, checker 19.1 (+0.53 %)  -> COUNTED
              BEAM re-measure WHOLE, engine 10.0 (this run 10.4)          -> STALE
              SLAB re-measure WHOLE                                       -> LINE_NOT_COMPARED (HELD)
              COL  RULE_DIFFERENCE WHOLE                                  -> counted
              FOOT PARTIAL re-measure                                     -> listed, not counted
    verified 1 / 4 = 25.00; rule difference 1 / 4 = 25.00
  PAINT m2:   WALL ref 50.0: L9 NOT_APPLICABLE_WITH_EVIDENCE (excluded), L10 BLOCKED_RFI no bound      HELD
              -> "1 ref line HELD; 1 engine line: 1 UNKNOWN (no bound); 1 more excluded with reason"
  FLOOR m2:   FLR ref 35.0: L11 PORCELAIN 30.0 MEASURED + 1 CONDITIONAL set holding PORCELAIN         HELD
  WINDOWS m2: WIN ref 12.0: L12 ARCH.WINDOW 1 pcs                                                 unit refused
  CEILING m2: CEIL ref 9.0: no engine line                                                       silent omission
"""

from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from tools import alsenan_keymap as K
from tools import scoreboard_v2 as V

TOL = 1e-9
M = V.REMEASURE_METHOD


def line(lid, code, unit, ev, net, element, br=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "evidence_state": ev, "measured_net": net,
            "bounded_range": br, "trade": "X", "location": {"element_id": element}}


def lines():
    return [
        line("L1", "STR.CONC.FOOTING", "m3", "SOURCE_DERIVED", 10.0, "F1"),
        line("L2", "STR.CONC.STRAP", "m3", "PROVISIONAL", 9.0, "S1"),
        line("L3", "STR.CONC.SLAB", "m3", "BLOCKED_RFI", None, "SL1", {"low": 2.0, "high": 3.0}),
        line("L4", "STR.CONC.SLAB", "m3", "BOUNDED_EXPOSURE", 5.0, "SL2", {"low": 4.0, "high": 6.5}),
        line("L5", "STR.CONC.SLAB", "m3", "BLOCKED_RFI", None, "SL3"),
        line("L6", "STR.CONC.SLAB", "m3", "SOURCE_DERIVED", 1.5, "SL4"),
        line("L7", "STR.CONC.BEAM", "m3", "MEASURED", 10.4, "B1"),
        line("L8", "STR.CONC.COLUMN", "m3", "PROVISIONAL", None, "C1", {"low": 1.0, "high": None}),
        line("L9", "FIN.PAINT", "m2", "NOT_APPLICABLE_WITH_EVIDENCE", None, "R1:paint"),
        line("L10", "FIN.PAINT", "m2", "BLOCKED_RFI", None, "R2:paint"),
        line("L11", "FIN.FLOOR.PORCELAIN", "m2", "MEASURED", 30.0, "R1:floor"),
        line("L12", "ARCH.WINDOW", "pcs", "SOURCE_DERIVED", 1.0, "W1"),
    ]


def release_report():
    return {"categories": {"CONDITIONAL": {"scenario_sets": [
        {"set_id": "REVIEW:X1", "by_scenario": {"DRY": {"FIN.FLOOR.PORCELAIN [m2]": 4.0}, "WET": {}}}]}}}


def rec(rid, unit, qty):
    return {"id": rid, "unit": unit, "qty": qty, "row_kind": "COVER_TOTAL", "trade": "T"}


def normalised():
    return {"records": [rec("R-FOOT", "m3", 20.0), rec("R-SLAB", "m3", 8.0), rec("R-BEAM", "m3", 10.0),
                        rec("R-COL", "m3", 5.0), rec("R-WALL", "m2", 50.0), rec("R-FLR", "m2", 35.0),
                        rec("R-WIN", "m2", 12.0), rec("R-CEIL", "m2", 9.0)]}


def key_map():
    return {"reference_row_kinds": ["COVER_TOTAL"], "keys": [
        {"key": "FOOT", "trade": "CONCRETE", "reference_id": "R-FOOT", "item_codes": ["STR.CONC.FOOTING", "STR.CONC.STRAP"]},
        {"key": "SLAB", "trade": "CONCRETE", "reference_id": "R-SLAB", "item_codes": ["STR.CONC.SLAB"]},
        {"key": "BEAM", "trade": "CONCRETE", "reference_id": "R-BEAM", "item_codes": ["STR.CONC.BEAM"]},
        {"key": "COL", "trade": "CONCRETE", "reference_id": "R-COL", "item_codes": ["STR.CONC.COLUMN"]},
        {"key": "WALL", "trade": "PAINT", "reference_id": "R-WALL", "item_codes": ["FIN.PAINT"]},
        {"key": "FLR", "trade": "FLOOR_AREA", "reference_id": "R-FLR", "item_codes": ["FIN.FLOOR.PORCELAIN"],
         "conditional_items": ["FIN.FLOOR.PORCELAIN [m2]"]},
        {"key": "WIN", "trade": "WINDOWS", "reference_id": "R-WIN", "item_codes": ["ARCH.WINDOW"]},
        {"key": "CEIL", "trade": "CEILING", "reference_id": "R-CEIL", "item_codes": ["FIN.CEILING"]}]}


def vd(ref_id, kind, scope="WHOLE", **kw):
    d = {"ref_id": ref_id, "kind": kind, "scope": scope, "source": "BOARD note X", "commit": "abc1234"}
    if kind == "REMEASURE":
        d["method"] = M
    d.update(kw)
    return d


def verdicts():
    return {"schema": V.VERDICTS_SCHEMA, "verdicts": [
        vd("R-FOOT", "REMEASURE", unit="m3", engine_qty=19.0, checker_qty=19.1),
        vd("R-BEAM", "REMEASURE", unit="m3", engine_qty=10.0, checker_qty=10.0),
        vd("R-SLAB", "REMEASURE", unit="m3", engine_qty=8.0, checker_qty=8.0),
        vd("R-COL", "RULE_DIFFERENCE"),
        vd("R-FOOT", "REMEASURE", "PARTIAL", unit="m3", checker_qty=10.0),
        vd("R-WALL", "RULE_DIFFERENCE", "PARTIAL")]}


def write_run(tmp_path, ls=None, name="run"):
    d = tmp_path / name
    d.mkdir()
    (d / "BOQ_LINES.json").write_text(json.dumps(ls if ls is not None else lines()), encoding="utf-8")
    (d / "BOQ_RELEASE_REPORT.json").write_text(json.dumps(release_report()), encoding="utf-8")
    return d


def side(ls=None, vdoc=None):
    return V.score_side(ls if ls is not None else lines(), release_report(), normalised(), key_map(),
                        vdoc if vdoc is not None else verdicts(), "BASE")


def row(s, trade, unit):
    return next(r for r in s["rows"] if r["trade"] == trade and r["unit"] == unit)


def cells(r):
    return dict(zip(V.COLUMNS, r["cells"]))


def test_concrete_hand_values():
    s = side()
    r = row(s, "CONCRETE", "m3")
    c = cells(r)
    assert c["Ref lines"] == "4" and c["Coverage %"] == "100.00" and c["Compared"] == "2"
    assert c["WAPE %"] == "4.67" and c["Signed %"] == "-2.00"
    assert r["held_ref_lines"] == 2 and r["bounded_lines"] == 2 and r["unknown_lines"] == 2
    assert abs(r["bounded_low"] - 6.0) < TOL and abs(r["bounded_high"] - 9.5) < TOL
    assert c["Held or UNKNOWN"] == "2 ref lines HELD; 4 engine lines: 2 bounded 6.000 .. 9.500 m3 + 2 UNKNOWN (no bound)"
    assert r["released_part_lines"] == 1 and abs(r["released_part_qty"] - 1.5) < TOL


def test_incomplete_bound_is_unknown_never_zero():
    r = row(side(), "CONCRETE", "m3")
    # L8 has low 1.0 and no high: it is UNKNOWN, its 1.0 never enters the bounded sum
    assert abs(r["bounded_low"] - 6.0) < TOL
    assert "0.000" not in cells(r)["Held or UNKNOWN"]


def test_verified_share_counts_only_whole_current_remeasures():
    s = side()
    c = cells(row(s, "CONCRETE", "m3"))
    assert c["Verified share %"] == "25.00 (1 / 4); 1 partial re-measure not counted"
    reasons = {(a["ref_id"], a["kind"], a["reason"].split(" ")[0]) for a in s["verdict_audit"]}
    assert ("R-FOOT", "REMEASURE", "COUNTED") in reasons
    assert ("R-BEAM", "REMEASURE", "STALE") in reasons
    assert ("R-SLAB", "REMEASURE", "LINE_NOT_COMPARED") in reasons
    assert ("R-FOOT", "REMEASURE", "PARTIAL_SCOPE") in reasons


def test_rule_difference_share_and_not_yet_measured():
    s = side()
    assert cells(row(s, "CONCRETE", "m3"))["Rule difference share %"] == "25.00 (1 / 4)"
    assert cells(row(s, "PAINT", "m2"))["Rule difference share %"] == \
        "NOT YET MEASURED (1 partial rule verdict not counted)"
    assert cells(row(s, "CEILING", "m2"))["Rule difference share %"] == "NOT YET MEASURED"


def test_no_rule_difference_assessment_gives_zero_share():
    vdoc = verdicts()
    vdoc["verdicts"].append(vd("R-FLR", "NO_RULE_DIFFERENCE"))
    assert cells(row(side(vdoc=vdoc), "FLOOR_AREA", "m2"))["Rule difference share %"] == "0.00 (0 / 1)"


def test_discrepancy_above_one_percent_is_not_verified():
    vdoc = verdicts()
    vdoc["verdicts"][0]["checker_qty"] = 19.5          # +2.6 % against the engine's 19.0
    s = side(vdoc=vdoc)
    assert cells(row(s, "CONCRETE", "m3"))["Verified share %"].startswith("0.00 (0 / 4)")
    assert any(a["reason"].startswith("DISCREPANCY") for a in s["verdict_audit"])


def test_verdict_in_another_unit_is_not_transferred():
    vdoc = verdicts()
    vdoc["verdicts"][0]["unit"] = "m2"
    s = side(vdoc=vdoc)
    assert any(a["ref_id"] == "R-FOOT" and a["reason"] == "UNIT_DIFFERS" for a in s["verdict_audit"])


def test_paint_excluded_and_floor_conditional():
    s = side()
    assert cells(row(s, "PAINT", "m2"))["Held or UNKNOWN"] == \
        "1 ref line HELD; 1 engine line: 1 UNKNOWN (no bound); 1 more excluded with reason"
    f = row(s, "FLOOR_AREA", "m2")
    assert cells(f)["Held or UNKNOWN"] == "1 ref line HELD; 1 conditional review set, quantity UNKNOWN (no bound)"
    assert f["released_part_lines"] == 1 and abs(f["released_part_qty"] - 30.0) < TOL
    assert cells(f)["WAPE %"] == "NOT YET MEASURED"


def test_unit_refused_and_silent_are_not_yet_measured():
    s = side()
    w = cells(row(s, "WINDOWS", "m2"))
    assert w["Coverage %"] == "0.00"
    assert w["Held or UNKNOWN"] == "NOT YET MEASURED (unit refused: the engine answers WIN in pcs, the reference in m2)"
    assert cells(row(s, "CEILING", "m2"))["Held or UNKNOWN"] == \
        "NOT YET MEASURED (silent omission: no engine line answers CEIL)"


def test_row_order_does_not_change_the_table():
    ls = lines()
    random.Random(7).shuffle(ls)
    a = V.markdown({"sides": [side()]})
    b = V.markdown({"sides": [side(ls)]})
    assert a == b


@pytest.mark.parametrize("mutate, msg", [
    (lambda d: d.update(schema="X"), "schema"),
    (lambda d: d["verdicts"].append(vd("R-NONE", "RULE_DIFFERENCE")), "not in the reference"),
    (lambda d: d["verdicts"].append(vd("R-FLR", "AGREES")), "kind"),
    (lambda d: d["verdicts"].append(vd("R-FLR", "RULE_DIFFERENCE", "SOME")), "scope"),
    (lambda d: d["verdicts"].append(vd("R-FLR", "RULE_DIFFERENCE", source="")), "source"),
    (lambda d: d["verdicts"].append(vd("R-FLR", "REMEASURE", unit="m2", engine_qty=30.0, checker_qty=30.0,
                                       method="FREELANCER_AGREEMENT")), "freelancer"),
    (lambda d: d["verdicts"].append(vd("R-FLR", "REMEASURE", unit="m2", checker_qty=30.0)), "engine_qty"),
    (lambda d: d["verdicts"].append(vd("R-COL", "NO_RULE_DIFFERENCE")), "second whole-scope"),
])
def test_bad_verdicts_are_refused(mutate, msg):
    vdoc = verdicts()
    mutate(vdoc)
    with pytest.raises(ValueError, match=msg):
        side(vdoc=vdoc)


def test_candidate_side_beside_base_release_report(tmp_path):
    run = write_run(tmp_path)
    cand = copy.deepcopy(lines())
    for ln in cand:
        if ln["line_id"] in ("L3", "L4", "L5"):
            ln.update(evidence_state="SOURCE_DERIVED", measured_net=2.0, bounded_range=None)
    cp = tmp_path / "V3_0_9_BOQ_LINES.json"
    cp.write_text(json.dumps(cand), encoding="utf-8")
    res = V.build(run, "BASE", normalised(), key_map(), verdicts(), cp, "CAND")
    assert [s["label"] for s in res["sides"]] == ["BASE", "CAND"]
    cand_c = cells(row(res["sides"][1], "CONCRETE", "m3"))
    # SLAB 2.0 x 3 + 1.5 = 7.5 compared against 8.0: WAPE (1.0 + 0.5 + 0.4) / 38 = 5.00 %; signed -1.1 / 38 = -2.89 %
    assert cand_c["Compared"] == "3" and cand_c["WAPE %"] == "5.00" and cand_c["Signed %"] == "-2.89"
    assert cand_c["Baseline"] == f"CAND, V3_0_9_BOQ_LINES.json {hashlib.sha256(cp.read_bytes()).hexdigest()[:8]}"
    # the base release report still holds the floor in the candidate
    assert "conditional review set" in cells(row(res["sides"][1], "FLOOR_AREA", "m2"))["Held or UNKNOWN"]
    md = V.markdown(res, "2026-01-01 00:00 UTC").splitlines()
    assert md[0] == "## SCOREBOARD v2 2026-01-01 00:00 UTC"
    assert md[2] == "| " + " | ".join(V.COLUMNS) + " |"
    conc = [m for m in md if m.startswith("| CONCRETE | m3 |")]
    assert conc[0].split(" | ")[2].startswith("BASE") and conc[1].split(" | ")[2].startswith("CAND")
    with pytest.raises(ValueError, match="label"):
        V.build(run, "BASE", normalised(), key_map(), verdicts(), cp, "")


def _manifest(run, lines_sha):
    man = {"run": {"outputs_sha256": {"BOQ_LINES.json": lines_sha, "BOQ_LINES.csv": "c" * 64}}}
    (run / "BASELINE_MANIFEST.json").write_text(json.dumps(man), encoding="utf-8")


def test_manifest_provenance_and_drift_refused(tmp_path):
    run = write_run(tmp_path)
    good = hashlib.sha256((run / "BOQ_LINES.json").read_bytes()).hexdigest()
    _manifest(run, good)
    res = V.build(run, "A (released X)", normalised(), key_map(), verdicts())
    mh = hashlib.sha256((run / "BASELINE_MANIFEST.json").read_bytes()).hexdigest()[:8]
    assert cells(res["sides"][0]["rows"][0])["Baseline"] == f"A (released X), manifest {mh}, BOQ_LINES.csv cccccccc"
    _manifest(run, "0" * 64)
    with pytest.raises(ValueError, match="differs from the manifest"):
        V.build(run, "A", normalised(), key_map(), verdicts())


def _keymap_cli(tmp_path, run, extra, name):
    inputs = tmp_path / "in"
    inputs.mkdir(exist_ok=True)
    for n, d in (("ref.json", normalised()), ("km.json", key_map()), ("v.json", verdicts())):
        (inputs / n).write_text(json.dumps(d), encoding="utf-8")
    out = tmp_path / name
    args = ["--run", str(run), "--reference", str(inputs / "ref.json"), "--key-map", str(inputs / "km.json"),
            "--out", str(out)]
    K.main(args + [a.replace("@V", str(inputs / "v.json")).replace("@T", str(tmp_path)) for a in extra])
    return out.read_bytes()


def test_keymap_v1_output_byte_identical_with_v2_options(tmp_path):
    run = write_run(tmp_path)
    plain = _keymap_cli(tmp_path, run, [], "v1a.json")
    with_v2 = _keymap_cli(tmp_path, run, ["--v2-out", "@T/v2.json", "--v2-markdown", "@T/v2.md",
                                          "--v2-label", "BASE", "--v2-verdicts", "@V"], "v1b.json")
    assert plain == with_v2
    v2 = json.loads((tmp_path / "v2.json").read_text(encoding="utf-8"))
    assert v2["SCHEMA"] == V.SCHEMA and v2["columns"] == list(V.COLUMNS)
    assert (tmp_path / "v2.md").read_text(encoding="utf-8") == V.markdown(v2)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["in", "run", "v1a.json", "v1b.json", "v2.json", "v2.md"]


def test_keymap_v2_options_need_v2_out(tmp_path):
    run = write_run(tmp_path)
    with pytest.raises(SystemExit):
        _keymap_cli(tmp_path, run, ["--v2-label", "BASE"], "x.json")
    with pytest.raises(SystemExit):
        _keymap_cli(tmp_path, run, ["--v2-out", "@T/v2.json"], "y.json")


def test_committed_dev_villa_verdict_file_is_valid():
    root = Path(__file__).resolve().parents[2]
    doc = json.loads((root / "research/agents_t177/CHECKER_VERDICTS_DEV_VILLA.json").read_text(encoding="utf-8"))
    km = json.loads((root / "tests/alsenan/T001B_KEY_MAP.json").read_text(encoding="utf-8"))
    vs = V.load_verdicts(doc, {k["reference_id"] for k in km["keys"]})
    assert vs and all(v["kind"] != "REMEASURE" or v["method"] == M for v in vs)
