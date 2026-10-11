"""M5 package: deliverables; hygiene, path and firewall over every committed text file; external figures only as
records (never a constant in the package code, never in engine / tools code); nothing tracked that embeds drawing
content; numbers agree across files; RC and plain concrete never added; every record in one group; the bridge
closes; nothing VERIFIED; the RECONCILIATION phase declared after a freeze; and - with the private drawings - a live
reproduction of every committed file byte for byte."""

from __future__ import annotations

import ast
import csv
import importlib.util
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research/urban_engine_m5_concrete_reconciliation"
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}|(?i:als[ey]?n[ya]?an)")
DELIVERABLES = ("00_README.md", "00_NUMBERS.json", "01_EXECUTIVE_CONCRETE_RECONCILIATION.md",
                "02_SOURCE_SCOPE_MATRIX.csv", "02A_SOURCE_INVENTORY.csv", "02B_FOUR_SOURCE_BASELINE.csv",
                "02C_FAMILY_TOTALS.csv", "03_ELEMENT_BY_ELEMENT_COMPARISON.csv", "03A_ELEMENT_MEMBERSHIP.csv",
                "04_FREELANCER_VS_URBAN_BRIDGE.csv", "05_GROUND_BEAM_AND_SLAB_AUDIT.md", "06_SUSPENDED_SLAB_AUDIT.md",
                "07_FOUNDATIONS_COLUMNS_BEAMS_AUDIT.md", "08_STAIRS_DOMES_POOL_AUDIT.md", "09_BLINDING_CONCRETE_AUDIT.md",
                "10_MISSING_CONCRETE_REGISTER.csv", "11_DOUBLE_COUNT_REGISTER.csv", "11A_M5_OWNERSHIP_DECISIONS.csv",
                "12_QUOTATION_COST_EXPOSURE.csv", "12A_QUOTATION_SCENARIOS.csv", "13_PRIORITY_RFIS.csv",
                "14_VISUAL_CONCRETE_QA.html", "15_INDEPENDENT_VALIDATION.md", "15A_INDEPENDENT_CHECKS.csv",
                "16_TEST_RESULTS.md", "17_CHATGPT_HANDOFF.md", "18_ENGINE_CHANGE_V3_TO_V4.csv", "build_m5_package.py",
                "evidence/M5_BRIEF_STATED_VALUES.json")
DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
ARCH = ROOT / "data/inputs/by_sha256/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"
sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))


def _rows(name):
    with open(PKG / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _num():
    return json.loads((PKG / "00_NUMBERS.json").read_text(encoding="utf-8"))


def _tracked():
    out = subprocess.run(["git", "ls-files", str(PKG.relative_to(ROOT))], cwd=ROOT, capture_output=True, text=True)
    return [ROOT / p for p in out.stdout.split()]


def _f(x):
    return float(x) if x not in ("", None) else 0.0


def test_deliverables_present():
    missing = [d for d in DELIVERABLES if not (PKG / d).exists()]
    assert not missing, missing
    assert len(list((PKG / "visual").glob("*.svg"))) >= 10


def test_hygiene_paths_and_firewall_over_every_text_file():
    files = [p for p in PKG.rglob("*") if p.is_file() and p.suffix in (".csv", ".json", ".md", ".html", ".svg", ".py")
             and "__pycache__" not in p.parts]
    assert len(files) > 40
    for p in files:
        t = p.read_text(encoding="utf-8")
        assert not HYGIENE.search(t), p
        assert not re.search(r"/home/|/tmp/|/root/|[A-Za-z]:\\\\|\.dwg\b", t), p
        assert "ae608411" not in t and "d025d9f0-" not in t, p


def test_external_figures_are_records_never_constants():
    """No reference-QS / oracle figure is a literal in the M5 code; the figures live in the records it reads."""
    import rebar_product_registry as RP                                           # noqa: F401
    from test_rebar_product_firewall import forbidden_number
    for p in sorted(PKG.glob("*.py")):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        bad = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and forbidden_number(n.value)]
        assert not bad, (p.name, bad)
    # ... and the engine / tools code never reads the M5 package
    for d in ("engine", "tools"):
        for p in (ROOT / d).rglob("*.py"):
            assert "urban_engine_m5_concrete_reconciliation" not in p.read_text(encoding="utf-8"), p


