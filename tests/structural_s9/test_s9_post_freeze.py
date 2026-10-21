"""S9 post-freeze comparison: run after the freeze, explains differences, never changes a frozen quantity."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_structural_s9"
PF = PKG / "post_freeze"
MANIFEST = PKG / "16_S9_FREEZE_MANIFEST.json"
HYG = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")
CLASSES = {"NO_DIFFERENCE", "METHOD", "SCOPE", "AUTHORITY", "MISSED_OBJECT", "NOT_DECOMPOSABLE", "NOT_COMPARABLE"}


def rows(name):
    with open(PF / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def summary():
    return json.loads((PF / "06_POST_FREEZE_SUMMARY.json").read_text(encoding="utf-8"))


def test_freeze_intact_and_comparison_downstream():
    DR.verify_frozen(MANIFEST, ROOT)
    s = summary()
    assert s["frozen_manifest_sha256"] == hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    assert s["other_frozen_manifests_verified"] == 29
    src = (PKG / "build_s9.py").read_text(encoding="utf-8")
    assert "BOQ_LINES_V3B" not in src and "STRUCTURAL_ELEMENT_CENSUS" not in src and "post_freeze_comparison" not in src
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert not [p for p in list(m["outputs"]) + list(m["inputs"]) if "post_freeze" in p or "registers_v3b" in p]
    reg = (ROOT / "tests/structural_comparison_engine/rebar_product_registry.py").read_text(encoding="utf-8")
    assert '"research/alsenan_structural_s9/post_freeze/post_freeze_comparison.py"' in reg


def test_every_old_boq_line_compared_and_classified():
    v3b = json.loads((ROOT / "tests/alsenan/registers_v3b/BOQ_LINES_V3B.json").read_text(encoding="utf-8"))
    conc = [x for x in v3b["lines"] if x["trade"] == "CONCRETE"]
    c = [x for x in rows("01_OLD_BOQ_CONCRETE_COMPARISON.csv") if not x["GROUP"].startswith("AREA ")]
    listed = {l.split(" ", 1)[1] for x in c for l in json.loads(x["V3B_LINES"])}
    assert listed == {x["code"] for x in conc}
    for x in c + rows("02_OLD_BOQ_REBAR_COMPARISON.csv"):
        assert x["EXPLANATION"] and set(x["CLASS"].split(" + ")) <= CLASSES, x["GROUP"]
    pops = json.loads((ROOT / "tests/alsenan/registers_v3b/REBAR_POPULATION_REGISTER.json").read_text(
        encoding="utf-8"))["rows"]
    r = rows("02_OLD_BOQ_REBAR_COMPARISON.csv")
    assert {p for x in r for p in json.loads(x["V3B_POPULATIONS"] or "[]")} == {p["population"] for p in pops}
    s = summary()
    assert s["v3b_technical"]["reinforcement_kg"] == pytest.approx(sum(float(p["technical_kg"]) for p in pops),
                                                                   abs=1e-6)


def test_footing_difference_is_the_overlap_prism_and_s9_figures_unchanged():
    s = summary()
    assert s["footing_difference_m3"] == pytest.approx(-0.14 * 0.30, abs=1e-9)
    s9 = json.loads((PKG / "14_RELEASE_SUMMARY.json").read_text(encoding="utf-8"))
    assert s["s9_released"] == {"concrete_m3": s9["released_concrete_m3_total"],
                                "reinforcement_kg": s9["released_reinforcement_kg_total"]}
    c = {x["GROUP"]: x for x in rows("01_OLD_BOQ_CONCRETE_COMPARISON.csv")}
    for g, fam in (("FOOTINGS", "FOOTINGS"), ("STAIRS", "STAIRS"), ("DOMES", "DOMES")):
        assert float(c[g]["S9_RELEASED_M3"]) == pytest.approx(s9["released_concrete_m3_by_family"][fam], abs=1e-6)
    assert c["BEAMS_GF"]["S9_RELEASED_M3"] == "0" and c["POOL"]["S9_RELEASED_M3"] == "0"
    for st in ("GF", "1F", "2F"):
        a = c[f"AREA {st}"]
        parts = sum(float(a[k]) for k in ("S9_RELEASED_PANELS_M2", "S9_OTHER_OWNER_PANELS_M2",
                                          "BEAM_FOOTPRINTS_CLEAR_M2", "COLUMN_FOOTPRINTS_M2"))
        assert float(a["RESIDUAL_M2"]) == pytest.approx(float(a["V3B_NET_PLATE_M2"]) - parts, abs=2e-3)


def test_pre_s8_census_crosswalk_and_the_missed_bands():
    census = list(csv.DictReader(open(ROOT / "research/pre_s8_structural_completeness/02_STRUCTURAL_ELEMENT_CENSUS.csv",
                                      encoding="utf-8", newline="")))
    x = [r for r in rows("03_PRE_S8_CENSUS_CROSSWALK.csv") if r["ROW_KIND"] != "COVERAGE_MATRIX"]
    assert sum(int(r["ELEMENTS"]) for r in x) == len(census)
    missed = [r for r in x if r["CLASS"] == "MISSED_OBJECT"]
    assert [r["PRE_S8_FAMILY"] for r in missed] == ["CANTILEVER_OR_BEARING_WALL_BAND"]
    hz = [r for r in census if r["ELEMENT_FAMILY"] == "CANTILEVER_OR_BEARING_WALL_BAND"]
    assert int(missed[0]["ELEMENTS"]) == len(hz) == 8
    s9 = {r["COMPONENT_ID"] for r in csv.DictReader(open(PKG / "02_CONCRETE_BOQ_RECONCILIATION.csv",
                                                         encoding="utf-8", newline=""))}
    assert not {r["ELEMENT_ID"] for r in hz} & s9                      # truly absent from the frozen S9
    f = {r["FINDING"]: r for r in rows("05_POST_FREEZE_FINDINGS.csv")}
    assert f["F-01"]["KIND"] == "MISSED_OBJECT" and "needs approval" in f["F-01"]["RECOMMENDATION"]
    assert "none on any released figure" in f["F-01"]["EFFECT_ON_S9"]


def test_nothing_released_and_hygiene():
    s = summary()
    assert s["release_delta"] == {"concrete_m3": 0.0, "kg": 0.0}
    assert "S9 is not tuned" in s["rule"] and "nothing is released" in s["rule"]
    for p in PF.iterdir():
        if p.is_file() and p.suffix in (".md", ".csv", ".json"):
            assert not HYG.search(p.read_text(encoding="utf-8")), p.name


def test_rerun_identical():
    before = {p.name: p.read_bytes() for p in PF.iterdir() if p.is_file() and p.suffix != ".py"}
    subprocess.run([sys.executable, "-I", str(PF / "post_freeze_comparison.py")], check=True, cwd=ROOT,
                   capture_output=True)
    after = {p.name: p.read_bytes() for p in PF.iterdir() if p.is_file() and p.suffix != ".py"}
    assert before == after
