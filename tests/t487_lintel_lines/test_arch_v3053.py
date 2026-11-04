"""T-487 ARCH_TAKEOFF_V3.0.53 on a synthetic villa-L candidate (hand fixture, not the development villa): B9-02 lintel
lines added from a lintel ledger by a PRINTED schedule; every candidate line byte-identical; adverse inputs refused.

Villa L by hand (its own printed schedule: L1 0 .. 1.00 m D 0.20, L2 1.01 .. 2.00 m D 0.25, L3 2.01 .. 3.00 m D 0.30;
MIN bearing 0.25 m each end):
  D1 door 0.90 m in a 0.20 wall, REQUIRED: L = 0.90 + 2 x 0.25 = 1.40; 0.20 x 0.20 x 1.40 = 0.056 m3; formwork 2 x 0.20
     x 1.40 + 0.20 x 0.90 = 0.74 m2; face 1.40 x 0.20 = 0.28 m2
  W1 window 1.80 m in a 0.15 wall, REQUIRED: L = 2.30; 0.15 x 0.25 x 2.30 = 0.08625 m3; formwork 2 x 0.25 x 2.30 + 0.15 x
     1.80 = 1.42 m2; face 2.30 x 0.25 = 0.575 m2
  W2 window 2.40 m, head HELD: blank; IF built at least 0.20 x 0.30 x 2.90 = 0.174 m3 beside (not a bound)
  W3 window 1.005 m between two printed bands: FLAGGED blank, no figure
  REQUIRED total 0.056 + 0.08625 = 0.14225 m3, 2 pieces; formwork beside 2.16 m2; host faces 0.855 m2."""
import copy
import json

import pytest

from engine.source import arch_v30 as A30
from engine.source import arch_v304 as A304
from engine.source import arch_v3050 as A50
from engine.source import arch_v3053 as M
from engine.source import boq_line as BL

PID, REV = "villa-l-t487", "0" * 64


def mk(eid, code, unit, state, net=None, floor="GF"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                        measured_net=net, gross=net, element_id=eid, floor=floor, formula="synthetic", rule_id="R-X",
                        rule_version="1", item_en=code, item_ar=code)


def candidate():
    return [mk("GF-WALLS:t=0.20", "MAS.BLOCK", "m2", "SOURCE_DERIVED", 40.0),
            mk("GF-WALLS:t=0.15", "MAS.BLOCK", "m2", "SOURCE_DERIVED", 25.5),
            mk("B1", "STR.CONC.BEAM", "m3", "PROVISIONAL", 0.9),
            mk("C1", "STR.CONC.COLUMN", "m3", "PROVISIONAL", 0.5)]


SRC = [{"task": "T-L", "file": "lintel_ledger.json", "sha256": "a" * 64, "merge_commit": "abcdef12",
        "checker_run": "run l"}]
SCHED = {"source": "villa L structural lintel schedule", "bearing_m": 0.25,
         "rows": [{"row": "L1", "lo_m": 0.0, "hi_m": 1.0, "d_m": 0.2}, {"row": "L2", "lo_m": 1.01, "hi_m": 2.0,
                                                                           "d_m": 0.25},
                  {"row": "L3", "lo_m": 2.01, "hi_m": 3.0, "d_m": 0.3}]}
OPEN = ["bearing at the jambs not measured"]


def lintels(c):
    by = {ln["location"]["element_id"]: ln["line_id"] for ln in c}
    base = {"floor": "GF", "source_tasks": ["T-L"], "basis": "ledger"}
    return [dict(base, opening_id="D1", host_wall="GF-W1", host_line=by["GF-WALLS:t=0.20"], host_net_m2=40.0,
                 kind="DOOR", wall_t_m=0.2, block_type="WHITE", width_m=0.9, decision="REQUIRED", schedule_row="L1",
                 length_m=1.4, concrete_m3=0.056, formwork_m2=0.74, face_m2=0.28, open_checks=OPEN,
                 evidence_status="ASSUMED - OWNER-APPROVED"),
            dict(base, opening_id="W1", host_wall="GF-W2", host_line=by["GF-WALLS:t=0.15"], kind="WINDOW",
                 wall_t_m=0.15, width_m=1.8, decision="REQUIRED", schedule_row="L2", length_m=2.3,
                 concrete_m3=0.08625, formwork_m2=1.42, face_m2=0.575, open_checks=OPEN,
                 evidence_status="DRAWING-CONFIRMED", checker_remeasured=True),
            dict(base, opening_id="W2", host_wall="GF-W3", host_line=None, kind="WINDOW", wall_t_m=0.2, width_m=2.4,
                 decision="HELD", schedule_row="L3", why="window head not established", evidence_status="HELD"),
            dict(base, opening_id="W3", host_wall="GF-W2", host_line=by["GF-WALLS:t=0.15"], kind="WINDOW",
                 wall_t_m=0.15, width_m=1.005, decision="FLAGGED", why="between two printed bands",
                 evidence_status="HELD")]


