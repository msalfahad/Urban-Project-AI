"""T-168: Gate B v2 (tools/v30_gate_b_v2.py) on a hand-made NON-Alsenan villa SYN-V2 (no client drawing: the two
"drawings" are a few made-up bytes written to tmp_path; only their sha256 matter). Every expectation is known by hand.

Villa SYN-V2: plan drawing P (bytes b"SYN plan rev 1"), structural drawing S (b"SYN structure rev 1"). As in the
real engine, the architectural lines carry the revision set of P alone and route G lines the revision set of S alone,
and route G prints its own project label "SYN-V2-ROUTE" (the T-235 s.3 identity defect): the candidate manifest
declares that label as an alias of project SYN-V2 for S's revision set only.

Lines (before = candidate SYN-V2.1, after = candidate SYN-V2.2):
  PAINT m2    E1 10.0 -> 10.0 | E2 10.0 -> 10.0004 (a 0.0004 change: flagged, scoreboard tolerance still holds)
              E3 10.0 -> 10.0 | E4 10.0 -> 10.0
  CONCRETE m3 C1 2.0 -> 2.0 (route G identity)
  PAINT m2    E0 10000.0 both (no verdict): every other paint line is 10 / 10,040 = 0.10 % of its trade
Verdicts (bound to SYN-V2.1): V-E1 (E1, COUNTED), V-E2 (E2, COUNTED), V-E34 (E3 + E4 PARTIAL, COUNTED), V-C1 (C1,
COUNTED), V-OFF (E3, checker 10.3 = +3 %: DISCREPANCY, never counted), V-OTHER (another candidate: NOT_THIS_SIDE).
Carry by hand: V-E1 CARRIED, V-E2 STALE (E2 changed), V-E34 CARRIED, V-C1 CARRIED -> one VERIFIED_CHANGED row (E2).
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from engine.source import boq_line as BL
from tools import v30_gate_b as G1
from tools import v30_gate_b_v2 as G

PID, ROUTE = "SYN-V2", "SYN-V2-ROUTE"


def h(b):
    return hashlib.sha256(b).hexdigest()


def rev(*shas):
    return h("|".join(sorted(shas)).encode())


@pytest.fixture()
def villa(tmp_path):
    p, s = tmp_path / "syn_plan.dxf", tmp_path / "syn_structure.dxf"
    p.write_bytes(b"SYN plan rev 1")
    s.write_bytes(b"SYN structure rev 1")
    dr = [{"role": "plan", "file": p.name, "size": p.stat().st_size, "sha256": h(p.read_bytes())},
          {"role": "structural", "file": s.name, "size": s.stat().st_size, "sha256": h(s.read_bytes())}]
    return {"dir": tmp_path, "plan": p, "st": s, "drawings": dr, "rev_p": rev(dr[0]["sha256"]),
            "rev_s": rev(dr[1]["sha256"])}


def ln(v, eid, q, code="FIN.PAINT", unit="m2", route=False, state="MEASURED", low=None, high=None, project=None,
       revision=None):
    kw = dict(project_id=project or (ROUTE if route else PID),
              revision_set_sha256=revision or (v["rev_s"] if route else v["rev_p"]), item_code=code, unit=unit,
              evidence_state=state, measured_net=q if state in BL.QUANTITY_STATES else None, element_id=eid,
              floor="GF", formula="synthetic", rule_id="UP-SYN", rule_version="1")
    if state == "BOUNDED_EXPOSURE":
        kw["bounded_range"] = {"low": low, "high": high, "basis": "synthetic"}
        kw["rfi"] = {"question": "synthetic hold"}
    return BL.make_line(**kw)


def runs(v):
    before = [ln(v, "E1", 10.0), ln(v, "E2", 10.0), ln(v, "E3", 10.0), ln(v, "E4", 10.0),
              ln(v, "C1", 2.0, code="STR.CONC.FOOTING", unit="m3", route=True),
              ln(v, "E0", 10000.0)]                                # keeps every other paint share under 2 %
    after = copy.deepcopy(before)
    after[1] = ln(v, "E2", 10.0004)
    return before, after


def dumps_sha(lines):
    t = BL.dumps(lines)
    return t, h(t.encode("utf-8"))


def manifest(v, lines, cver, verdicts=None, project=PID, drawings=None):
    _, s = dumps_sha(lines)
    m = G.build_candidate_manifest(lines, s, candidate_version=cver, code_commit="abcdef1234", project_id=project,
                                   drawings=drawings or v["drawings"], verdicts=verdicts)
    return m, h(json.dumps(m, sort_keys=True).encode())


def vrec(lines, vid, eids, checker, cver="SYN-V2.1", scope="WHOLE"):
    sel = [x for x in lines if x["location"]["element_id"] in eids]
    _, s = dumps_sha(lines)
    return {"schema": "URBAN_CHECKER_VERDICT_V2", "verdict_id": vid, "project_id": sel[0]["project"]["project_id"],
            "revision_set_sha256": sel[0]["project"]["revision_set_sha256"], "candidate_version": cver,
            "boq_lines_sha256": s, "line_ids": sorted(x["line_id"] for x in sel),
            "element_scope": {"ids": sorted(eids), "count": len(eids)}, "unit": sel[0]["unit"],
            "engine_qty": round(sum(x["measured_net"] for x in sel), 6), "checker_qty": checker,
            "evidence": [{"sheet": "SYN-A1", "printed_value": "synthetic"}],
            "checker": {"run_token": "syn", "routine": "Checker", "verdict_commit": "abcdef12"},
            "scope": scope, "time": "2026-10-24T10:00:00Z"}


def verdicts(before):
    return [vrec(before, "V-E1", ["E1"], 10.0), vrec(before, "V-E2", ["E2"], 10.02),
            vrec(before, "V-E34", ["E3", "E4"], 20.1, scope="PARTIAL"), vrec(before, "V-C1", ["C1"], 2.0),
            vrec(before, "V-OFF", ["E3"], 10.3), vrec(before, "V-OTHER", ["E1"], 10.0, cver="SYN-V2.0")]


def run_diff(v, before, after, **kw):
    mb = kw.pop("before_manifest") if "before_manifest" in kw else manifest(v, before, "SYN-V2.1")
    ma = kw.pop("after_manifest") if "after_manifest" in kw else manifest(v, after, "SYN-V2.2")
    args = dict(before_manifest=mb, after_manifest=ma,
                before_sha=dumps_sha(before)[1], after_sha=dumps_sha(after)[1])
    args.update(kw)
    return G.diff(before, after, **args)


def rows(doc):
    return {r["element_id"]: r for r in doc["rows"]}


# ------------------------------------------------------------------------------------------------- normal case
def test_pinned_diff_names_both_sides_and_the_route_alias(villa):
    b, a = runs(villa)
    doc = run_diff(villa, b, a, verdicts=verdicts(b))
    for side, cver in (("before", "SYN-V2.1"), ("after", "SYN-V2.2")):
        s = doc["sides"][side]
        assert s["kind"] == "CANDIDATE" and s["spec_id"] == cver and s["project_id"] == PID
        assert len(s["manifest_sha256"]) == 64 and s["boq_lines_sha256"] == dumps_sha(b if side == "before" else a)[1]
        assert {(i["line_project_id"], tuple(i["drawing_roles"]), i["alias"]) for i in s["identities"]} == \
            {(PID, ("plan",), False), (ROUTE, ("structural",), True)}


def test_verdict_carry_by_hand(villa):
    b, a = runs(villa)
    doc = run_diff(villa, b, a, verdicts=verdicts(b))
    st = {x["verdict_id"]: (x["before"], x["carry"]) for x in doc["verdicts"]}
    assert st == {"V-E1": ("COUNTED", "CARRIED"), "V-E2": ("COUNTED", "STALE"), "V-E34": ("COUNTED", "CARRIED"),
                  "V-C1": ("COUNTED", "CARRIED"), "V-OFF": ("DISCREPANCY", None), "V-OTHER": ("NOT_THIS_SIDE", None)}
    r = rows(doc)
    assert r["E2"]["flags"] == ["VERIFIED_CHANGED"] and r["E2"]["scoreboard_tolerance_holds"] is True
    assert r["E2"]["verdict_carry"] == "STALE" and r["E2"]["change_log"] == "MISSING"
    assert r["E1"]["verdict_carry"] == "CARRIED" and r["E3"]["verified_by"] == ["V-E34"]   # V-OFF never counts
    assert [x for x in doc["rows"] if "VERIFIED_CHANGED" in x["flags"]] == [r["E2"]]
    s = doc["summary"]
    assert (s["verified_changed"], s["verified_changed_unlogged"], s["verdicts_counted_before"], s["verdicts_carried"],
            s["verdicts_stale"], s["status"]) == (1, 1, 4, 3, 1, "REVIEW_REQUIRED")
    req = doc["changes_required"]["rows"]
    assert len(req) == 1 and req[0]["old"] == 10.0 and req[0]["new"] == 10.0004 and req[0]["verified_by"] == ["V-E2"]


def test_t156_flags_and_counts_unchanged_without_verdicts():
    from tests.t156_gate_b.test_v30_gate_b import EXPECTED, REGISTER, runs as t156_runs
    b, a = t156_runs()
    v1 = G1.diff(b, a, register=REGISTER)
    v2 = G.diff(b, a, register=REGISTER, require_manifests=False)
    assert {r["row_id"]: set(r["flags"]) for r in v2["rows"]} == EXPECTED
    for k in ("rows", "changed_rows", "changed_rows_unflagged", "flagged", "unflagged", "pairing"):
        assert v2["summary"][k] == v1["summary"][k]
    assert {k: v for k, v in v2["summary"]["per_rule"].items() if k != "VERIFIED_CHANGED"} == v1["summary"]["per_rule"]
    assert v2["summary"]["status"] == "CHECKS_COMPLETE" and G1.remaining(v2) == G1.remaining(v1)


def test_stale_verdict_takes_its_unchanged_lines_out_too(villa):
    b, a = runs(villa)
    a[2] = ln(villa, "E3", 10.5)                                   # E3 of the two-line verdict V-E34 moves +5 %
    doc = run_diff(villa, b, a, verdicts=verdicts(b)[:4])
    r = rows(doc)
    assert set(r["E3"]["flags"]) == {"VERIFIED_CHANGED", "MOVED_5PCT"} and r["E4"]["flags"] == []
    assert r["E4"]["verdict_carry"] == "STALE_WITH_VERDICT"


def test_reverified_only_with_a_new_bound_verdict_cited_in_the_log(villa, tmp_path):
    b, a = runs(villa)
    a[1] = ln(villa, "E2", 10.6)
    new_v = vrec(a, "V-E2-NEW", ["E2"], 10.6, cver="SYN-V2.2")
    log = G.changes_append(tmp_path / "CH.json", {"line_id": a[1]["line_id"], "element_ids": ["E2"], "unit": "m2",
                                                  "old": 10.0, "new": 10.6, "cause": "wall length re-read",
                                                  "evidence": [{"sheet": "SYN-A1", "value": "6.00 m"}],
                                                  "checker_verdict": "V-E2-NEW"},
                           candidate_version="SYN-V2.2", project_id=PID)
    doc = run_diff(villa, b, a, verdicts=verdicts(b)[:4] + [new_v], changes=log)
    r = rows(doc)["E2"]
    assert r["verdict_carry"] == "REVERIFIED" and r["change_log"] == log["changes"][0]["change_id"]
    assert "VERIFIED_CHANGED" in r["flags"] and doc["summary"]["status"] == "REVIEW_REQUIRED"   # still reviewed
    doc = run_diff(villa, b, a, verdicts=verdicts(b)[:4], changes=log)                       # verdict not given
    assert rows(doc)["E2"]["verdict_carry"] == "STALE"


def test_unchanged_quantity_on_a_new_revision_set_is_verified_changed(villa, tmp_path):
    b, _ = runs(villa)
    p2 = tmp_path / "syn_plan.dxf"                                   # same file name, new bytes: a reissued plan
    p2.write_bytes(b"SYN plan rev 2")
    d2 = [dict(villa["drawings"][0], sha256=h(p2.read_bytes()), size=p2.stat().st_size), villa["drawings"][1]]
    a = [ln(villa, x["location"]["element_id"], x["measured_net"], code=x["item_code"], unit=x["unit"],
            route=x["project"]["project_id"] == ROUTE,
            revision=None if x["project"]["project_id"] == ROUTE else rev(d2[0]["sha256"])) for x in b]
    ma = manifest(villa, a, "SYN-V2.2", drawings=d2)
    with pytest.raises(G.Refused) as ex:                            # same name, different sha256: refused
        run_diff(villa, b, a, after_manifest=ma, verdicts=verdicts(b))
    assert ex.value.codes == ["DRAWING_MISMATCH"]
    doc = run_diff(villa, b, a, after_manifest=ma, verdicts=verdicts(b), new_revision_set=True)
    r = rows(doc)
    assert {e for e, x in r.items() if "VERIFIED_CHANGED" in x["flags"]} == {"E1", "E2", "E3", "E4"}
    assert r["E1"]["delta"] == 0.0 and r["C1"]["verdict_carry"] == "CARRIED"   # route G drawing unchanged
    assert len(doc["summary"]["revision_changes"]) == 1


# ------------------------------------------------------------------------------------------------- refusals
def test_missing_manifest_refused(villa):
    b, a = runs(villa)
    with pytest.raises(G.Refused) as ex:
        G.diff(b, a, after_manifest=manifest(villa, a, "SYN-V2.2"))
    assert ex.value.codes == ["MANIFEST_MISSING"]


def test_mismatched_manifest_refused(villa):
    b, a = runs(villa)
    with pytest.raises(G.Refused) as ex:                            # manifest of the after file used for the before
        run_diff(villa, b, a, before_manifest=manifest(villa, a, "SYN-V2.2"))
    assert "MANIFEST_MISMATCH" in ex.value.codes
    m, s = manifest(villa, b, "SYN-V2.1")
    m["line_count"] = 4
    with pytest.raises(G.Refused) as ex:
        run_diff(villa, b, a, before_manifest=(m, s))
    assert ex.value.codes == ["MANIFEST_MISMATCH"]
    with pytest.raises(G.Refused) as ex:
        run_diff(villa, b, a, before_manifest=({"schema": "SOMETHING_ELSE"}, None))
    assert ex.value.codes == ["MANIFEST_INVALID"]


def test_release_manifest_spec_and_status_checked(villa, tmp_path):
    b, a = runs(villa)
    spec = tmp_path / "spec.json"
    spec.write_bytes(b'{"schema": "URBAN_BASELINE_SPEC_V1"}')
    _, bsha = dumps_sha(b)
    rel = {"schema": "URBAN_BASELINE_MANIFEST_V1", "baseline_id": "SYN-B", "status": "REPRODUCED",
           "spec_sha256": h(spec.read_bytes()), "project": PID, "engine": {"commit": "abc"},
           "inputs": [dict(d) for d in villa["drawings"]], "run": {"line_count": 6, "outputs_sha256":
                                                                   {"BOQ_LINES.json": bsha}}}
    with pytest.raises(G.Refused) as ex:                            # the route label is not the release's project
        run_diff(villa, b, a, before_manifest=(rel, "f" * 64), before_spec_sha=h(spec.read_bytes()))
    assert ex.value.codes == ["PROJECT_MIX"]
    b3 = [x if x["project"]["project_id"] == PID else ln(villa, "C1", 2.0, code="STR.CONC.FOOTING", unit="m3",
                                                         route=True, project="new project") for x in b]
    rel3 = json.loads(json.dumps(rel))
    rel3["run"]["outputs_sha256"]["BOQ_LINES.json"] = dumps_sha(b3)[1]
    ok3 = G.diff(b3, a[:4], before_manifest=(rel3, "f" * 64), after_manifest=manifest(villa, a[:4], "SYN-V2.2"),
                 before_sha=dumps_sha(b3)[1], after_sha=dumps_sha(a[:4])[1])
    assert {(i["line_project_id"], i["alias"]) for i in ok3["sides"]["before"]["identities"]} == \
        {(PID, False), ("new project", True)}                       # a route run without the id: listed alias
    b2 = [x for x in b if x["project"]["project_id"] == PID]
    _, b2sha = dumps_sha(b2)
    rel2 = json.loads(json.dumps(rel))
    rel2["run"] = {"line_count": len(b2), "outputs_sha256": {"BOQ_LINES.json": b2sha}}
    ok = G.diff(b2, a[:4], before_manifest=(rel2, "f" * 64), after_manifest=manifest(villa, a[:4], "SYN-V2.2"),
                before_sha=b2sha, after_sha=dumps_sha(a[:4])[1], before_spec_sha=h(spec.read_bytes()))
    assert ok["sides"]["before"]["kind"] == "RELEASE" and ok["sides"]["before"]["spec_id"] == "SYN-B"
    with pytest.raises(G.Refused) as ex:
        G.diff(b2, a[:4], before_manifest=(rel2, "f" * 64), after_manifest=manifest(villa, a[:4], "SYN-V2.2"),
               before_sha=b2sha, after_sha=dumps_sha(a[:4])[1], before_spec_sha="0" * 64)
    assert ex.value.codes == ["MANIFEST_MISMATCH"]
    rel2["status"] = "NOT_REPRODUCED"
    with pytest.raises(G.Refused) as ex:
        G.diff(b2, a[:4], before_manifest=(rel2, "f" * 64), after_manifest=manifest(villa, a[:4], "SYN-V2.2"))
    assert ex.value.codes == ["MANIFEST_INVALID"]


def test_two_project_sides_refused(villa):
    b, a = runs(villa)
    with pytest.raises(G.Refused) as ex:
        run_diff(villa, b, a, after_manifest=manifest(villa, a, "SYN-V2.2", project="SYN-OTHER-VILLA"))
    assert ex.value.codes == ["PROJECT_MIX"]


def test_line_from_an_unpinned_drawing_refused_whatever_its_label(villa):
    b, a = runs(villa)
    _, s = dumps_sha(a)
    a2 = a + [ln(villa, "X9", 3.0, route=True, revision=rev(h(b"another villa's drawing")))]
    with pytest.raises(G.Refused) as ex:                            # the builder refuses it ...
        G.build_candidate_manifest(a2, dumps_sha(a2)[1], candidate_version="SYN-V2.2", code_commit="abcdef1",
                                   project_id=PID, drawings=villa["drawings"])
    assert ex.value.codes == ["REVISION_MIX"]
    m, ms = manifest(villa, a, "SYN-V2.2")
    m["line_count"] += 1
    m["boq_lines_sha256"] = dumps_sha(a2)[1]
    with pytest.raises(G.Refused) as ex:                            # ... and so does the diff with a hand-edited one
        run_diff(villa, b, a2, after_manifest=(m, ms), after_sha=dumps_sha(a2)[1])
    assert ex.value.codes == ["REVISION_MIX"]


def test_sealed_project_and_sealed_names_refused(villa, tmp_path):
    b, a = runs(villa)
    reg = {"schema": "URBAN_SEALED_REGISTRY_V1", "entries": [{"kind": "SEALED_PROJECT", "project_id": PID,
                                                              "sha256": None, "label": "a sealed test villa"}]}
    with pytest.raises(G.Refused) as ex:
        run_diff(villa, b, a, sealed_registry=reg)
    assert ex.value.codes == ["SEALED"]
    default = G.load_sealed_registry()
    names = G.sealed_names(default)
    assert {"QORTUBA_BENCHMARK_SEAL.json", "QORTUBA_FINAL_PRE_PRICING_TAKEOFF.json", "site_benchmark.json"} <= names
    p = tmp_path / "QORTUBA_BENCHMARK_SEAL.json"
    p.write_bytes(b"{}")
    with pytest.raises(G.Refused) as ex:
        G.guard_inputs({"verdicts": p})
    assert ex.value.codes == ["SEALED"]
    assert all(e["sha256"] is None or len(e["sha256"]) == 64 for e in default["entries"])


def test_invalid_verdict_file_refused(villa):
    b, a = runs(villa)
    bad = verdicts(b)[:1]
    bad[0]["checker"]["routine"] = "Worker 1"                       # a verdict is the Checker's alone
    with pytest.raises(G.Refused) as ex:
        run_diff(villa, b, a, verdicts=bad)
    assert ex.value.codes == ["VERDICTS_INVALID"]


# ------------------------------------------------------------------------------------------------- change log
def test_change_log_append_only_and_cause_required(tmp_path):
    rec = {"line_id": "L-1", "element_ids": ["E1"], "unit": "m2", "old": 10.0, "new": 10.5, "cause": "  ",
           "evidence": [{"sheet": "SYN-A1", "value": "5.25 m"}], "checker_verdict": "NONE"}
    with pytest.raises(G.Refused) as ex:
        G.changes_append(tmp_path / "C.json", rec, candidate_version="V", project_id="P")
    assert ex.value.codes == ["CHANGES_INVALID"] and not (tmp_path / "C.json").exists()
    rec["cause"] = "length re-read"
    d1 = G.changes_append(tmp_path / "C.json", rec, candidate_version="V", project_id="P")
    held = dict(rec, line_id="L-2", old=None, new=4.0)
    d2 = G.changes_append(tmp_path / "C.json", held, candidate_version="V", project_id="P")
    assert [c["seq"] for c in d2["changes"]] == [1, 2] and d2["changes"][0] == d1["changes"][0]
    assert d1["changes"][0]["difference"] == 0.5 and d2["changes"][1]["difference"] is None   # held: never 0
    assert G.check_append_only(d1, d2) == [] and G.validate_changes(d2, "V", "P") == []
    edited = json.loads(json.dumps(d2))
    edited["changes"][0]["new"] = 10.4
    assert G.check_append_only(d2, edited) and G.validate_changes(edited)                     # tamper visible
    assert G.check_append_only(d2, {**d2, "changes": d2["changes"][1:]})
    with pytest.raises(G.Refused):
        G.changes_append(tmp_path / "C.json", rec, candidate_version="OTHER", project_id="P")
    with pytest.raises(G.Refused):
        G.changes_append(tmp_path / "C.json", dict(rec, evidence=[]), candidate_version="V", project_id="P")


# ------------------------------------------------------------------------------------------------- two baselines
def test_element_diff_against_run_a_by_hand(villa):
    a_lines = [ln(villa, "E1", 10.0, project="new project"), ln(villa, "E2", 10.0, project="new project"),
               ln(villa, "E3", 10.0, project="new project"), ln(villa, "E4", 10.0, project="new project"),
               ln(villa, "E5", 10.0, project="new project")]
    after = [ln(villa, "E1", 10.0), ln(villa, "E2", 10.4), ln(villa, "E3", 11.0),
             ln(villa, "E4", None, state="BOUNDED_EXPOSURE", low=9.0, high=11.0), ln(villa, "E6", 1.0)]
    d = G.element_diff(a_lines, after)
    r = {x["element_id"]: x for x in d["rows"]}
    assert {k: x["status"] for k, x in r.items()} == {"E1": "SAME", "E2": "CHANGED", "E3": "CHANGED",
                                                      "E4": "STATE_CHANGE", "E5": "DROPPED", "E6": "NEW"}
    assert r["E2"]["delta_pct"] == 4.0 and r["E2"]["flags"] == [] and r["E3"]["flags"] == ["MOVED_5PCT"]
    assert r["E4"]["delta"] is None and r["E4"]["after"]["qty"] is None and r["E4"]["after"]["low"] == 9.0
    assert d["summary"]["by_status"] == {"CHANGED": 2, "DROPPED": 1, "NEW": 1, "SAME": 1, "STATE_CHANGE": 1}


def test_two_baseline_report_in_one_diff(villa):
    b, a = runs(villa)
    a_lines = [ln(villa, x["location"]["element_id"], x["measured_net"], code=x["item_code"], unit=x["unit"],
                  project="new project", revision=x["project"]["revision_set_sha256"]) for x in b]
    _, asha = dumps_sha(a_lines)
    rel = {"schema": "URBAN_BASELINE_MANIFEST_V1", "baseline_id": "SYN-A", "status": "RUN_NO_EXPECTED_FIGURES",
           "spec_sha256": "1" * 64, "project": None, "engine": {"commit": "abc"},
           "inputs": [dict(d) for d in villa["drawings"]],
           "run": {"line_count": 6, "outputs_sha256": {"BOQ_LINES.json": asha}}}
    doc = run_diff(villa, b, a, baseline_a=a_lines, baseline_a_manifest=(rel, "e" * 64), baseline_a_sha=asha)
    assert doc["sides"]["baseline_a"]["spec_id"] == "SYN-A" and doc["sides"]["baseline_a"]["project_id"] is None
    assert doc["element_diff_a"]["summary"]["by_status"] == {"CHANGED": 1, "SAME": 5}
    rel_bad = json.loads(json.dumps(rel))
    rel_bad["inputs"][0]["sha256"] = "0" * 64
    rel_bad["inputs"][0]["file"] = "other_plan.dxf"
    rel_bad["inputs"][0]["role"] = "plan-old"
    with pytest.raises(G.Refused) as ex:                            # A measured on drawings the after side does not pin
        run_diff(villa, b, a, baseline_a=a_lines, baseline_a_manifest=(rel_bad, "e" * 64), baseline_a_sha=asha)
    assert "REVISION_MIX" in ex.value.codes or "DRAWING_MISMATCH" in ex.value.codes


# ------------------------------------------------------------------------------------------------- manifest content
def test_candidate_manifest_content(villa, tmp_path):
    b, _ = runs(villa)
    b.append(ln(villa, "H1", None, state="BOUNDED_EXPOSURE", low=1.0, high=2.0))
    regcsv = tmp_path / "REGISTER.csv"
    regcsv.write_text("sheet_key,revision_basis\nSYN-A1,FILE_PIN\nSYN-A2,PRINTED\nSYN-S1,FILE_PIN\n", encoding="utf-8")
    vs = verdicts(b[:6])
    _, s = dumps_sha(b)
    for v in vs:
        v["boq_lines_sha256"] = s
    m = G.build_candidate_manifest(b, s, candidate_version="SYN-V2.1", code_commit="abcdef1", project_id=PID,
                                   drawings=villa["drawings"], document_register=G.register_basis(regcsv),
                                   verdicts=vs)
    assert m["revision_set_sha256"] == rev(*(d["sha256"] for d in villa["drawings"]))
    assert m["document_register"]["revision_basis"] == {"FILE_PIN": 2, "PRINTED": 1}
    lines = {x["element_id"]: x for x in m["lines"]}
    assert lines["H1"]["measured_net"] is None and (lines["H1"]["low"], lines["H1"]["high"]) == (1.0, 2.0)
    assert lines["E1"]["verification"] == "COUNTED" and ["V-E1", "COUNTED"] in lines["E1"]["verdicts"]
    assert lines["E3"]["verdicts"] == [["V-E34", "COUNTED"], ["V-OFF", "DISCREPANCY"]]
    pc = {(x["item_code"], x["unit"]): x for x in m["baseline_quantities"]}
    assert pc[("FIN.PAINT", "m2")]["released_qty"] == 10040.0 and pc[("FIN.PAINT", "m2")]["held_lines"] == 1
    assert "syn_plan" not in json.dumps(m["lines"])                 # drawings by hash only in the line records


# ------------------------------------------------------------------------------------------------- CLI and freelancer
def _cli_setup(villa):
    d = villa["dir"]
    b, a = runs(villa)
    for n, lines in (("b.json", b), ("a.json", a)):
        (d / n).write_text(BL.dumps(lines), encoding="utf-8")
    for n, lines, cv in (("mb.json", "b.json", "SYN-V2.1"), ("ma.json", "a.json", "SYN-V2.2")):
        assert G.main(["manifest", "--lines", str(d / lines), "--candidate-version", cv, "--code-commit", "abcdef1",
                       "--project-id", PID, "--drawing", f"plan={villa['plan']}", "--drawing",
                       f"structural={villa['st']}", "--out", str(d / n)]) == 0
    (d / "v.json").write_text(json.dumps({"schema": "URBAN_CHECKER_VERDICT_V2_SET",
                                          "verdicts": sorted(verdicts(b), key=lambda v: v["verdict_id"])}),
                              encoding="utf-8")
    return d


def _cli_diff(d, out, *extra):
    return G.main(["diff", str(d / "b.json"), str(d / "a.json"), "--before-manifest", str(d / "mb.json"),
                   "--after-manifest", str(d / "ma.json"), "--verdicts", str(d / "v.json"), "--out", str(out),
                   "--sha", "a1b2c3d4", *extra])


def test_cli_end_to_end_and_refusal(villa, capsys):
    d = _cli_setup(villa)
    assert _cli_diff(d, d / "o") == 0
    doc = json.loads((d / "o" / "GATE_B_DIFF_V2.json").read_text(encoding="utf-8"))
    assert doc["summary"]["verified_changed"] == 1 and doc["random_picks"]["L"] == doc["summary"]["unflagged"]
    assert set(doc["inputs_sha256"]) == {"after", "after_manifest", "before", "before_manifest", "verdicts"}
    req = json.loads((d / "o" / "ESTABLISHED_QUANTITY_CHANGES_REQUIRED.json").read_text(encoding="utf-8"))
    assert len(req["rows"]) == 1
    assert "VERIFIED_CHANGED" in (d / "o" / "GATE_B_DIFF_V2.csv").read_text(encoding="utf-8")
    rc = G.main(["diff", str(d / "b.json"), str(d / "a.json"), "--after-manifest", str(d / "ma.json"),
                 "--out", str(d / "o2")])
    assert rc == 2 and not (d / "o2").exists() and "MANIFEST_MISSING" in capsys.readouterr().err
    rc = G.main(["change-add", "--log", str(d / "CH.json"), "--candidate-version", "SYN-V2.2", "--project-id", PID,
                 "--line-id", doc["changes_required"]["rows"][0]["line_id"], "--element-id", "E2", "--unit", "m2",
                 "--old", "10", "--new", "10.0004", "--cause", "synthetic rounding fix", "--evidence",
                 "SYN-A1=4.0001 m", "--checker-verdict", "NONE"])
    assert rc == 0
    assert _cli_diff(d, d / "o3", "--changes", str(d / "CH.json")) == 0
    doc3 = json.loads((d / "o3" / "GATE_B_DIFF_V2.json").read_text(encoding="utf-8"))
    assert doc3["summary"]["verified_changed_unlogged"] == 0


def test_freelancer_file_changes_no_engine_output(villa):
    d = _cli_setup(villa)
    assert _cli_diff(d, d / "clean") == 0
    fl = d / "freelancer_boq.json"                                   # a reference workbook export beside the inputs
    fl.write_text(json.dumps({"rows": [{"row_id": "R1", "trade": "PAINT", "unit": "m2", "qty": 999.0}]}),
                  encoding="utf-8")
    assert _cli_diff(d, d / "with_fl") == 0
    for n in ("GATE_B_DIFF_V2.json", "GATE_B_DIFF_V2.csv", "ESTABLISHED_QUANTITY_CHANGES_REQUIRED.json"):
        assert (d / "clean" / n).read_bytes() == (d / "with_fl" / n).read_bytes()
    assert (G1.SHARE_PCT, G1.MOVE_PCT, G.QTY_MATCH_TOL, G.DISCREPANCY_REL) == (2.0, 5.0, 0.0005, 0.01)
    with pytest.raises(G.Refused) as ex:                            # a freelancer file is never a BOQ side
        G.read_lines(fl)
    assert ex.value.codes == ["INPUT_INVALID"]


def test_per_code_equals_the_t165_runner_figures(villa):
    from tools import release_baseline as RB
    b, _ = runs(villa)
    b.append(ln(villa, "H1", None, state="BOUNDED_EXPOSURE", low=1.0, high=2.0))
    assert G.per_code(b) == RB.per_code(b)
