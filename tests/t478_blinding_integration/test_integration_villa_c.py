"""T-478 integration on a synthetic villa-C candidate: the mixed footing-blinding line SPLIT (verified pits valued,
held pieces on their own lines, re-adding to the former value), a held range fixed to its scenarios, a strip line
netted (record only), a printed element added HELD BLANK; every other line byte-identical; adverse bindings refused."""
import copy

import pytest

from engine.source import arch_v30 as A30
from engine.source import arch_v3045 as M
from engine.source import boq_line as BL

PID, REV = "villa-c-t478", "0" * 64


def mk(eid, state, net=None, rng=None, code="STR.CONC.BLINDING"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit="m3", evidence_state=state,
                        measured_net=net, gross=net, element_id=eid, floor="FOUNDATION",
                        bounded_range=None if rng is None else {"low": rng[0], "high": rng[1], "basis": "x"},
                        formula="synthetic", rule_id="R-X", rule_version="1", rule_set=None)


def candidate():
    return [mk("FOOT", "PROVISIONAL", 1.342),                 # 1.053 pits + 0.272 raft (p 0.10) + 0.017 beyond
            mk("TWO_TAG", "BOUNDED_EXPOSURE", rng=(0.30, 0.36)),
            mk("GB", "BOUNDED_EXPOSURE", rng=(0.14, 0.2475)),
            mk("COL", "PROVISIONAL", 2.0, code="STR.CONC.COLUMN")]


SRC = [{"task": "T-V", "file": "ledger.csv", "sha256": "a" * 64, "merge_commit": "abcdef12", "checker_run": "run"}]


def doc(cand, **over):
    by = {ln["location"]["element_id"]: ln["line_id"] for ln in cand}
    d = {"schema": M.INPUTS_SCHEMA, "project_id": PID, "sources": SRC,
         "split": [{"line_id": by["FOOT"], "expect": {"value": 1.342},
                    "verified": {"value": 1.053, "area_m2": 10.53, "t": 0.1, "verdict": "checker", "basis": "b",
                                 "physical_element": "pits", "source_tasks": ["T-V"]},
                    "held": [{"key": "RAFT", "element_id": "RAFT", "physical_element": "raft", "low": 0.272,
                              "high": 0.29, "at_least": 0.25, "former": 0.272, "status": "AT_LEAST",
                              "blocker": "projection not printed", "basis": "b", "source_tasks": ["T-V"]},
                             {"key": "BEYOND", "element_id": "BEYOND", "physical_element": "beyond", "low": 0.0,
                              "high": 0.017, "former": 0.017, "status": "HELD", "blocker": "plot line",
                              "basis": "b", "source_tasks": ["T-V"]}]}],
         "ranges": [{"line_id": by["TWO_TAG"], "expect": {"low": 0.30, "high": 0.36}, "low": 0.27, "high": 0.36,
                     "scenarios": [{"name": "a", "clipped_m3": 0.27, "unclipped_m3": 0.30},
                                   {"name": "b", "clipped_m3": 0.33, "unclipped_m3": 0.36}],
                     "basis": "b", "why": "w", "source_tasks": ["T-V"]}],
         "netting": [{"line_id": by["GB"], "expect": {"low": 0.14, "high": 0.2475},
                      "overlap": {"overlap_m2": 1.075}, "basis": "b", "why": "w", "source_tasks": ["T-V"]}],
         "add": [{"key": "BW", "element_id": "BW", "physical_element": "wall base", "floor": "FOUNDATION",
                  "per_unit_at_least": 0.117, "per_unit": "per pad", "held_items": "pad count",
                  "basis": "b", "source_tasks": ["T-V"]}],
         "plate": {"m3": 5.0, "basis": "plate", "source_tasks": ["T-V"],
                   "terms": [{"term": "pits", "line_id": by["FOOT"], "cause": "v"},
                             {"term": "raft", "key": "RAFT", "cause": "h"},
                             {"term": "two tag", "line_id": by["TWO_TAG"], "inside_low": 0.27, "inside_high": 0.33,
                              "cause": "s"}]}}
    d.update(over)
    return d


def run(cand, d):
    ch, log = M.changes_for(M.load_inputs(d, PID), cand)
    return ch, log, M.integrate(cand, ch)


