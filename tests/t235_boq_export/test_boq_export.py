"""T-235 r1: tools/boq_export_v1.py on a hand-made synthetic villa (not the development villa).

Hand calculation (written before running the tool):
  CONCRETE STR.CONC.FOOTING m3: F1 1.200 + F2 0.800 + F3 2.000 MEASURED = 4.000 measured unverified (3 rows)
  CONCRETE STR.CONC.SLAB m3:   S1 BOUNDED_EXPOSURE 5.000 .. 6.000 (HELD, range) ; S2 BLOCKED_RFI (HELD, no range)
  CONCRETE STR.CONC.LINTEL m3: L1 NOT_APPLICABLE_WITH_EVIDENCE (EXCLUDED, blank)
  PAINT FIN.PAINT m2:          P1 PROVISIONAL 40.000, line states 'ASSUMED - OWNER-APPROVED' -> PROJECT-SPECIFIC
  MASONRY (zero check):        W0 MEASURED 0.000 with gross 4.000 and deduction 4.000 -> accepted, MEASURED 0
  -> 8 rows; VERIFIED 0 (no V2 record, no completeness: by construction); MEASURED UNVERIFIED 5; HELD 2; EXCLUDED 1;
     footing group 4.000 m3 unverified, 0 rows without quantity; slab group held 5.000 .. 6.000 + 1 without range.
"""

from __future__ import annotations

import copy
import json
import random

import pytest
from openpyxl import load_workbook

from engine.source import boq_line as BL
from tools import boq_export_v1 as X

PID, REV = "SYNTH-VILLA-7", "c" * 64
CVER, BSHA = "ARCH_TAKEOFF_V3.0.TEST", "d" * 64


def ln(code, eid, ev="MEASURED", q=None, unit="m3", **kw):
    base = dict(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                measured_net=q, element_id=eid, formula=kw.pop("formula", "L*B*H"), rule_id="R-SYN",
                rule_version="1", floor=kw.pop("floor", "FDN"))
    base.update(kw)
    return BL.make_line(**base)


def villa():
    return [
        ln("STR.CONC.FOOTING", "F1", q=1.2, inputs={"L": 1.5, "B": 1.0, "H": 0.8}, documents=[{"file": "S-01", "page": 2}]),
        ln("STR.CONC.FOOTING", "F2", q=0.8, inputs={"L": 1.0, "B": 1.0, "H": 0.8}),
        ln("STR.CONC.FOOTING", "F3", q=2.0, inputs={"L": 2.5, "B": 1.0, "H": 0.8}),
        ln("STR.CONC.SLAB", "S1", ev="BOUNDED_EXPOSURE", bounded_range={"low": 5.0, "high": 6.0, "basis": "depth"},
           rfi={"question": "slab depth 0.20 or 0.24"}, floor="GF"),
        ln("STR.CONC.SLAB", "S2", ev="BLOCKED_RFI", rfi={"question": "drop panel extent not drawn"}, floor="1F"),
        ln("STR.CONC.LINTEL", "L1", ev="NOT_APPLICABLE_WITH_EVIDENCE", notes="no lintel: arches only", floor="GF"),
        ln("FIN.PAINT", "P1", ev="PROVISIONAL", q=40.0, unit="m2", floor="GF",
           inputs={"gross": 44.0, "evidence_status": "ASSUMED - OWNER-APPROVED", "assumption": "Q-60 A height"}),
        ln("MAS.BLOCK", "W0", q=0.0, unit="m2", gross=4.0, deductions=[{"opening": "D1", "area": 4.0}], floor="GF"),
    ]


def run(tmp_path, lines, name="o", **kw):
    m = X.export(lines, tmp_path / name, candidate_version=CVER, boq_lines_sha256=BSHA, **kw)
    return m, X.read_csv(tmp_path / name / "BOQ.csv")


def by(rows, eid):
    return [r for r in rows if r["element_id"] == eid][0]


# ---- normal case ----------------------------------------------------------------------------------------------------

