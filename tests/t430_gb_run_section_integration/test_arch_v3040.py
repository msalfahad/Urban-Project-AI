"""T-430: ARCH_TAKEOFF_V3.0.40 (ground-beam section per run between founded supports; neck owns the joint; picked range
ends and unprinted sections HELD) on a hand-calculated NON-Alsenan villa (K430).

Villa K430, by hand (own figures; nothing from the development villa). Ground beams 0.25 wide; printed titles
'> 5 m' 0.60, '< 5 m' 0.40 (both 'without concentrated load').
  A  band 9.00 m, founded neck N1 0.25 m inside it: runs A#1 4.25 m (nothing lands, 4.25 on every frame) and A#2
     4.50 m (a beam lands; frames 4.50 / 4.55). Candidate 0.25 x 0.60 x 9.00 = 1.350 m3 (read on the band).
     -> A#1 valued 0.25 x 0.40 x 4.25 = 0.425 m3 (same id); A#2 ADDED, HELD, beside 0.25 x 0.40 x 4.50 = 0.450 ..
        0.25 x 0.60 x 4.55 = 0.6825 m3; the neck 0.25 x 0.60 x 0.25 = 0.0375 m3 is the neck's.
  B  band 8.00 m, founded neck N2 0.30 m: runs B#1 3.70 m (loaded), B#2 4.00 m (unloaded). Candidate 1.200 m3.
     -> B#2 valued 0.25 x 0.40 x 4.00 = 0.400 m3 (same id); B#1 ADDED, HELD 0.370 .. 0.555 m3.
  C  5.10 m run valued 0.25 x 0.60 x 5.10 = 0.765 m3; the other reading 5.05 m (column face) is '< 5 m': RANGE 0.505 ..
     0.765 -> HELD blank, range beside.
  S  0.15 m sliver at 0.30 = 0.01125 m3, no printed section -> HELD blank, nothing beside.
  K  4.00 m run 0.25 x 0.40 x 4.00 = 0.400 m3 (AGREE): untouched.
Valued ground beam: 1.350 + 1.200 + 0.765 + 0.01125 + 0.400 = 3.72625 -> 0.425 + 0.400 + 0.400 = 1.225 m3 (-2.50125).
"""
from __future__ import annotations

import copy
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3040 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-k430", "e" * 64
DOCS = [{"file": "k430_struct.dxf", "sha256": "c" * 64}]
GB = A.GB