def doc(c, **over):
    d = {"schema": M.INPUTS_SCHEMA, "project_id": PID, "sources": SRC, "schedule": copy.deepcopy(SCHED),
         "lintels": lintels(c)}
    d.update(over)
    return d


def run(c, d):
    ch, log = M.changes_for(M.load_inputs(d, PID), c)
    return ch, log, M.integrate(c, ch)


def lint(lines):
    return {ln["calculation"]["inputs"][M.REC_KEY]["opening_id"]: ln for ln in lines if ln["item_code"] == M.CODE}


def test_hand_quantities_and_states():
    c = candidate()
    ch, log, (new, ident) = run(c, doc(c))
    L = lint(new)
    assert set(L) == {"D1", "W1", "W2", "W3"} and ident["added"] == 4 and ident["replaced"] == 0
    assert L["D1"]["measured_net"] == pytest.approx(0.056, abs=1e-9) and L["D1"]["evidence_state"] == "PROVISIONAL"
    assert L["W1"]["measured_net"] == pytest.approx(0.08625, abs=1e-9) and L["W1"]["gross"] == L["W1"]["measured_net"]
    r = L["D1"]["calculation"]["inputs"][M.REC_KEY]
    assert (r["pieces"], r["length_m"], r["formwork_m2_beside"], r["host_face_m2"]) == (1, 1.4, 0.74, 0.28)
    assert ident["lintels"] == {"lines": 4, "required": 2, "held": 1, "flagged": 1, "required_m3": 0.14225,
                                "formwork_m2_beside": 2.16, "host_face_m2_beside": 0.855}
    assert log["required_m3"] == 0.14225 and log["by_decision"] == {"FLAGGED": 1, "HELD": 1, "REQUIRED": 2}


def test_held_and_flagged_are_blank_never_zero():
    c = candidate()
    _, _, (new, _) = run(c, doc(c))
    L = lint(new)
    for k in ("W2", "W3"):
        ln = L[k]
        assert ln["evidence_state"] == "BLOCKED_RFI" and ln["measured_net"] is None and ln["gross"] is None
        assert ln["bounded_range"] is None and ln["rfi"]["question"]
    w2 = L["W2"]["calculation"]["inputs"][M.REC_KEY]
    assert w2["if_built_at_least_m3"] == pytest.approx(0.174) and "not a bound" in L["W2"]["rfi"]["bound_beside"]
    assert L["W3"]["calculation"]["inputs"][M.REC_KEY]["if_built_at_least_m3"] is None
    assert not M.FORMULA_END_RE.search(L["W2"]["calculation"]["formula"])


def test_every_candidate_line_byte_identical_and_totals_only_in_lintel():
    c = candidate()
    before = [A30.line_sha(x) for x in c]
    _, _, (new, ident) = run(c, doc(c))
    assert [A30.line_sha(x) for x in new[:len(c)]] == before
    assert ident["outside_rows_identical_to_base"] == len(c)
    moved = M.check_totals(A304.code_totals(c), A304.code_totals(new))
    assert set(k.split("|")[0] for k in moved) == {M.CODE}


def test_write_files(tmp_path):
    c = candidate()
    d = M.load_inputs(doc(c), PID)
    ch, log = M.changes_for(d, c)
    names, ident, led = M.write(tmp_path, c, ch, log)
    assert "V3_0_53_BOQ_LINES.json" in names and led["integration_package"] is True
    assert led["summary"]["required_pieces"] == 2 and led["summary"]["formwork_m2_beside"] == 2.16
    diff = (tmp_path / "V3_0_53_DIFF.csv").read_text(encoding="utf-8").splitlines()
    assert sum(",ADDED," in x for x in diff) == 4 and sum(",SAME," in x for x in diff) == 4
    run_rec = json.loads((tmp_path / "V3_0_53_RUN.json").read_text(encoding="utf-8"))
    assert run_rec["released_default"] is False and run_rec["extends"] == A50.METHOD


def test_mirror_and_order_do_not_matter():
    """a mirrored plan gives the same widths and walls: the inputs in another order give the same lines"""
    c = candidate()
    d1 = doc(c)
    d2 = doc(c, lintels=list(reversed(lintels(c))))
    a = {x["line_id"]: A30.line_sha(x) for x in run(c, d1)[2][0]}
    b = {x["line_id"]: A30.line_sha(x) for x in run(c, d2)[2][0]}
    assert a == b


# ---------------------------------------------------------------------------------------------------------- adverse
def _bad(c, mutate, match):
    d = doc(c)
    mutate(d)
    with pytest.raises(M.InputsError, match=match):
        M.changes_for(M.load_inputs(d, PID), c)


