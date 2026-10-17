"""M4 reports on the hand-made continuous-beam plan: the missing-reinforcement register names the missing roles and
the detail that would supply them, counts never kg by ratio; the unresolved-concrete exceptions are numbered and
located; the continuous-beam registers carry the span matching and the physical bars; the visual QA renders."""

from __future__ import annotations

import json

import pytest

pytest.importorskip("ezdxf")

from engine.source import generic_route as GR                       # noqa: E402
from engine.source import provisional_estimate as PE                # noqa: E402
from tests.m4_correctness import test_m4_continuous_beams as CBT    # noqa: E402
from tools import m4_overlay as OV4                                  # noqa: E402
from tools import m4_reports as MR                                   # noqa: E402
from tools import urban_intake as UI                                 # noqa: E402


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    I = UI.read(CBT._set(tmp_path_factory.mktemp("rep") / "cb.dxf"))
    conv = GR.merge_conventions(json.loads(CBT.V3.read_text()), {"profile": "T", "conventions": []})
    D = GR.detect(I)
    items, reg, risk = GR.items_from(D, conv, {})
    PE.check(items, conv)
    return D, items, reg, risk


def test_missing_register_roles_and_counts(run):
    D, items, reg, risk = run
    rows = MR.missing_register(D, items, reg)
    by = {r["COMPONENT_ID"]: r for r in rows}
    assert set(by) == {r["COMPONENT_ID"] for r in reg if r["REBAR_STATE"] in MR.MISSING}
    cb = [r for r in rows if "continuous-beam line" in r["AVAILABLE_EVIDENCE"]]
    mapped = [r for r in cb if "MATCH_" in r["AVAILABLE_EVIDENCE"]]
    conflict = [r for r in cb if "SPAN_COUNT_CONFLICT" in r["AVAILABLE_EVIDENCE"]]
    assert mapped and all(r["MISSING_ROLES"] != "ALL" and r["DETAIL_REQUIRED"] for r in mapped)
    assert conflict and all(r["MISSING_ROLES"] == "ALL" and "span sequence" in r["DETAIL_REQUIRED"] for r in conflict)
    assert all(r["PROVISIONAL_KG_BASE"] > 0 for r in cb if r["REBAR_STATE"] == "PARTIAL_MISSING")
    un = [r for r in rows if r["EXISTENCE"] == "SECTION_UNRESOLVED"]
    assert un and all(r["CONCRETE_EXPOSURE_HIGH_M3"] and r["MISSING_ROLES"] == "ALL" for r in un)
    s = MR.missing_summary(rows)
    fam = {x["VALUE"]: x for x in s if x["BY"] == "FAMILY"}
    assert sum(x["COMPONENTS"] for x in fam.values()) == len(rows)
    assert not any("kg/m3" in json.dumps(r) for r in rows)              # never a ratio


def test_unresolved_concrete_numbered_and_located(run):
    D, items, reg, risk = run
    ex = MR.unresolved_concrete(D, items)
    n = [i for i in items if i["trade"] == "CONCRETE" and i["category"] == "UNRESOLVED"]
    assert len(ex) == len(n) and len({r["NO"] for r in ex}) == len(ex)
    assert all(r["X_M"] is not None and r["SHEET"] for r in ex)
    b1 = [r for r in ex if r["BLOCKER"] == "UNLABELLED_SPAN_ACROSS_SUPPORT"]
    assert b1 and b1[0]["CLASS"] == "SOURCE_AMBIGUITY" and "collinear" in b1[0]["ALTERNATIVES"]


def test_cb_registers_and_visual_qa(run):
    D, items, reg, risk = run
    lines = {r["MARK"]: r for r in MR.cb_lines(D)}
    assert lines["CB1"]["STATE"] == "MATCH_FORWARD" and lines["CB1"]["PRINTED_SPANS_M"] == "4 / 5 / 6"
    assert lines["CB2"]["STATE"] == "SPAN_COUNT_CONFLICT" and lines["CB2"]["BAR_GROUPS"] == 0
    bars = [r for r in MR.cb_bars(D) if r["MARK"] == "CB1"]
    b1 = next(r for r in bars if r["BAR_ID"] == "CB1:BOTTOM1")
    assert b1["LENGTH_M_BASE"] == pytest.approx(4.79) and b1["COUNT"] == 3
    rec = next(r for r in D["sheets"].values() if r["sheet"]["role"] == "SLAB_PLAN")
    svg = OV4.cb_svg(rec)
    assert svg.startswith("<svg") and "CB1.3" in svg
    loc = MR.locate(D)
    polys = {k: v["poly"] for k, v in loc.items()}
    ex = MR.unresolved_concrete(D, items)
    e_svg = OV4.exceptions_svg(rec, [r for r in ex if r["SHEET"] == rec["sheet"]["sheet_id"]], polys)
    assert e_svg and e_svg.count("<circle") == len([r for r in ex if r["SHEET"] == rec["sheet"]["sheet_id"]])
    html = OV4.html([("t", "n", [("c", svg)])], banner="b")
    assert "<svg" in html and "M4 visual QA" in html
