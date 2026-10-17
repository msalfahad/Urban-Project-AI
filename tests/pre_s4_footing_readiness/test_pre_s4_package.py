"""Pre-S4 readiness package integrity (research/pre_s4_footing_readiness).

* every output matches INDEX.json; the package rebuilds byte for byte when ST7757.dxf is present
  (PRE_S4_ST7757_DXF, or the local data/inputs/by_sha256 copy);
* the annotation census conserves (SOURCE_ITEMS == TERMINAL_ITEMS, unique ids, no blocked quantity);
* the token-parity decisions are re-run live from the raw tokens with the production guard;
* BOXED stays UNRESOLVED / BLOCKED_COMPONENT; the readiness matrix never calls a semantics-less component READY;
* firewall: the guard is project-agnostic and production never refers to this package.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from engine.source import footing_rebar_guard as FG

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "pre_s4_footing_readiness"
DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
DXF = Path(os.environ.get("PRE_S4_ST7757_DXF") or ROOT / "data/inputs/by_sha256" / f"{DXF_SHA}.dxf")


def rows(name):
    return list(csv.DictReader(open(PKG / name, encoding="utf-8")))


def J(name):
    return json.loads((PKG / name).read_text(encoding="utf-8"))


def test_index_hashes_and_deliverables():
    idx = J("INDEX.json")
    assert idx["baseline"] == "445dd1d"
    for n in ("00_README.md", "01_FOOTING_TOKEN_PARITY_REGISTER.csv", "02_FOOTING_ANNOTATION_CENSUS.csv",
              "03_BOXED_OCCURRENCES.csv", "04_BOXED_SOURCE_EXHAUSTION.md", "05_S4_PROVENANCE_CONTRACT.md",
              "06_S4_READINESS_MATRIX.csv", "07_POST_S4_FROZEN_BACKLOG.md", "TEST_RUN.md", "PRE_S4_SUMMARY.json"):
        assert n in idx["files"], n
    for n, h in idx["files"].items():
        assert hashlib.sha256((PKG / n).read_bytes()).hexdigest() == h, n


def test_census_conserves_every_source_item_once():
    c = rows("02_FOOTING_ANNOTATION_CENSUS.csv")
    s = J("PRE_S4_SUMMARY.json")["census"]
    ids = [r["ITEM_ID"] for r in c]
    assert len(ids) == len(set(ids)) == s["source_items"] == s["terminal_items"]
    assert s["conserved"] and not s["unterminated"] and not s["blocked_with_quantity"]
    assert {r["TERMINAL_STATE"] for r in c} <= set(FG.TERMINALS)
    for r in c:
        if r["TERMINAL_STATE"] in FG.BLOCKED_TERMINALS:
            assert r["QUANTITY"] == "", r["ITEM_ID"]
    by = Counter(r["ITEM_TYPE"] for r in c)
    assert by["PLAN_OUTLINE"] == 26 and by["PLAN_TAG"] == 27 and by["SCHEDULE_ROW"] == 17
    assert by["SCHEDULE_CELL"] == 12 * 9 + 5 * 14                            # every FT / FTB ATTRIB
    boxed = [r for r in c if r["ITEM_TYPE"] == "SCHEDULE_CELL" and re.fullmatch(r"\d\+\d|", r["RAW"])
             and "BOXED" in r["LOCATION"] and "BOXED-" not in r["LOCATION"]]
    assert len(boxed) == 12 and {r["TERMINAL_STATE"] for r in boxed} == {FG.BLOCKED_SEMANTICS}


def test_conflict_and_count_query_are_carried_not_resolved():
    c = rows("02_FOOTING_ANNOTATION_CENSUS.csv")
    conflict = [r for r in c if r["FOOTING_MARK"] == "F|F10"]
    assert len(conflict) == 3 and {r["TERMINAL_STATE"] for r in conflict} == {FG.PARSED_SOURCE_CONFLICT}
    f3 = [r for r in c if r["FOOTING_MARK"] == "F3" and r["ITEM_TYPE"] in ("PLAN_TAG", "PLAN_OUTLINE")]
    assert len(f3) == 4 and all("OQ-11" in r["REASON"] for r in f3)       # 2 tags + 2 outlines, query kept
    assert J("PRE_S4_SUMMARY.json")["count_queries"] == {"F3": "OQ-11"}


def test_token_parity_decisions_rerun_live():
    for r in rows("01_FOOTING_TOKEN_PARITY_REGISTER.csv"):
        raw = r["RAW_TEXT"]
        if r["SOURCE_TYPE"].startswith("SCHEDULE_ATTRIB_CELL_PAIR"):
            c, d = [x.strip() for x in raw.split("|")]
            a = FG.admit_cells(c, d)
        elif r["SOURCE_HANDLE"].startswith("PDF:"):
            a = FG.admit_token(raw.replace(" ", ""))
        else:
            a = FG.admit_token(raw)
        assert a["decision"] == r["S4_DECISION"], r["TOKEN_ID"]
        assert a["token_class"] == r["TOKEN_CLASS"], r["TOKEN_ID"]
    t = rows("01_FOOTING_TOKEN_PARITY_REGISTER.csv")
    bars = [r for r in t if r["SOURCE_TYPE"].startswith("SCHEDULE_ATTRIB_CELL_PAIR")]
    assert len(bars) == 44 and all(r["PARITY_STATUS"] == "PARITY_OK" and r["JOINED_FORM_PARITY"] == "AGREE"
                                   for r in bars)
    assert not {r["TOKEN_CLASS"] for r in t} & set(FG.KNOWN_DISAGREEMENT_CLASSES)


def test_boxed_is_unresolved_and_blocked():
    s = J("PRE_S4_SUMMARY.json")
    assert s["boxed"]["terminal_classification"] == FG.UNRESOLVED
    assert s["boxed"]["component_existence"] == FG.SOURCE_EXPLICIT
    assert s["boxed"]["diagnostics"]["status"].startswith("DIAGNOSTIC_ONLY")
    b = rows("03_BOXED_OCCURRENCES.csv")
    ft = [r for r in b if r["BLOCK"] == "FT"]
    assert len(ft) == 12 and {r["SEMANTICS_CLASS"] for r in ft} == {FG.UNRESOLVED}
    assert all(r["SCHEDULE_COLUMN_HEADER"] == "BOXED" for r in b)
    assert {r["RAW_VALUE"] for r in b if r["BLOCK"] == "FTB"} == {"TOP", "BOT"}


def test_readiness_matrix_is_honest():
    m = {r["ITEM"]: r for r in rows("06_S4_READINESS_MATRIX.csv")}
    assert m["BOXED"]["S4_STATUS"] == "BLOCKED_COMPONENT"
    for r in m.values():
        assert r["S4_STATUS"] in ("READY", "READY_LOWER_BOUND", "PROVISIONAL_ONLY", "BLOCKED_COMPONENT",
                                  "NOT_APPLICABLE")
        if r["S4_STATUS"] in ("READY", "READY_LOWER_BOUND"):
            assert r["SEMANTICS_AVAILABLE"].startswith("YES"), r["ITEM"]
    hb = J("PRE_S4_SUMMARY.json")["header_binding"]
    assert hb["bound"] == hb["total"] == 22


def test_guard_is_project_agnostic_and_production_never_reads_this_package():
    src = (ROOT / "engine/source/footing_rebar_guard.py").read_text(encoding="utf-8")
    assert not re.search(r"ALSENAN|ST7757|P7757|freelancer|christiannp|UC4N|\bF10\b|OQ-11", src, re.I)
    for p in (ROOT / "engine").rglob("*.py"):
        assert "pre_s4_footing_readiness" not in p.read_text(encoding="utf-8", errors="ignore"), p


@pytest.mark.skipif(not DXF.is_file(), reason="ST7757.dxf not present")
def test_rebuild_byte_for_byte():
    before = {k: (PKG / k).read_bytes() for k in J("INDEX.json")["files"]}
    subprocess.run([sys.executable, "-I", str(PKG / "scripts" / "build_pre_s4.py"), str(DXF)], check=True,
                   capture_output=True, cwd=ROOT)
    for k, v in before.items():
        assert (PKG / k).read_bytes() == v, k
