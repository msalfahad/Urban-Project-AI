"""S8.3 post-freeze comparison: run after the freeze, every difference classified, nothing frozen changed.

The old figures are explained, not adopted: the old terrace shells come from a rise read from the wrong line, the old
rings from the drawn N.I.S depth, the old tower lines from counting an architectural-only dome."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_dome_ring_s8_3"
PF = PKG / "post_freeze"
CLASSES = {"POPULATION", "SCOPE", "GEOMETRY_INPUT", "NTS_BASIS", "SURFACE_BASIS", "NOT_COMPARABLE", "NO_DIFFERENCE"}


def rows(name):
    with open(PF / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_the_freeze_is_intact_and_named():
    s = json.loads((PF / "03_POST_FREEZE_SUMMARY.json").read_text(encoding="utf-8"))
    assert s["frozen_quantities_unchanged"] is True
    assert s["frozen_manifest_sha256"] == DR.verify_frozen(PKG / "16_S8_3_FREEZE_MANIFEST.json", ROOT)["manifest_sha256"]
    frozen = json.loads((PKG / "15_S8_3_SUMMARY.json").read_text(encoding="utf-8"))
    assert s["headline"]["s8_3_concrete_m3"] == frozen["released"]["concrete_m3"]
    assert s["headline"]["s8_3_reinforcement_kg"] == frozen["released"]["reinforcement_kg"]


def test_every_row_is_classified_and_explained():
    r = rows("01_POST_FREEZE_COMPARISON.csv")
    assert r and all(x["CLASS"] in CLASSES and x["EXPLANATION"] for x in r)
    for x in r:
        if x["S8_3_VALUE"] and x["REFERENCE_VALUE"]:
            assert float(x["DIFFERENCE"]) == pytest.approx(float(x["S8_3_VALUE"]) - float(x["REFERENCE_VALUE"]), abs=1e-9)


def test_the_old_figures_are_reproduced_by_their_own_formula():
    rec = rows("02_OLD_FORMULA_RECONSTRUCTION.csv")
    shells = [x for x in rec if x["CASE"].startswith("old shell formula, plan radius")]
    assert float(shells[0]["SHELL_M3"]) == pytest.approx(2.34, abs=0.002)        # the old terrace line, rise 1.72
    frozen = json.loads((PKG / "15_S8_3_SUMMARY.json").read_text(encoding="utf-8"))["shell"]["volume"]
    assert float(shells[1]["SHELL_M3"]) == pytest.approx(frozen, abs=0.002)        # the same formula at the p.7 rise
    tower = next(x for x in rec if "tower" in x["CASE"])
    assert float(tower["SHELL_M3"]) == pytest.approx(2.843, abs=0.002)
    ring = next(x for x in rec if x["CASE"].startswith("old ring:"))
    assert float(ring["SHELL_M3"]) == pytest.approx(1.989, abs=0.002)              # the drawn N.I.S depth 0.75


def test_population_differences_are_named():
    r = {x["ROW_ID"]: x for x in rows("01_POST_FREEZE_COMPARISON.csv")}
    assert r["PF-03"]["CLASS"] == r["PF-04"]["CLASS"] == r["PF-09"]["CLASS"] == "POPULATION"
    assert r["PF-01"]["SAME_SCOPE"] == "True" and r["PF-01"]["CLASS"] == "GEOMETRY_INPUT"
    assert r["PF-05-DOME-A"]["CLASS"] == "NTS_BASIS" and r["PF-13"]["CLASS"] == r["PF-14"]["CLASS"] == "NO_DIFFERENCE"


def test_registered_as_a_comparison_module():
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert "research/alsenan_dome_ring_s8_3/post_freeze/post_freeze_comparison.py" in RP.COMPARISON_MODULES


def test_rerun_is_identical_and_leaves_the_freeze_alone():
    names = sorted(p.name for p in PF.iterdir() if p.suffix in (".csv", ".json", ".md"))
    frozen = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in PKG.iterdir() if p.is_file()}
    before = {n: hashlib.sha256((PF / n).read_bytes()).hexdigest() for n in names}
    spec = importlib.util.spec_from_file_location("s83_pf", PF / "post_freeze_comparison.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.build()
    assert before == {n: hashlib.sha256((PF / n).read_bytes()).hexdigest() for n in names}
    assert frozen == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in PKG.iterdir() if p.is_file()}
