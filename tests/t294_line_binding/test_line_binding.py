"""T-294: V2 verdict / downgrade records bound to the canonical content of THEIR OWN line ids (tools/boq_export_v1.py),
plus parts (g) (tools/v30_gate_b_v2.py sealed-name guard through links) and (h) (a downgrade of an already-HELD row).

Hand-made synthetic villa N294 (not the development villa), quantities by hand:
  F1 footing 1.50 x 1.50 x 0.60 = 1.350 m3 MEASURED          F2 footing 1.20 x 1.20 x 0.50 = 0.720 m3 MEASURED
  C1 column  0.30 x 0.30 x 3.50 = 0.315 m3 MEASURED          C2 column  0.30 x 0.40 x 3.50 = 0.420 m3 MEASURED
  S1 slab BLOCKED_RFI (depth not printed; owner decision required)
  S2 slab BOUNDED_EXPOSURE 12.0 x 0.20 .. 0.24 x 5.0 = 12.000 .. 14.400 m3 (held range)
Candidate A = these lines ("ARCH_TAKEOFF_V3.0.A"); candidate B ("ARCH_TAKEOFF_V3.0.B") = A with only C2 changed by
+0.001 m3 (0.421: the Verifier's own probe, one line elsewhere). A record on F1 (COMPONENT 1.350) and a WHOLE record on
the footing line (F1 + F2 = 2.070) must stay COUNTED on B; any change of F1 itself makes them STALE.
"""

from __future__ import annotations

import copy
import json
import os

import pytest

from engine.source import boq_line as BL
from tools import boq_export_v1 as X
from tools import v30_gate_b_v2 as G

PID, REV = "villa-n294", "4" * 64
CA, CB = "ARCH_TAKEOFF_V3.0.A", "ARCH_TAKEOFF_V3.0.B"
DOC = {"file": "S-02 foundation plan.dxf", "sha256": "a" * 64}
CHK = dict(run_token="20261026T030000-1-1", routine="Verifier", verdict_commit="c0ffee12", time="2026-10-26T03:00:00Z")
EV = [{"sheet": "S-02 footing schedule", "printed_value": "F1 150x150x60"}]


def ln(code, eid, q=None, ev="MEASURED", floor="FDN", **kw):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit="m3", evidence_state=ev,
                        measured_net=q, element_id=eid, floor=floor, formula="L*B*H", rule_id="R-N294",
                        rule_version=kw.pop("rule_version", "1"), documents=[DOC],
                        inputs=kw.pop("inputs", {"V": q} if q is not None else {}), **kw)


def cand_a():
    return [ln("STR.CONC.FOOTING", "F1", 1.35, inputs={"L": 1.5, "B": 1.5, "H": 0.6}),
            ln("STR.CONC.FOOTING", "F2", 0.72, inputs={"L": 1.2, "B": 1.2, "H": 0.5}),
            ln("STR.CONC.COLUMN", "C1", 0.315, floor="GF", inputs={"L": 0.3, "B": 0.3, "H": 3.5}),
            ln("STR.CONC.COLUMN", "C2", 0.42, floor="GF", inputs={"L": 0.3, "B": 0.4, "H": 3.5}),
            ln("STR.CONC.SLAB", "S1", ev="BLOCKED_RFI", floor="GF",
               rfi={"question": "slab depth not printed", "owner_decision_required": True}),
            ln("STR.CONC.SLAB", "S2", ev="BOUNDED_EXPOSURE", floor="1F", bounded_range={"low": 12.0, "high": 14.4},
               rfi={"question": "slab depth 0.20 or 0.24"})]


def eid_line(lines, eid):
    return [x for x in lines if x["location"]["element_id"] == eid][0]


def lid(lines, eid):
    return eid_line(lines, eid)["line_id"]


def edit(lines, eid, fn):
    out = copy.deepcopy(lines)
    fn(eid_line(out, eid))
    return out


def cand_b():                      # one line ELSEWHERE changes (+0.001 m3 on C2)
    return edit(cand_a(), "C2", lambda x: x.update(measured_net=0.421))