def test_m5_code_is_declared_comparison_and_unreachable_from_accurate():
    import rebar_product_registry as RP
    assert "research/urban_engine_m5_concrete_reconciliation" in RP.COMPARISON_DIRS
    for p in sorted(PKG.glob("*.py")):
        assert str(p.relative_to(ROOT)) in RP.COMPARISON_MODULES, p.name


def test_no_drawing_workbook_pdf_or_image_in_git():
    bad = [p for p in _tracked() if p.suffix.lower() in (".dxf", ".dwg", ".pdf", ".xlsx", ".png", ".jpg", ".zip")]
    assert not bad, bad


def test_reconciliation_phase_declared_after_a_freeze():
    n = _num()
    assert n["phase"] == "BENCHMARK_RECONCILIATION"
    assert n["freeze"]["phase"] == "CANDIDATE_GEOMETRY_FROZEN" and len(n["freeze"]["CANDIDATE_GEOMETRY_HASH"]) == 24
    ex = (PKG / "01_EXECUTIVE_CONCRETE_RECONCILIATION.md").read_text(encoding="utf-8")
    assert "RECONCILIATION" in ex and n["freeze"]["CANDIDATE_GEOMETRY_HASH"] in ex


def test_rc_and_plain_concrete_never_added():
    n = _num()
    fam = {r["FAMILY"]: r for r in _rows("02C_FAMILY_TOTALS.csv")}
    rc = sum(_f(r["URBAN_M5_MEASURED_BASE_M3"]) for k, r in fam.items() if r["RC"] == "YES")
    assert abs(rc - n["urban_m5"]["MEAS_BASE"]) < 1e-4
    assert fam["BLINDING"]["RC"] == "NO"
    tot = [r for r in _rows("12_QUOTATION_COST_EXPOSURE.csv") if r["LINE"] == "TOTAL_RC"][0]
    assert "BLINDING" not in [r["LINE"] for r in _rows("12_QUOTATION_COST_EXPOSURE.csv")]
    assert abs(_f(tot["MEASURED_BASE_M3"]) - n["urban_m5"]["MEAS_BASE"]) < 1e-4
    assert abs(n["m4_total_incl_plain_m3"] - n["m4_rc_m3"] - n["m4_plain_m3"]) < 1e-6


def test_bridge_closes_and_every_step_is_classified_and_priced():
    n = _num()
    st = _rows("04_FREELANCER_VS_URBAN_BRIDGE.csv")
    assert abs(n["bridge"]["closure"]) < 1e-6
    assert abs(n["bridge"]["start"] + sum(_f(r["M3"]) for r in st) - n["bridge"]["end"]) < 1e-4
    assert all(r["CLASS"] and r["EVIDENCE"] for r in st)
    rate = n["rate_kwd_per_m3"]
    assert all(abs(_f(r["KWD"]) - _f(r["M3"]) * rate) < 0.01 for r in st)
    assert abs(n["bridge"]["end"] - n["urban_m5"]["MEAS_BASE"]) < 1e-6


def test_every_record_in_exactly_one_group_nothing_dropped():
    mem = _rows("03A_ELEMENT_MEMBERSHIP.csv")
    ids = Counter(r["RECORD_ID"] for r in mem)
    assert max(ids.values()) == 1
    n = _num()
    assert len(mem) == n["n_urban_items"] + sum(1 for r in mem if r["SOURCE"].startswith("FREELANCER"))
    el = {r["ELEMENT_ID"] for r in _rows("03_ELEMENT_BY_ELEMENT_COMPARISON.csv")}
    assert {r["ELEMENT_ID"] for r in mem} == el
    # the freelancer side of the membership adds up to its RC total + its plain concrete
    fl = sum(_f(r["BASE_M3"]) for r in mem if r["SOURCE"].startswith("FREELANCER"))
    assert abs(fl - n["freelancer_rc_m3"] - n["freelancer_plain_m3"]) < 1e-4


