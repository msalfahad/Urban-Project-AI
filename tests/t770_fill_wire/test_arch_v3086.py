"""T-770 r9: ARCH_TAKEOFF_V3.0.86 (FILL_WIRE_V6, R-T770-7) on a synthetic index and synthetic BOQ lines (no project
data): a set naming its base as "base": "<METHOD> (...)" is read as built on that method; a row label carried in after
is taken; a NO_LINE row that closes an element as the complement of a released line is RECORDED and never written (no
line, never 0); a BASIS_TEXT row restates the text only; a base basis correction changes only the text of a line an
earlier round wired; adverse cases stop the run. Plus the committed r9 outputs equal their builder."""
from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3081 as B  # noqa: E402
from engine.source import arch_v3086 as A  # noqa: E402

V84 = "ARCH_TAKEOFF_V3.0.84"
LC = "L-" + "c" * 20          # the complement line (an RC parapet billed whole)
LM = "L-" + "a" * 20          # a masonry line restated by text only
LW = "L-" + "b" * 20          # a line an earlier round wired, its basis text wrong


def _ln(lid, code, unit, cls="HELD", net=None, lo=None, hi=None, label=None, basis=None, el=None):
    d = {"binding": None, "class": cls, "element_id": el or f"E:{lid}", "held_high": hi, "held_low": lo,
         "item_code": code, "line_id": lid, "measured_net": net, "unbound_records": [], "unit": unit}
    if label:
        d["method_label"], d["fill_basis"] = label, basis
    return d


def _index():
    return {"schema": B.INDEX_SCHEMA, "candidate_version": A.EXTENDS, "lines": [
        _ln("L-p1", "ARCH.WALL_PANEL", "m2"),
        _ln("L-v1", "ARCH.WALL_VOLUME", "m3"),
        _ln("L-na", "ARCH.WALL_PANEL", "m2"),
        _ln(LC, "STR.CONC.PARAPET", "m3", "RELEASED", 4.0, label="DEFAULT", basis="runs x h"),
        _ln(LM, "MAS.BLOCK", "m2", "RELEASED", 11.0, label="ESTIMATE", basis="run x 0.70 m, the only printed depth"),
        _ln(LW, "FIN.EXT.FINISH", "m2", "RELEASED", 58.25, label="DEFAULT", basis="54.6 low + 4.4 x 1.20 = 5.28 (d)"),
        _ln("L-out", "FIN.PAINT", "m2", "RELEASED", 10.0)]}


def _r(lid, code, unit, before, after, label, basis, **kw):
    d = {"line_id": lid, "item_code": code, "unit": unit, "element_id": f"E:{lid}", "before": before,
         "after": after, "label": label, "basis": basis}
    d.update(kw)
    return d


def _held():
    return {"class": "HELD", "net": None}


