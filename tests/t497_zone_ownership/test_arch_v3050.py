"""T-497: ARCH_TAKEOFF_V3.0.50 (a V3.0.48 ranged excavation zone restated on the plan it alone owns, R-T497-1) on the
hand-calculated NON-Alsenan villa E350 of the T-350 tests, with the trench geometry of villa E497 (test_zone_ownership):
its V3.0.43 zone lines and V3.0.48 values are built first by the merged modules, unchanged; V3.0.48 here also ranges the
trench zone Z1-T1 the list-based way (0.185 .. 0.225 m3: only the in-plot pits removed), V3.0.50 restates it on its own
plan: 1.65 m2 in plot + 0.15 m2 beyond x 0.10 = 0.165 .. 0.180 m3 (gives up 2.00 m2 to the pits, 0.20 m2 to zone F).
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v3048 as A48  # noqa: E402
from engine.source import arch_v3050 as A  # noqa: E402
from tests.t350r4_earthworks_values import test_arch_v3048 as R4  # noqa: E402

PID = R4.PID
EID = "EW:B1-02:Z1-T1"


def v3048():
    z = R4.zones() + [{"action": "RANGE", "family": "B1-02", "zone": "Z1-TRENCH-T1", "element_id": EID,
                       "low": 0.185, "high": 0.225, "evidence_status": "HELD",
                       "basis": "strip 4.00 m2 less the in-plot pits 1.75 x 0.10", "held_items": "beyond plot 0.04",
                       "source_tasks": ["T-C"]}]
    prev, ch, _ = R4.run(R4.doc(z))
    return A48.integrate(prev, ch)[0]


def _src(t):
    return {"task": t, "file": f"research/e497/{t}.json", "sha256": "e" * 64, "merge_commit": "c" * 40,
            "checker_run": f"checker {t} own re-measure"}


def zones():
    return [{"action": "RESTATE_RANGE", "family": "B1-02", "zone": "Z1-TRENCH-T1", "element_id": EID,
             "evidence_status": "HELD", "low": 0.165, "high": 0.180, "was_low": 0.185, "was_high": 0.225,
             "given_up_m2": {"footing pits": 2.00, "footing zone F": 0.20},
             "basis": "own plan 1.65 m2 in plot + 0.15 beyond x 0.10", "held_items": "beyond plot 0.015 m3",
             "scenarios_beside": "list-based 0.185 .. 0.225 superseded", "source_tasks": ["F-E", "T-E"]}]


def doc(z=None):
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("F-E"), _src("T-E")],
            "zones": zones() if z is None else z}


def run(d=None, prev=None):
    prev = prev or v3048()
    ch, log = A.changes_for(A.load_inputs(d or doc(), PID), prev)
    return prev, ch, log


def _el(lines, code, eid):
    return next(x for x in lines if x["item_code"] == code and x["location"]["element_id"] == eid)


# ================================================================================================ normal case
def test_trench_restated_on_its_own_plan():
    prev, ch, log = run()
    new, ident = A.integrate(prev, ch)
    t, o = _el(new, A48.EXC, EID), _el(prev, A48.EXC, EID)
    assert t["line_id"] == o["line_id"] and t["evidence_state"] == "BOUNDED_EXPOSURE" and t["measured_net"] is None
    assert (t["bounded_range"]["low"], t["bounded_range"]["high"]) == (0.165, 0.180)
    inp = t["calculation"]["inputs"]
    assert inp[A.REC_KEY]["was"]["bounded_range"]["high"] == 0.225 and inp[A.PRIOR_KEY] == \
        o["calculation"]["inputs"][A.PRIOR_KEY] and inp[A.ZONE_KEY] == o["calculation"]["inputs"][A.ZONE_KEY]
    assert "footing zone F 0.2 m2" in t["rfi"]["bound_beside"]
    e = ident["earthworks"]
    assert e["restated"] == 1 and e["earthworks_v3048"]["ranged"] == 2 and e["earthworks_v3048"]["valued"] == 1
    assert log["restated_m3"] == {"B1-02|Z1-TRENCH-T1": {"was": [0.185, 0.225], "now": [0.165, 0.18]}}


def test_every_other_line_byte_identical_and_only_excavation_total_moves(tmp_path):
    prev, ch, log = run()
    names, ident, led = A.write(tmp_path, prev, ch, log)
    assert ident["outside_rows_identical_to_base"] == len(prev) - 1 and ident["added"] == 0
    run_ = json.loads((tmp_path / "V3_0_50_RUN.json").read_text(encoding="utf-8"))
    moved = run_["totals_moved_by_code"]
    assert set(moved) == {"STR.EARTH.EXCAVATION|m3"}
    diff = (tmp_path / "V3_0_50_DIFF.csv").read_text(encoding="utf-8")
    assert diff.count(",CHANGED,") == 1 and diff.count(",ADDED,") == 0 and "v3_0_50" in diff.splitlines()[0]
    assert led["integration_package"] is True and led["rows"][0]["release_status"] == "NOT RELEASED"
    # pits / backfill / held lines byte-identical
    for code, eid in ((A48.EXC, "EW:B1-02:Z1-PITS"), (A48.BKF, "EW:B1-03:Z1-PITS"), (A48.DSP, "EW:B1-04:ALL")):
        new = json.loads((tmp_path / "V3_0_50_BOQ_LINES.json").read_text(encoding="utf-8"))
        new = new["lines"] if isinstance(new, dict) else new
        assert A30.line_sha(_el(new, code, eid)) == A30.line_sha(_el(prev, code, eid))


# ================================================================================================ adverse cases
@pytest.mark.parametrize("mutate,msg", [
    (lambda z: z[0].update(high=0.30, was_high=0.30), "stale binding"),        # not the candidate's range
    (lambda z: z[0].update(high=0.25), "never grows"),                          # above the range it replaces
    (lambda z: z[0].update(low=0.19, high=0.18), "low"),
    (lambda z: z[0].update(low=0), "not positive"),
    (lambda z: z[0].update(value=0.17), "never a single value"),
    (lambda z: z[0].update(evidence_status="ESTIMATED"), "stays HELD"),
    (lambda z: z[0].update(family="B1-03"), "EXCAVATION zone only"),
    (lambda z: z[0].update(action="RANGE"), "not RESTATE_RANGE"),
    (lambda z: z[0].update(given_up_m2={"pits": 0}), "positive area"),
    (lambda z: z[0].update(given_up_m2={}), "given_up_m2 missing"),
    (lambda z: z[0].update(source_tasks=["T-X"]), "no merged"),
    (lambda z: z.append(dict(z[0])), "named twice"),
    (lambda z: z[0].update(high=180.0e3, was_high=180.0e3), "not a quantity in m3"),
])
def test_inputs_refused(mutate, msg):
    z = zones()
    mutate(z)
    with pytest.raises(A.InputsError, match=msg):
        run(doc(z))


def test_stale_binding_valued_line_and_applied_once():
    z = zones()
    z[0]["element_id"] = "EW:B1-02:Z1-PITS"                 # a VALUED line, not a ranged one
    z[0].update(was_low=8.0, was_high=9.0)
    with pytest.raises(A.InputsError, match="not a V3.0.48 ranged zone line"):
        run(doc(z))
    z[0]["element_id"] = "EW:B1-02:NOPE"
    with pytest.raises(A.InputsError, match="stale binding"):
        run(doc(z))
    prev, ch, _ = run()
    new, _ = A.integrate(prev, ch)
    with pytest.raises(A.InputsError, match="applied once"):
        run(prev=new)


def test_check_refuses_tampered_lines():
    prev, ch, _ = run()
    new, _ = A.integrate(prev, ch)
    bad = copy.deepcopy(new)
    _el(bad, A48.EXC, EID)["bounded_range"]["high"] = 0.2
    with pytest.raises(ValueError, match="not held at its record's range"):
        A.check_zone_owner(bad, prev)
    bad = copy.deepcopy(new)
    t = _el(bad, A48.EXC, EID)
    t["bounded_range"]["high"] = t["calculation"]["inputs"][A.REC_KEY]["high_m3"] = 0.3
    with pytest.raises(ValueError, match="grew beyond"):
        A.check_zone_owner(bad)
    bad = copy.deepcopy(new)
    t = _el(bad, A48.EXC, EID)
    del t["calculation"]["inputs"][A.PRIOR_KEY]
    with pytest.raises(ValueError, match="without its zone"):
        A.check_zone_owner(bad)
    bad = copy.deepcopy(new)
    _el(bad, A48.EXC, EID)["location"] = dict(_el(bad, A48.EXC, EID)["location"], floor="GF")
    with pytest.raises(ValueError, match="moved location"):
        A.check_zone_owner(bad, prev)
    # the V3.0.48 invariants still hold on every other line: a held line valued as 0 is refused
    bad = copy.deepcopy(new)
    d = _el(bad, A48.DSP, "EW:B1-04:ALL")
    d["evidence_state"], d["measured_net"] = "PROVISIONAL", 0.0
    with pytest.raises(ValueError, match="not HELD BLANK"):
        A.check_zone_owner(bad, prev)
    # without `before` the V3.0.48 form is rebuilt from the record and passes
    assert A.check_zone_owner(new)["restated"] == 1


def test_only_excavation_may_change_and_no_line_added():
    prev, ch, _ = run()
    c = copy.deepcopy(ch[0])
    c["after"]["item_code"] = "STR.EARTH.BACKFILL"
    with pytest.raises(ValueError, match="not a code this version"):
        A.integrate(prev, [c])
    c = copy.deepcopy(ch[0])
    c["action"] = "ADD"
    with pytest.raises(ValueError, match="adds no line"):
        A.integrate(prev, [c])


def test_policy():
    p = A.policy_record()
    assert p["method"] == "ARCH_TAKEOFF_V3.0.50" and p["extends"] == "ARCH_TAKEOFF_V3.0.48"
    assert p["released_default"] is False and A.DEFAULT_GUARD_CLASS == "TOOLING"