def test_element_rows_classified_and_located():
    allowed = ("MATCHED_WITHIN_TOLERANCE", "MISSING_IN_URBAN", "MISSING_IN_FREELANCER", "MISSING_IN_MCP",
               "DOUBLE_COUNTED", "SCOPE_DIFFERENCE", "GEOMETRY_DIFFERENCE", "THICKNESS_OR_DEPTH_DIFFERENCE",
               "HEIGHT_OR_LEVEL_DIFFERENCE", "BEAM_SLAB_OVERLAP", "ASSUMPTION_DIFFERENCE", "SOURCE_CONFLICT",
               "UNRESOLVED_REQUIRES_ENGINEER")
    rows = _rows("03_ELEMENT_BY_ELEMENT_COMPARISON.csv")
    assert len(rows) > 100
    for r in rows:
        assert any(r["CLASS"].startswith(a) for a in allowed), r["CLASS"]
        if r["CLASS"] != "MATCHED_WITHIN_TOLERANCE" and abs(_f(r["DIFF_FREELANCER_MINUS_URBAN_BASE_M3"])) > 0.5:
            assert r["URBAN_LOCATION"] or r["EXPLANATION"], r["ELEMENT_ID"]     # located or explained
        assert r["RELEASE_STATUS"] not in ("VERIFIED", "APPROVED", "RELEASED")


def test_nothing_verified_and_not_quotation_ready():
    ex = (PKG / "01_EXECUTIVE_CONCRETE_RECONCILIATION.md").read_text(encoding="utf-8")
    assert "NOT QUOTATION-READY" in ex and "not engineering approval" in ex
    assert "INCOMPLETE" in ex
    assert all(r["STATUS"] != "VERIFIED" for r in _rows("10_MISSING_CONCRETE_REGISTER.csv"))


def test_no_ratio_fills_missing_quantities():
    for name in ("10_MISSING_CONCRETE_REGISTER.csv", "12_QUOTATION_COST_EXPOSURE.csv", "03A_ELEMENT_MEMBERSHIP.csv"):
        assert "kg/m3" not in (PKG / name).read_text(encoding="utf-8").lower()
    unm = [r for r in _rows("10_MISSING_CONCRETE_REGISTER.csv") if r["STATUS"] == "UNMEASURABLE"]
    assert unm and all(_f(r["LOW_M3"]) == 0 and _f(r["HIGH_M3"]) == 0 and r["NEEDED"] for r in unm)


def test_independent_checks_all_pass():
    rows = _rows("15A_INDEPENDENT_CHECKS.csv")
    assert len(rows) >= 18 and all(r["RESULT"] == "PASS" for r in rows), [r for r in rows if r["RESULT"] != "PASS"]
    assert _num()["checks_pass"] == len(rows)


def test_missing_sources_recorded_not_recreated():
    inv = {r["SOURCE_ID"]: r for r in _rows("02A_SOURCE_INVENTORY.csv")}
    for sid in ("FL-WORKBOOK-ORIGINAL", "CHR-REPORT", "UC4N-REPORT"):
        assert inv[sid]["STATE"] == "MISSING" and inv[sid]["NOTE"], sid
    assert inv["S31-FREELANCER_CATEGORY_LINEAGE"]["STATE"] == "HASH_MATCH"
    assert all(r["STATE"] in ("HASH_MATCH", "PRESENT", "MISSING") for r in inv.values())


def test_rfis_ranked_with_quantity_and_cost():
    rf = _rows("13_PRIORITY_RFIS.csv")
    assert len(rf) >= 12
    sw = [_f(r["SWING_M3"]) for r in rf]
    assert sw == sorted(sw, reverse=True)
    assert all(r["QUESTION"] and r["TO"] for r in rf)


@pytest.mark.skipif(not (DXF.exists() and ARCH.exists()), reason="prerequisite: the private ST7757 drawings")
def test_live_reproduction_of_every_committed_text_file(tmp_path):
    sys.path.insert(0, str(PKG))
    spec = importlib.util.spec_from_file_location("m5b_t", PKG / "build_m5_package.py")
    B = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(B)
    P = B.compute()
    files, _ = B.write_all(P, out=tmp_path, pdf=False, xlsx=False)
    for name, text in files.items():
        assert text == (PKG / name).read_text(encoding="utf-8"), name
