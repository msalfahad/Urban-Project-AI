"""S8.8 post-freeze comparison: run after the freeze, explains differences, never changes a frozen quantity."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_lift_s8_8"
PF = PKG / "post_freeze"
MANIFEST = PKG / "18_S8_8_FREEZE_MANIFEST.json"


def rows(name):
    with open(PF / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_freeze_intact_and_comparison_downstream():
    DR.verify_frozen(MANIFEST, ROOT)
    s = json.loads((PF / "03_POST_FREEZE_SUMMARY.json").read_text(encoding="utf-8"))
    assert s["frozen_manifest_sha256"] == hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    src = (PKG / "build_s8_8.py").read_text(encoding="utf-8")
    for bad in ("post_freeze", "BOQ_LINES_V3B", "registers_v3b", "R9_1_CHRIS", "CONCRETE_QUANTITY_STATE\"]",
                "03_CONCRETE_COVERAGE", "06_S8_CANDIDATE"):
        assert bad not in src, bad
    reg = (ROOT / "tests/structural_comparison_engine/rebar_product_registry.py").read_text(encoding="utf-8")
    assert '"research/alsenan_lift_s8_8/post_freeze/post_freeze_comparison.py"' in reg


def test_every_earlier_lift_figure_classified():
    r = rows("01_POST_FREEZE_COMPARISON.csv")
    assert all(x["CLASS"] in {"NO_DIFFERENCE", "AUTHORITY", "SCOPE", "METHOD", "MISSED_OBJECT", "NEW_RELEASE",
                              "NOT_COMPARABLE"} and x["EXPLANATION"] for x in r)
    refs = " ".join(x["REFERENCE"] for x in r)
    for need in ("V3b lines for the lift", "B0001 C-FTG", "PRE-S8 02 CONCRETE_QUANTITY_STATE SPC-LIFT_PIT",
                 "PRE-S8 03", "PRE-S8 04", "PRE-S8 06", "PRE-S8 07 LIFT WALL -> PIT BASE", "R9.1 freelancer"):
        assert need in refs, need
    v3b = next(x for x in r if x["REFERENCE"].startswith("V3b lines for the lift"))
    assert v3b["REFERENCE_TECHNICAL"] == "0 lines" and v3b["CLASS"] == "MISSED_OBJECT"


def test_footing_agrees_and_nothing_released():
    s = json.loads((PF / "03_POST_FREEZE_SUMMARY.json").read_text(encoding="utf-8"))
    assert s["ff_v3b_m3"] == s["ff_r9_1_m3"] == s["ff_s8_8_computed_m3"] == 11.385
    assert s["s8_8_released"]["concrete_m3"] == 0.0 and s["s8_8_released"]["kg"] == 0.0
    t = rows("02_S8_8_CONDITIONAL_TOTALS.csv")
    assert all(float(x["RELEASED_M3"]) == 0 for x in t) and all("never a quantity" in x["NOTE"] for x in t)


def test_rerun_identical():
    before = {p.name: p.read_bytes() for p in PF.iterdir() if p.is_file() and p.suffix != ".py"}
    subprocess.run([sys.executable, "-I", str(PF / "post_freeze_comparison.py")], check=True, cwd=ROOT,
                   capture_output=True)
    after = {p.name: p.read_bytes() for p in PF.iterdir() if p.is_file() and p.suffix != ".py"}
    assert before == after