def test_synthetic_villa_rows_states_and_classes(tmp_path):
    m, rows = run(tmp_path, villa())
    assert m["row_counts"] == {"VERIFIED": 0, "VERIFIED ZERO": 0, "VERIFIED COMPONENT": 0, "MEASURED UNVERIFIED": 5,
                               "HELD": 2, "UNMEASURED": 0, "EXCLUDED": 1, "total": 8}
    assert by(rows, "F1")["qty_measured_unverified"] == "1.200000" and by(rows, "F1")["qty_verified"] == ""
    assert by(rows, "F1")["owner_status_class"] == X.CLS_SOURCE
    assert by(rows, "F1")["source_sheets"] == "S-01 p.2"
    assert by(rows, "P1")["owner_status_class"] == X.CLS_PROJECT
    s1 = by(rows, "S1")
    assert (s1["quantity_state"], s1["net"], s1["held_low"], s1["held_high"]) == ("HELD", "", "5.000000", "6.000000")
    s2 = by(rows, "S2")
    assert s2["net"] == "" and s2["held_low"] == "" and "drop panel" in s2["held_reason"]
    assert by(rows, "L1")["quantity_state"] == "EXCLUDED" and by(rows, "L1")["qty_verified_zero"] == ""
    w0 = by(rows, "W0")
    assert (w0["quantity_state"], w0["qty_measured_unverified"], w0["deductions_total"]) == \
        ("MEASURED UNVERIFIED", "0.000000", "4.000000")
    assert {r["project_id"] for r in rows} == {PID} and {r["candidate_version"] for r in rows} == {CVER}
    assert all(r["verdict_status"] == "NONE" for r in rows)
    assert "none (T-236 not merged)" in m["completeness_input"]


def test_open_convention_range_on_a_quantity_line_is_kept(tmp_path):
    lines = villa() + [ln("STR.CONC.FOOTING", "F10", ev="PROVISIONAL", q=1.96, inputs={"L": 1.4, "B": 1.4, "H": 1.0},
                          bounded_range={"low": 0.216, "high": 1.96, "basis": "two tags"}),
                       ln("STR.CONC.FOOTING", "F11", ev="SOURCE_DERIVED", q=0.5, inputs={"L": 1},
                          bounded_range={"low": 0.5, "high": 0.5, "basis": "degenerate"})]
    m, rows = run(tmp_path, lines)
    f10, f11 = by(rows, "F10"), by(rows, "F11")
    assert (f10["qty_measured_unverified"], f10["open_range_low"], f10["open_range_high"]) == \
        ("1.960000", "0.216000", "1.960000")
    assert f11["open_range_low"] == "" and f11["qty_measured_unverified"] == "0.500000"
    s = {x["item_code"]: x for x in X.read_csv(tmp_path / "o" / "BOQ_TRADE_SUMMARY.csv")}["STR.CONC.FOOTING"]
    assert s["open_range_rows"] == "1" and s["open_range_components"] == "F10 [0.216000 .. 1.960000, net 1.960000]"


def test_canonical_order_and_trade_summary(tmp_path):
    m, rows = run(tmp_path, villa())
    keys = [(r["trade"], r["item_code"], r["floor"], r["element_id"], r["line_id"]) for r in rows]
    assert keys == sorted(keys)
    summ = {(s["item_code"]): s for s in X.read_csv(tmp_path / "o" / "BOQ_TRADE_SUMMARY.csv")}
    f = summ["STR.CONC.FOOTING"]
    assert (f["line_status"], f["measured_unverified_sum"], f["rows_without_quantity"], f["verified_subtotal"]) == \
        ("NOT VERIFIED", "4.000000", "0", "")
    s = summ["STR.CONC.SLAB"]
    assert (s["held_low"], s["held_high"], s["held_rows"], s["measured_unverified_sum"]) == \
        ("5.000000", "6.000000", "2", "")
    assert s["held_components"] == "S2 [no range]; S1 [5.000000 .. 6.000000]"   # canonical order: floor 1F before GF
    assert {t["trade"]: t["status"] for t in m["trades"]}["CONCRETE"] == "NOT VERIFIED"


