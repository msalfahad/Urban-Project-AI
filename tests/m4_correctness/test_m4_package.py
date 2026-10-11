"""M4 package: deliverables present; hygiene, path and benchmark firewall over every committed text file; no drawing,
workbook, PDF or image in git; the registers agree with each other; nothing VERIFIED; no OCR record promoted; every
independent check passes; and - when the private drawings are present - a live reproduction of the M4 registers
byte for byte from the drawings (the CLI pipeline the package builder runs)."""

from __future__ import annotations

import csv
import importlib.util
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research/urban_engine_m4_correctness"
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}|(?i:als[ey]?n[ya]?an)")
DELIVERABLES = ("00_README.md", "00_NUMBERS.json", "01_EXECUTIVE_REPORT.md", "02_BEFORE_AFTER_QUANTITIES.csv",
                "03_RECONCILIATION_M3_TO_M4.csv", "03_RECONCILIATION_SUMMARY.csv", "03A_CB_SPAN_AUDIT.csv",
                "03B_EXTERIOR_GB_AUDIT.csv", "03C_SLAB_THICKNESS_AUDIT.csv", "03D_BLINDING_AUDIT.csv",
                "04_OCR_REVIEW_SHEET.csv", "05_CB_LINES.csv", "05_CB_PHYSICAL_BARS.csv",
                "06_MISSING_REINFORCEMENT_REGISTER.csv", "06_MISSING_REINFORCEMENT_SUMMARY.csv",
                "07_UNRESOLVED_CONCRETE_EXCEPTIONS.csv", "07_LINTEL_OPENINGS.csv", "08_CONFLICTS.csv",
                "08_OCR_DERIVED_ITEMS.csv", "09_BENCHMARK_POSITIONS.csv", "10_INDEPENDENT_VALIDATION.csv",
                "11_HELDOUT_EVALUATION.json", "11_HELDOUT_EVALUATION.md", "12_RFIS.csv", "13_TEST_RECORD.md",
                "14_COMMANDS.md", "15_CHATGPT_NOTES.md", "build_m4_package.py", "evaluate_heldout_m4.py",
                "independent_checks.py", "profile_st7757_m4.json", "evidence/OCR_INDEPENDENT_READINGS.json")
DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
ARCH = ROOT / "data/inputs/by_sha256/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"


