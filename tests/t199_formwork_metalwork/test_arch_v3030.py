"""T-199: ARCH_TAKEOFF_V3.0.30 (formwork and railings / shutters as their own line families, from checker-merged
ledgers) on a hand-calculated NON-Alsenan villa (V199), normal and adverse.

Villa V199, by hand (a formed face is a concrete surface cast against a form; it bounds ONE member):
  B1 suspended beam 3.00 x 0.20 x 0.60 under a 0.15 slab: soffit 3.00 x 0.20 = 0.600; sides 2 x 3.00 x (0.60 - 0.15)
     = 2.700 -> method G 3.300 m2 (faces F-B1-S, F-B1-L, F-B1-R); element method E (sides at full depth) 4.200 is the
     COMPARISON only, never a second line
  C1 column 0.30 x 0.30, clear height 3.00: 4 x 0.30 x 3.00 = 3.600 m2 (E = G); its beam joint J-C1 HELD 0 .. 0.270
  S1 slab 4.00 x 3.00 soffit less the beam soffit 3.00 x 0.20: 12.000 - 0.600 = 11.400 m2 (G)
  F1 footing 1.20 x 1.20 x 0.40 below the existing ground: sides 4 x 1.20 x 0.40 = 1.920 FORMED or 0 EARTH_CAST
     (owner question OQ-10 open): ONE blank line, both figures beside it, never summed
  ST1 stair: waist soffit 1.10 x 3.00 = 3.300 (G) + void side 0.850 (T-352-type side face) ; wall side HELD 0 .. 0.850
  P1 parapet face with no concrete line: HELD 1.200 .. 2.000, blank
  railings: R1 roof guard 3.000 + 2.500 = 5.500 lm (VERIFIED by the Checker); R2 stair guard on the pitch line
     sqrt(2.70^2 + 1.50^2) = 3.0887 -> 3.089 lm (never the 2.700 plan); R3 HELD: 2.000 lm measured + a turn not
     dimensioned -> blank; W1 shutters 2 leaves (pcs), area HELD
  totals: STR.FORMWORK 3.300 + 3.600 + 11.400 = 18.300 m2; STR.FORMWORK.STAIR 3.300 + 0.850 = 4.150 m2;
  MET.RAILING.GUARD 5.500 lm; FIN.RAILING 3.089 lm; ARCH.SHUTTER 2 pcs. Every V3.0.29 line byte-identical.
"""
from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3030 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-v199", "e" * 64
DOCS = [{"file": "v199_structural.dxf", "sha256": "c" * 64}]
SRC = [{"task": "T-332", "file": "research/v199/fill.csv", "sha256": "1" * 64, "merge_commit": "a" * 40,
        "checker_run": "checker run 20 (Gate A PASS)"},
       {"task": "T-352", "file": "research/v199/stairs.csv", "sha256": "2" * 64, "merge_commit": "b" * 40,
        "checker_run": "checker run 21 (Gate A PASS)"},
       {"task": "T-164", "file": "research/v199/rails.csv", "sha256": "3" * 64, "merge_commit": "c" * 40,
        "checker_run": "checker run 22 (Gate A PASS)"}]


def _line(code, eid, ev, net=None, unit="m3", floor="GF"):
    kw = {"rfi": {"question": "held"}} if ev == "BLOCKED_RFI" else {}
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=eid, floor=floor, physical_element=eid,
                        formula=f"{eid} {net}", documents=DOCS, rule_id="R", rule_version="1", notes="v199", **kw)


def lines_3029():
    return [_line("STR.CONC.BEAM", "B1", "SOURCE_DERIVED", 0.27),
            _line("STR.CONC.COLUMN", "C1", "PROVISIONAL", 0.27),
            _line("STR.CONC.SLAB", "S1", "SOURCE_DERIVED", 1.8),
            _line("STR.CONC.FOOTING", "F1", "SOURCE_DERIVED", 0.576, floor="FDN"),
            _line("STR.CONC.STAIR", "ST1", "SOURCE_DERIVED", 0.9),
            _line("STR.CONC.STAIR", "ST2", "BLOCKED_RFI"),
            _line("FIN.RAILING", "GF-ST1:railing", "BLOCKED_RFI", unit="lm")]


def _id(lines, eid):
    return next(ln["line_id"] for ln in lines if ln["location"]["element_id"] == eid)


def _bound(lines):
    out = []
    for ln in lines:
        if ln["item_code"].startswith("STR.CONC."):
            out.append({"line_id": ln["line_id"], "item_code": ln["item_code"],
                        "element_id": ln["location"]["element_id"], "evidence_state": ln["evidence_state"],
                        "measured_net": ln["measured_net"], "bounded_low": None, "bounded_high": None,
                        "floor": ln["location"]["floor"]})
    return out