def verdict(lines, eids, q, scope="COMPONENT", cver=CA, **kw):
    return X.verdict_add(lines, candidate_version=cver, boq_lines_sha256=X.lines_sha256(lines),
                         line_ids=[lid(lines, e) for e in eids], scope=scope, checker_qty=q, evidence=EV, **CHK, **kw)


def legacy(rec):                   # the same record as the T-245 helper wrote it (whole-file binding, no binding field)
    return {k: v for k, v in rec.items() if k not in ("binding", "line_content_sha256")}


def status(lines, rec, cver):
    """bind_verdict against the footing group (trade, item code, unit) as build() does it."""
    group = [x for x in lines if x["item_code"] == "STR.CONC.FOOTING"]
    els = sorted(str(x["location"]["element_id"]) for x in group)
    return X.bind_verdict(rec, (PID, REV, cver, X.lines_sha256(lines)), group, els)


def export_status(tmp_path, lines, cver, name, **kw):
    m = X.export(lines, tmp_path / name, candidate_version=cver, boq_lines_sha256=X.lines_sha256(lines), **kw)
    return m, {r["element_id"]: r for r in X.read_csv(tmp_path / name / "BOQ.csv")}


# ---- the binding itself ---------------------------------------------------------------------------------------------

def test_new_records_carry_the_line_content_binding_of_exactly_their_own_lines():
    a = cand_a()
    rec = verdict(a, ["F1"], 1.35)
    assert rec["binding"] == X.LINE_BINDING and X.line_bound(rec) and not X.validate_v2(rec)
    assert rec["line_content_sha256"] == X.line_content_sha256([eid_line(a, "F1")])
    assert rec["line_content_sha256"] == X.sha256_bytes(BL.dumps([eid_line(a, "F1")]).encode("utf-8"))
    whole = verdict(a, ["F2", "F1"], 2.07, scope="WHOLE")          # order given never matters: sorted by line id
    assert whole["line_content_sha256"] == X.line_content_sha256(sorted(
        [eid_line(a, "F1"), eid_line(a, "F2")], key=lambda x: x["line_id"]))
    assert whole["line_content_sha256"] == X.line_content_sha256([eid_line(a, "F2"), eid_line(a, "F1")])
    assert whole["line_content_sha256"] != X.lines_sha256(a)        # never the whole candidate
    with pytest.raises(X.ExportError, match="each once"):
        X.line_content_sha256([eid_line(a, "F1"), eid_line(a, "F1")])
    with pytest.raises(X.ExportError, match="at least one line"):
        X.line_content_sha256([])


def test_normal_a_change_outside_the_record_leaves_it_valid_on_a_new_candidate_version(tmp_path):
    a, b = cand_a(), cand_b()
    assert X.lines_sha256(a) != X.lines_sha256(b)                   # the whole file DID change (T-245 would go STALE)
    comp, whole = verdict(a, ["F1"], 1.35), verdict(a, ["F1", "F2"], 2.07, scope="WHOLE")
    for rec in (comp, whole):
        assert status(a, rec, CA) == "COUNTED"
        assert status(b, rec, CB) == "COUNTED"                       # new candidate version, other line changed
    m, r = export_status(tmp_path, b, CB, "b", v2_records=[comp, whole])
    st = {v["verdict_id"]: v["status"] for v in m["v2_verdicts"]}
    assert st[comp["verdict_id"]].startswith("COUNTED") and st[whole["verdict_id"]].startswith("COUNTED")
    assert r["F1"]["quantity_state"] == "VERIFIED COMPONENT" and r["F1"]["qty_verified_component"] == "1.350000"
    assert r["C2"]["quantity_state"] == "MEASURED UNVERIFIED" and r["C2"]["net"] == "0.421000"


