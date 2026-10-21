"""S8.5 post-freeze comparison: run after the freeze, explains every difference, changes no frozen quantity."""

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
PKG = ROOT / "research" / "alsenan_special_columns_s8_5"
PF = PKG / "post_freeze"
OUT = ["00_POST_FREEZE_README.md", "01_POST_FREEZE_COMPARISON.csv", "02_OBJECT_AND_STOREY_CROSSWALK.csv",
       "03_POST_FREEZE_SUMMARY.json"]
CLASSES = {"NO_DIFFERENCE", "LABEL_ONLY", "SCOPE", "MISSED_OBJECT", "OWNERSHIP_CLAIM", "STOREY_CONVENTION",
           "SEGMENTATION", "NOT_COMPARABLE"}
needs_refs = pytest.mark.skipif(not (ROOT / "tests/alsenan/registers_v3b/REBAR_POPULATION_REGISTER.json").exists(),
                                reason="earlier V3b register not present")


def rows(name):
    with open(PF / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_freeze_intact_and_comparison_after_it():
    m = json.loads((PKG / "17_S8_5_FREEZE_MANIFEST.json").read_text(encoding="utf-8"))
    assert m["state"] == "FROZEN_BEFORE_COMPARISON" and m["references_read"] == []
    assert not [o for o in m["outputs"] if o.startswith("post_freeze")]       # the comparison is not in the freeze
    s = json.loads((PF / "03_POST_FREEZE_SUMMARY.json").read_text(encoding="utf-8"))
    assert s["frozen_unchanged"] is True
    assert s["frozen_manifest_sha256"] == DR.verify_frozen(PKG / "17_S8_5_FREEZE_MANIFEST.json", ROOT)["manifest_sha256"]


def test_every_row_classified_and_explained():
    r = rows("01_POST_FREEZE_COMPARISON.csv")
    assert r and all(x["CLASS"] in CLASSES and x["EXPLANATION"] for x in r)
    o = rows("02_OBJECT_AND_STOREY_CROSSWALK.csv")
    assert {x["SPECIAL_ID"] for x in o} == {
        "SPC-TURN_COLUMN-GFRS-31F", "SPC-TURN_COLUMN-GFRS-324", "SPC-DEAD_COLUMN-GFRS-38A",
        "SPC-PLANTED_COLUMN-GFRS-544", "SPC-PLANTED_COLUMN-GFRS-548", "SPC-PLANTED_COLUMN-FFRS-77C"}
    by = {x["CHRIS_ID"]: x["CLASS"] for x in o}
    assert by["COL09"] == by["COL12"] == by["COL30"] == "STOREY_CONVENTION"
    assert by["COL22"] == by["COL23"] == "SEGMENTATION" and by["COL16"] == by["COL31"] == "NO_DIFFERENCE"


@needs_refs
def test_v3b_reproduced_by_its_own_formula_and_special_scope_absent():
    s = json.loads((PF / "03_POST_FREEZE_SUMMARY.json").read_text(encoding="utf-8"))
    for x in s["v3b_type_level_ordinary_bars"]:
        n, L, d = x["V3B_FORMULA"].replace("^2/162", "").split(" x ")
        assert int(n) * float(L) * int(d) ** 2 / 162 == pytest.approx(x["V3B_KG"], abs=1e-6)
        assert abs(x["V3B_KG"] - x["S3_1_KG"]) < 5e-4
    sk = s["special_component_kg"]
    assert sk["v3b_equal_scope"] == 0.0 and sk["s8_5_incremental"] == 0.0
    assert sk["already_owned_s3_1"] == pytest.approx(2 * 4 * 2.0 * 256 / 162, abs=1e-3)
    sets = json.loads((ROOT / "tests/alsenan/registers_v3b/REBAR_POPULATION_REGISTER.json").read_text(
        encoding="utf-8"))["sets"]
    assert not [x for x in sets if "extra" in json.dumps(x).lower() or "spiral" in json.dumps(x).lower()]
    assert not [x for x in sets if x.get("population") == "COLUMNS" and " P.C " in x.get("ref", "")]


def test_registered_as_comparison_never_upstream():
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert "research/alsenan_special_columns_s8_5/post_freeze/post_freeze_comparison.py" in RP.COMPARISON_MODULES
    text = (PKG / "build_s8_5.py").read_text(encoding="utf-8")
    assert "post_freeze" not in text


@needs_refs
def test_rerun_is_identical_and_leaves_the_freeze_alone():
    names = [PF / o for o in OUT] + [PKG / "17_S8_5_FREEZE_MANIFEST.json"]
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in names}
    subprocess.run([sys.executable, "-I", str(PF / "post_freeze_comparison.py")], check=True, cwd=ROOT,
                   capture_output=True)
    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in names}
    assert before == after