def _fw(lines, eid, st, meth, m2, ids, **kw):
    r = {"line_id": _id(lines, eid), "item_code": next(x["item_code"] for x in lines if x["location"]["element_id"]
                                                         == eid),
         "line_state": next(x["evidence_state"] for x in lines if x["location"]["element_id"] == eid),
         "status": st, "alternative": None, "method": meth, "faces": len(ids), "m2": m2, "lo": None, "hi": None,
         "held_from": None, "bound_classes": f"VALUE {len(ids)}", "face_ids": ids, "source_task": "T-332"}
    r.update(kw)
    return r


def doc(lines=None):
    lines = lines or lines_3029()
    return {
        "schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": copy.deepcopy(SRC),
        "downgrade_bound_lines": [],
        "bound_concrete_lines": _bound(lines),
        "formwork": [_fw(lines, "B1", "CALCULATED", "G", 3.3, ["F-B1-S", "F-B1-L", "F-B1-R"]),
                     _fw(lines, "C1", "CALCULATED", "E=G", 3.6, ["F-C1-1", "F-C1-2", "F-C1-3", "F-C1-4"]),
                     _fw(lines, "C1", "HELD", "G", None, ["J-C1"], lo=0.0, hi=0.27, bound_classes="RANGE 1"),
                     _fw(lines, "S1", "CALCULATED", "G", 11.4, ["F-S1"]),
                     _fw(lines, "ST1", "CALCULATED", "G", 3.3, ["F-ST1-W"])],
        "alternatives": [{"line_id": _id(lines, "F1"), "method": "E=G", "item_code": "STR.CONC.FOOTING",
                          "line_state": "SOURCE_DERIVED", "source_task": "T-332",
                          "alternatives": {"OQ10_FORMED": {"m2": 1.92, "faces": 1, "face_ids": ["F-F1-FORMED"]},
                                           "OQ10_EARTH_CAST": {"m2": 0.0, "faces": 1, "face_ids": ["F-F1-EARTH"]}}}],
        "comparison_e_m2": {_id(lines, "B1"): 4.2},
        "not_applicable": [],
        "untied": [{"face_id": "P1-RC", "element": "PARAPET", "floor": "+9.70", "item": "parapet cast faces",
                    "tie": "NO_LINE", "method": "G", "alternative": None, "lo": 1.2, "hi": 2.0, "held_from": None,
                    "reason": "parapet RC has no concrete line", "source_task": "T-332"}],
        "named_not_lines": [{"face_id": "F-S1-SCEN", "why": "S1 scenario face", "class": "SCENARIO_NOT_IN_CANDIDATE"}],
        "stair_sides": [{"line_id": _id(lines, "ST1"), "item_code": "STR.CONC.STAIR", "line_state": "SOURCE_DERIVED",
                         "status": "CALCULATED", "faces": 1, "m2": 0.85, "lo": None, "hi": None,
                         "face_ids": ["SS-1"], "source_task": "T-352", "notes": []},
                        {"line_id": _id(lines, "ST1"), "item_code": "STR.CONC.STAIR", "line_state": "SOURCE_DERIVED",
                         "status": "HELD", "faces": 1, "m2": None, "lo": 0.0, "hi": 0.85,
                         "face_ids": ["SS-2"], "source_task": "T-352", "notes": []}],
        "railings": [{"run": "R1", "kind": "ROOF_GUARD", "status": "DRAWING-CONFIRMED", "verified": True, "lm": 5.5,
                      "measured_part_lm": None, "unmeasured_segments": 0, "height_printed_m": 1.1,
                      "segments": [{"segment": "street edge", "lm": 3.0, "status": "DRAWING-CONFIRMED"},
                                   {"segment": "return", "lm": 2.5, "status": "DRAWING-CONFIRMED"}],
                      "source": "roof plan band", "note": "", "source_task": "T-164"},
                     {"run": "R2", "kind": "STAIR_GUARD", "status": "DRAWING-CONFIRMED", "verified": False,
                      "lm": 3.089, "measured_part_lm": None, "unmeasured_segments": 0, "height_printed_m": None,
                      "segments": [{"segment": "flight pitch line", "lm": 3.089, "status": "DRAWING-CONFIRMED"}],
                      "source": "plan + section", "note": "", "source_task": "T-164"},
                     {"run": "R3", "kind": "STAIR_GUARD", "status": "HELD", "verified": False, "lm": None,
                      "measured_part_lm": 2.0, "unmeasured_segments": 1, "height_printed_m": None,
                      "segments": [{"segment": "flight", "lm": 2.0, "status": "HELD"},
                                   {"segment": "turn", "lm": None, "status": "HELD"}],
                      "source": "plan", "note": "turn not dimensioned", "source_task": "T-164"}],
        "shutters": [{"opening": "W1", "pcs": 2, "leaf_size_m": "(0.60, 1.50)", "status": "DRAWING-CONFIRMED (count)",
                      "m2": None, "m2_state": "HELD", "source": "elevation", "source_task": "T-164"}]}