@pytest.mark.parametrize("field,fn", [
    ("quantity", lambda x: x.update(measured_net=1.351)),
    ("quantity within the 0.0005 scoreboard tolerance", lambda x: x.update(measured_net=1.3504)),
    ("rule version", lambda x: x["rule"].update(version="2")),
    ("evidence state", lambda x: x.update(evidence_state="SOURCE_DERIVED")),
    ("drawing sha", lambda x: x["source"].update(documents=[dict(DOC, sha256="b" * 64)])),
    ("formula input", lambda x: x["calculation"]["inputs"].update(H=0.61)),
    ("element", lambda x: x["location"].update(floor="GF")),
])
def test_adverse_any_change_of_an_own_line_makes_it_stale(tmp_path, field, fn):
    a = cand_a()
    comp, whole = verdict(a, ["F1"], 1.35), verdict(a, ["F1", "F2"], 2.07, scope="WHOLE")
    b = edit(cand_b(), "F1", fn)
    for rec in (comp, whole):
        assert status(b, rec, CB) == "STALE", field
        assert status(b, rec, CA) == "STALE", field                  # same candidate version: still STALE
    m, r = export_status(tmp_path, b, CB, "x", v2_records=[comp])
    assert {v["verdict_id"]: v["status"] for v in m["v2_verdicts"]}[comp["verdict_id"]].startswith("STALE")
    assert r["F1"]["quantity_state"] != "VERIFIED COMPONENT"


def test_adverse_a_line_id_that_disappears_is_stale_never_valid(tmp_path):
    a = cand_a()
    whole = verdict(a, ["F1", "F2"], 2.07, scope="WHOLE")
    comp = verdict(a, ["F1"], 1.35)
    b = [x for x in cand_b() if x["location"]["element_id"] != "F1"]
    assert status(b, whole, CB) == "STALE"
    m, _r = export_status(tmp_path, b, CB, "gone", v2_records=[whole, comp])
    st = {v["verdict_id"]: v["status"] for v in m["v2_verdicts"]}
    assert st[whole["verdict_id"]].startswith("STALE")
    assert st[comp["verdict_id"]] == "NO_LINE_IN_THIS_EXPORT"         # listed, binds nothing, never COUNTED
    assert m["row_counts"].get("VERIFIED COMPONENT", 0) == 0


def test_adverse_another_project_or_revision_set_is_stale():
    a = cand_a()
    rec = verdict(a, ["F1"], 1.35)
    for k, val in (("project_id", "other-villa"), ("revision_set_sha256", "5" * 64)):
        assert status(a, dict(rec, **{k: val}), CA) == "STALE"


def test_adverse_a_tampered_or_half_binding_binds_nothing():
    a = cand_a()
    rec = verdict(a, ["F1"], 1.35)
    assert status(a, dict(rec, line_content_sha256="0" * 64), CA) == "STALE"
    half = {k: v for k, v in rec.items() if k != "line_content_sha256"}
    assert any("together" in p for p in X.validate_v2(half)) and status(a, half, CA) == "BINDING_INCOMPLETE"
    other = dict(rec, binding="WHOLE_FILE_V9")
    assert any("is not LINE_CONTENT_V1" in p for p in X.validate_v2(other)) and status(a, other, CA) == \
        "BINDING_INCOMPLETE"
    assert any("64 lower-case" in p for p in X.validate_v2(dict(rec, line_content_sha256="xyz")))
    assert status(a, dict(rec, engine_qty=1.40), CA) == "STALE"       # its own engine qty must still be the lines'


# ---- records issued under the T-245 binding: never auto-migrated ----------------------------------------------------

def test_t245_records_keep_their_whole_file_binding_and_are_stale_on_a_new_candidate():
    a = cand_a()
    old = legacy(verdict(a, ["F1"], 1.35))
    assert not X.line_bound(old) and not X.validate_v2(old)
    assert status(a, old, CA) == "COUNTED"                           # on the candidate it was issued on: as before
    assert status(cand_b(), old, CB) == "STALE"                      # elsewhere: STALE, even with F1 unchanged
    assert status(copy.deepcopy(a), old, CB) == "STALE"              # same lines, new version label: STALE


