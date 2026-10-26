"""T-245 (f) / (f2): Checker-issued DOWNGRADE-ONLY records in tools/boq_export_v1.py (owner 2026-10-24 23:53 / 23:57).

Hand-made synthetic villa N245D (not the development villa), quantities by hand:
  GB-E1 exterior ground beam 0.40 x 0.60 x 10.00 = 2.400 m3 MEASURED, but measured at the INTERIOR depth (wrong basis)
  ST-1 stair flight 0.300 m3 MEASURED on a convention riser / waist (wrong basis)
  C-1 column 0.30 x 0.30 x 4.00 = 0.360 m3 MEASURED, Checker COMPONENT verdict 0.360 (VERIFIED COMPONENT), then a
       downgrade on it (a VERIFIED verdict that conflicts with an unresolved downgrade -> HELD / CONFLICT)
  F-1 footing 1.20 x 1.20 x 0.50 = 0.720 m3 MEASURED, not listed (untouched)
  S-1 slab BLOCKED_RFI (held, no quantity), listed: stays HELD, its own reason kept
  The four owner-named quantities (11.930 / 0.948 / 3.528 / 3.7125 m3) are carried as four synthetic lines of the
  same classes: each HELD in the contractual view, its number only in the audit file, labelled UNSUPPORTED BASIS.
"""

from __future__ import annotations

import copy
import json

import pytest

from engine.source import boq_line as BL
from tools import boq_export_v1 as X

PID, REV = "villa-n245d", "d" * 64
CVER = "ARCH_TAKEOFF_V3.0.16"
EV = [{"sheet": "S-03 ground beam section", "printed_value": "exterior beam depth not printed"}]
CHK = dict(run_token="20261025T060000-1-1", routine="Verifier", verdict_commit="c0ffee12", time="2026-10-25T06:00:00Z")


def ln(code, eid, q=None, ev="MEASURED", floor="FDN", **kw):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit="m3", evidence_state=ev,
                        measured_net=q, element_id=eid, floor=floor, formula="L*B*H", rule_id="R-SYN",
                        rule_version="1", inputs=kw.pop("inputs", {"V": q} if q is not None else {}), **kw)


def villa():
    return [ln("STR.CONC.GROUND_BEAM", "GB-E1", 2.4), ln("STR.CONC.STAIR", "ST-1", 0.3, floor="GF"),
            ln("STR.CONC.COLUMN", "C-1", 0.36, floor="GF"), ln("STR.CONC.FOOTING", "F-1", 0.72),
            ln("STR.CONC.SLAB", "S-1", ev="BLOCKED_RFI", rfi={"question": "slab depth not printed"}, floor="GF")]


def lid(lines, eid):
    return [x["line_id"] for x in lines if x["location"]["element_id"] == eid][0]


def dg(lines, eids, state="HELD", **kw):
    base = dict(candidate_version=CVER, line_ids=[lid(lines, e) for e in eids], state=state,
                basis_label="UNSUPPORTED BASIS", reason="depth not printed: measured at the interior depth",
                evidence=EV, **CHK)
    base.update(kw)
    return X.downgrade_add(lines, **base)


def rows_of(tmp_path, lines, name, **kw):
    m = X.export(lines, tmp_path / name, candidate_version=CVER, boq_lines_sha256=X.lines_sha256(lines), **kw)
    return m, {r["element_id"]: r for r in X.read_csv(tmp_path / name / "BOQ.csv")}


def test_listed_lines_are_held_unlisted_untouched_candidate_unchanged(tmp_path):
    lines = villa()
    before = copy.deepcopy(lines)
    recs = [dg(lines, ["GB-E1"]), dg(lines, ["ST-1"], state="CONFLICT", reason="convention riser / waist")]
    _m0, r0 = rows_of(tmp_path, lines, "a")
    m, r = rows_of(tmp_path, lines, "b", downgrades=recs)
    assert lines == before                                                   # the candidate lines stay byte-identical
    assert r["F-1"] == r0["F-1"] and r["C-1"] == r0["C-1"]                   # unlisted: untouched
    for e, st in (("GB-E1", "HELD"), ("ST-1", "CONFLICT")):
        assert r[e]["quantity_state"] == "HELD" and r[e]["net"] == "" and r[e]["qty_measured_unverified"] == ""
        assert r[e]["held_reason"].startswith(f"{st}: ") and "UNSUPPORTED BASIS" in r[e]["held_reason"]
    audit = {a["element_id"]: a for a in X.read_csv(tmp_path / "b" / "BOQ_AUDIT_UNSUPPORTED_BASIS.csv")}
    assert set(audit) == {"GB-E1", "ST-1"}
    assert audit["GB-E1"]["candidate_qty"] == "2.400000" and audit["GB-E1"]["basis_label"] == "UNSUPPORTED BASIS"
    assert all(s["status"].startswith("APPLIED") for s in m["downgrades"]["records"])
    summ = {s["item_code"]: s for s in X.read_csv(tmp_path / "b" / "BOQ_TRADE_SUMMARY.csv")}
    assert summ["STR.CONC.GROUND_BEAM"]["measured_unverified_sum"] == ""      # never shown as measured