def _rows(name):
    with open(PKG / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _tracked():
    out = subprocess.run(["git", "ls-files", str(PKG.relative_to(ROOT))], cwd=ROOT, capture_output=True, text=True)
    return [ROOT / p for p in out.stdout.split()]


def _bench():
    spec = importlib.util.spec_from_file_location("m1pf_m4t", ROOT / "research/alsenan_m1_usable_boq/post_freeze/"
                                                               "post_freeze_comparison.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.BENCH


def test_deliverables_present():
    missing = [d for d in DELIVERABLES if not (PKG / d).exists()]
    assert not missing, missing


def test_hygiene_paths_and_firewall_over_every_text_file():
    bench = _bench()
    files = [p for p in PKG.rglob("*") if p.is_file() and p.suffix in (".csv", ".json", ".md", ".html", ".svg", ".py")
             and "__pycache__" not in p.parts and p.name != "run_log.json"]
    assert len(files) > 40
    for p in files:
        t = p.read_text(encoding="utf-8")
        if p.suffix != ".py":
            assert not HYGIENE.search(t), p
            assert not re.search(r"/home/|/tmp/|[A-Za-z]:\\\\|\.dwg\b", t), p
        assert not [b for b in bench if re.search(r"(?<![\d.])" + re.escape(b) + r"(?!\d)", t)], p
        assert "ae608411" not in t and "d025d9f0-" not in t, p


def test_no_drawing_workbook_pdf_or_image_in_git():
    bad = [p for p in _tracked() if p.suffix.lower() in (".dxf", ".dwg", ".pdf", ".xlsx", ".png", ".jpg", ".zip")]
    assert not bad, bad
    assert not [p for p in _tracked() if p.name == "run_log.json"]


def test_registers_agree():
    reg = _rows("06_MISSING_REINFORCEMENT_REGISTER.csv")
    comp = _rows("st7757_route_g/REBAR_COMPLETENESS.csv")
    miss = {r["COMPONENT_ID"] for r in comp if r["REBAR_STATE"] in ("MISSING_DATA", "PARTIAL_MISSING")}
    assert {r["COMPONENT_ID"] for r in reg} == miss
    s = [r for r in _rows("06_MISSING_REINFORCEMENT_SUMMARY.csv") if r["BY"] == "FAMILY"]
    assert sum(int(r["COMPONENTS"]) for r in s) == len(reg)
    ex = _rows("07_UNRESOLVED_CONCRETE_EXCEPTIONS.csv")
    un = [r for r in _rows("st7757_route_g/UNRESOLVED_REGISTER.csv") if r["TRADE"] == "CONCRETE"]
    assert len(ex) == len(un) and len({r["NO"] for r in ex}) == len(ex)
    assert all(r["X_M"] for r in ex)                                   # every exception is located
    n = json.loads((PKG / "00_NUMBERS.json").read_text())
    assert sum(n["m4_unresolved_concrete"].values()) == len(ex)
    fam = {(r["TRADE"], r["FAMILY"]): r for r in _rows("02_BEFORE_AFTER_QUANTITIES.csv")}
    tot = n["summary"]["totals"]["CONCRETE"]
    assert abs(float(fam[("CONCRETE", "ALL_FAMILIES")]["M4_BASE"]) - tot["PROVISIONAL_BASE"]) < 1e-3


def test_nothing_verified_and_no_ocr_record_promoted():
    assert not [r for r in _rows("st7757_route_g/VERIFIED_REGISTER.csv")]
    rows = _rows("04_OCR_REVIEW_SHEET.csv")
    assert len(rows) == 15 and all(r["PROMOTED"] == "False" for r in rows)
    assert all(r["STATE_AFTER_REVIEW"] != "MANUALLY_CONFIRMED" for r in rows)
    assert Counter(r["OUTCOME"] for r in rows) == {"AGREES": 14, "REJECTED_STAYS": 1}
    assert all(r["DOWNSTREAM_ITEMS"] != "" for r in rows)


def test_independent_checks_all_pass_and_disclose_shared_code():
    rows = _rows("10_INDEPENDENT_VALIDATION.csv")
    assert rows and all(r["RESULT"] == "PASS" for r in rows)
    assert all(r["SHARED_WITH_ENGINE"] for r in rows)
    assert {r["CHECK_ID"][:5] for r in rows} >= {"IC-01", "IC-02", "IC-03", "IC-04", "IC-05", "IC-06", "IC-07",
                                                   "IC-08", "IC-09"}


def test_missing_steel_counted_never_by_ratio():
    reg = _rows("06_MISSING_REINFORCEMENT_REGISTER.csv")
    assert reg and all(r["DETAIL_REQUIRED"] and r["MISSING_ROLES"] for r in reg)
    assert not any("kg/m3" in json.dumps(r).lower() for r in reg)
    assert {r["EXISTENCE"] for r in reg} <= {"MEASURED", "SECTION_UNRESOLVED", "NEED_UNRESOLVED", "NO_CONCRETE_ITEM"}


def test_benchmark_positions_only():
    rows = _rows("09_BENCHMARK_POSITIONS.csv")
    for r in rows:
        assert set(r) <= {"GROUP", "ENGINE", "GENERIC_PLANNING_LOW_M3", "GENERIC_PLANNING_BASE_M3",
                          "GENERIC_PLANNING_HIGH_M3", "EXTERNAL_POSITION_VS_GENERIC", "EXTERNAL_POSITION_VS_M1",
                          "GENERIC_SCOPE", "STATE", "WHY"}


def test_heldout_m4_never_assigns_a_wrong_section():
    h = json.loads((PKG / "11_HELDOUT_EVALUATION.json").read_text())
    m4 = h["m4_M4"]["unlabelled_spans"]
    assert m4["precision"] == 1.0 and m4["outcomes"].get("WRONG_SECTION", 0) == 0
    assert m4["never_wrong_or_covered"] == 1.0
    assert h["m4_M3"]["unlabelled_spans"]["outcomes"].get("WRONG_SECTION", 0) > 0     # the risk M4 removes
    assert h["clean_M4"]["end_to_end_success"] == 40 and h["m4_M4"]["end_to_end_success"] == 40


def test_rfis_and_profile_provenance():
    rf = _rows("12_RFIS.csv")
    assert len(rf) >= 10 and all(r["QUESTION"] and r["SCOPE"] for r in rf)
    prof = json.loads((PKG / "profile_st7757_m4.json").read_text())
    assert all(c.get("provenance") and c.get("source") for c in prof["conventions"])


@pytest.mark.skipif(not (DXF.exists() and ARCH.exists()), reason="prerequisite: the private ST7757 drawings")
def test_live_reproduction_of_the_m4_registers():
    import sys
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("m4b_t", PKG / "build_m4_package.py")
    B = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(B)
    R = B.m4_run()
    R["generic"]["previous_register"] = B.m3_register()
    T = B.CLI.m4_tables(R)
    for name, key in (("06_MISSING_REINFORCEMENT_REGISTER.csv", "MISSING_REINFORCEMENT_REGISTER"),
                      ("07_UNRESOLVED_CONCRETE_EXCEPTIONS.csv", "UNRESOLVED_CONCRETE_EXCEPTIONS"),
                      ("05_CB_LINES.csv", "CB_LINES"), ("05_CB_PHYSICAL_BARS.csv", "CB_PHYSICAL_BARS")):
        assert B._csv(T[key]) == (PKG / name).read_text(encoding="utf-8"), name
    ic = B._module(PKG / "independent_checks.py", "m4ic_t")
    rows = ic.checks(R["generic"]["D"], R["items"], R["generic"]["register"], R["conv"], R["generic"].get("arch"))
    assert B._csv(rows) == (PKG / "10_INDEPENDENT_VALIDATION.csv").read_text(encoding="utf-8")
