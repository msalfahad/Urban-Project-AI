"""M1 post-freeze comparison: downstream of the freeze, positions and classes only, no external figure written."""

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
PKG = ROOT / "research" / "alsenan_m1_usable_boq"
PF = PKG / "post_freeze"
MANIFEST = PKG / "06_M1_FREEZE_MANIFEST.json"
BENCH = ("44.19", "352.436075", "77.6305", "75.09", "39.7515", "65.965875", "59.8174", "21.8328", "12.348",
         "337.812", "333.173", "22.619", "22.916", "ae608411", "d025d9f0-")
HYG = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")
CLASSES = {"AGREES_WITHIN_M1_RANGE", "SCOPE", "MEASUREMENT_CONVENTION", "MISSING_COMPONENT",
           "GEOMETRY_EXTRACTION_ERROR", "UNSUPPORTED_ASSUMPTION", "DOUBLE_COUNTING", "UNRESOLVED"}


def rows(name):
    with open(PF / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_freeze_intact_and_comparison_downstream():
    DR.verify_frozen(MANIFEST, ROOT)
    m = json.loads(MANIFEST.read_text())
    assert not [k for k in m["outputs"] if k.startswith("post_freeze/")]
    assert "post_freeze" not in json.dumps(m["inputs"]) and m["references_read"] == []
    for p in list(m["code"]):
        assert "post_freeze" not in p


def test_every_comparison_is_classified_and_positioned():
    conc, steel = rows("01_CONCRETE_RECONCILIATION.csv"), rows("02_REINFORCEMENT_RECONCILIATION.csv")
    assert len(conc) == 80 and {r["ENGINE"] for r in conc} == {"freelancer QS", "christiannp-autocad", "U-C4N",
                                                               "old Urban V3b"}
    for r in conc + steel:
        assert r["CLASS"] in CLASSES and r["EXTERNAL_POSITION"] in {"BELOW", "INSIDE", "ABOVE", "NO_EXTERNAL_VALUE",
                                                                   "NO_M1_VALUE"}
        if r["CLASS"] == "AGREES_WITHIN_M1_RANGE":
            assert r["EXTERNAL_POSITION"] == "INSIDE"
        if r["EXTERNAL_POSITION"] in ("BELOW", "ABOVE"):
            assert r["CLASS"] != "AGREES_WITHIN_M1_RANGE" and r["REASON"]
    assert all(r["DIFF_PCT_OF_M1_BASE"] == "" for r in conc if r["GROUP"].startswith("TOTAL"))
    m1 = json.loads((PKG / "boq" / "SUMMARY.json").read_text())["concrete_rc"]
    for r in conc:
        if r["GROUP"].startswith("TOTAL"):
            assert float(r["M1_PLANNING_BASE_M3"]) == round(m1["PLANNING_BASE"], 3)


def test_no_external_figure_and_hygiene():
    for p in sorted(PF.iterdir()):
        if p.suffix in (".csv", ".md", ".json"):
            t = p.read_text(encoding="utf-8")
            assert not [x for x in BENCH if x in t], p.name
            assert not HYG.search(t), p.name
    assert json.loads((PF / "06_POST_FREEZE_SUMMARY.json").read_text())["external_figures_written"] is False


def test_missing_reinforcement_candidates_are_counted_from_the_registers():
    cand = rows("04_MISSING_REINFORCEMENT_CANDIDATES.csv")
    s = json.loads((PF / "06_POST_FREEZE_SUMMARY.json").read_text())
    assert s["missing_reinforcement_candidates"] == sum(int(r["CONCRETE_COMPONENTS_WITHOUT_ANY_BAR_ROW"])
                                                        for r in cand) > 0


def test_rerun_is_identical_and_leaves_m1_untouched():
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in PF.iterdir() if p.is_file()
              and p.suffix != ".py"}
    out = json.loads(MANIFEST.read_text())["outputs"]
    subprocess.run([sys.executable, "-I", str(PF / "post_freeze_comparison.py")], check=True, capture_output=True,
                   cwd=str(ROOT))
    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in PF.iterdir() if p.is_file()
             and p.suffix != ".py"}
    assert after == before
    assert all(hashlib.sha256((PKG / k).read_bytes()).hexdigest() == v for k, v in out.items())