def run(d=None, lines=None):
    lines = lines or lines_3029()
    inp = A.load_inputs(d or doc(lines), PID)
    ch, log = A.changes_for(inp, lines)
    out, ident = A.integrate(lines, ch)
    return lines, ch, log, out, ident


def _by(out, code, unit=None):
    return [ln for ln in out if ln["item_code"] == code and (unit is None or ln["unit"] == unit)]


# ------------------------------------------------------------------------------------------------ normal
def test_hand_totals_and_states():
    lines, ch, log, out, ident = run()
    fw = ident["formwork_metalwork"]
    assert fw["valued"] == {"ARCH.SHUTTER|pcs": 2, "FIN.RAILING|lm": 3.089, "MET.RAILING.GUARD|lm": 5.5,
                            "STR.FORMWORK.STAIR|m2": 4.15, "STR.FORMWORK|m2": 18.3}
    assert abs(math.hypot(2.7, 1.5) - 3.089) < 0.0005          # the pitch line, never the 2.700 plan
    assert fw["blank"] == {"ARCH.SHUTTER|m2": 1, "FIN.RAILING|lm": 1, "STR.FORMWORK.STAIR|m2": 1,
                           "STR.FORMWORK|m2": 3}               # J-C1, OQ-10 F1, untied P1; SS-2; R3; W1 area
    assert fw["oq10_lines"] == 1 and fw["faces"] == 15
    assert ident["outside_rows_identical_to_v3_0_29"] == len(lines) and ident["replaced"] == 0
    assert out[:len(lines)] == lines


def test_valued_line_beside_its_concrete_line_with_its_state():
    lines, ch, log, out, ident = run()
    by = {ln["line_id"]: ln for ln in lines}
    for ln in _by(out, A.FW_CODE) + _by(out, A.FW_STAIR_CODE):
        rec = ln["calculation"]["inputs"][A.REC_KEY]
        if ln["evidence_state"] in ("SOURCE_DERIVED", "PROVISIONAL"):
            assert by[rec["concrete_line"]]["evidence_state"] == ln["evidence_state"]
            assert abs(rec["m2"] - ln["measured_net"]) < 1e-9
            assert rec["evidence_status"] == "CALCULATED" and rec["release_status"] == "NOT RELEASED"


def test_comparison_method_beside_never_a_line():
    lines, ch, log, out, ident = run()
    b1 = [ln for ln in _by(out, A.FW_CODE) if ln["calculation"]["inputs"][A.REC_KEY]["concrete_line"]
          == _id(lines, "B1")]
    assert len(b1) == 1 and b1[0]["measured_net"] == 3.3
    assert b1[0]["calculation"]["inputs"][A.REC_KEY]["comparison_method_e_m2"] == 4.2
    assert not any(ln["calculation"]["inputs"][A.REC_KEY].get("method") == "E" for ln in _by(out, A.FW_CODE))


def test_oq10_alternatives_blank_both_beside():
    lines, ch, log, out, ident = run()
    f1 = [ln for ln in _by(out, A.FW_CODE) if ln["calculation"]["inputs"][A.REC_KEY].get("status") == "ALTERNATIVE"]
    assert len(f1) == 1 and f1[0]["evidence_state"] == "BLOCKED_RFI" and f1[0]["measured_net"] is None
    alts = f1[0]["calculation"]["inputs"][A.REC_KEY]["alternatives"]
    assert alts["OQ10_FORMED"]["m2"] == 1.92 and alts["OQ10_EARTH_CAST"]["m2"] == 0.0
    assert "OQ-10" in f1[0]["rfi"]["question"]


def test_held_lines_blank_with_bounds_named():
    lines, ch, log, out, ident = run()
    for ln in out[len(lines):]:
        if ln["evidence_state"] == "BLOCKED_RFI":
            assert ln["measured_net"] is None and not ln.get("bounded_range") and ln["rfi"]["question"]
    p1 = [ln for ln in out if ln["location"]["element_id"] == "FW:FACE:P1-RC"][0]
    assert p1["calculation"]["inputs"][A.REC_KEY]["bounds"] == {"lo": 1.2, "hi": 2.0}


