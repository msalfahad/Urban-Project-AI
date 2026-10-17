"""S8.7A post-freeze comparison: run after the freeze, explains differences, never changes a frozen quantity."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_stairs_s8_7a"
PF = PKG / "post_freeze"
MANIFEST = PKG / "15_S8_7A_CORRECTION_MANIFEST.json"
S87_MANIFEST = ROOT / "research" / "alsenan_stairs_s8_7" / "17_S8_7_FREEZE_MANIFEST.json"
HYG = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")


def rows(name):
    with open(PF / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_freezes_intact_and_comparison_downstream():
    DR.verify_frozen(MANIFEST, ROOT)
    DR.verify_frozen(S87_MANIFEST, ROOT)
    s = json.loads((PF / "03_POST_FREEZE_SUMMARY.json").read_text(encoding="utf-8"))
    assert s["frozen_manifest_sha256"] == hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    assert s["s8_7_manifest_sha256"] == hashlib.sha256(S87_MANIFEST.read_bytes()).hexdigest()
    src = (PKG / "build_s8_7a.py").read_text(encoding="utf-8")
    for ref in ("post_freeze", "BOQ_LINES_V3B", "STAIR_ARCHITECTURAL_REGISTER", "REBAR_POPULATION_REGISTER",
                "03_CONCRETE_COVERAGE", "04_REBAR_COVERAGE", "06_S8_CANDIDATE", "07_INTERFACE_DOUBLE"):
        assert ref not in src, ref
    reg = (ROOT / "tests/structural_comparison_engine/rebar_product_registry.py").read_text(encoding="utf-8")
    assert '"research/alsenan_stairs_s8_7a/post_freeze/post_freeze_comparison.py"' in reg


def test_v3b_method_reproduced_and_its_riser_counts_classified():
    s = json.loads((PF / "03_POST_FREEZE_SUMMARY.json").read_text(encoding="utf-8"))
    assert s["v3b_reproduced_exactly"] and s["v3b_method_reproduced_m3"] == s["v3b_c_stair_commercial_m3"] == 5.2312
    assert s["v3b_risers"] == {"A1": 26, "A2": 24}
    rep = {r["STOREY_RUN"]: r for r in rows("02_V3B_METHOD_REPRODUCTION.csv")}
    assert rep["A1"]["V3B_COUNT_DRAWN_ON_ANY_VIEW"] == "False" and rep["A2"]["V3B_COUNT_DRAWN_ON_ANY_VIEW"] == "True"
    assert abs(sum(float(r["V3B_RISER_FINISH_M2"]) for r in rep.values()) - 10.005) < 1e-6
    assert abs(sum(float(r["V3B_NOSING_LM"]) for r in rep.values()) - 55.2) < 1e-6
    assert abs(sum(float(r["V3B_HANDRAIL_LM"]) for r in rep.values()) - 19.124) < 1e-6
    lo, hi = s["s8_7a_main_stair_whole_m3_range"]
    assert lo < 5.2312 < hi                                  # inside the range, by compensating method differences
    c = rows("01_POST_FREEZE_COMPARISON.csv")
    v3b = {x["REFERENCE"].split()[2] for x in c if x["REFERENCE"].startswith("V3b B")}
    assert v3b == {"C-STAIR", "R-STAIRS-GF", "S-GOING", "S-RAIL", "S-TREAD", "S-RISER", "S-NOSING"}
    assert all(x["CLASS"] and x["EXPLANATION"] for x in c)


def test_interfaces_agree_and_nothing_released():
    c = {x["REFERENCE"]: x for x in rows("01_POST_FREEZE_COMPARISON.csv")}
    assert c["PRE-S8 07 SLAB -> STAIR interface"]["CLASS"] == "NO_DIFFERENCE"
    assert c["R5 radial lines"]["CLASS"] == "MISSED_OBJECT"
    s = json.loads((PF / "03_POST_FREEZE_SUMMARY.json").read_text(encoding="utf-8"))
    assert s["released_by_s8_7a"] is None
    for p in PF.iterdir():
        if p.is_file() and p.suffix != ".py":
            assert not HYG.search(p.read_text(encoding="utf-8")), p.name


def test_rerun_identical():
    before = {p.name: p.read_bytes() for p in PF.iterdir() if p.is_file() and p.suffix != ".py"}
    subprocess.run([sys.executable, "-I", str(PF / "post_freeze_comparison.py")], check=True, cwd=ROOT,
                   capture_output=True)
    after = {p.name: p.read_bytes() for p in PF.iterdir() if p.is_file() and p.suffix != ".py"}
    assert before == after
