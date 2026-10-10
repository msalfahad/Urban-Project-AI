"""S8.7B post-freeze comparison: run after the freeze, explains differences, never changes a frozen quantity."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_stairs_s8_7b"
PF = PKG / "post_freeze"
MANIFEST = PKG / "16_S8_7B_FREEZE_MANIFEST.json"


def rows(name):
    with open(PF / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_freeze_intact_and_comparison_downstream():
    DR.verify_frozen(MANIFEST, ROOT)
    s = json.loads((PF / "03_POST_FREEZE_SUMMARY.json").read_text(encoding="utf-8"))
    assert s["frozen_manifest_sha256"] == hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    src = (PKG / "build_s8_7b.py").read_text(encoding="utf-8")
    assert "BOQ_LINES_V3B" not in src and "STAIR_ARCHITECTURAL_REGISTER" not in src and "post_freeze" not in src
    reg = (ROOT / "tests/structural_comparison_engine/rebar_product_registry.py").read_text(encoding="utf-8")
    assert '"research/alsenan_stairs_s8_7b/post_freeze/post_freeze_comparison.py"' in reg


def test_v3b_reproduced_and_classified():
    s = json.loads((PF / "03_POST_FREEZE_SUMMARY.json").read_text(encoding="utf-8"))
    assert s["v3b_reproduced_exactly"] and s["v3b_method_reproduced_m3"] == s["v3b_c_stair_commercial_m3"] == 5.2312
    assert s["v3b_risers"] == {"A1": 26, "A2": 24}
    r = rows("01_POST_FREEZE_COMPARISON.csv")
    assert all(x["CLASS"] and x["EXPLANATION"] for x in r)
    refs = {x["REFERENCE"] for x in r}
    assert {"V3b C-STAIR (GF)", "V3b riser count A1", "V3b riser count A2", "R5 stair register"} <= refs
    rep = {x["STOREY_RUN"]: x for x in rows("02_V3B_VS_OWNER_SCENARIO.csv")}
    assert (rep["A1"]["V3B_RISERS"], rep["A1"]["OWNER_RISERS"], rep["A2"]["V3B_RISERS"], rep["A2"]["OWNER_RISERS"]) == \
        ("26", "28", "24", "27")


def test_nothing_released():
    s = json.loads((PF / "03_POST_FREEZE_SUMMARY.json").read_text(encoding="utf-8"))
    assert s["release_delta"] == {"concrete_m3": 0.0, "kg": 0.0}
    m = s["owner_scenario_main_stair_m3_by_waist"]
    assert m["150"] < m["160"] < m["175"] < m["200"]


def test_rerun_identical():
    before = {p.name: p.read_bytes() for p in PF.iterdir() if p.is_file() and p.suffix != ".py"}
    subprocess.run([sys.executable, "-I", str(PF / "post_freeze_comparison.py")], check=True, cwd=ROOT,
                   capture_output=True)
    after = {p.name: p.read_bytes() for p in PF.iterdir() if p.is_file() and p.suffix != ".py"}
    assert before == after