def test_split_value_add_range_net():
    cand = candidate()
    d = doc(cand)
    ch, log, (out, ident) = run(cand, d)
    assert log["by_action"] == {"ADD_HELD": 1, "NETTING": 1, "RANGE_FIX": 1, "SPLIT_ADD": 2, "SPLIT_VALUE": 1}
    by = {ln["location"]["element_id"]: ln for ln in out}
    assert by["FOOT"]["evidence_state"] == "SOURCE_DERIVED" and by["FOOT"]["measured_net"] == 1.053
    assert by["FOOT"]["line_id"] == cand[0]["line_id"]
    assert by["RAFT"]["bounded_range"]["low"] == 0.272 and by["BEYOND"]["bounded_range"]["high"] == 0.017
    assert by["TWO_TAG"]["bounded_range"]["low"] == 0.27 and by["GB"]["bounded_range"]["low"] == 0.14
    assert by["BW"]["evidence_state"] == "BLOCKED_RFI" and by["BW"]["measured_net"] is None
    assert A30.line_sha(by["COL"]) == A30.line_sha(cand[3])
    b = ident["blinding"]
    assert b == {"valued_lines": 1, "valued_m3": 1.053, "split_lines": 2, "added_held": 1, "ranges_fixed": 1,
                 "netted": 1}
    p = M.plate_restatement(M.load_inputs(d, PID), out)
    assert p["engine_valued_m3"] == 1.053 and p["closes_low"] and p["closes_high"]
    assert p["rows"][-1]["low"] == round(5.0 - 1.053 - 0.29 - 0.33, 6)


def test_write_moves_only_blinding_totals(tmp_path):
    cand = candidate()
    d = M.load_inputs(doc(cand), PID)
    ch, log = M.changes_for(d, cand)
    names, ident, led = M.write(tmp_path, cand, ch, log, doc=d)
    assert "V3_0_45_PLATE.json" in names and led["integration_package"] is True
    assert ident["diff"]["vs_base"] == {"SAME": 1, "CHANGED": 3, "ADDED": 3}


@pytest.mark.parametrize("mut,msg", [
    (lambda d: d["split"][0]["held"][0].update(former=0.30), "re-add"),
    (lambda d: d["split"][0]["held"][0].update(value=0.272), "HELD_WITH_VALUE"),
    (lambda d: d["split"][0]["verified"].update(area_m2=10.0), "is not area"),
    (lambda d: d["split"][0]["held"][0].update(status="VERIFIED"), "never VERIFIED"),
    (lambda d: d["split"][0]["held"][0].update(at_least=0.28), "above the range low"),
    (lambda d: d["ranges"][0].update(low=0.30), "min\\(clipped\\)"),
    (lambda d: d["add"][0].update(value=0.117), "HELD_WITH_VALUE"),
    (lambda d: d["add"][0].update(per_unit=None), "names its unit"),
    (lambda d: d["netting"].append(dict(d["ranges"][0], overlap={"overlap_m2": 0})), "named twice"),
])
def test_adverse_inputs_refused(mut, msg):
    cand = candidate()
    d = copy.deepcopy(doc(cand))
    mut(d)
    with pytest.raises(M.InputsError, match=msg):
        M.load_inputs(d, PID)


def test_adverse_stale_binding_and_applied_once():
    cand = candidate()
    d = doc(cand)
    d["split"][0]["expect"]["value"] = 1.342
    bad = copy.deepcopy(cand)
    bad[0]["measured_net"] = 1.5
    with pytest.raises(M.InputsError, match="stale binding"):
        M.changes_for(M.load_inputs(d, PID), bad)
    ch, _, (out, _) = run(cand, d)
    with pytest.raises(M.InputsError, match="applied once"):
        M.changes_for(M.load_inputs(d, PID), out)


def test_adverse_held_line_valued_is_caught():
    cand = candidate()
    _, _, (out, _) = run(cand, doc(cand))
    raft = next(ln for ln in out if ln["location"]["element_id"] == "BW")
    raft["evidence_state"], raft["measured_net"] = "PROVISIONAL", 0.0
    with pytest.raises(ValueError, match="HELD BLANK"):
        M.check_blinding(out, cand)