def _pkg():
    views = {"schema": "URBAN_FIX_ROWS_V1", "task": "T-2", "base": f"{A.EXTENDS} (LINE_INDEX_V3_0_85.json)", "rows": [
        _r("L-p1", "ARCH.WALL_PANEL", "m2", _held(), {"class": "RELEASED", "net": 20.0}, "DEFAULT", "= MAS.BLOCK 20"),
        _r("L-v1", "ARCH.WALL_VOLUME", "m3", _held(), {"class": "RELEASED", "net": 4.0}, "DEFAULT", "20 x t 0.20"),
        _r("L-na", "ARCH.WALL_PANEL", "m2", _held(), {"class": "EXCLUDED", "net": None,
                                                      "reason": "NOT_APPLICABLE_WITH_EVIDENCE"},
           "NOT_APPLICABLE", "view of an excluded strip")]}
    mas = {"schema": "URBAN_FIX_ROWS_V1", "task": "T-1", "base": f"{V84} (LINE_INDEX_V3_0_84.json)", "rows": [
        {"id": "F-1", "line_id": None, "item_code": "MAS.BLOCK.PARAPET", "unit": "m2", "element_id": "R#PARAPET",
         "action": "NO_LINE", "before": {"class": "HELD (draft, never wired)", "low": 0.0, "high": None},
         "after": {"class": "RELEASED", "net": 0.0, "label": "DRAWING-READ"},
         "basis": f"sections cut the parapet in the slab hatch: billed whole as {LC} STR.CONC.PARAPET; complement 0"},
        _r(LM, "MAS.BLOCK", "m2", {"class": "RELEASED", "net": 11.0, "label": "ESTIMATE"},
           {"class": "RELEASED", "net": 11.0, "label": "ESTIMATE"}, None, "run x 0.70 = slab to band top",
           action="BASIS_TEXT (supersedes an earlier text)")]}
    mas["rows"][1].pop("label")
    domes = {"schema": "URBAN_FIX_ROWS_V1", "task": "T-3", "candidate_version": V84, "rows": [], "new_lines": [
        {"line_id": "NEW:DOME:A:MEMBRANE", "item_code": "FIN.WP.ROOF", "unit": "m2", "element_id": "DOME:A:MEMBRANE",
         "label": "DEFAULT", "net": 26.685, "basis": "pi (2.21^2 + 1.90^2)"}]}
    return {"schema": A.PACKAGE_SCHEMA, "method": A.METHOD, "base": A.EXTENDS, "row_bases": [V84],
            "set_names": ["T-3", "T-1", "T-2"], "sets": [domes, mas, views],
            "base_basis_corrections": {LW: {"old": "4.4 x 1.20 = 5.28", "new": "4.4 x (1.20 - 0.385) = 3.59",
                                            "source": "Checker finding X"}}}


def test_index_normal_case():
    base = _index()
    new, applied, late, rep = A.apply_index(base, _pkg())
    by = {ln["line_id"]: ln for ln in new["lines"]}
    assert by["L-p1"]["measured_net"] == 20.0 and by["L-v1"]["measured_net"] == 4.0
    assert by["L-na"]["class"] == "EXCLUDED" and by["L-na"]["measured_net"] is None
    # NO_LINE: recorded, never a line, never 0
    assert not any(ln["item_code"] == "MAS.BLOCK.PARAPET" for ln in new["lines"])
    assert len(rep["no_line_rows"]) == 1 and rep["no_line_rows"][0]["complement"][0]["line_id"] == LC
    assert by[LC] == base["lines"][3]                                          # complement untouched
    # BASIS_TEXT: figure and label unchanged, text restated
    assert by[LM]["measured_net"] == 11.0 and by[LM]["method_label"] == "ESTIMATE"
    assert by[LM]["fill_basis"] == "run x 0.70 = slab to band top"
    # base basis correction: only the text
    w0, w1 = base["lines"][5], by[LW]
    assert w1["measured_net"] == w0["measured_net"] and w1["method_label"] == w0["method_label"]
    assert "4.4 x (1.20 - 0.385) = 3.59" in w1["fill_basis"] and "5.28" not in w1["fill_basis"]
    assert "Checker finding X" in w1["fill_basis"] and A.RULE_V7 in w1["fill_basis"]
    assert {k for k in w0 if w0[k] != w1[k]} == {"fill_basis"}
    assert by["L-out"] == base["lines"][6]
    dome = new["lines"][-1]
    assert dome["item_code"] == "FIN.WP.ROOF" and dome["measured_net"] == 26.685 and len(new["lines"]) == 8
    assert {x["set"] for x in rep["set_base_read"]} == {"T-1", "T-2"}
    assert new["candidate_version"] == A.METHOD and new["extends"] == A.EXTENDS
    assert new["fill"]["no_line_rows"] == 1 and new["fill"]["base_basis_corrections"] == 1
    d = A.diff_rows(applied, {}, late, rep)
    assert any(x["line_id"] == LW and x["set"] == "BASIS_TEXT" for x in d)


def _boq(ln):
    st = {"RELEASED": "PROVISIONAL", "HELD": "BOUNDED_EXPOSURE" if ln["held_low"] is not None else "BLOCKED"}
    d = {"line_id": ln["line_id"], "item_code": ln["item_code"], "unit": ln["unit"],
         "evidence_state": st[ln["class"]], "measured_net": ln["measured_net"],
         "bounded_range": {"low": ln["held_low"], "high": ln["held_high"]} if ln["held_low"] is not None else None,
         "location": {"element_id": ln["element_id"]}, "gross": None}
    if "method_label" in ln:
        d["method_label"], d["fill_basis"] = ln["method_label"], ln["fill_basis"]
    return d


