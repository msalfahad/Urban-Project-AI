"""S8.7C post-freeze comparison: run after the freeze, explains differences, never changes a frozen quantity."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_stairs_s8_7c"
PF = PKG / "post_freeze"
MANIFEST = PKG / "13_S8_7C_FREEZE_MANIFEST.json"


def rows(name):
    with open(PF / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def summary():
    return json.loads((PF / "03_POST_FREEZE_SUMMARY.json").read_text(encoding="utf-8"))


def test_freeze_intact_and_comparison_downstream():
    DR.verify_frozen(MANIFEST, ROOT)
    s = summary()
    assert s["frozen_manifest_sha256"] == hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    src = (PKG / "build_s8_7c.py").read_text(encoding="utf-8")
    assert "BOQ_LINES_V3B" not in src and "STAIR_ARCHITECTURAL_REGISTER" not in src and "post_freeze" not in src
    assert not [p for p in json.loads(MANIFEST.read_text(encoding="utf-8"))["outputs"] if "post_freeze" in p]
    reg = (ROOT / "tests/structural_comparison_engine/rebar_product_registry.py").read_text(encoding="utf-8")
    assert '"research/alsenan_stairs_s8_7c/post_freeze/post_freeze_comparison.py"' in reg


def test_v3b_reproduced_and_every_difference_classified():
    s = summary()
    assert s["v3b_reproduced_exactly"] and s["v3b_method_reproduced_m3"] == s["v3b_c_stair_commercial_m3"] == 5.2312
    assert s["v3b_risers"] == {"A1": 26, "A2": 24}
    r = rows("01_POST_FREEZE_COMPARISON.csv")
    assert len(r) == s["rows"] and all(x["CLASS"] and x["EXPLANATION"] for x in r)
    assert {x["CLASS"] for x in r} <= {"NO_DIFFERENCE", "AUTHORITY", "SCOPE", "METHOD", "METHOD + SCOPE",
                                       "METHOD + MISSED_OBJECT", "NOT_COMPARABLE"}
    same = next(x for x in r if x["REFERENCE"].startswith("S8.7B frozen owner-28"))
    assert same["CLASS"] == "NO_DIFFERENCE" and s["a_28_minus_s8_7b_owner_28_max_m3"] < 1e-6


def test_candidates_against_earlier_figures():
    C = rows("02_CANDIDATES_VS_EARLIER_FIGURES.csv")
    for x in C:
        whole = float(x["S8_7C_NEW_GROSS_M3"]) + float(x["S8_7_A1_L1_PLATE_M3"])
        assert float(x["WHOLE_GF_1F_GROSS_M3"]) == pytest.approx(whole, abs=1e-8)
        assert float(x["MINUS_V3B_M3"]) == pytest.approx(whole - float(x["V3B_GF_1F_METHOD_M3"]), abs=1e-6)
        assert x["LANE"] == "RESEARCH_SENSITIVITY_NOT_RELEASED"
    for sid in ("A-28", "B-27-S", "B-27-SM", "REF-25"):
        g = [float(x["WHOLE_GF_1F_GROSS_M3"]) for x in C if x["SCENARIO"] == sid]
        assert g == sorted(g)
    s = summary()
    b = s["main_stair_with_b_27_s_m3_by_waist"]
    assert b["150"] < b["160"] < b["175"] < b["200"]
    assert s["most_consistent_gf_1f"] == "B-27-S"


def test_nothing_released():
    s = summary()
    assert s["release_delta"] == {"concrete_m3": 0.0, "kg": 0.0}
    assert "nothing is released" in s["rule"] and "no arrangement is chosen" in s["rule"]


def test_rerun_identical():
    before = {p.name: p.read_bytes() for p in PF.iterdir() if p.is_file() and p.suffix != ".py"}
    subprocess.run([sys.executable, "-I", str(PF / "post_freeze_comparison.py")], check=True, cwd=ROOT,
                   capture_output=True)
    after = {p.name: p.read_bytes() for p in PF.iterdir() if p.is_file() and p.suffix != ".py"}
    assert before == after
