"""S8.4 post-freeze comparison: run after the freeze, explains every earlier figure at equal scope, changes nothing."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_water_tank_s8_4"
PF = PKG / "post_freeze"
OUT = ["00_POST_FREEZE_README.md", "01_POST_FREEZE_COMPARISON.csv", "02_OLD_FORMULA_RECONSTRUCTION.csv",
       "03_POST_FREEZE_SUMMARY.json"]


def rows(name):
    with open(PF / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_freeze_intact_and_the_comparison_is_outside_it():
    m = DR.verify_frozen(PKG / "15_S8_4_FREEZE_MANIFEST.json", ROOT)
    s = json.loads((PF / "03_POST_FREEZE_SUMMARY.json").read_text(encoding="utf-8"))
    assert s["frozen_unchanged"] and s["frozen_manifest_sha256"] == m["manifest_sha256"]
    frozen = json.loads((PKG / "15_S8_4_FREEZE_MANIFEST.json").read_text(encoding="utf-8"))
    assert not any("post_freeze" in k for k in list(frozen["outputs"]) + list(frozen["inputs"]) + list(frozen["code"]))


def test_every_row_is_classified_and_explained():
    allowed = {"LAYER", "RUN_BASIS", "COUNT_BASIS", "STOP_ZONE", "SCOPE", "THICKNESS_BASIS", "PLATE_BASIS",
               "NOT_COMPARABLE", "NO_DIFFERENCE"}
    for r in rows("01_POST_FREEZE_COMPARISON.csv"):
        assert {c.strip() for c in r["DIFFERENCE_CLASS"].split("+")} <= allowed and r["EXPLANATION"], r["ROW_ID"]


def test_old_tank_sets_reproduced_by_their_own_formula_and_bridged():
    rec = rows("02_OLD_FORMULA_RECONSTRUCTION.csv")
    assert sorted(r["CALLOUT"] for r in rec) == ["796", "798", "7A7", "7A8"]
    for r in rec:
        assert float(r["V3B_COUNT"]) * float(r["V3B_BAR_M"]) * int(r["DIA_MM"]) ** 2 / 162 == pytest.approx(float(r["V3B_KG"]))
        assert r["V3B_FACES"].startswith("ONE")
    s = json.loads((PF / "03_POST_FREEZE_SUMMARY.json").read_text(encoding="utf-8"))["equal_scope"]
    assert math.fsum(b["kg"] for b in s["bridge"]) == pytest.approx(s["s8_4_released_kg"], abs=1e-5)
    frozen = json.loads((PKG / "14_S8_4_SUMMARY.json").read_text(encoding="utf-8"))
    assert s["s8_4_released_kg"] == pytest.approx(frozen["released"]["reinforcement_kg"])
    assert s["concrete_v3b_rule_on_tank_faces_m3"] == pytest.approx(frozen["released"]["concrete_m3"])
    layer = [b for b in s["bridge"] if b["step"].startswith("LAYER")][0]["kg"]
    assert layer == pytest.approx(frozen["full_mesh_kg"] / 2)                    # the missing (T&B) faces


def test_module_registered_as_comparison():
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert "research/alsenan_water_tank_s8_4/post_freeze/post_freeze_comparison.py" in RP.COMPARISON_MODULES


def test_identical_rerun():
    before = {o: hashlib.sha256((PF / o).read_bytes()).hexdigest() for o in OUT}
    subprocess.run([sys.executable, "-I", str(PF / "post_freeze_comparison.py")], check=True, cwd=ROOT,
                   capture_output=True)
    assert before == {o: hashlib.sha256((PF / o).read_bytes()).hexdigest() for o in OUT}