def test_same_inputs_twice_and_shuffled_give_identical_bytes_and_semantics(tmp_path):
    a, _ = run(tmp_path, villa(), "a")
    b, _ = run(tmp_path, villa(), "b")
    sh = villa()
    random.Random(3).shuffle(sh)
    c, _ = run(tmp_path, sh, "c")
    for f in ("BOQ.csv", "BOQ.xlsx", "BOQ_TRADE_SUMMARY.csv", "EXPORT_MANIFEST.json"):
        assert (tmp_path / "a" / f).read_bytes() == (tmp_path / "b" / f).read_bytes() == \
            (tmp_path / "c" / f).read_bytes(), f
    assert a["semantic_sha256"] == b["semantic_sha256"] == c["semantic_sha256"]
    assert "قواعد" in (tmp_path / "a" / "BOQ.csv").read_text(encoding="utf-8")  # Arabic kept


def test_semantic_identity_is_separate_from_bytes(tmp_path):
    a, _ = run(tmp_path, villa(), "a")
    lines = villa()
    lines[1] = ln("STR.CONC.FOOTING", "F2", q=0.81, inputs={"L": 1.0, "B": 1.0, "H": 0.81})
    b, _ = run(tmp_path, lines, "b")
    assert a["semantic_sha256"] != b["semantic_sha256"]
    c, _ = run(tmp_path, villa(), "c", code_commit="another")       # bytes of the manifest move, the rows do not
    assert c["semantic_sha256"] == a["semantic_sha256"] and c["outputs"]["BOQ.csv"] == a["outputs"]["BOQ.csv"]


def test_held_unmeasured_verified_zero_survive_csv_and_xlsx_read_back(tmp_path):
    lines = villa()
    inv = {"schema": X.INVENTORY_SCHEMA, "project_id": PID, "revision_set_sha256": REV,
           "elements": [{"element_id": e, "item_code": "STR.CONC.FOOTING", "unit": "m3"} for e in ("F1", "F2", "F3", "F4")]
           + [{"element_id": "L1", "item_code": "STR.CONC.LINTEL", "unit": "m3"}]}
    whole = v2(lines, ["L1"], 0.0, "WHOLE", unit="m3", qty=0.0)
    comp = {("CONCRETE", "STR.CONC.LINTEL", "m3"): completeness("CONCRETE", "STR.CONC.LINTEL", "m3", 1)}
    m, rows = run(tmp_path, lines, inventory_doc=inv, v2_records=[whole], completeness=comp)
    assert by(rows, "F4")["quantity_state"] == "UNMEASURED" and by(rows, "F4")["net"] == ""
    assert by(rows, "L1")["quantity_state"] == "VERIFIED ZERO" and by(rows, "L1")["qty_verified_zero"] == "0.000000"
    ws = load_workbook(tmp_path / "o" / "BOQ.xlsx")["BOQ"]
    head = [c.value for c in ws[1]]
    xr = [dict(zip(head, [c.value for c in r])) for r in ws.iter_rows(min_row=2)]
    x = {r["element_id"]: r for r in xr}
    assert x["F4"]["quantity_state"] == "UNMEASURED" and x["F4"]["net"] is None
    assert x["S2"]["quantity_state"] == "HELD" and x["S2"]["net"] is None and x["S2"]["held_low"] is None
    assert x["S1"]["held_low"] == 5.0
    assert x["L1"]["quantity_state"] == "VERIFIED ZERO" and x["L1"]["qty_verified_zero"] == 0
    assert x["F1"]["qty_verified"] is None and x["F1"]["qty_measured_unverified"] == 1.2
    assert len(xr) == len(rows) == 9


# ---- adverse: identity, zeros, sealed -------------------------------------------------------------------------------

def test_two_revision_sets_refused(tmp_path):
    lines = villa() + [ln("STR.CONC.FOOTING", "F9", q=1.0, inputs={"L": 1}, revision_set_sha256="e" * 64)]
    with pytest.raises(X.ExportError, match="revision set"):
        run(tmp_path, lines)


def test_expected_project_and_inventory_project_pinned(tmp_path):
    with pytest.raises(X.ExportError, match="expected"):
        run(tmp_path, villa(), expect_project="OTHER")
    inv = {"schema": X.INVENTORY_SCHEMA, "project_id": "OTHER", "revision_set_sha256": REV, "elements": []}
    with pytest.raises(X.ExportError, match="inventory"):
        run(tmp_path, villa(), inventory_doc=inv)