def test_railing_and_shutter_lines():
    lines, ch, log, out, ident = run()
    r1 = [ln for ln in out if ln["location"]["element_id"] == "RAIL:R1"][0]
    assert r1["item_code"] == A.RAIL_GUARD and r1["unit"] == "lm" and r1["measured_net"] == 5.5
    assert r1["calculation"]["inputs"][A.REC_KEY]["evidence_status"].startswith("VERIFIED")
    r3 = [ln for ln in out if ln["location"]["element_id"] == "RAIL:R3"][0]
    assert r3["evidence_state"] == "BLOCKED_RFI" and "2" in r3["rfi"]["question"]
    w = _by(out, A.SHUTTER)
    assert sorted((ln["unit"], ln["measured_net"]) for ln in w if ln["unit"] == "pcs") == [("pcs", 2)]
    assert [ln["evidence_state"] for ln in w if ln["unit"] == "m2"] == ["BLOCKED_RFI"]
    old = [ln for ln in out if ln["location"]["element_id"] == "GF-ST1:railing"][0]
    assert old == lines[-1]                                     # the existing blank railing line untouched


def test_totals_moved_only_new_codes_and_order_invariant():
    lines, ch, log, out, ident = run()
    t29, t30 = A304.code_totals(lines), A304.code_totals(out)
    moved = {k for k in set(t29) | set(t30) if t29.get(k) != t30.get(k)}
    assert all(k.split("|")[0] in A.ITEMS for k in moved)
    d = doc(lines)
    d["formwork"] = list(reversed(d["formwork"]))
    d["railings"] = list(reversed(d["railings"]))
    _l, _c, _g, out2, _i = run(d, lines)
    assert sorted(A30.line_sha(x) for x in out2) == sorted(A30.line_sha(x) for x in out)


def test_mirror_ids_independent_of_floor_names():
    lines = lines_3029()
    _l, _c, _g, out, ident = run(doc(lines), lines)
    ids = {ln["location"]["element_id"] for ln in out[len(lines):]}
    assert all(i.startswith(("FW:", "RAIL:", "SHUTTER:")) for i in ids) and len(ids) == len(out) - len(lines)


def test_ledger_and_diff_rows():
    lines, ch, log, out, ident = run()
    rows = A.ledger_rows(ch, released_lines=[])
    assert all(r["before_v3_0_29"]["state"] == "NOT_IN_V3_0_29" for r in rows)
    assert all(r["before_released_v2_9"]["state"] == "NOT_IN_RELEASED" for r in rows)
    csv = A.ledger_csv(rows)
    assert "OQ10" not in csv.splitlines()[0] and "formed_m2" in csv.splitlines()[0]
    diff = A.diff_rows(lines, out, [])
    assert sum(d["vs_v3_0_29"] == "SAME" for d in diff) == len(lines)
    assert sum(d["vs_v3_0_29"] == "ADDED" for d in diff) == len(out) - len(lines)


# ------------------------------------------------------------------------------------------------ adverse
def _bad(mut, msg):
    lines = lines_3029()
    d = doc(lines)
    mut(d, lines)
    with pytest.raises((A.InputsError, ValueError), match=msg):
        inp = A.load_inputs(d, PID)
        ch, _log = A.changes_for(inp, lines)
        A.integrate(lines, ch)


def test_held_with_figure_refused():
    _bad(lambda d, l: d["formwork"][2].update(m2=0.0), "held is BLANK")


def test_e_method_as_a_line_refused():
    _bad(lambda d, l: d["formwork"].append(_fw(l, "S1", "CALCULATED", "E", 12.0, ["E-S1"])), "comparison method")


def test_oq10_reading_valued_refused():
    _bad(lambda d, l: d["formwork"].append(_fw(l, "F1", "CALCULATED", "E=G", 1.92, ["F-F1-X"],
                                               alternative="OQ10_FORMED")), "alternative")


def test_alternative_without_formed_refused():
    _bad(lambda d, l: d["alternatives"][0]["alternatives"].pop("OQ10_FORMED"), "FORMED")


def test_stale_binding_refused():
    def m(d, l):
        d["bound_concrete_lines"][0]["measured_net"] = 0.30
    _bad(m, "stale binding")


def test_valued_face_on_downgraded_line_refused():
    _bad(lambda d, l: d.update(downgrade_bound_lines=[_id(l, "B1")]), "downgrade")