def test_boq_view_matches_the_index_view():
    lines = [_boq(ln) for ln in _index()["lines"]]
    new, applied, added, late, rep = A.apply_boq_lines(lines, _pkg())
    by = {ln["line_id"]: ln for ln in new}
    idx = {ln["line_id"]: ln for ln in A.apply_index(_index(), _pkg())[0]["lines"]}
    assert set(by) == set(idx)
    for lid, ln in by.items():
        assert B.line_class(ln) == idx[lid]["class"], lid
        if idx[lid]["class"] == "RELEASED":
            assert ln["measured_net"] == idx[lid]["measured_net"], lid
    assert by[LW]["fill_basis"] == idx[LW]["fill_basis"]
    assert by["L-out"] == lines[6] and by[LC] == lines[3]
    assert new[-1]["rule"]["version"] == A.METHOD


def _no_line(p):
    return p["sets"][1]["rows"][0]


@pytest.mark.parametrize("break_it, msg", [
    (lambda p: _no_line(p)["after"].update(net=2.0), "RELEASED 0 only"),                          # adverse (z)
    (lambda p: _no_line(p).update(basis="billed whole by the RC parapet"), "names no complement"),
    (lambda p: _no_line(p).update(basis=f"complement of L-{'d' * 20}"), "is not in the base"),
    (lambda p: _no_line(p).update(line_id="L-p1"), "names a line|without a line id"),
    (lambda p: (_no_line(p).update(item_code="ARCH.WALL_PANEL", unit="m2", element_id="E:L-p1")),
     "bind it by line id"),
    (lambda p: _no_line(p)["after"].update(label="MAGIC"), "not one of"),
    (lambda p: p["sets"][1]["rows"][1]["after"].update(net=12.0), "moves the figure"),             # adverse (aa)
    (lambda p: p["sets"][1]["rows"][1]["after"].update(label="DEFAULT"), "relabels"),
    (lambda p: p["sets"][1]["rows"][1].update(label="DEFAULT"), "differ"),                       # adverse (y)
    (lambda p: p["sets"][2].update(base="the latest index"), "does not name a method"),           # adverse (x)
    (lambda p: p["sets"][2].update(candidate_version=V84), "disagree"),
    (lambda p: p["base_basis_corrections"][LW].update(old="not in the text"), "old text once"),   # adverse (ab)
    (lambda p: p["base_basis_corrections"][LW].update(source=""), "needs a source"),
    (lambda p: p["base_basis_corrections"].update({"L-p1": {"old": "x", "new": "y", "source": "s"}}),
     "on a row of this package"),
    (lambda p: p["base_basis_corrections"].update({"L-none": {"old": "x", "new": "y", "source": "s"}}),
     "names no base line"),
    (lambda p: p.update(base="ARCH_TAKEOFF_V3.0.84"), "built for"),
    (lambda p: p.update(schema="URBAN_FILL_PACKAGE_V5"), "is not URBAN_FILL_PACKAGE_V6"),
])
def test_adverse_cases_stop_the_run(break_it, msg):
    p = copy.deepcopy(_pkg())
    break_it(p)
    with pytest.raises(B.FillError, match=msg):
        A.apply_index(_index(), p)


def test_no_line_complement_must_be_a_released_figure():
    """adverse: a complement line still HELD does not close the other trade's element"""
    base = _index()
    base["lines"][3] = _ln(LC, "STR.CONC.PARAPET", "m3")
    with pytest.raises(B.FillError, match="not a released figure"):
        A.apply_index(base, _pkg())


def test_index_of_another_version_refused():
    base = _index()
    base["candidate_version"] = "ARCH_TAKEOFF_V3.0.84"
    with pytest.raises(B.FillError, match="base is"):
        A.apply_index(base, _pkg())


def test_committed_r9_outputs_equal_their_builder():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t770/v3086_index.py"), "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0 and "check: OK" in r.stdout, r.stdout + r.stderr