def test_the_checker_rebinds_an_unchanged_t245_record_onto_the_new_candidate():
    a, b = cand_a(), cand_b()
    old = legacy(verdict(a, ["F1", "F2"], 2.07, scope="WHOLE"))
    new = X.verdict_rebind(old, a, b, old_candidate_version=CA, candidate_version=CB,
                           run_token="20261026T040000-2-2", routine="Checker", verdict_commit="dd6a6114",
                           time="2026-10-26T04:00:00Z")
    assert X.line_bound(new) and new["rebound_from"] == old["verdict_id"] and new["verdict_id"] != old["verdict_id"]
    assert (new["checker_qty"], new["scope"], new["evidence"], new["engine_qty"]) == (2.07, "WHOLE", EV, 2.07)
    assert new["candidate_version"] == CB and new["boq_lines_sha256"] == X.lines_sha256(b)
    assert new["checker"]["routine"] == "Checker" and not X.validate_v2(new)
    assert status(b, new, CB) == "COUNTED"


@pytest.mark.parametrize("case,kw,match", [
    ("own line changed", dict(new=lambda: edit(cand_b(), "F1", lambda x: x.update(measured_net=1.36))), "changed"),
    ("own line absent", dict(new=lambda: [x for x in cand_b() if x["location"]["element_id"] != "F2"]),
     "not in the new candidate"),
    ("not the old candidate", dict(old=lambda: cand_b()), "boq_lines_sha256 differs"),
    ("wrong old version", dict(oldver="ARCH_TAKEOFF_V3.0.Z"), "issued on"),
    ("new revision set", dict(new=lambda: [dict(x, project={"project_id": PID, "revision_set_sha256": "6" * 64})
                                           for x in cand_b()]), "revision set"),
    ("not the Checker", dict(routine="Worker 3"), "not the Checker"),
])
def test_adverse_rebind_is_refused_unless_proven_unchanged(case, kw, match):
    a = cand_a()
    old = legacy(verdict(a, ["F1", "F2"], 2.07, scope="WHOLE"))
    with pytest.raises(X.ExportError, match=match):
        X.verdict_rebind(old, kw.get("old", lambda: a)(), kw.get("new", cand_b)(),
                         old_candidate_version=kw.get("oldver", CA), candidate_version=CB,
                         run_token="20261026T040000-2-2", routine=kw.get("routine", "Checker"),
                         verdict_commit="dd6a6114", time="2026-10-26T04:00:00Z")


def test_cli_verdict_rebind_writes_only_the_unchanged_records(tmp_path):
    a = cand_a()
    b = edit(cand_b(), "F2", lambda x: x.update(measured_net=0.73))  # F2 changed: its record must not be re-bound
    r1, r2 = legacy(verdict(a, ["F1"], 1.35)), legacy(verdict(a, ["F2"], 0.72))
    (tmp_path / "old.json").write_text(json.dumps({"schema": X.V2_SET_SCHEMA, "verdicts": sorted(
        [r1, r2], key=lambda v: v["verdict_id"])}), encoding="utf-8")
    (tmp_path / "a.json").write_text(BL.dumps(a), encoding="utf-8")
    (tmp_path / "b.json").write_text(BL.dumps(b), encoding="utf-8")
    rc = X.main(["verdict-rebind", "--verdicts", str(tmp_path / "old.json"), "--old-lines", str(tmp_path / "a.json"),
                 "--old-candidate-version", CA, "--lines", str(tmp_path / "b.json"), "--candidate-version", CB,
                 "--run-token", "20261026T040000-2-2", "--routine", "Verifier", "--verdict-commit", "dd6a6114",
                 "--time", "2026-10-26T04:00:00Z", "--out", str(tmp_path / "new.json")])
    assert rc == 1                                                   # one record could not be re-bound
    doc = json.loads((tmp_path / "new.json").read_text(encoding="utf-8"))
    assert [v["rebound_from"] for v in doc["verdicts"]] == [r1["verdict_id"]] and not X.validate_v2_set(doc)
    with pytest.raises(X.ExportError, match="old set"):
        X.main(["verdict-rebind", "--verdicts", str(tmp_path / "old.json"), "--old-lines", str(tmp_path / "a.json"),
                "--old-candidate-version", CA, "--lines", str(tmp_path / "b.json"), "--candidate-version", CB,
                "--run-token", "t", "--routine", "Verifier", "--verdict-commit", "dd6a6114",
                "--out", str(tmp_path / "old.json")])