def test_zero_without_any_input_refused_but_zero_with_gross_kept(tmp_path):
    with pytest.raises(X.ExportError, match="zero"):
        run(tmp_path, villa() + [ln("ARCH.WINDOW", "W14", q=0.0, unit="m2", inputs={"note": "height missing"})])


def test_sealed_benchmark_input_refused(tmp_path):
    from engine.reference_mapping import SEALED, SealedReferenceError
    p = tmp_path / SEALED[0]
    p.write_text(json.dumps([]), encoding="utf-8")
    with pytest.raises(SealedReferenceError):
        X.main(["--lines", str(p), "--candidate-version", CVER, "--out", str(tmp_path / "x")])
    assert not (tmp_path / "x").exists()


def test_duplicate_line_id_refused(tmp_path):
    lines = villa()
    with pytest.raises(X.ExportError, match="twice"):
        run(tmp_path, lines + [copy.deepcopy(lines[0])])


def test_cli_writes_the_three_files_and_manifest_inputs(tmp_path):
    p = tmp_path / "V3_0_T_BOQ_LINES.json"
    p.write_text(BL.dumps(villa()), encoding="utf-8")
    assert X.main(["--lines", str(p), "--candidate-version", CVER, "--out", str(tmp_path / "cli"),
                   "--code-commit", "abc"]) == 0
    m = json.loads((tmp_path / "cli" / "EXPORT_MANIFEST.json").read_text(encoding="utf-8"))
    assert m["identity"]["boq_lines_sha256"] == m["inputs_sha256"]["lines"] == X.sha256_bytes(p.read_bytes())
    assert m["row_counts"]["VERIFIED"] == 0 and m["row_counts"]["total"] == 8


# ---- verdicts: V1 never, V2 bound only ------------------------------------------------------------------------------

def v2(lines, eids, chk, scp, unit="m3", qty=None, **over):
    ls = [x for x in lines if x["location"]["element_id"] in eids]
    rec = {"schema": X.V2_VERDICT_SCHEMA, "verdict_id": f"V-{scp}-{'-'.join(eids)[:40]}", "project_id": PID,
           "revision_set_sha256": REV, "candidate_version": CVER, "boq_lines_sha256": BSHA,
           "line_ids": [x["line_id"] for x in ls], "element_scope": {"ids": sorted(eids), "count": len(eids)},
           "unit": unit, "engine_qty": qty if qty is not None else sum(x["measured_net"] or 0 for x in ls),
           "checker_qty": chk, "evidence": [{"sheet": "S-01", "printed": "1.50 x 1.00 x 0.80"}],
           "checker": {"run_token": "tok", "routine": "Verifier", "verdict_commit": "c0ffee"}, "scope": scp,
           "time": "2026-10-23T23:30Z"}
    rec.update(over)
    return rec


def completeness(trade, code, unit, n, **over):
    rec = {"schema": X.COMPLETENESS_SCHEMA, "project_id": PID, "revision_set_sha256": REV, "trade": trade,
           "item_code": code, "unit": unit, "inventory_count": n, "element_scope_count": n, "missing": 0,
           "duplicated": 0, "held": 0}
    rec.update(over)
    return rec


FOOT = ("CONCRETE", "STR.CONC.FOOTING", "m3")


def test_v1_record_never_makes_a_row_verified(tmp_path):
    km = {"keys": [{"key": "FOOT", "trade": "CONCRETE", "reference_id": "REF-1", "item_codes": ["STR.CONC.FOOTING"]}]}
    v1 = {"schema": X.V1_VERDICTS_SCHEMA, "verdicts": [
        {"ref_id": "REF-1", "kind": "REMEASURE", "scope": "WHOLE", "method": "CHECKER_REMEASURE_FROM_DRAWING",
         "unit": "m3", "engine_qty": 3.0, "checker_qty": 3.0, "source": "board", "commit": "abc"}]}
    m, rows = run(tmp_path, villa(), v1_doc=v1, key_map_doc=km)
    f1 = by(rows, "F1")
    assert f1["verdict_status"] == "V1_NOT_BINDING" and "V1#0 REMEASURE/WHOLE" in f1["verdict_id"]
    assert f1["quantity_state"] == "MEASURED UNVERIFIED" and m["row_counts"]["VERIFIED"] == 0