def test_a_verified_component_conflicting_with_a_downgrade_exports_held(tmp_path):
    lines = villa()
    v = X.verdict_add(lines, candidate_version=CVER, boq_lines_sha256=X.lines_sha256(lines),
                      line_ids=[lid(lines, "C-1")], scope="COMPONENT", checker_qty=0.36,
                      evidence=[{"sheet": "S-04 column schedule", "printed_value": "C-1 30x30"}], **CHK)
    _m, r1 = rows_of(tmp_path, lines, "v", v2_records=[v])
    assert r1["C-1"]["quantity_state"] == "VERIFIED COMPONENT"
    _m, r2 = rows_of(tmp_path, lines, "w", v2_records=[v],
                     downgrades=[dg(lines, ["C-1"], state="CONFLICT", reason="carried to the finished roof level")])
    assert r2["C-1"]["quantity_state"] == "HELD" and r2["C-1"]["qty_verified_component"] == ""
    assert "OVERRIDDEN BY DOWNGRADE" in r2["C-1"]["verdict_status"]
    audit = X.read_csv(tmp_path / "w" / "BOQ_AUDIT_UNSUPPORTED_BASIS.csv")
    assert audit[0]["verdict_overridden"].startswith("VERIFIED COMPONENT")


def test_a_held_line_stays_held_with_its_own_reason(tmp_path):
    lines = villa()
    _m, r = rows_of(tmp_path, lines, "h", downgrades=[dg(lines, ["S-1"])])
    # T-294 (h): the row's own reason stays first, unchanged; the record is appended, never written over it
    assert r["S-1"]["quantity_state"] == "HELD" and r["S-1"]["held_reason"].startswith(
        "BLOCKED_RFI: slab depth not printed | + HELD: ") and "UNSUPPORTED BASIS; downgrade DG-" in r["S-1"]["held_reason"]


@pytest.mark.parametrize("change,needle", [
    (lambda d: d.update(checker_qty=2.0), "INVALID"),                       # never a fabricated Checker measurement
    (lambda d: d.update(state="VERIFIED"), "INVALID"),                      # a record can only downgrade
    (lambda d: d["checker"].update(routine="Worker 3"), "INVALID"),         # Checker only
    (lambda d: d.update(project_id="other-villa"), "OTHER_PROJECT"),
    (lambda d: d.update(engine_qty=2.5), "STALE"),                           # the line was corrected since: review
    (lambda d: d.update(line_ids=["L-unknown"]), "NO_LINE"),
    (lambda d: d.update(resolved=True), "RESOLVED"),
])
def test_records_that_bind_nothing_leave_the_line_as_it_is(tmp_path, change, needle):
    lines = villa()
    d = dg(lines, ["GB-E1"])
    change(d)
    m, r = rows_of(tmp_path, lines, "x", downgrades=[d])
    assert r["GB-E1"]["quantity_state"] == "MEASURED UNVERIFIED" and r["GB-E1"]["net"] == "2.400000"
    assert m["downgrades"]["records"][0]["status"].startswith(needle)


def test_helper_refuses_bad_requests():
    lines = villa()
    with pytest.raises(X.ExportError, match="unknown line"):
        X.downgrade_add(lines, candidate_version=CVER, line_ids=["L-x"], state="HELD",
                        basis_label="UNSUPPORTED BASIS", reason="r", evidence=EV, **CHK)
    with pytest.raises(X.ExportError, match="state"):
        dg(lines, ["GB-E1"], state="VERIFIED")
    with pytest.raises(X.ExportError, match="routine"):
        dg(lines, ["GB-E1"], routine="Worker 3")


def test_the_four_owner_named_quantities_are_held_by_name(tmp_path):
    lines = [ln("STR.CONC.GROUND_BEAM", "GB-EXT-24", 11.93), ln("STR.CONC.STAIR", "ST-03", 0.948, floor="GF"),
             ln("STR.CONC.COLUMN", "C-2F", 3.528, floor="2F"), ln("STR.CONC.COLUMN", "C-ANNEX-7", 3.7125, floor="RF")]
    recs = [dg(lines, ["GB-EXT-24"], reason="exterior depth not printed: interior depth used (D-35)"),
            dg(lines, ["ST-03"], reason="convention riser 0.165 + waist 0.175, not printed"),
            dg(lines, ["C-2F"], reason="carried to the finished roof +13.90 (D-39)"),
            dg(lines, ["C-ANNEX-7"], reason="annex height 4.50 provisional (Q-54 B / D-39)")]
    m, r = rows_of(tmp_path, lines, "f", downgrades=recs)
    assert all(r[e]["quantity_state"] == "HELD" and r[e]["net"] == "" for e in r)
    audit = {a["element_id"]: a["candidate_qty"] for a in X.read_csv(tmp_path / "f" / "BOQ_AUDIT_UNSUPPORTED_BASIS.csv")}
    assert audit == {"GB-EXT-24": "11.930000", "ST-03": "0.948000", "C-2F": "3.528000", "C-ANNEX-7": "3.712500"}
    assert m["row_counts"]["MEASURED UNVERIFIED"] == 0 and m["row_counts"]["HELD"] == 4


