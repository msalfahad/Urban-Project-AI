"""Phase 2B-3 (ARCH_TAKEOFF_V2.5) project rules sheets (WP-5) and BOQ traceability (WP-6), through the CLI on the
proof drawing PD-1 (two WP-B bathrooms and a corridor, drawn): the scope of a ROOM rule, a same-rank conflict, the
binding to the drawing's sha256, the invalidation of earlier outputs; the traceability chain of every BOQ line with
the five statuses, INDEPENDENTLY_VERIFIED only from an independent value for that line."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import proof_cases as C                                       # noqa: E402
import proof_cases_rules as RC                                # noqa: E402
import proof_drawings as PD                                   # noqa: E402
import proof_engine as E                                      # noqa: E402
from engine.source import traceability as TR                  # noqa: E402


@pytest.fixture(scope="module")
def pd1(tmp_path_factory):
    return PD.bathrooms(tmp_path_factory.mktemp("pd") / "pd1.dxf")


def _check(expected, q):
    bad = []
    for k, e in expected.items():
        v = q.get(k)
        if isinstance(e, dict):
            for kk, ee in e.items():
                vv = (v or {}).get(kk)
                if not (ee == vv or (isinstance(ee, float) and isinstance(vv, float) and abs(ee - vv) < 1e-6)):
                    bad.append((k, kk, ee, vv))
        elif e != v:
            bad.append((k, e, v))
    return bad


@pytest.mark.parametrize("case", [RC.RS_01, RC.RS_02, RC.RS_03], ids=lambda c: c["id"])
def test_rules_sheet_cases(case, pd1, tmp_path):
    run = E.cli_run(pd1, tmp_path / "out", rules=case["rules"])
    assert run["code"] == 0
    assert _check(case["expected"], E.rules_quantities(case, run)) == []
    sheet = run["read"]("PROJECT_RULES_SHEET.json")["sheet"]
    assert sheet["project"]["drawing"]["sha256"] == E._sha(pd1)            # tied to the drawing and its input hash
    assert sheet["rules_sha256"] and sheet["sheet_sha256"]
    for r in sheet["rows"]:                                                 # the columns the program asks for
        assert {"urban_standard", "drawing_specification", "applied_rule", "source", "status", "impact"} <= set(r)


def test_a_rules_file_for_another_drawing_is_refused_and_an_unbound_one_flagged(pd1, tmp_path):
    with pytest.raises(SystemExit) as ex:
        E.cli_run(pd1, tmp_path / "wrong", rules=RC.RS_04["rules"])
    assert "PROJECT_RULES_DRAWING_MISMATCH" in str(ex.value)
    assert not (tmp_path / "wrong" / "BOQ_LINES.json").exists()            # refused before any quantity
    run = E.cli_run(pd1, tmp_path / "unbound", rules=RC.RS_04["rules_unbound"])
    q = E.rules_quantities(RC.RS_04, run)
    exp = RC.RS_04["expected"]
    assert (q["binding"], q["open_items_project_rules"], q["BATH1"]["upturn_m2"]) == (
        exp["unbound_binding"], exp["unbound_open_items"], exp["unbound_BATH1_upturn_m2"])
    assert any(a.get("subject") == "PROJECT_RULES" and "drawing_sha256" in a["what"]
               for a in run["read"]("APPROVALS_REQUIRED.json")["approvals"]["items"])


def test_a_changed_rules_sheet_supersedes_the_earlier_outputs(pd1, tmp_path):
    out = tmp_path / "out"
    E.cli_run(pd1, out, rules=RC.RS_05["rules"])
    changed = copy.deepcopy(RC.RS_05["rules"])
    changed["rules"][0]["value"] = RC.RS_05["changed_value"]
    run = E.cli_run(pd1, out, rules=changed)
    sheet = run["read"]("PROJECT_RULES_SHEET.json")["sheet"]
    exp = RC.RS_05["expected"]
    assert sheet["invalidation"]["state"] == exp["invalidation"]
    assert (out / "SUPERSEDED_1").is_dir() == exp["superseded_folder"]
    assert E.rules_quantities(RC.RS_05, run)["BATH1"]["upturn_m2"] == pytest.approx(exp["BATH1_upturn_m2"])


def _checks_from_hand(run, case):
    """an independent checks file typed from a case's hand calculation (the reviewer's own figures), for the rooms
    of PD-1 that are that case."""
    ids = E.pd1_room_ids(run)
    e = case["expected"]
    checks = []
    for name, rid in ids.items():
        checks += [{"room_id": rid, "item_code": "FIN.WP.FLOOR", "value": e["A_net_m2"], "tolerance": 0.001,
                    "source": f"hand calculation {case['id']}"},
                   {"room_id": rid, "item_code": "FIN.WP.WALL_UPTURN", "value": e["upturn_m2"], "tolerance": 0.001,
                    "source": f"hand calculation {case['id']}"}]
    return {"schema": TR.SCHEMA_CHECKS, "checks": checks}


def test_traceability_statuses_follow_independent_values_only(pd1, tmp_path):
    first = E.cli_run(pd1, tmp_path / "plain")
    tr = first["read"]("BOQ_TRACEABILITY.json")["traceability"]
    assert tr["summary"]["by_status"]["INDEPENDENTLY_VERIFIED"] == 0          # tests passing are not verification
    assert set(tr["statuses"]) == set(TR.STATUSES)
    up = [r for r in tr["rows"] if r["item_code"] == "FIN.WP.WALL_UPTURN"]
    assert up and all(r["status"] == "ENGINE_TESTED_ONLY" and r["method_status"] == "INDEPENDENTLY_PROVEN_ON_CASES"
                      for r in up)
    assert all(r["status"] == "BLOCKED_MISSING_EVIDENCE" for r in tr["rows"] if r["engine_result"] is None)
    for r in tr["rows"]:                                                       # the whole chain on every line
        assert r["owner_rule"] and r["drawing_evidence"] and r["formula"] and r["rules_sha256"]
    run = E.cli_run(pd1, tmp_path / "checked", checks=_checks_from_hand(first, C.WP_B))
    rows = run["read"]("BOQ_TRACEABILITY.json")["traceability"]["rows"]
    ver = [r for r in rows if r["status"] == "INDEPENDENTLY_VERIFIED"]
    assert {(r["item_code"]) for r in ver} == {"FIN.WP.FLOOR", "FIN.WP.WALL_UPTURN"} and len(ver) == 4
    assert all(r["independent_source"] == "hand calculation WP-B" and r["difference"] == 0 for r in ver)
    wrong = _checks_from_hand(first, C.WP_B)
    wrong["checks"][1]["value"] = 2.8                                          # a wrong independent figure
    run = E.cli_run(pd1, tmp_path / "wrong", checks=wrong)
    rows = run["read"]("BOQ_TRACEABILITY.json")["traceability"]["rows"]
    assert sum(1 for r in rows if r["status"] == "FAILED_VALIDATION") == 1


def test_every_method_proof_listed_in_the_traceability_table_exists_and_passes():
    import proof_cases_doors as D
    known = {c["id"]: c for c in C.WP_CASES + D.DOOR_CASES + RC.RULES_CASES}
    for (code, _), (_f, cases) in TR.METHOD_PROOFS.items():
        for cid in cases:
            assert cid in known, (code, cid)
            c = known[cid]
            if cid.startswith("WP-") and cid != "WP-H":
                rows = E.compare(c["expected"], E.wp_quantities(E.wp_area(c, E.V25)))
            elif cid.startswith("DR-"):
                rows = E.compare(c["expected"], E.door_quantities(c, E.V25))
            else:
                continue                                                      # RS-02: test_rules_sheet_cases
            assert all(r["result"] == "PASS" for r in rows), (code, cid)
    assert set(TR.MATERIAL_PROOFS) <= set(known)


def test_independent_checks_need_their_schema():
    with pytest.raises(ValueError):
        TR.chain([], {"rules_sha256": "x"}, independent={"schema": "OTHER", "checks": []})
    assert json.loads(json.dumps(TR.policy_record()))["statuses"] == list(TR.STATUSES)