def test_whole_v2_needs_completeness_then_verifies(tmp_path):
    lines = villa()
    rec = v2(lines, ["F1", "F2", "F3"], 4.01, "WHOLE")                       # +0.25 %
    m, rows = run(tmp_path, lines, "a", v2_records=[rec])
    assert m["row_counts"]["VERIFIED"] == 0 and "completeness record missing" in by(rows, "F1")["verdict_status"]
    m, rows = run(tmp_path, lines, "b", v2_records=[rec], completeness={FOOT: completeness(*FOOT, 3)})
    assert m["row_counts"]["VERIFIED"] == 3 and by(rows, "F2")["qty_verified"] == "0.800000"
    assert by(rows, "F2")["qty_measured_unverified"] == "" and by(rows, "F2")["checker_qty"] == "4.010000"
    summ = {s["item_code"]: s for s in X.read_csv(tmp_path / "b" / "BOQ_TRADE_SUMMARY.csv")}
    assert summ["STR.CONC.FOOTING"]["line_status"] == "VERIFIED"
    assert summ["STR.CONC.FOOTING"]["trade_verified_whole_lines"] == "1 / 3"      # footing, lintel, slab
    m, rows = run(tmp_path, lines, "c", v2_records=[rec],
                  completeness={FOOT: completeness(*FOOT, 3, missing=1)})
    assert m["row_counts"]["VERIFIED"] == 0


@pytest.mark.parametrize("over,why", [({"candidate_version": "ARCH_TAKEOFF_V3.0.OLD"}, "STALE"),
                                      ({"boq_lines_sha256": "f" * 64}, "STALE"),
                                      ({"revision_set_sha256": "e" * 64}, "STALE"),
                                      ({"project_id": "OTHER"}, "STALE"),
                                      ({"unit": "m2"}, "STALE"),
                                      ({"engine_qty": 4.1}, "STALE"),
                                      ({"checker": {"run_token": "", "routine": "V", "verdict_commit": "c"}},
                                       "BINDING_INCOMPLETE"),
                                      ({"scope": "PARTIAL"}, "PARTIAL_SCOPE")])
def test_v2_bound_to_another_line_is_never_verified(tmp_path, over, why):
    lines = villa()
    rec = v2(lines, ["F1", "F2", "F3"], 4.0, "WHOLE", **over)
    m, rows = run(tmp_path, lines, v2_records=[rec], completeness={FOOT: completeness(*FOOT, 3)})
    assert m["row_counts"]["VERIFIED"] == 0 and by(rows, "F1")["verdict_status"].startswith(why)


def test_discrepancy_holds_the_line(tmp_path):
    lines = villa()
    rec = v2(lines, ["F1", "F2", "F3"], 4.3, "WHOLE")                         # +7.5 %
    m, rows = run(tmp_path, lines, v2_records=[rec], completeness={FOOT: completeness(*FOOT, 3)})
    f1 = by(rows, "F1")
    assert (f1["quantity_state"], f1["net"], f1["owner_status_class"]) == ("HELD", "", "HELD")
    assert "DISCREPANCY" in f1["held_reason"] and m["row_counts"]["VERIFIED"] == 0


def test_components_never_add_up_to_a_verified_line(tmp_path):
    lines = villa()
    recs = [v2(lines, [e], q, "COMPONENT") for e, q in (("F1", 1.2), ("F2", 0.8), ("F3", 2.0))]
    m, rows = run(tmp_path, lines, v2_records=recs, completeness={FOOT: completeness(*FOOT, 3)})
    assert m["row_counts"]["VERIFIED"] == 0 and m["row_counts"]["VERIFIED COMPONENT"] == 3
    summ = {s["item_code"]: s for s in X.read_csv(tmp_path / "o" / "BOQ_TRADE_SUMMARY.csv")}
    assert summ["STR.CONC.FOOTING"]["line_status"] == "PARTIALLY VERIFIED 3 / 3"
    assert summ["STR.CONC.FOOTING"]["verified_subtotal"] == "4.000000"
    assert summ["STR.CONC.FOOTING"]["measured_unverified_sum"] == ""