def _src(t):
    return {"task": t, "file": f"research/k430/{t}.json", "sha256": t[-1] * 64, "merge_commit": "b" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def _gb(band, net, ev="PROVISIONAL"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=GB, unit="m3", evidence_state=ev,
                        measured_net=net, element_id=f"P-C:GROUND_BEAMS:GROUND:{band}", floor="GROUND",
                        physical_element=f"ground beam {band}", gross=net, formula="route G band",
                        documents=DOCS, rule_id="RG-GB", rule_version="1", notes="k")


def lines_3039():
    return [_gb("A", 1.35), _gb("B", 1.2), _gb("C", 0.765), _gb("S", 0.01125), _gb("K", 0.4),
            BL.make_line(project_id=PID, revision_set_sha256=REV, item_code="FIN.FLOOR.PORCELAIN", unit="m2",
                         evidence_state="SOURCE_DERIVED", measured_net=40.0, element_id="GF-01", floor="GF",
                         formula="floor", documents=DOCS, rule_id="X", rule_version="1", notes="k")]


def _id(lines, band):
    return next(x["line_id"] for x in lines if x["location"]["element_id"].endswith(f":{band}"))


def _run(name, lo, hi, loaded, held_D=None, pd=(0.40,)):
    return {"run": name, "spans": [lo, hi], "printed_D": list(pd), "loaded": loaded, "held_D": held_D,
            "cause": "beam lands" if loaded else "nothing lands"}


def inputs(lines, **over):
    doc = {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-426"), _src("T-416")],
           "splits": [
               {"line_id": _id(lines, "A"), "band": "A", "b": 0.25, "candidate": {"D": 0.60, "L": 9.00, "value": 1.35},
                "necks": [{"id": "N1", "length": 0.25, "founded": True}],
                "runs": [_run("A#1", 4.25, 4.25, False), _run("A#2", 4.50, 4.55, True, [0.40, 0.60])],
                "evidence_status": "VERIFIED", "source_tasks": ["T-426", "T-416"]},
               {"line_id": _id(lines, "B"), "band": "B", "b": 0.25, "candidate": {"D": 0.60, "L": 8.00, "value": 1.2},
                "necks": [{"id": "N2", "length": 0.30, "founded": True}],
                "runs": [_run("B#1", 3.70, 3.70, True, [0.40, 0.60]), _run("B#2", 4.00, 4.00, False)],
                "evidence_status": "VERIFIED", "source_tasks": ["T-426", "T-416"]}],
           "holds": [
               {"line_id": _id(lines, "C"), "kind": "RANGE", "candidate": {"D": 0.60, "L": 5.10, "value": 0.765},
                "range": {"low": 0.505, "high": 0.765, "low_basis": "0.25 x 0.40 x 5.05", "high_basis": "0.25 x 0.60 x 5.10"},
                "cause": "two titles by reading", "items": ["D-33"], "source_tasks": ["T-426"]},
               {"line_id": _id(lines, "S"), "kind": "BLANK", "candidate": {"D": 0.30, "L": 0.15, "value": 0.01125},
                "range": None, "cause": "no printed section", "items": ["D-35"], "source_tasks": ["T-426"]}]}
    doc.update(over)
    return doc


def run(lines=None, doc=None):
    lines = lines or lines_3039()
    d = A.load_inputs(doc or inputs(lines), PID)
    ch, log = A.changes_for(d, lines)
    out, ident = A.integrate(lines, ch)
    return lines, out, ident, ch, log


def _by(out):
    return {x["location"]["element_id"].split("GROUND:")[-1]: x for x in out if x["item_code"] == GB}


def _gb_valued(lines):
    return round(sum(x["measured_net"] for x in lines if x["item_code"] == GB and x["evidence_state"] in A.VALUED), 6)


# ------------------------------------------------------------------------------------------------ normal
def test_hand_figures_k430():
    lines, out, ident, ch, log = run()
    b = _by(out)
    assert b["A"]["measured_net"] == pytest.approx(0.425, abs=1e-9)
    assert b["B"]["measured_net"] == pytest.approx(0.400, abs=1e-9)
    assert b["A"]["line_id"] == _id(lines, "A") and b["B"]["line_id"] == _id(lines, "B")
    assert b["A:A#2"]["evidence_state"] == "BLOCKED_RFI" and b["A:A#2"]["measured_net"] is None
    rec = b["A:A#2"]["calculation"]["inputs"][A.REC_KEY]
    assert rec["beside"] == [pytest.approx(0.45), pytest.approx(0.6825)]
    rec = b["B:B#1"]["calculation"]["inputs"][A.REC_KEY]
    assert rec["beside"] == [pytest.approx(0.37), pytest.approx(0.555)]
    assert b["K"] == next(x for x in lines if x["line_id"] == _id(lines, "K"))
    assert _gb_valued(lines) == pytest.approx(3.72625) and _gb_valued(out) == pytest.approx(1.225)
    assert ident["added"] == 2 and ident["replaced"] == 4 and ident["v3_0_40_lines"] == len(lines) + 2
    assert log["by_action"] == {"HOLD_BLANK": 1, "HOLD_RANGE": 1, "SPLIT_HELD": 2, "SPLIT_VALUED": 2}


def test_neck_owns_the_joint_and_band_closes():
    lines, out, *_ = run()
    rec = _by(out)["A"]["calculation"]["inputs"][A.REC_KEY]
    assert rec["L"] + sum(n["length"] for n in rec["necks"]) + 4.50 == pytest.approx(9.00)
    assert "neck owns the joint" in _by(out)["A"]["calculation"]["formula"]


def test_holds_blank_with_range_or_nothing_beside():
    lines, out, *_ = run()
    b = _by(out)
    c, s = b["C"], b["S"]
    assert c["evidence_state"] == s["evidence_state"] == "BLOCKED_RFI"
    assert c["measured_net"] is None and s["measured_net"] is None
    assert c["calculation"]["inputs"][A.REC_KEY]["beside"] == [0.505, 0.765]
    assert s["calculation"]["inputs"][A.REC_KEY]["beside"] is None
    assert c["rfi"]["question"] and s["rfi"]["question"]


def test_check_runs_summary():
    _, out, ident, *_ = run()
    g = ident["gb_runs"]
    assert g["valued_runs"] == 2 and g["held_runs"] == 2 and g["held_lines"] == 2
    assert g["valued_m3"] == pytest.approx(0.825)
    assert g["held_beside_m3"] == [pytest.approx(0.45 + 0.37 + 0.505), pytest.approx(0.6825 + 0.555 + 0.765)]
    assert g["bands"] == {"A": ["A#1", "A#2"], "B": ["B#1", "B#2"]}


def test_outside_lines_byte_identical_and_totals_only_gb():
    lines, out, ident, ch, _ = run()
    named = {c["after"]["line_id"] for c in ch}
    for ln in lines:
        if ln["line_id"] not in named:
            assert A30.line_sha(ln) == A30.line_sha(next(x for x in out if x["line_id"] == ln["line_id"]))
    t0, t1 = A304.code_totals(lines), A304.code_totals(out)
    assert {k.split("|")[0] for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)} == {GB}