def test_cli_roundtrip_and_no_flag_bytes_unchanged(tmp_path):
    lines = villa()
    p = tmp_path / "L.json"
    p.write_text(BL.dumps(lines), encoding="utf-8")
    dgf = tmp_path / "DG.json"
    assert X.main(["downgrade-add", "--lines", str(p), "--candidate-version", CVER, "--line-ids", lid(lines, "GB-E1"),
                   "--state", "HELD", "--reason", "interior depth used", "--evidence", "S-03=depth not printed",
                   "--run-token", "t1", "--routine", "Verifier", "--verdict-commit", "abcdef1",
                   "--time", "2026-10-25T06:00:00Z", "--out", str(dgf)]) == 0
    assert X.main(["--lines", str(p), "--candidate-version", CVER, "--out", str(tmp_path / "o1"),
                   "--code-commit", "abc"]) == 0
    assert X.main(["--lines", str(p), "--candidate-version", CVER, "--out", str(tmp_path / "o2"),
                   "--code-commit", "abc", "--downgrades", str(dgf)]) == 0
    assert not (tmp_path / "o1" / "BOQ_AUDIT_UNSUPPORTED_BASIS.csv").exists()
    m = json.loads((tmp_path / "o2" / "EXPORT_MANIFEST.json").read_text(encoding="utf-8"))
    assert m["downgrades"]["records"][0]["status"] == "APPLIED (HELD, 1 line(s))"
    a = {r["element_id"]: r for r in X.read_csv(tmp_path / "o1" / "BOQ.csv")}
    b = {r["element_id"]: r for r in X.read_csv(tmp_path / "o2" / "BOQ.csv")}
    assert {e for e in a if a[e] != b[e]} == {"GB-E1"}


def test_an_excluded_row_named_by_a_downgrade_stays_excluded(tmp_path):
    """F-T245-01 (Verifier 2026-10-25 07:58): the real (STR.CONC.COLUMN, 2F) group is 14 line ids, some of them
    NOT_APPLICABLE (EXCLUDED rows); a record over the whole group moved one EXCLUDED row to HELD (774 -> 773).
    Synthetic 2F group by hand: C-2F-A 0.30 x 0.30 x 4.00 = 0.360 m3, C-2F-B 0.30 x 0.60 x 4.00 = 0.720 m3 (both
    measured on the wrong basis), C-2F-X NOT_APPLICABLE (counted in its parent, no quantity). Normal: the two measured
    rows go HELD, the excluded row stays EXCLUDED with its own reason, the EXCLUDED count does not move."""
    lines = [ln("STR.CONC.COLUMN", "C-2F-A", 0.36, floor="2F"), ln("STR.CONC.COLUMN", "C-2F-B", 0.72, floor="2F"),
             ln("STR.CONC.COLUMN", "C-2F-X", ev="NOT_APPLICABLE_WITH_EVIDENCE", floor="2F",
                notes="counted in its parent column"),
             ln("STR.CONC.FOOTING", "F-1", 0.72)]
    m0, r0 = rows_of(tmp_path, lines, "e0")
    assert r0["C-2F-X"]["quantity_state"] == "EXCLUDED"
    rec = dg(lines, ["C-2F-A", "C-2F-B", "C-2F-X"], reason="carried to the finished roof +13.90 (D-39)")
    assert rec["engine_qty"] == "1.080000" or float(rec["engine_qty"]) == pytest.approx(1.08)
    m, r = rows_of(tmp_path, lines, "e1", downgrades=[rec])
    assert r["C-2F-X"] == r0["C-2F-X"]                                        # adverse: untouched, still EXCLUDED
    assert m["row_counts"]["EXCLUDED"] == m0["row_counts"]["EXCLUDED"] == 1
    assert r["C-2F-A"]["quantity_state"] == r["C-2F-B"]["quantity_state"] == "HELD"
    assert m["row_counts"]["HELD"] == m0["row_counts"]["HELD"] + 2
    assert m["downgrades"]["records"][0]["status"] == "APPLIED (HELD, 2 line(s); 1 EXCLUDED row(s) left EXCLUDED)"
    audit = {a["element_id"] for a in X.read_csv(tmp_path / "e1" / "BOQ_AUDIT_UNSUPPORTED_BASIS.csv")}
    assert audit == {"C-2F-A", "C-2F-B"}                                      # no audit quantity for an excluded row
