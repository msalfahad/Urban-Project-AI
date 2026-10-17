"""S8.6 post-freeze comparison: freeze intact, every V3b lintel row classified, V3b reproduced by its own formula,
the double counts are the R5 pairs, and a rerun is identical."""

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
PKG = ROOT / "research" / "alsenan_lintels_s8_6"
PF = PKG / "post_freeze"


def rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_freeze_intact_and_comparison_after_it():
    m = json.loads((PKG / "15_S8_6_FREEZE_MANIFEST.json").read_text(encoding="utf-8"))
    DR.verify_frozen(PKG / "15_S8_6_FREEZE_MANIFEST.json", ROOT)
    assert m["references_read"] == [] and not any("post_freeze" in o for o in m["outputs"])
    src = (PKG / "build_s8_6.py").read_text(encoding="utf-8")
    assert "BOQ_LINES_V3B" not in src and not re.search(r"\bC-LINT-", src)


def test_every_row_classified_and_v3b_reproduced():
    r = rows(PF / "01_POST_FREEZE_COMPARISON.csv")
    assert {x["CLASS"] for x in r} <= {"NO_DIFFERENCE", "GEOMETRY", "SUPPORT_IDENTITY", "DOUBLE_COUNT",
                                       "MISSED_OBJECT", "NOT_COMPARABLE"}
    for x in r:
        if x["V3B_FORMULA"]:
            w, k, t, d = map(float, re.match(r"\((\d+\.\d+) \+ 2 x (\d\.\d+)\) x (\d\.\d+) x (\d\.\d+)",
                                             x["V3B_FORMULA"]).groups())
            assert round((w + 2 * k) * t * d, 3) == float(x["V3B_M3"])
    for t in rows(PF / "02_FLOOR_TOTALS.csv"):
        if t["ITEM"] == "CONCRETE_M3":
            assert float(t["V3B_QTY"]) == float(t["V3B_DETAIL_SUM"])


def test_double_counts_are_the_r5_pairs():
    s = json.loads((PKG / "14_S8_6_SUMMARY.json").read_text(encoding="utf-8"))
    dup = [x for x in rows(PF / "01_POST_FREEZE_COMPARISON.csv") if x["CLASS"] == "DOUBLE_COUNT"]
    assert dup and {x["S8_6_OPENING"] for x in dup} <= set(s["r5_double_counts"])
    sup = [x for x in rows(PF / "01_POST_FREEZE_COMPARISON.csv") if x["CLASS"] == "SUPPORT_IDENTITY"]
    assert all(x["S8_6_DECISION"] != "SCHEDULE_BOUND_LINTEL" for x in sup)


def test_rerun_identical():
    h = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in PF.glob("0*")}
    subprocess.run([sys.executable, "-I", str(PF / "post_freeze_comparison.py")], check=True, cwd=ROOT,
                   capture_output=True)
    assert h == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in PF.glob("0*")}