def test_input_order_invariance():
    lines = lines_3039()
    doc = inputs(lines)
    doc2 = copy.deepcopy(doc)
    random.Random(4).shuffle(doc2["splits"])
    random.Random(5).shuffle(doc2["holds"])
    o1 = {x["line_id"]: A30.line_sha(x) for x in run(lines, doc)[1]}
    o2 = {x["line_id"]: A30.line_sha(x) for x in run(lines, doc2)[1]}
    assert o1 == o2


def test_write_files(tmp_path):
    lines, _, _, ch, log = run()
    names, ident, led = A.write(tmp_path, lines, ch, log)
    assert "V3_0_40_BOQ_LINES.json" in names and (tmp_path / "V3_0_40_DIFF.csv").exists()
    assert ident["diff"]["vs_v3_0_39"] == {"SAME": 2, "CHANGED": 4, "ADDED": 2}
    assert led["integration_package"] is True and led["released_default"] is False


def test_no_project_input():
    assert A.changes_for(None, lines_3039()) == ([], {"piece": "GB_RUN_SECTION+GB_HOLD", "state": "NO_PROJECT_INPUT"})


# ------------------------------------------------------------------------------------------------ adverse
def _bad(mut, match):
    lines = lines_3039()
    doc = inputs(lines)
    mut(doc)
    with pytest.raises(A.InputsError, match=match):
        A.changes_for(A.load_inputs(doc, PID), lines)


def test_founded_neck_ignored_one_span_through_it():
    def m(d):
        d["splits"][0]["runs"] = [_run("A#1", 9.00, 9.00, False)]
    _bad(m, "founded neck ignored")


def test_split_without_neck_refused():
    def m(d):
        d["splits"][0]["necks"] = []
    _bad(m, "founded neck")


def test_unfounded_neck_refused():
    def m(d):
        d["splits"][0]["necks"][0]["founded"] = False
    _bad(m, "not a FOUNDED neck")


def test_length_lost_or_borrowed_refused():
    def m(d):
        d["splits"][0]["runs"][0]["spans"] = [4.50, 4.50]   # neck length counted in a run as well
    _bad(m, "no length lost")


def test_held_run_without_range_refused_never_zero():
    def m(d):
        d["splits"][0]["runs"][1]["held_D"] = None
    _bad(m, "never 0")