# ---- downgrade records: the same binding ----------------------------------------------------------------------------

def dg(lines, eids, cver=CA, **kw):
    base = dict(candidate_version=cver, line_ids=[lid(lines, e) for e in eids], state="HELD",
                basis_label="UNSUPPORTED BASIS", reason="footing depth read from the wrong section", evidence=EV,
                **CHK)
    base.update(kw)
    return X.downgrade_add(lines, **base)


def test_downgrade_normal_still_applied_after_a_change_elsewhere(tmp_path):
    a, b = cand_a(), cand_b()
    d = dg(a, ["F1"])
    assert X.line_bound(d) and not X.validate_downgrade(d)
    m, r = export_status(tmp_path, b, CB, "d", downgrades=[d])
    assert m["downgrades"]["records"][0]["status"].startswith("APPLIED")
    assert r["F1"]["quantity_state"] == "HELD" and r["F1"]["net"] == ""


@pytest.mark.parametrize("fn,needle", [
    (lambda ls: edit(ls, "F1", lambda x: x["rule"].update(version="2")), "STALE (the content"),
    (lambda ls: edit(ls, "F1", lambda x: x.update(evidence_state="SOURCE_DERIVED")), "STALE (the content"),
    (lambda ls: [x for x in ls if x["location"]["element_id"] != "F1"], "NO_LINE_IN_THIS_EXPORT (STALE"),
])
def test_downgrade_adverse_own_line_changed_or_absent_is_stale_and_not_applied(tmp_path, fn, needle):
    a = cand_a()
    d = dg(a, ["F1", "F2"])
    b = fn(cand_b())
    m, r = export_status(tmp_path, b, CB, "s", downgrades=[d])
    assert m["downgrades"]["records"][0]["status"].startswith(needle)
    assert r["F2"]["quantity_state"] == "MEASURED UNVERIFIED"           # not applied to any of its lines


def test_t245_downgrade_keeps_its_quantity_binding(tmp_path):
    a = cand_a()
    d = legacy(dg(a, ["F1"]))
    assert not X.line_bound(d) and not X.validate_downgrade(d)
    b = edit(cand_b(), "F1", lambda x: x["source"].update(documents=[dict(DOC, sha256="b" * 64)]))
    m, _r = export_status(tmp_path, b, CB, "l", downgrades=[d])
    assert m["downgrades"]["records"][0]["status"].startswith("APPLIED")  # as T-245 wrote it: qty + unit only
    assert any("together" in p for p in X.validate_downgrade(dict(d, binding=X.LINE_BINDING)))


# ---- part (h): a downgrade of an already-HELD row -------------------------------------------------------------------

def test_h_normal_a_measured_row_is_cleared_to_held_with_the_record_reason(tmp_path):
    a = cand_a()
    _m, r = export_status(tmp_path, a, CA, "h0", downgrades=[dg(a, ["C1"])])
    assert r["C1"]["quantity_state"] == "HELD" and r["C1"]["held_reason"].startswith("HELD: footing depth")


