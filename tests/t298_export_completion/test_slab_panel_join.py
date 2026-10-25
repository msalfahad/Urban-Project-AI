"""T-298 part (2) (F-REC-01): the slab completeness join by PANEL ID on the current grain, and NOT_APPLICABLE elements
with / without evidence in the export's completeness scope.

Hand calculation (synthetic villa VG-298, not the development villa; t = 0.16 m everywhere):
  GF panels (independent ledger): P-A 4.00 x 3.125 = 12.5000 m2 -> 2.000000 m3; P-B 2.50 x 2.00 = 5.0000 m2 -> 0.800000;
                                  P-C 1.50 x 2.00 = 3.0000 m2 -> 0.480000                       floor 3.280000 m3
  GF lines (engine): L-A 2.000004, L-B 0.799990, L-C 0.480000 (the engine's own polygon areas)  floor 3.279994 m3
    -> EXACT pairs, residual (line - panel) +0.000004 / -0.000010 / 0 = -0.000006 m3
  1F two quarter-circle corners (r 0.75: pi/4 x 0.5625 = 0.441786 m2 -> 0.070686 m3) drawn as arcs in the ledger
     (P-D1 0.070650, P-D2 0.070720), the engine's polygons equal (0.070686 each)
    -> INTERCHANGEABLE pair (which equal line is which corner changes no count and no sum)
  NA face: a 0.20 m beam strip 0.20 x 3.70 = 0.740 m2 retired from the slab line with its home (NOT_APPLICABLE) and
    its drawing evidence: out of the element scope (3 + 2 = 5 panels = 5 elements), not 6.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from engine.source import boq_line as BL
from engine.source import trade_completeness_v1 as TC
from tools import boq_export_v1 as X

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "agents_t236"))
import slab_panel_join as SPJ  # noqa: E402

PID, REV, CVER = "SYNTH-VILLA-VG298", "d" * 64, "ARCH_TAKEOFF_V3.0.TEST"
PANELS = [{"floor": "GF", "panel": "P-A", "m3": 2.0}, {"floor": "GF", "panel": "P-B", "m3": 0.8},
          {"floor": "GF", "panel": "P-C", "m3": 0.48}, {"floor": "1F", "panel": "P-D1", "m3": 0.07065},
          {"floor": "1F", "panel": "P-D2", "m3": 0.07072}]
LIVE = {"L-A": ("GF", 2.000004), "L-B": ("GF", 0.79999), "L-C": ("GF", 0.48), "L-D1": ("1F", 0.070686),
        "L-D2": ("1F", 0.070686)}
DOC = [{"title": "VG-S-05 roof slab plan", "sheet": "S-05"}]


def jl(spec):
    return [{"line_id": k, "floor": v[0], "m3": v[1]} for k, v in spec.items()]


def test_normal_exact_and_interchangeable_pairs():
    r = SPJ.join(PANELS, jl(LIVE))
    by = {x["panel"]: x for x in r["pairs"]}
    assert {p: by[p]["line_id"] for p in ("P-A", "P-B", "P-C")} == {"P-A": "L-A", "P-B": "L-B", "P-C": "L-C"}
    assert {by[p]["join"] for p in ("P-A", "P-B", "P-C")} == {"EXACT"}
    assert by["P-D1"]["join"] == by["P-D2"]["join"] == "INTERCHANGEABLE" and by["P-D1"]["group"] == "P-D1|P-D2"
    assert {by["P-D1"]["line_id"], by["P-D2"]["line_id"]} == {"L-D1", "L-D2"}
    assert r["unmatched_lines"] == [] and r["missing_panels"] == []
    f = SPJ.floor_residuals(r, PANELS, jl(LIVE))
    assert f["GF"]["pair_residual_m3"] == -0.000006 and f["GF"]["panel_m3"] == 3.28
    assert f["1F"]["pair_residual_m3"] == round(2 * 0.070686 - 0.07065 - 0.07072, 6)        # +0.000002


def test_a_panel_missing_and_an_extra_face_on_one_storey_do_not_cancel():
    """the count join would read 3 lines = 3 panels on GF; the panel join sees which one is wrong"""
    spec = dict(LIVE)
    spec.pop("L-B")
    spec["L-X"] = ("GF", 0.118400)                                           # a beam strip left in the slab line
    r = SPJ.join(PANELS, jl(spec))
    assert [m["panel"] for m in r["missing_panels"]] == ["P-B"]
    assert [u["line_id"] for u in r["unmatched_lines"]] == ["L-X"]


def test_one_line_within_tolerance_of_two_panels_is_ambiguous_never_picked():
    panels = [{"floor": "2F", "panel": "Q1", "m3": 1.0}, {"floor": "2F", "panel": "Q2", "m3": 1.00015}]
    r = SPJ.join(panels, [{"line_id": "L1", "floor": "2F", "m3": 1.00008}])
    assert r["pairs"] == [] and sorted(m["panel"] for m in r["missing_panels"]) == ["Q1", "Q2"]
    assert [u["line_id"] for u in r["unmatched_lines"]] == ["L1"]


def test_lines_of_different_volume_near_one_panel_are_ambiguous():
    panels = [{"floor": "GF", "panel": "Q1", "m3": 1.0}]
    r = SPJ.join(panels, [{"line_id": "L1", "floor": "GF", "m3": 0.99992},
                          {"line_id": "L2", "floor": "GF", "m3": 1.00009}])
    assert r["pairs"] == [] and r["missing_panels"][0]["why"].startswith("AMBIGUOUS")


def test_a_held_volume_never_joins_and_a_repeated_panel_is_refused():
    with pytest.raises(ValueError, match="never joins"):
        SPJ.join(PANELS, [{"line_id": "L-H", "floor": "GF", "m3": None}])
    with pytest.raises(ValueError, match="twice"):
        SPJ.join(PANELS + PANELS[:1], jl(LIVE))


def test_a_volume_outside_tolerance_is_not_joined():
    r = SPJ.join([{"floor": "GF", "panel": "P", "m3": 0.8}], [{"line_id": "L", "floor": "GF", "m3": 0.8003}])
    assert r["pairs"] == [] and r["missing_panels"][0]["panel"] == "P" and r["unmatched_lines"][0]["line_id"] == "L"


# ---- the export's completeness scope (NOT_APPLICABLE with / without evidence) ---------------------------------------

def sl(eid, q=None, ev="PROVISIONAL", floor="GF", docs=DOC, notes=""):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code="STR.CONC.SLAB", unit="m3",
                        evidence_state=ev, measured_net=q, element_id=eid, floor=floor, formula="A*t",
                        inputs={"A": None if q is None else q / 0.16, "t": 0.16}, rule_id="R-SYN", rule_version="1",
                        documents=docs, notes=notes)


def slab_lines(na_docs=DOC, extra=()):
    out = [sl(k, q=v[1], floor=v[0]) for k, v in LIVE.items()]
    out.append(sl("L-NA", ev="NOT_APPLICABLE_WITH_EVIDENCE", docs=na_docs,
                  notes="beam strip 0.20 x 3.70: home beam run CB5 span 2 (retired from the slab line)"))
    return out + list(extra)


def report(lines, panels=PANELS):
    r = SPJ.join(panels, [{"line_id": x["line_id"], "floor": x["location"]["floor"], "m3": x["measured_net"]}
                          for x in lines if x["evidence_state"] in SPJ.QUANTITY_STATES])
    links = {x["line_id"]: [f"{x['floor']}:{x['panel']}"] for x in r["pairs"]}
    for x in lines:
        if x["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE":
            links[x["line_id"]] = [f"{x['location']['floor']}:NOT_SLAB:{x['line_id'][-8:]}"]
    for u in r["unmatched_lines"]:
        links[u["line_id"]] = [f"{u['floor']}:UNMATCHED:{u['line_id'][-8:]}"]
    inv = [{"source": "SLAB-LEDGER", "basis": "CENSUS", "trade": "CONCRETE.SLAB", "floors": ["GF", "1F"],
            "elements": [{"floor": p["floor"], "label": p["panel"], "ref": f"panel {p['panel']}"} for p in panels]}]
    return TC.check(inventories=inv, lines=lines, line_links=links)


def whole(lines, qty):
    ids = [x["line_id"] for x in lines]
    return X.verdict_add(lines, candidate_version=CVER, boq_lines_sha256=X.lines_sha256(lines), line_ids=ids,
                         scope="WHOLE", checker_qty=qty, evidence=[{"sheet": "S-05", "printed_value": "t 16 cm"}],
                         run_token="20261025T130000-1-1", routine="Verifier", verdict_commit="c0ffee12",
                         time="2026-10-25T13:00:00Z")


def run(tmp_path, lines, name="o", **kw):
    m = X.export(lines, tmp_path / name, candidate_version=CVER, boq_lines_sha256=X.lines_sha256(lines), **kw)
    s = {(r["trade"], r["item_code"], r["unit"]): r for r in X.read_csv(tmp_path / name / "BOQ_TRADE_SUMMARY.csv")}
    return m, s[("CONCRETE", "STR.CONC.SLAB", "m3")]


def test_na_with_evidence_leaves_the_scope_and_the_whole_line_verifies(tmp_path):
    lines = slab_lines()
    live = sum(v[1] for v in LIVE.values())                                    # 3.421366 m3
    rec = whole(lines, round(live * 1.0002, 6))                                # Checker within 1 %
    assert rec["element_scope"]["count"] == 6                                  # the verdict binds every line id
    m, s = run(tmp_path, lines, v2_records=[rec], completeness_report=report(lines))
    assert s["completeness"].startswith("PASS") and "inventory 5 = element scope 5" in s["completeness"]
    assert s["line_status"] == "VERIFIED" and s["verified_subtotal"] == f"{live:.6f}"
    assert m["v2_verdicts"][0]["status"] == "COUNTED (WHOLE)"


def test_na_without_evidence_keeps_the_line_unverified(tmp_path):
    lines = slab_lines(na_docs=())                                             # a reason, but no document
    rec = whole(lines, 3.421366)
    m, s = run(tmp_path, lines, v2_records=[rec], completeness_report=report(lines))
    assert s["line_status"] == "NOT VERIFIED" and "NOT_APPLICABLE WITHOUT EVIDENCE 1" in s["completeness"]
    assert "not VERIFIED" in m["v2_verdicts"][0]["status"]


def test_a_panel_missing_from_the_lines_fails_and_shows_as_unmeasured(tmp_path):
    lines = [x for x in slab_lines() if x["location"]["element_id"] != "L-B"]
    rec = whole(lines, 2.621376)
    m, s = run(tmp_path, lines, v2_records=[rec], completeness_report=report(lines))
    assert s["line_status"] == "NOT VERIFIED" and "MISSING 1" in s["completeness"]
    assert s["unmeasured_components"] == "P-B" and s["unmeasured_rows"] == "1"     # a blank row, never 0


def test_a_panel_missing_from_the_inventory_fails(tmp_path):
    lines = slab_lines()
    rec = whole(lines, 3.421366)
    m, s = run(tmp_path, lines, v2_records=[rec], completeness_report=report(lines, panels=PANELS[1:]))
    assert s["line_status"] == "NOT VERIFIED" and "REGISTER_ONLY 1" in s["completeness"]
