"""M3 package checks: the deliverables exist, carry no owner text, file path or firewalled benchmark number, the
registers keep their categories and classes, and the files that depend on the current engine only (not on the M2
worktree) reproduce byte for byte from the private drawing (skipped when it is not present). Nothing is written."""

from __future__ import annotations

import csv
import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research/urban_engine_m3_recovery"
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}|(?i:als[ey]?n[ya]?an)")
PATH = re.compile(r"(?i)[a-z]:\\|\\[a-z0-9_]+\\|\.dwg\b|/home/|/tmp/")
DELIVERABLES = ["00_README.md", "00_NUMBERS.json", "01_FINAL_REPORT.md", "02_BEFORE_AFTER_DETECTION.csv",
                "03_CONCRETE_BY_FAMILY.csv", "04_REINFORCEMENT_BY_FAMILY.csv", "05_RECONCILIATION_M2_TO_M3.csv",
                "05_RECONCILIATION_SUMMARY.csv", "06_BEAMS_BY_MARK_VS_FROZEN.csv",
                "07_REINFORCEMENT_COMPLETENESS_89.csv", "08_MISSING_STEEL_BY_FAMILY_STOREY.csv",
                "09_BENCHMARK_POSITIONS.csv", "10_UNRESOLVED_REGISTER.csv", "11_NOT_DETECTED_REGISTER.csv",
                "11_COVERAGE_RISK.csv", "12_COVERAGE_DASHBOARD.html", "13_HELDOUT_EVALUATION.md",
                "13_HELDOUT_EVALUATION.json", "14_PERFORMANCE.json", "15_WORKFLOW.md", "16_REGRESSION_RECORD.md",
                "17_TEST_RUN.md", "18_CHATGPT_NOTES.md", "19_RFIS.csv", "profile_st7757_m3.json",
                "evidence/DETAIL_EVIDENCE.json", "st7757_route_g/CONTRACTOR_BOQ.csv",
                "st7757_route_g/REBAR_COMPLETENESS.csv", "st7757_route_g/MISSING_STEEL_BY_FAMILY_STOREY.csv",
                "st7757_route_g/FAMILY_COVERAGE.csv", "st7757_route_g/SUMMARY.json"]
CLASSES = {"Corrected omission", "Corrected double count", "Source interpretation", "Provisional assumption",
           "Remaining extraction failure", "Remaining source ambiguity"}
REBAR_STATES = {"MEASURED", "PROVISIONAL_MODEL", "PARTIAL_MISSING", "MISSING_DATA", "EXPLICIT_NONE", "OUTSIDE_SCOPE"}
UNMATCHED = {"NO_GENERIC_BAND_AT_STATIONS", "NO_UNIQUE_GENERIC_BAND", "TAG_NOT_BOUND_BY_GENERIC", "TAG_NOT_FOUND",
             "NO_GENERIC_BAND", "NO_GEOMETRY_IN_ID"}
PROVENANCE = {"PRINTED_VALUE", "PRINTED_MINIMUM", "PRINTED_PROJECT_DEFAULT", "PRINTED_TYPICAL_DETAIL",
              "READING_OF_PRINTED_VALUE", "DRAWN_GEOMETRY", "FROZEN_STAGE_MODEL", "STANDARD_PRACTICE",
              "ENGINEERING_JUDGEMENT"}