# ---- footing-shaped partial line (owner 20:59) ----------------------------------------------------------------------

def footing_villa():
    """25 measured footings (0.500 + i * 0.010 m3) + F10 HELD 0.216 .. 1.960 + band B1 owner-held (no range) +
    inventory: the 25 + F10 + B1 + FN9 (never measured) = 28 elements."""
    lines = [ln("STR.CONC.FOOTING", f"F{i:02d}", q=round(0.5 + i * 0.01, 3), inputs={"L": 1, "B": 1, "H": 0.5})
             for i in range(1, 26)]
    lines.append(ln("STR.CONC.FOOTING", "F10X", ev="BOUNDED_EXPOSURE", bounded_range={"low": 0.216, "high": 1.960},
                    rfi={"question": "outline carries two schedule tags"}))
    lines.append(ln("STR.CONC.FOOTING", "B1", ev="BLOCKED_RFI",
                    rfi={"question": "band cast with the footing?", "owner_decision_required": True}))
    inv = {"schema": X.INVENTORY_SCHEMA, "project_id": PID, "revision_set_sha256": REV,
           "elements": [{"element_id": x["location"]["element_id"], "item_code": "STR.CONC.FOOTING", "unit": "m3"}
                        for x in lines] + [{"element_id": "FN9", "item_code": "STR.CONC.FOOTING", "unit": "m3",
                                            "label": "neck footing"}]}
    return lines, inv


def test_footing_shaped_partial_line(tmp_path):
    lines, inv = footing_villa()
    recs = [v2(lines, [f"F{i:02d}"], round(0.5 + i * 0.01, 3), "COMPONENT") for i in range(1, 26)]
    hand_sub = sum(round(0.5 + i * 0.01, 3) for i in range(1, 26))        # 12.5 + 3.25 = 15.750
    m, rows = run(tmp_path, lines, v2_records=recs, inventory_doc=inv)
    assert len(rows) == 28 and m["row_counts"]["VERIFIED COMPONENT"] == 25 and m["row_counts"]["VERIFIED"] == 0
    s = X.read_csv(tmp_path / "o" / "BOQ_TRADE_SUMMARY.csv")[0]
    assert s["line_status"] == "PARTIALLY VERIFIED 25 / 28"
    assert s["verified_subtotal"] == f"{hand_sub:.6f}" == "15.750000"
    assert s["held_components"] == "B1 [no range]; F10X [0.216000 .. 1.960000]"
    assert s["unmeasured_components"] == "FN9" and s["rows_without_quantity"] == "3"
    assert by(rows, "B1")["owner_status_class"] == X.CLS_OWNER and by(rows, "B1")["net"] == ""
    assert by(rows, "F10X")["net"] == "" and by(rows, "FN9")["quantity_state"] == "UNMEASURED"
    # a WHOLE verdict over 25 of the 26 measured-or-held lines is refused as WHOLE
    w = v2(lines, [f"F{i:02d}" for i in range(1, 26)], hand_sub, "WHOLE")
    m2, rows2 = run(tmp_path, lines, "w", v2_records=[w], inventory_doc=inv,
                    completeness={FOOT: completeness(*FOOT, 28)})
    assert m2["row_counts"]["VERIFIED"] == 0 and by(rows2, "F01")["verdict_status"].startswith("SCOPE_DIFFERS")


def test_a_removed_held_row_is_flagged_as_missing_scope(tmp_path):
    lines, inv = footing_villa()
    cut = [x for x in lines if x["location"]["element_id"] != "F10X"]
    m, rows = run(tmp_path, cut, inventory_doc=inv)
    f10 = by(rows, "F10X")
    assert f10["quantity_state"] == "UNMEASURED" and "no BOQ line" in f10["unmeasured_reason"]
    assert len(rows) == 28                                                    # nothing silently gone