def test_width_in_millimetres_refused():
    c = candidate()
    _bad(c, lambda d: d["lintels"][0].update(width_m=900), "not a quantity in metres")


def test_typed_quantity_that_is_not_the_schedule_refused():
    c = candidate()
    _bad(c, lambda d: d["lintels"][0].update(concrete_m3=0.06), "not the printed-schedule figure")
    _bad(c, lambda d: d["lintels"][0].update(value=0.056), "never typed")


def test_wrong_band_refused():
    c = candidate()
    _bad(c, lambda d: d["lintels"][1].update(schedule_row="L1"), "not in printed band")


def test_schedule_and_precast_rule_together_refused():
    c = candidate()
    _bad(c, lambda d: d.update(precast_rule={"lengths_m": [1.2, 1.5]}), "printed lintel schedule governs")
    _bad(c, lambda d: d.update(schedule=None), "no printed lintel schedule")


def test_held_lintel_with_a_volume_refused():
    c = candidate()
    _bad(c, lambda d: d["lintels"][2].update(concrete_m3=0.0), "carries no volume")


def test_zero_wall_refused():
    c = candidate()
    _bad(c, lambda d: d["lintels"][0].update(wall_t_m=0), "not positive")


def test_missing_data_required_refused():
    c = candidate()
    _bad(c, lambda d: d["lintels"][0].pop("formwork_m2"), "formwork_m2 missing")
    _bad(c, lambda d: d["lintels"][2].pop("why"), "why missing")


def test_opening_twice_refused():
    c = candidate()
    _bad(c, lambda d: d["lintels"].append(dict(d["lintels"][0])), "named twice")


def test_host_line_not_masonry_refused():
    c = candidate()
    beam = next(x["line_id"] for x in c if x["item_code"] == "STR.CONC.BEAM")
    _bad(c, lambda d: d["lintels"][0].update(host_line=beam), "not a MAS.BLOCK line")
    _bad(c, lambda d: d["lintels"][0].update(host_net_m2=41.0), "stale binding")


def test_unknown_evidence_or_source_refused():
    c = candidate()
    _bad(c, lambda d: d["lintels"][0].update(evidence_status="GUESS"), "WORKFLOW_CONTROLS")
    _bad(c, lambda d: d["lintels"][0].update(evidence_status="HELD"), "not valued here")
    _bad(c, lambda d: d["lintels"][0].update(source_tasks=["T-X"]), "no merged")


def test_overlapping_bands_refused():
    c = candidate()
    _bad(c, lambda d: d["schedule"]["rows"][1].update(lo_m=0.9), "overlap")


def test_applied_once_and_existing_lintel_line_refused():
    c = candidate()
    _, _, (new, _) = run(c, doc(c))
    with pytest.raises(M.InputsError, match="applied once"):
        M.changes_for(M.load_inputs(doc(new), PID), new)
    c2 = c + [mk("LX", M.CODE, "m3", "PROVISIONAL", 0.1)]
    with pytest.raises(M.InputsError, match="already carries"):
        M.changes_for(M.load_inputs(doc(c2), PID), c2)


def test_check_catches_a_held_line_made_zero_and_a_wrong_volume():
    c = candidate()
    _, _, (new, _) = run(c, doc(c))
    bad = copy.deepcopy(new)
    held = next(x for x in bad if x["item_code"] == M.CODE and x["evidence_state"] == "BLOCKED_RFI")
    held["measured_net"] = 0.0
    with pytest.raises(ValueError, match="never"):
        M.check_lintels(bad)
    bad = copy.deepcopy(new)
    req = next(x for x in bad if x["item_code"] == M.CODE and x["evidence_state"] == "PROVISIONAL")
    req["measured_net"] = req["gross"] = req["measured_net"] * 1.1
    with pytest.raises(ValueError, match="1 piece"):
        M.check_lintels(bad)


def test_integrate_refuses_a_change_to_a_candidate_line():
    c = candidate()
    ch, _ = M.changes_for(M.load_inputs(doc(c), PID), c)
    other = copy.deepcopy(c[2])
    with pytest.raises(ValueError, match="only adds"):
        M.integrate(c, ch + [{"piece": M.P_LINTEL, "action": "CHANGE", "before": c[2], "after": other}])


def test_no_project_input_is_a_no_op():
    c = candidate()
    ch, log = M.changes_for(None, c)
    assert ch == [] and log["state"] == "NO_PROJECT_INPUT"


def test_extends_merged_v3050():
    assert M.EXTENDS == A50.METHOD == "ARCH_TAKEOFF_V3.0.50" and M.METHOD == "ARCH_TAKEOFF_V3.0.53"
