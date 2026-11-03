"""T-479: research/agents_t479/t479_registry_census.py and t479_completeness.py on a synthetic villa K479 (not the
development villa). Lines made with engine/source/boq_line.make_line, verdicts with tools/boq_export_v1.verdict_add (the
Checker's own record builder). Every expected figure is a hand calculation:

  B8-08  footing membrane F1 12.000 m2 (COMPONENT verdict: its group also holds F2, BLOCKED_RFI, no bound)
         pit base screed  P1  4.500 m2 (WHOLE verdict: the group's only line)
         -> released 16.500, verified whole 4.500 (1 line), verified component 12.000 (1 line), held 1 UNKNOWN
  B10-13 formwork W1 8.250 m2 released unverified; W2 held 1.000 .. 1.500 m2
  B13-09 pool water face Q1 held 6.000 .. 7.000 m2 (never 0)
  ARCH.EXTERIOR E1 9.000 m2: NOT_A_BOQ_LINE (registry declaration with evidence), apart, in no family
  STR.CONC.OTHER X1 0.700 m3: owned by no family and not declared -> LINE_OUTSIDE_EVERY_FAMILY
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t469", ROOT / "research" / "agents_t471", ROOT / "research" / "agents_t479"):
    sys.path.insert(0, str(p))

from engine.source import boq_line as BL  # noqa: E402
from tools import boq_export_v1 as EX  # noqa: E402
import t479_registry_census as C  # noqa: E402
import t479_completeness as K  # noqa: E402

PID, REV, VER = "synthetic-k479", "b" * 64, "V-K479"
NAB = {"ARCH.EXTERIOR": {"evidence": ["register line of an exterior space (K479 hand note)"]}}


def master(**kw):
    m = {"version": "k479", "families": [
        {"code": "B8-08", "group": "B8 Waterproofing", "unit": "m2", "in_v3_0_candidate": "no",
         "candidate": {"method_version": "ARCH_TAKEOFF_V3.0.7"},
         "item_codes": ["WP.FOUNDATION.FOOTING_MEMBRANE", "WP.FOUNDATION.LIFT_PIT_SCREED"]},
        {"code": "B10-13", "group": "B10 Concrete", "unit": "m2", "in_v3_0_candidate": "yes",
         "item_codes": ["STR.FORMWORK"]},
        {"code": "B13-09", "group": "B13 Other", "unit": "m2", "in_v3_0_candidate": "yes",
         "item_codes": ["EXT.POOL.WATER_FACE"]},
        {"code": "B1-01", "group": "B1 Site", "unit": "m2", "in_v3_0_candidate": "no", "item_codes": []},
    ], "not_a_boq_line_codes": copy.deepcopy(NAB)}
    m.update(kw)
    return m


def mk(code, el, ev, net=None, unit="m2", br=None, trade="WATERPROOFING"):
    kw = {}
    if ev == "BLOCKED_RFI":
        kw["rfi"] = {"question": "which section?"}
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=el, bounded_range=br, formula="L x W", rule_id="R-K479",
                        rule_version="1.0.0", trade=trade, item_en=code, item_ar=code, **kw)


def lines():
    return [
        mk("WP.FOUNDATION.FOOTING_MEMBRANE", "WPF:FOOTING", "MEASURED", 12.0),
        mk("WP.FOUNDATION.FOOTING_MEMBRANE", "WPF:FOOTING_F10", "BLOCKED_RFI"),
        mk("WP.FOUNDATION.LIFT_PIT_SCREED", "WPF:PIT_SCREED", "MEASURED", 4.5),
        mk("STR.FORMWORK", "FW:B1", "MEASURED", 8.25, trade="CONCRETE"),
        mk("STR.FORMWORK", "FW:B2", "BOUNDED_EXPOSURE", None, br={"low": 1.0, "high": 1.5, "basis": "range"},
           trade="CONCRETE"),
        mk("EXT.POOL.WATER_FACE", "POOL#WATER_FACE", "BLOCKED_RFI", None, br={"low": 6.0, "high": 7.0, "basis": "b"},
           trade="EXTERNAL_WORKS"),
        mk("ARCH.EXTERIOR", "GARDEN:space", "PROVISIONAL", 9.0, trade="EXTERNAL_WORKS"),
        mk("STR.CONC.OTHER", "X1", "MEASURED", 0.7, unit="m3", trade="CONCRETE"),
    ]


def lid(ls, el):
    return next(x["line_id"] for x in ls if x["location"]["element_id"] == el)


def verdict(ls, els, scope, checker):
    ids = [lid(ls, e) for e in els]
    return EX.verdict_add(ls, candidate_version=VER, boq_lines_sha256=EX.lines_sha256(ls), line_ids=ids, scope=scope,
                          checker_qty=checker, evidence=[{"sheet": "K-1", "printed_value": "hand"}], run_token="t",
                          routine="Checker", verdict_commit="abcdef1", time="2026-11-03T00:00:00Z")


def verdicts(ls):
    return [verdict(ls, ["WPF:FOOTING"], "COMPONENT", 12.0), verdict(ls, ["WPF:PIT_SCREED"], "WHOLE", 4.5)]


def run(ls=None, m=None, vs=None):
    ls = lines() if ls is None else ls
    idx = C.index_lines(ls, verdicts(ls) if vs is None else vs, [], VER)
    return idx, C.census(idx, m or master())


def test_hand_figures_per_family_and_unit():
    _idx, doc = run()
    b8 = doc["families"]["B8-08"]
    assert b8["in_candidate"] == "yes" and b8["lines"] == 3
    u = b8["units"]["m2"]
    assert (u["released"], u["released_lines"]) == (16.5, 2)
    assert (u["verified_whole"], u["verified_whole_lines"]) == (4.5, 1)
    assert (u["verified_component"], u["verified_component_lines"]) == (12.0, 1)
    assert (u["held_lines"], u["held_unknown_lines"], u["held_low"], u["held_high"]) == (1, 1, 0.0, 0.0)
    fw = doc["families"]["B10-13"]["units"]["m2"]
    assert (fw["released"], fw["verified_whole"], fw["verified_component"]) == (8.25, 0.0, 0.0)
    assert (fw["held_lines"], fw["held_low"], fw["held_high"], fw["held_unknown_lines"]) == (1, 1.0, 1.5, 0)
    pool = doc["families"]["B13-09"]["units"]["m2"]
    assert (pool["released_lines"], pool["held_lines"], pool["held_low"], pool["held_high"]) == (0, 1, 6.0, 7.0)
    assert doc["families"]["B1-01"] == {"in_candidate": C.NOT_LINE_ATTRIBUTABLE, "lines": 0, "item_codes_present": [],
                                        "units": {}}


def test_not_a_boq_line_apart_and_line_outside_every_family_reported():
    _idx, doc = run()
    assert doc["not_a_boq_lines"]["ARCH.EXTERIOR"]["units"]["m2"]["released"] == 9.0
    assert doc["not_a_boq_lines"]["ARCH.EXTERIOR"]["evidence"] == NAB["ARCH.EXTERIOR"]["evidence"]
    assert list(doc["no_family"]) == ["STR.CONC.OTHER"] and doc["no_family"]["STR.CONC.OTHER"]["units"]["m3"][
        "released"] == 0.7
    assert doc["issue_counts"] == {"LINE_OUTSIDE_EVERY_FAMILY": 1} and doc["complete_map"] is False
    # every line in exactly one bucket: 3 + 2 + 1 (families) + 1 (not a BOQ line) + 1 (no family) = 8
    n = sum(f["lines"] for f in doc["families"].values()) + sum(len(b["line_ids"]) for b in
                                                                 doc["not_a_boq_lines"].values())
    assert n + sum(len(b["line_ids"]) for b in doc["no_family"].values()) == doc["lines"] == 8
    ls = [x for x in lines() if x["item_code"] != "STR.CONC.OTHER"]
    _idx, doc2 = run(ls)
    assert doc2["complete_map"] is True and doc2["issue_counts"] == {}


def test_held_is_never_zero_and_never_released():
    idx, _doc = run()
    held = [r for r in idx["lines"] if r["class"] == C.HELD]
    assert len(held) == 3 and all(r["measured_net"] is None and r["binding"] is None for r in held)


def test_adverse_unbound_verified_line_is_reported_never_dropped():
    ls = lines()
    vs = verdicts(ls)
    moved = copy.deepcopy(ls)
    f1 = next(x for x in moved if x["location"]["element_id"] == "WPF:FOOTING")
    moved[moved.index(f1)] = mk("WP.FOUNDATION.FOOTING_MEMBRANE", "WPF:FOOTING", "MEASURED", 12.5)
    moved[moved.index(next(x for x in moved if x["location"]["element_id"] == "WPF:PIT_SCREED"))] = mk(
        "WP.FOUNDATION.FOOTING_MEMBRANE", "WPF:OTHER", "MEASURED", 1.0)       # the WHOLE record's line is gone
    _idx, doc = run(moved, vs=vs)
    un = [i for i in doc["issues"] if i["kind"] == "UNBOUND_VERIFIED_LINE"]
    assert sorted(i["verdict_id"] for i in un) == sorted(v["verdict_id"] for v in vs)
    assert sorted((i["scope"], i["status"]) for i in un) == [("COMPONENT", "STALE (own line content changed)"),
                                                            ("WHOLE", "STALE (a line absent)")]
    assert [i["item_code"] for i in un if i["scope"] == "WHOLE"] == [None]   # the absent line is still named
    assert [i["line_id"] for i in un if i["scope"] == "WHOLE"] == [lid(ls, "WPF:PIT_SCREED")]
    u = doc["families"]["B8-08"]["units"]["m2"]
    assert u["verified_whole_lines"] == 0 and u["verified_component_lines"] == 0


def test_adverse_code_in_two_families_is_listed_under_both_and_flagged():
    m = master()
    m["families"][3]["item_codes"] = ["STR.FORMWORK"]
    _idx, doc = run(m=m)
    assert {"kind": "DOUBLY_OWNED_CODE", "item_code": "STR.FORMWORK", "families": ["B1-01", "B10-13"]} in doc["issues"]
    dm = [i for i in doc["issues"] if i["kind"] == "DOUBLY_MAPPED_LINE"]
    assert len(dm) == 2 and doc["families"]["B1-01"]["lines"] == doc["families"]["B10-13"]["lines"] == 2
    assert doc["complete_map"] is False


def test_adverse_not_a_boq_declaration_owned_or_without_evidence():
    m = master(not_a_boq_line_codes={"STR.FORMWORK": {"evidence": ["x"]}, "ARCH.EXTERIOR": {"evidence": []}})
    _idx, doc = run(m=m)
    kinds = {i["kind"] for i in doc["issues"]}
    assert {"NOT_A_BOQ_LINE_CONFLICT", "NOT_A_BOQ_LINE_WITHOUT_EVIDENCE"} <= kinds and doc["complete_map"] is False


def test_compare_blocks_flags_a_stale_registry_block():
    _idx, doc = run()
    st = C.compare_blocks(doc, master())
    assert [(s["family"], s["registry"], s["census"]) for s in st] == [("B8-08", "no", "yes")]
    assert st[0]["registry_as_of"] == "ARCH_TAKEOFF_V3.0.7" and st[0]["census_lines"] == 3


REG = {"schema": "URBAN_T471_EIMP_REGISTER_V1", "project": "K479", "version": "1.0.0", "owner_gate": {
    "pool": ["C-GAP-POOL-FINISH"], "exterior": ["C-GAP-EXTERIOR-AREA", "C-B10-13"]}, "components": [
    {"component_id": "C-B8-08", "family": "B8-08", "applicability": "APPLICABLE", "level": 1, "evidence": ["k"],
     "item_codes": ["WP.FOUNDATION.FOOTING_MEMBRANE", "WP.FOUNDATION.LIFT_PIT_SCREED"]},
    {"component_id": "C-B10-13", "family": "B10-13", "applicability": "APPLICABLE", "level": 1, "evidence": ["k"],
     "item_codes": ["STR.FORMWORK"]},
    {"component_id": "C-B1-01", "family": "B1-01", "applicability": "NOT_APPLICABLE", "level": 1, "evidence": ["k"],
     "item_codes": []},
    {"component_id": "C-GAP-POOL-FINISH", "family": None, "applicability": "POSSIBLY_APPLICABLE", "level": 5,
     "evidence": ["k"], "item_codes": ["EXT.POOL.WATER_FACE"]},
    {"component_id": "C-GAP-EXTERIOR-AREA", "family": None, "applicability": "APPLICABLE", "level": 1,
     "evidence": ["k"], "item_codes": ["ARCH.EXTERIOR"]}]}


def test_completeness_gaps_resolved_zero_outside_zero_double():
    ls = [x for x in lines() if x["item_code"] != "STR.CONC.OTHER"]
    idx, _doc = run(ls)
    reg = K.register_1_1_0(REG, master())
    assert [c["component_id"] for c in reg["components"]] == ["C-B8-08", "C-B10-13", "C-B1-01", "C-B13-09"]
    assert reg["owner_gate"] == {"pool": ["C-B13-09"], "exterior": ["C-B10-13"]}
    doc = K.run(reg, idx, master())
    assert doc["complete_map"] is True
    assert not any(i["kind"] in ("UNMAPPED_LINE", "DOUBLY_MAPPED_LINE", "REGISTRY_GAP") for i in doc["issues"])
    assert doc["not_a_boq_lines"]["ARCH.EXTERIOR"]["quantities"]["m2"]["released"] == 9.0
    row = next(r for r in doc["rows"] if r["component_id"] == "C-B8-08")
    assert row["quantities"]["m2"]["verified"] == 4.5          # WHOLE only, the T-471 rule unchanged


def test_completeness_adverse_line_both_component_and_not_a_boq_and_unmapped():
    ls = lines()
    idx, _doc = run(ls)
    reg = K.register_1_1_0(REG, master())
    reg["components"][1]["item_codes"] = ["STR.FORMWORK", "ARCH.EXTERIOR"]
    doc = K.run(reg, idx, master())
    kinds = [i["kind"] for i in doc["issues"]]
    assert "DOUBLY_MAPPED_LINE" in kinds and "UNMAPPED_LINE" in kinds and doc["complete_map"] is False


def test_register_refuses_an_undeclared_resolution():
    with pytest.raises(ValueError):
        K.register_1_1_0(REG, master(not_a_boq_line_codes={}))
    m = master()
    m["families"] = [f for f in m["families"] if f["code"] != "B13-09"]
    with pytest.raises(ValueError):
        K.register_1_1_0(REG, m)


def test_register_takes_codes_a_family_gained_only_when_it_has_one_component():
    ls = [x for x in lines() if x["item_code"] != "STR.CONC.OTHER"]
    ls.append(mk("STR.FORMWORK.EDGE", "FW:E1", "MEASURED", 2.0, trade="CONCRETE"))   # a code B10-13 gained later
    idx, _doc = run(ls)
    m = master()
    m["families"][1]["item_codes"] = ["STR.FORMWORK", "STR.FORMWORK.EDGE"]
    reg = K.register_1_1_0(REG, m)
    assert reg["codes_added_from_registry"] == {"C-B10-13": ["STR.FORMWORK.EDGE"]}
    doc = K.run(reg, idx, m)
    assert doc["complete_map"] is True
    row = next(r for r in doc["rows"] if r["component_id"] == "C-B10-13")
    assert row["quantities"]["m2"]["released"] == 10.25                 # 8.25 + 2.00 by hand
    # adverse: two components of B10-13 -> the new code is handed to neither; its line is UNMAPPED, never guessed
    two = copy.deepcopy(REG)
    two["components"].append(dict(two["components"][1], component_id="C-B10-13-B", item_codes=[]))
    reg2 = K.register_1_1_0(two, m)
    assert reg2["codes_added_from_registry"] == {}
    doc2 = K.run(reg2, idx, m)
    assert [i["kind"] for i in doc2["issues"] if i["kind"] == "UNMAPPED_LINE"] == ["UNMAPPED_LINE"]