ST_DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _rows(name):
    with (PKG / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_deliverables_present():
    missing = [d for d in DELIVERABLES if not (PKG / d).exists()]
    assert not missing, missing


def test_package_text_is_clean_and_firewalled():
    bench = _module(ROOT / "research/alsenan_m1_usable_boq/post_freeze/post_freeze_comparison.py", "m1pf_m3t").BENCH
    for p in PKG.rglob("*"):
        if p.suffix not in (".md", ".csv", ".json", ".html", ".svg") or not p.is_file():
            continue
        t = p.read_text(encoding="utf-8")
        where = p.relative_to(ROOT)
        assert not HYGIENE.search(t), where
        assert not PATH.search(t), where
        leaked = [b for b in bench if re.search(r"(?<![\d.])" + re.escape(b) + r"(?!\d)", t)]
        assert not leaked, (where, leaked)


def test_no_client_content_in_the_package():
    # crops, page renders, PDFs and workbooks are generated and git-ignored; no drawing is ever copied in
    assert not [p for p in PKG.rglob("*") if p.suffix.lower() in (".dxf", ".dwg")]
    ignore = (ROOT / ".gitignore").read_text()
    for rule in ("research/urban_engine_m3_recovery/**/crops/", "research/urban_engine_m3_recovery/**/*.png",
                 "research/urban_engine_m3_recovery/**/*.pdf", "*.xlsx"):
        assert rule in ignore, rule


def test_89_components_each_with_an_m3_state():
    rows = _rows("07_REINFORCEMENT_COMPLETENESS_89.csv")
    assert len(rows) == 89 and len({r["M1_COMPONENT_ID"] for r in rows}) == 89
    for r in rows:
        # a rebar state when the historical component is matched, else the named reason it is not (never blank)
        assert r["M3_GENERIC_REBAR_STATE"] in REBAR_STATES | UNMATCHED, r
        if r["M3_GENERIC_REBAR_STATE"] in ("MISSING_DATA", "PARTIAL_MISSING"):
            assert r["M3_REASON"], r


def test_benchmark_positions_carry_no_values():
    rows = _rows("09_BENCHMARK_POSITIONS.csv")
    assert rows and not any(k.startswith("EXTERNAL_") and "POSITION" not in k for k in rows[0])
    pos = {"BELOW", "INSIDE", "ABOVE", "NO_EXTERNAL_VALUE", "NO_GENERIC_VALUE"}
    assert {r["EXTERNAL_POSITION_VS_GENERIC"] for r in rows} <= pos
    assert {r["EXTERNAL_POSITION_VS_M1"] for r in rows} <= pos | {"NO_M1_VALUE"}


def test_reconciliation_classes_and_tags():
    rows = _rows("05_RECONCILIATION_M2_TO_M3.csv")
    assert {r["CLASS"] for r in rows} <= CLASSES | {""}
    # a cause tag always carries its class; an untagged change (re-numbered ids) carries none
    for r in rows:
        assert (r["CLASS"] == "") == (r["CHANGE"] in ("REMOVED_OR_RENAMED", "NEW_OR_RENAMED", "VALUE_CHANGED")), r
    # every UNRESOLVED M3 item is classed as a remaining failure / ambiguity or a source interpretation
    unresolved = [r for r in rows if r["KIND"] == "M3_UNRESOLVED"]
    assert len(unresolved) == len(_rows("10_UNRESOLVED_REGISTER.csv")) - sum(
        1 for r in _rows("10_UNRESOLVED_REGISTER.csv") if r["trade"] == "REINFORCEMENT")
    assert {r["CLASS"] for r in unresolved} <= {"Remaining extraction failure", "Remaining source ambiguity",
                                                 "Source interpretation"}


def test_summary_deltas_add_up():
    for r in _rows("05_RECONCILIATION_SUMMARY.csv"):
        d = float(r["M3_BASE"]) - float(r["M2_BASE"])
        assert abs(d - float(r["DELTA"])) < 1e-3, r
        assert abs(float(r["DELTA_WITH_A_CAUSE_TAG"]) + float(r["DELTA_UNTAGGED"]) - d) < 1e-3, r


def test_missing_steel_is_counted_never_zero():
    numbers = json.loads((PKG / "00_NUMBERS.json").read_text())
    rows = _rows("08_MISSING_STEEL_BY_FAMILY_STOREY.csv")
    assert sum(int(r["MISSING_STEEL_COMPONENTS"]) for r in rows) == numbers["missing_steel_components"]
    for r in rows:
        assert int(r["MISSING_STEEL_COMPONENTS"]) == int(r["MISSING_DATA"]) + int(r["PARTIAL_MISSING"]), r
    summary = json.loads((PKG / "st7757_route_g/SUMMARY.json").read_text())
    assert summary["missing_steel_components"] == numbers["missing_steel_components"]
    boq = (PKG / "st7757_route_g/CONTRACTOR_BOQ.csv").read_text(encoding="utf-8")
    assert "MISSING" in boq.upper()


def test_categories_never_claim_verified_on_a_new_project():
    summary = json.loads((PKG / "st7757_route_g/SUMMARY.json").read_text())
    assert summary["steel_t"]["VERIFIED"] == 0 and summary["concrete_rc"]["N_VERIFIED"] == 0
    assert _rows("st7757_route_g/VERIFIED_REGISTER.csv") == []


def test_family_coverage_names_the_missing_input():
    rows = _rows("11_NOT_DETECTED_REGISTER.csv")
    states = {"QUANTIFIED", "PARTLY_QUANTIFIED", "COUNTED_IN_PARENT", "DETECTED_NOT_QUANTIFIED", "NO_EVIDENCE_FOUND"}
    assert rows and {r["STATE"] for r in rows} <= states
    for r in rows:
        if r["STATE"] in ("DETECTED_NOT_QUANTIFIED", "NO_EVIDENCE_FOUND", "PARTLY_QUANTIFIED"):
            assert r["NEEDED"], r
        if r["STATE"] == "NO_EVIDENCE_FOUND":
            assert "confirm absent" in r["REASON"], r


def test_heldout_evaluation_m3_no_worse_than_m2():
    h = json.loads((PKG / "13_HELDOUT_EVALUATION.json").read_text())
    assert set(h) == {"clean_m2", "clean_m3", "defects_m2", "defects_m3", "m3_m2", "m3_m3"}
    for s in ("clean", "defects", "m3"):
        a, b = h[f"{s}_m2"], h[f"{s}_m3"]
        assert b["end_to_end_success"] == b["drawings"] == 40
        assert b["detect_beams"]["recall"] >= a["detect_beams"]["recall"]
        assert b["detect_beams"]["precision"] == 1.0
        for k in ("FOOTINGS", "SLABS", "COLUMNS"):
            assert b["mean_abs_error"][k] <= a["mean_abs_error"][k] + 1e-9, (s, k)
    assert h["m3_m3"]["mean_abs_error"]["BEAMS_TOTAL_DEPTH"] < 0.01 < h["m3_m2"]["mean_abs_error"]["BEAMS_TOTAL_DEPTH"]


def test_rfis_and_profile_provenance():
    rfis = _rows("19_RFIS.csv")
    assert [r["RFI_ID"] for r in rfis] == [f"M3-RFI-{i:02d}" for i in range(1, len(rfis) + 1)]
    assert all(r["QUESTION"] and r["WHY_IT_MATTERS"] and r["EVIDENCE"] for r in rfis)
    prof = json.loads((PKG / "profile_st7757_m3.json").read_text())
    entries = prof["conventions"]
    for e in entries:
        assert e.get("provenance") in PROVENANCE and e.get("source"), e.get("id")
    blind = next(e for e in entries if e["id"] == "BLINDING_THICKNESS_M")
    assert blind["provenance"] == "READING_OF_PRINTED_VALUE"          # OCR-read, not reviewed (M3-RFI-06)


def test_evidence_never_promoted():
    de = _module(ROOT / "engine/source/detail_evidence.py", "de_m3t")
    ev = json.loads((PKG / "evidence/DETAIL_EVIDENCE.json").read_text())
    assert de.validate(ev) == []
    assert not any(r["state"] == "MANUALLY_CONFIRMED" for r in ev["records"])   # no person has reviewed them yet
    assert all(d["ocr"] for d in de.ground_beam_details(ev))


@pytest.mark.skipif(not ST_DXF.exists(), reason="private ST7757 drawing not present")
def test_engine_only_files_reproduce():
    """the files built from the current engine alone (no M2 worktree) come out byte for byte from the drawing."""
    b = _module(PKG / "build_m3_reports.py", "m3b_t")
    D, conv, ev, items, reg, risk = b.m3_run()
    rc = b.GR.rebar_completeness(items, reg)
    cov = b.FC.coverage(D, items, risk, b.GR.scope_scan(D), ev)
    for name, text in (("06_BEAMS_BY_MARK_VS_FROZEN.csv", b._csv(b.beams_by_mark(items))),
                       ("07_REINFORCEMENT_COMPLETENESS_89.csv", b._csv(b.completeness_89(D, reg))),
                       ("08_MISSING_STEEL_BY_FAMILY_STOREY.csv", b._csv(rc["by_family_storey"])),
                       ("11_NOT_DETECTED_REGISTER.csv", b._csv(cov)),
                       ("11_COVERAGE_RISK.csv", b._csv([{"KIND": r["KIND"], "WHERE": r["WHERE"]} for r in risk]))):
        assert text == (PKG / name).read_text(encoding="utf-8"), name
    roll = {(r["trade"], r["family"]): r for r in b.PE.rollup(items, ("trade", "family"))}
    for name, trade in (("03_CONCRETE_BY_FAMILY.csv", "CONCRETE"), ("04_REINFORCEMENT_BY_FAMILY.csv", "REINFORCEMENT")):
        for r in _rows(name):
            if r["FAMILY"] == "CORE_SIX_TOTAL":
                continue
            g = roll.get((trade, r["FAMILY"]), {})
            assert abs(float(r["M3_BASE"]) - float(g.get("PROVISIONAL_BASE", 0.0))) < 1e-4, (name, r["FAMILY"])
