"""Phase B1 comparison: arithmetic, comparability gate, readers, manual-QA detectors, the engine firewall, and the
frozen B1 registers (benchmark reveal + forensic comparison only - no engine change)."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "research/external_engine_lab"
sys.path.insert(0, str(LAB))
import alsenan_b1_benchmark as BB                                                 # noqa: E402
import alsenan_phase_b1 as B1                                                     # noqa: E402

REG = Path(__file__).parent / "registers_b1"
A3 = Path(__file__).parent / "registers_a3"
NAMES = ("BENCHMARK_SOURCE_MANIFEST", "BENCHMARK_DEPENDENCY", "FREELANCER_RAW_ROWS", "WEB_APP_ROWS",
         "BENCHMARK_NORMALISED", "COMPARABILITY_MATRIX", "FOOTING_COMPARISON", "F_F10_FORENSIC_COMPARISON",
         "STRUCTURAL_COMPARISON", "ARCHITECTURAL_COMPARISON", "MANUAL_BOQ_QA", "DIFFERENCE_REGISTER",
         "PROPOSED_FIX_BACKLOG", "OWNER_QUESTION_REGISTER_B1", "ALSENAN_PHASE_B1_COMPARISON_FREEZE", "TEST_RESULTS")
TOL = {"area_volume": {"close_match_pct": 1.0, "investigate_pct": 2.0, "material_above_pct": 2.0}}


# ------------------------------------------------------------------ arithmetic
def test_pct_diff_is_urban_minus_benchmark_over_benchmark():
    assert B1.pct_diff(110.0, 100.0) == pytest.approx(0.10)
    assert B1.pct_diff(90.0, 100.0) == pytest.approx(-0.10)
    assert B1.pct_diff(1.0, 0.0) is None and B1.pct_diff(None, 1.0) is None


@pytest.mark.parametrize("u,b,kind,expect", [
    (100.5, 100.0, "area", "CLOSE"), (101.5, 100.0, "area", "INVESTIGATE"), (103.0, 100.0, "area", "MATERIAL"),
    (100.0, 100.0, "volume", "EXACT"), (4.55, 4.551, "linear", "CLOSE"), (10.15, 10.0, "linear", "INVESTIGATE"),
    (10.5, 10.0, "linear", "MATERIAL"), (3, 3, "count", "EXACT"), (3, 2, "count", "DIFFERENT")])
def test_bands(u, b, kind, expect):
    assert B1.band(kind, u, b, TOL) == expect


def test_only_exact_comparable_rows_get_a_percentage():
    bk = B1.Book(TOL)
    a = bk.add("X", "FLOOR", "a", unit="m2", urban=10.0, bench=9.0, comparability="PARTIAL_SCOPE_COMPARABLE",
               confidence="HIGH")
    b = bk.add("X", "FLOOR", "b", unit="m2", urban=10.05, bench=10.0, comparability="EXACT_COMPARABLE",
               confidence="HIGH")
    assert a["pct_diff"] is None and a["abs_diff"] is None
    assert b["pct_diff"] == pytest.approx(0.5) and b["band"] == "CLOSE" and b["primary_class"] == "MATCH_WITHIN_TOLERANCE"
    c = bk.add("X", "FLOOR", "c", unit="m2", urban=12.0, bench=10.0, comparability="EXACT_COMPARABLE",
               confidence="HIGH")
    assert c["primary_class"] == "UNRESOLVED_REQUIRES_REVIEW"          # a difference is never assumed an Urban error


def test_class_and_comparability_vocabulary_enforced():
    bk = B1.Book(TOL)
    with pytest.raises(AssertionError):
        bk.add("X", "FLOOR", "a", unit="m2", urban=1.0, bench=1.0, comparability="ROUGHLY", confidence="HIGH")
    with pytest.raises(AssertionError):
        bk.add("X", "FLOOR", "a", unit="m2", urban=1.0, bench=2.0, comparability="EXACT_COMPARABLE",
               confidence="HIGH", primary="URBAN_IS_WRONG")


def test_metrics_never_report_a_global_accuracy_and_skip_low_rows():
    bk = B1.Book(TOL)
    bk.add("X", "FLOOR", "a", unit="m2", urban=10.0, bench=10.0, comparability="EXACT_COMPARABLE", confidence="HIGH")
    bk.add("X", "FLOOR", "b", unit="m2", urban=20.0, bench=10.0, comparability="EXACT_COMPARABLE", confidence="LOW")
    m = B1.metrics(bk.rows)
    assert m["global_accuracy"].startswith("NOT COMPUTED")
    assert m["by_trade"]["FLOOR"]["quantity_rows_high"] == 1 and m["by_trade"]["FLOOR"]["max_abs_pct_high"] == 0.0


# ------------------------------------------------------------------ readers
def _wb(tmp_path, rows, sheet="القواعد"):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet
    for r in rows:
        ws.append(r)
    p = tmp_path / "t.xlsx"
    wb.save(p)
    return p


def test_concrete_reader_details_subtotals_and_header_context(tmp_path):
    p = _wb(tmp_path, [["حصر خرسانة القواعد المسلحة "], ["بيان البند ", "العرض م"],
                       ["F", 0.8, 0.9, 0.3, 0.216, 4, None, None, 0.864],
                       ["إجمالي", None, None, None, None, None, None, None, 0.864]])
    raw, _ = BB.raw_xlsx(p, "RC")
    n = BB.normalise(raw)
    det = [x for x in n if x["row_kind"] == "DETAIL"]
    sub = [x for x in n if x["row_kind"] == "SUBTOTAL"]
    assert len(det) == 1 and det[0]["subtrade"] == "F" and det[0]["count"] == 4 and det[0]["floor"] == "FOUNDATION"
    assert det[0]["qty"] == pytest.approx(0.864) and det[0]["origin"] == "BENCHMARK"
    assert len(sub) == 1 and sub[0]["trade"] is None


def test_aluminium_reader_never_inherits_a_label(tmp_path):
    p = _wb(tmp_path, [["الطابق الأول"], ["شباك المسبح", 2, 1.55, 3, None, None, None, 9.3],
                       [None, 1, 1.55, 2, None, None, None, 3.1]], sheet="الكميات")
    raw, _ = BB.raw_xlsx(p, "ALU")
    n = [x for x in BB.normalise(raw) if x["row_kind"] == "DETAIL"]
    assert n[0]["label_ar"] == "شباك المسبح" and n[1]["label_ar"] is None
    assert n[1]["subtrade"] == "WINDOW" and n[1]["subtrade_basis"].startswith("COVER_ARITHMETIC")


def test_web_regex_keeps_arabic_indic_digits_out_of_the_quantity():
    m = BB.WEB_ROW.match("ﻃﺎﺑﻮﻗﻪﺍﻟﻒ ٢٢21,500 qty 0.10 KWD 2,042.50 KWD")
    assert m and BB._f(m["qty"]) == 21500.0 and "٢٢" in m["desc"]


def test_hash_verification_fails_closed(tmp_path):
    with pytest.raises(RuntimeError):
        BB.verify(tmp_path)


# ------------------------------------------------------------------ manual-QA detectors (synthetic raw rows)
def _raw(cells, sheet="S", key="RC"):
    rows = {}
    for ref, (v, f) in cells.items():
        r = int("".join(ch for ch in ref if ch.isdigit()))
        rows.setdefault(r, {"file": key, "sheet": sheet, "row": r, "cells": {}})["cells"][ref] = {"v": v, "f": f}
    return [rows[k] for k in sorted(rows)]


def test_qa_detects_a_sum_that_skips_the_first_row_and_a_cross_row_product():
    raw = _raw({"A1": ("B1", None), "I1": (0.128, None), "I2": (0.32, None), "I3": (0.24, None),
                "I4": (0.688, "=SUM(I1:I3)"), "A5": ("إجمالي", None), "I5": (0.56, "=SUM(I2:I3)"),
                "B6": (1.0, None), "C6": (2.0, None), "D6": (3.0, None), "D7": (3.0, None),
                "H6": (6.0, "=D7*C6*B6")})
    checks = {f["check"] for f in B1.manual_qa(raw, [])["findings"]}
    assert "SUM_SKIPS_LEADING_ROWS" in checks and "PRODUCT_REFERENCES_ANOTHER_ROW" in checks


def test_qa_detects_a_total_that_contains_another_reported_total():
    raw = _raw({"H13": (151.8, None), "H16": (14.0, None), "H44": (165.8, "=SUM(H13:H41)")}, sheet="رخام+حوش", key="FIN")
    raw += _raw({"B22": (151.8, "='رخام+حوش'!H13"), "B24": (165.8, "='رخام+حوش'!H44")}, sheet="الغلاف", key="FIN")
    f = [x for x in B1.manual_qa(raw, [])["findings"] if x["check"] == "TOTAL_CONTAINS_ANOTHER_REPORTED_TOTAL"]
    assert f and f[0]["contains"] == "H13" and f[0]["class"] == "BENCHMARK_POSSIBLE_ERROR"


def test_qa_flags_broken_references():
    raw = _raw({"D19": ("#REF!", "=I16+#REF!")})
    assert any(f["check"] == "BROKEN_REFERENCE" for f in B1.manual_qa(raw, [])["findings"])


# ------------------------------------------------------------------ firewall
def _imports(path):
    tree = ast.parse(Path(path).read_text())
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
            out |= {f"{node.module}.{a.name}" for a in node.names}
        elif isinstance(node, ast.Import):
            out |= {a.name for a in node.names}
    return out


def test_b1_code_imports_no_engine_quantity_module():
    for f in ("alsenan_phase_b1.py", "alsenan_b1_benchmark.py", "alsenan_b1_package.py"):
        p = LAB / f
        if not p.exists():
            continue
        eng = {m for m in _imports(p) if m.startswith("engine")}
        assert eng <= {"engine", "engine.boq_rc1_xlsx"}, (f, eng)        # the XLSX zip repack only


def test_no_engine_module_references_the_b1_lab():
    for p in (ROOT / "engine").rglob("*.py"):
        t = p.read_text(errors="ignore")
        assert "alsenan_b1" not in t and "alsenan_phase_b1" not in t, p


# ------------------------------------------------------------------ frozen B1 registers
def R(n):
    p = REG / f"{n}.json"
    if not p.exists():
        pytest.skip(f"{n} not generated")
    return json.loads(p.read_text())


def test_all_b1_registers_exist():
    if not REG.exists():
        pytest.skip("B1 registers not generated")
    assert sorted(p.stem for p in REG.glob("*.json")) == sorted(NAMES)


def test_freeze_boundary():
    fz = R("ALSENAN_PHASE_B1_COMPARISON_FREEZE")
    assert fz["BENCHMARK_OPENED"] is True and fz["ENGINE_CHANGED"] is False and fz["QORTUBA_CHANGED"] is False
    assert fz["PHASE_A3_FREEZE_PRESERVED"] is True and fz["engine_tree"]["unchanged"] is True
    assert fz["phase_a3"]["freeze_sha256"] == B1.A3_FREEZE_SHA
    cm = R("COMPARABILITY_MATRIX")
    assert fz["comparison_digest"] == B1.digest(cm["rows"])
    assert fz["extracted_rows_digest"] == B1.digest(R("FREELANCER_RAW_ROWS")["rows"])
    assert fz["xlsx"]["readback"] == "PASS" and fz["xlsx"]["rewrite_identical"] is True


def test_a3_registers_unchanged_since_9aa2741():
    try:
        names = subprocess.run(["git", "ls-tree", "--name-only", "9aa2741", "tests/alsenan/registers_a3/"],
                               capture_output=True, text=True, cwd=ROOT, check=True).stdout.split()
    except Exception:
        pytest.skip("git history not available")
    for n in names:
        blob = subprocess.run(["git", "show", f"9aa2741:{n}"], capture_output=True, cwd=ROOT, check=True).stdout
        assert hashlib.sha256(blob).hexdigest() == hashlib.sha256((ROOT / n).read_bytes()).hexdigest(), n


def test_comparability_gate_and_vocabulary_in_the_frozen_rows():
    for r in R("COMPARABILITY_MATRIX")["rows"]:
        assert r["comparability"] in B1.COMPARABILITY and r["primary_class"] in B1.CLASSES
        assert all(s in B1.CLASSES for s in r["secondary_classes"]) and r["confidence"] in ("HIGH", "MEDIUM", "LOW")
        if r["comparability"] != "EXACT_COMPARABLE":
            assert r["pct_diff"] is None


def test_every_benchmark_record_is_marked_benchmark_origin():
    assert R("FREELANCER_RAW_ROWS")["origin"] == "BENCHMARK"
    assert all(n["origin"] == "BENCHMARK" for n in R("BENCHMARK_NORMALISED")["records"])
    assert R("BENCHMARK_DEPENDENCY")["WEB_APP_DEPENDENCY"] == "DERIVED_FROM_FREELANCER_BOQ"


def test_footing_findings():
    fc = {t["type"]: t for t in R("FOOTING_COMPARISON")["types"]}
    assert fc["F3"]["urban_tags"] == 2 and fc["F3"]["manual_count"] == 1 and fc["F3"]["count_class"] == "BENCHMARK_POSSIBLE_ERROR"
    assert fc["F"]["urban_tags"] == 5 and fc["F"]["manual_count"] == 4 and fc["F"]["count_class"] == "SOURCE_GAP"
    assert all(t["manual_dims_equal_schedule"] in (True, None) for t in fc.values())
    ff = R("F_F10_FORENSIC_COMPARISON")
    assert ff["manual_method"] == "E_F_ABSORBED_INTO_F10" and ff["urban_change"].startswith("NONE")
    for s in R("FOOTING_COMPARISON")["straps"]:
        assert s["section_equal"] and abs(s["urban_length_m"] - s["manual_length_m"]) <= 0.05


def test_rebar_is_an_allowance_and_never_gold():
    rb = R("STRUCTURAL_COMPARISON")["rebar"]
    assert rb["all_typed_constants"] and rb["deterministic"] is False and rb["method_class"] == "MANUAL_ESTIMATE_METHOD"


def test_owner_values_not_changed_to_match():
    al = R("ARCHITECTURAL_COMPARISON")["aluminium"]
    assert al["salon"]["urban_area_m2"] == 23.1045 and al["salon"]["width_attributable_m2"] == 0.0
    a3 = json.loads((A3 / "ALUMINIUM_GLAZING_REGISTER.json").read_text())
    assert a3["salon"]["height_m"] == 3.65


def test_backlog_is_not_implemented():
    assert R("PROPOSED_FIX_BACKLOG")["implemented"].startswith("NONE")