def test_held_range_zero_refused():
    def m(d):
        d["holds"][0]["range"]["low"] = 0
    _bad(m, "not positive")


def test_mm_as_m_refused():
    def m(d):
        d["splits"][0]["runs"][0]["spans"] = [4250, 4250]
    _bad(m, "mm refused")


def test_frames_differ_unloaded_run_needs_range():
    def m(d):
        d["splits"][0]["runs"][0]["spans"] = [4.25, 4.30]
    _bad(m, "never 0")


def test_two_titles_never_valued():
    def m(d):
        d["splits"][0]["runs"][0]["printed_D"] = [0.30, 0.40]
    _bad(m, "never 0")


def test_stale_candidate_refused():
    lines = lines_3039()
    doc = inputs(lines)
    doc["splits"][0]["candidate"]["value"] = 1.36
    with pytest.raises(A.InputsError, match="stale"):
        A.load_inputs(doc, PID)


def test_candidate_differs_from_census_refused():
    lines = lines_3039()
    lines[0] = _gb("A", 1.30)
    doc = inputs(lines_3039())
    doc["splits"][0]["line_id"] = lines[0]["line_id"]
    with pytest.raises(A.InputsError, match="stale binding"):
        A.changes_for(A.load_inputs(doc, PID), lines)


def test_range_not_containing_candidate_refused():
    def m(d):
        d["holds"][0]["range"]["high"] = 0.70
    _bad(m, "not a picked end")


def test_blank_with_range_refused():
    def m(d):
        d["holds"][1]["range"] = {"low": 0.01, "high": 0.02, "low_basis": "x", "high_basis": "y"}
    _bad(m, "BLANK hold carries no range")


def test_line_named_twice_refused():
    def m(d):
        d["holds"][0]["line_id"] = d["splits"][0]["line_id"]
    _bad(m, "named twice")


def test_wrong_code_refused():
    lines = lines_3039()
    doc = inputs(lines)
    floor = next(x for x in lines if x["item_code"] != GB)
    doc["holds"][1]["line_id"] = floor["line_id"]
    with pytest.raises(A.InputsError, match="not a ground-beam"):
        A.changes_for(A.load_inputs(doc, PID), lines)


def test_unknown_source_refused():
    def m(d):
        d["splits"][0]["source_tasks"] = ["T-999"]
    _bad(m, "no merged source")


def test_applied_twice_refused():
    lines, out, *_ = run()
    doc = inputs(lines)
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(doc, PID), out)


def test_change_outside_own_codes_refused():
    lines, _, _, ch, _ = run()
    bad = copy.deepcopy(ch)
    floor = next(x for x in lines if x["item_code"] != GB)
    bad.append({"piece": A.P_HOLD, "action": "CHANGE", "before": floor, "after": dict(floor, measured_net=1.0)})
    with pytest.raises(ValueError, match="not a code this version"):
        A.integrate(lines, bad)


def test_held_line_valued_caught_by_check():
    _, out, *_ = run()
    bad = [dict(x) for x in out]
    i = next(k for k, x in enumerate(bad) if x["location"]["element_id"].endswith(":C"))
    bad[i] = dict(bad[i], evidence_state="SOURCE_DERIVED", measured_net=0.765, rfi=None)
    with pytest.raises(ValueError, match="not blank"):
        A.check_runs(bad)


def test_run_carried_twice_caught_by_check():
    _, out, *_ = run()
    dup = copy.deepcopy(next(x for x in out if x["location"]["element_id"].endswith(":A#2")))
    dup["line_id"] = "L-dup"
    with pytest.raises(ValueError, match="carried twice"):
        A.check_runs(out + [dup])


def test_wrong_schema_and_project_refused():
    lines = lines_3039()
    with pytest.raises(A.InputsError, match="schema"):
        A.load_inputs(dict(inputs(lines), schema="X"), PID)
    with pytest.raises(A.InputsError, match="are for"):
        A.load_inputs(inputs(lines), "other-villa")
