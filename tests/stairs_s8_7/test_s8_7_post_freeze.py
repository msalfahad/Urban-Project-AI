"""S8.7 post-freeze comparison: run after the freeze, explains differences, never changes a frozen quantity."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_stairs_s8_7"
PF = PKG / "post_freeze"
MANIFEST = PKG / "17_S8_7_FREEZE_MANIFEST.json"


def rows(name):
    with open(PF / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_freeze_intact_and_comparison_downstream():
    DR.verify_frozen(MANIFEST, ROOT)
    s = json.loads((PF / "03_POST_FREEZE_SUMMARY.json").read_text(encoding="utf-8"))
    assert s["frozen_manifest_sha256"] == hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    src = (PKG / "build_s8_7.py").read_text(encoding="utf-8")
    assert "post_freeze" not in src and "BOQ_LINES_V3B" not in src and "STAIR_ARCHITECTURAL_REGISTER" not in src
    reg = (ROOT / "tests/structural_comparison_engine/rebar_product_registry.py").read_text(encoding="utf-8")
    assert '"research/alsenan_stairs_s8_7/post_freeze/post_freeze_comparison.py"' in reg


def test_every_v3b_stair_line_classified():
    r = rows("01_POST_FREEZE_COMPARISON.csv")
    v3b = [x for x in r if x["REFERENCE"].startswith("V3b B")]
    assert {x["REFERENCE"].split()[2] for x in v3b} == {"C-STAIR", "R-STAIRS-GF", "F-STAIR", "S-GOING", "S-RAIL",
                                                        "S-TREAD", "S-RISER", "S-NOSING"}
    assert all(x["CLASS"] for x in r)
    c = next(x for x in v3b if " C-STAIR " in x["REFERENCE"])
    assert c["REFERENCE_TECHNICAL"] == "BLOCKED None" and "5.2312" in c["REFERENCE_COMMERCIAL"]


def test_sensitivity_stays_context():
    t = rows("02_S8_7_CONDITIONAL_TOTALS.csv")
    s87 = json.loads((PKG / "16_S8_7_SUMMARY.json").read_text(encoding="utf-8"))
    assert abs(sum(float(x["RELEASED_M3"]) for x in t) - s87["released"]["concrete_m3"]) < 1e-6
    assert all("never a quantity" in x["NOTE"] for x in t)


def test_rerun_identical():
    before = {p.name: p.read_bytes() for p in PF.iterdir() if p.is_file() and p.suffix != ".py"}
    subprocess.run([sys.executable, "-I", str(PF / "post_freeze_comparison.py")], check=True, cwd=ROOT,
                   capture_output=True)
    after = {p.name: p.read_bytes() for p in PF.iterdir() if p.is_file() and p.suffix != ".py"}
    assert before == after