def test_valued_face_on_blank_concrete_line_refused():
    _bad(lambda d, l: d["formwork"].append(_fw(l, "ST2", "CALCULATED", "G", 1.0, ["F-ST2"])), "valued face")


def test_s1_face_refused():
    _bad(lambda d, l: d["formwork"][0]["face_ids"].__setitem__(0, "R4-346.S1"), "S1")


def test_face_twice_refused():
    _bad(lambda d, l: d["untied"][0].update(face_id="F-S1"), "one face, one line")


def test_face_count_mismatch_refused():
    _bad(lambda d, l: d["formwork"][0].update(faces=2), "face ids")


def test_negative_or_zero_figure_refused():
    _bad(lambda d, l: d["formwork"][0].update(m2=-3.3), "positive")
    _bad(lambda d, l: d["stair_sides"][0].update(m2=0.0), "positive")


def test_stair_side_on_non_stair_line_refused():
    _bad(lambda d, l: d["stair_sides"][0].update(line_id=_id(l, "B1")), "stair")


def test_unmerged_source_refused():
    _bad(lambda d, l: d["sources"].pop(0), "no merged source")
    _bad(lambda d, l: d["sources"][2].update(checker_run=""), "checker_run missing")


def test_confirmed_run_with_held_segment_refused():
    def m(d, l):
        d["railings"][0]["segments"][1]["status"] = "HELD"
    _bad(m, "HELD segment")


def test_confirmed_run_not_its_segments_refused():
    _bad(lambda d, l: d["railings"][0].update(lm=5.0), "sum of its measured segments")


def test_plan_projection_relabelled_refused():
    _bad(lambda d, l: d["railings"][1].update(lm=2.7), "sum of its measured segments")


def test_held_run_with_lm_refused():
    _bad(lambda d, l: d["railings"][2].update(lm=2.0), "carries no lm")


def test_verified_held_run_refused():
    _bad(lambda d, l: d["railings"][2].update(verified=True), "re-measure")


def test_run_twice_refused():
    _bad(lambda d, l: d["railings"].append(copy.deepcopy(d["railings"][0])), "one run")


def test_shutter_area_given_refused():
    _bad(lambda d, l: d["shutters"][0].update(m2=1.8), "HELD")


def test_shutter_count_not_int_refused():
    _bad(lambda d, l: d["shutters"][0].update(pcs=2.0), "leaf count")


def test_applied_twice_refused():
    lines = lines_3029()
    inp = A.load_inputs(doc(lines), PID)
    ch, _log = A.changes_for(inp, lines)
    out, _ = A.integrate(lines, ch)
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(doc(lines), PID), out)


def test_concrete_line_missing_refused():
    lines = lines_3029()
    d = doc(lines)
    with pytest.raises(A.InputsError, match="stale binding"):
        A.changes_for(A.load_inputs(d, PID), lines[1:])


def test_replace_or_changed_line_refused():
    lines, ch, log, out, ident = run()
    bad = copy.deepcopy(ch)
    bad[0] = dict(bad[0], action="REPLACE", before=lines[0])
    with pytest.raises(ValueError, match="only adds"):
        A.integrate(lines, bad)


def test_finished_lines_double_face_detected():
    lines, ch, log, out, ident = run()
    out2 = copy.deepcopy(out)
    a = [ln for ln in out2 if ln["location"]["element_id"].startswith("FW:") and
         ln["evidence_state"] == "SOURCE_DERIVED"]
    a[1]["calculation"]["inputs"][A.REC_KEY]["face_ids"] = list(a[0]["calculation"]["inputs"][A.REC_KEY]["face_ids"])
    with pytest.raises(ValueError, match="double count"):
        A.check_formwork_metalwork(out2)


def test_finished_held_line_with_figure_detected():
    lines, ch, log, out, ident = run()
    out2 = copy.deepcopy(out)
    h = [ln for ln in out2 if ln["location"]["element_id"] == "FW:FACE:P1-RC"][0]
    h["bounded_range"] = {"low": 1.2, "high": 2.0}
    with pytest.raises(ValueError, match="BLANK"):
        A.check_formwork_metalwork(out2)


def test_per_flight_railing_with_figure_beside_runs_detected():
    lines, ch, log, out, ident = run()
    assert ident["formwork_metalwork"]["per_flight_railing_lines_blank"] == 1
    out2 = copy.deepcopy(out)
    fl = [ln for ln in out2 if ln["location"]["element_id"] == "GF-ST1:railing"][0]
    fl.update(evidence_state="MEASURED", measured_net=3.0, rfi=None)
    with pytest.raises(ValueError, match="same guard twice"):
        A.check_formwork_metalwork(out2)