def test_h_adverse_a_held_row_keeps_its_own_reason_class_and_range(tmp_path):
    a = cand_a()
    _m0, r0 = export_status(tmp_path, a, CA, "h1")
    d1, d2 = dg(a, ["S1"], reason="slab is a ribbed slab"), dg(a, ["S2"], state="CONFLICT", reason="two depths")
    m, r = export_status(tmp_path, a, CA, "h2", downgrades=[d1, d2])
    for e, d in (("S1", d1), ("S2", d2)):
        assert r[e]["quantity_state"] == "HELD"
        assert r[e]["held_reason"] == f"{r0[e]['held_reason']} | + {d['state']}: {d['reason']} (UNSUPPORTED BASIS; " \
                                      f"downgrade {d['downgrade_id']})"
        assert r[e]["owner_status_class"] == r0[e]["owner_status_class"]
        assert (r[e]["held_low"], r[e]["held_high"]) == (r0[e]["held_low"], r0[e]["held_high"])
    assert r0["S1"]["owner_status_class"] == "OWNER DECISION REQUIRED"   # kept, not rewritten to HELD
    assert (r["S2"]["held_low"], r["S2"]["held_high"]) == ("12.000000", "14.400000")
    assert all(s["status"].startswith("APPLIED") for s in m["downgrades"]["records"])
    assert not any(r[e][c] for e in ("S1", "S2") for c in ("qty_verified", "qty_verified_component", "net"))


# ---- Gate B v2 binds the same way -----------------------------------------------------------------------------------

def test_gate_b_bind_carries_a_line_content_record_and_keeps_t245_records_side_bound():
    a, b = cand_a(), cand_b()
    rec = verdict(a, ["F1"], 1.35)
    pairs = {(PID, REV)}
    A, B = {x["line_id"]: x for x in a}, {x["line_id"]: x for x in b}
    assert G.bind(rec, A, pairs, CA, X.lines_sha256(a)) == "COUNTED"
    assert G.bind(rec, B, pairs, CB, X.lines_sha256(b)) == "COUNTED"
    b2 = edit(b, "F1", lambda x: x.update(measured_net=1.36))
    assert G.bind(rec, {x["line_id"]: x for x in b2}, pairs, CB, X.lines_sha256(b2)) == "STALE"
    assert G.bind(rec, B, {("other-villa", REV)}, CB, X.lines_sha256(b)) == "NOT_THIS_SIDE"
    old = legacy(rec)
    assert G.bind(old, A, pairs, CA, X.lines_sha256(a)) == "COUNTED"
    assert G.bind(old, B, pairs, CB, X.lines_sha256(b)) == "NOT_THIS_SIDE"


# ---- part (g): the sealed-name guard follows links --------------------------------------------------------------------

def _reg():
    return {"schema": G.SEALED_SCHEMA, "entries": [{"kind": "SEALED_FILE", "project_id": "sealed-x",
                                                    "names": ["hidden_benchmark.json"], "sha256": "c" * 64}]}


def test_g_a_link_with_an_innocent_name_to_a_sealed_name_is_refused(tmp_path):
    t = tmp_path / "hidden_benchmark.json"
    t.write_text("{}", encoding="utf-8")
    os.symlink(t, tmp_path / "lines.json")
    os.symlink("lines.json", tmp_path / "relative_hop.json")          # a chain, relative target
    for p in ("lines.json", "relative_hop.json"):
        with pytest.raises(G.Refused) as e:
            G.guard_inputs({"after": tmp_path / p}, _reg())
        assert "SEALED" in str(e.value.problems) and "via a link" in str(e.value.problems)
    from engine.reference_mapping import SEALED
    t2 = tmp_path / SEALED[0]
    t2.write_text("{}", encoding="utf-8")
    os.symlink(t2, tmp_path / "plain.json")
    with pytest.raises(G.Refused):
        G.guard_inputs({"after": tmp_path / "plain.json"}, _reg())


def test_g_normal_an_innocent_link_to_an_innocent_file_passes(tmp_path):
    t = tmp_path / "V3_0_B_BOQ_LINES.json"
    t.write_text("[]", encoding="utf-8")
    os.symlink(t, tmp_path / "after.json")
    out = G.guard_inputs({"after": tmp_path / "after.json"}, _reg())
    assert out["after"] == G.sha256_file(t)
    assert G.link_names(tmp_path / "after.json") == ["after.json", "V3_0_B_BOQ_LINES.json"]
